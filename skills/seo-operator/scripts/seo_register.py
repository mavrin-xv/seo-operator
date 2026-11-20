#!/usr/bin/env python3
"""Register: the ledger of every action, and the verdict weeks later.

    add    <site> --target /menu/cold-brew --kind title-meta --note "new title"
           pins the baseline (clicks, impressions, CTR, position for the target,
           plus site totals as a control) from the latest gsc snapshot.
    list   <site>
    verify <site>
           for every open action older than verify_min_days (21), compares the
           latest snapshot with the baseline and writes a verdict:
             worked / backfired  |delta clicks| >= max(3, 15% of baseline),
                                 after removing the site-wide trend
             no change           anything smaller
             fixed / still open  link-fix and sitemap actions, read from
                                 the latest crawl instead of clicks
             unverifiable        no baseline, target left the data, or the
                                 two windows have different lengths
           Losers stay in the ledger. That is the point of it.

Targets are paths (/menu/cold-brew) or "query: <text>". Git Bash turns a bare
/path into C:/Program Files/Git/path; such targets are refused. Pass
MSYS_NO_PATHCONV=1 or write the target without the leading slash.
"""
import argparse
import datetime
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import seo_common as C  # noqa: E402

LANES = {"title-meta": "ctr", "content": "content", "link-fix": "links", "internal-link": "links",
         "schema": "aeo", "speed": "tech", "sitemap": "tech", "other": "other"}


def clean_target(t):
    t = t.strip()
    if re.match(r"^[A-Za-z]:[\\/]", t) or "/Git/" in t:
        sys.exit("target %r looks like a path mangled by Git Bash. Use MSYS_NO_PATHCONV=1 "
                 "or drop the leading slash." % t)
    if t.startswith("query:") or t in ("site-wide", "sitemap.xml"):
        return t
    if "://" in t:
        t = t.split("://", 1)[1].partition("/")[2]
    t = "/" + t.lstrip("/")
    return t.split("#")[0].rstrip("/") or "/"


def row_for(snap, target):
    if target.startswith("query:"):
        key, rows = target[6:].strip(), snap.get("queries", [])
    else:
        key, rows = target, snap.get("pages", [])
    for r in rows:
        if r["key"] == key:
            return r
    return None


def cmd_add(a):
    root = C.state_root(a.state)
    d = C.site_dir(root, a.site)
    target = clean_target(a.target)
    stem, snap = C.latest(root, a.site, "gsc")
    base = None
    if snap:
        r = row_for(snap, target)
        if r:
            base = {k: r[k] for k in ("clicks", "impressions", "ctr", "position")}
    rec = {"id": "%s-%s" % (C.today(a.today).isoformat(), len(C.load_jsonl(os.path.join(d, "outcomes.jsonl"))) + 1),
           "date": C.today(a.today).isoformat(), "target": target, "kind": a.kind,
           "lane": LANES.get(a.kind, "other"), "note": a.note, "status": "open",
           "baseline": base, "baseline_snapshot": stem,
           "baseline_window_days": snap["window"]["days"] if snap else None,
           "control": dict(snap["totals"]) if snap else None}
    C.append_jsonl(os.path.join(d, "outcomes.jsonl"), rec)
    print("registered %s %s (%s)" % (rec["id"], target, a.kind))
    if not base and a.kind not in CRAWL_KINDS:
        print("warn: no baseline row for this target in the latest snapshot; it will verify as unverifiable"
              " unless it appears later. Run seo_measure.py first if the snapshot is old.")


def cmd_list(a):
    root = C.state_root(a.state)
    recs = C.load_jsonl(os.path.join(C.site_dir(root, a.site), "outcomes.jsonl"))
    if not recs:
        print("no actions registered")
        return
    for r in recs:
        v = r.get("verdict") or r["status"]
        print("%-14s %-10s %-13s %-12s %s" % (r["id"], r["date"], r["kind"], v, r["target"]))


CRAWL_KINDS = ("link-fix", "sitemap")


def judge_crawl(rec, health):
    """Link and sitemap fixes are checked against the crawl, not clicks."""
    if not health:
        return "unverifiable", "no crawl after the change", None
    t = rec["target"]
    hit = [x for x in health["issues"]["broken"] + health["issues"]["redirects"]
           if (x["url"].split("://", 1)[-1].partition("/")[2].rstrip("/") or "") == t.strip("/")]
    if t == "sitemap.xml":
        n = health["counts"]["not_in_sitemap"]
        return ("fixed" if n == 0 else "still open"), "%d indexable pages off the sitemap" % n, None
    if hit:
        return "still open", "still in the crawl as %s" % hit[0].get("status", "redirect"), None
    return "fixed", "no longer broken or redirected in the crawl", None


def judge(rec, snap, th):
    base = rec.get("baseline")
    if not base:
        return "unverifiable", "no baseline was pinned", None
    if rec.get("baseline_window_days") and snap["window"]["days"] != rec["baseline_window_days"]:
        return "unverifiable", "window %d days vs baseline %d days" % (
            snap["window"]["days"], rec["baseline_window_days"]), None
    now = row_for(snap, rec["target"])
    if not now:
        return "unverifiable", "target is not in the latest data", None
    raw = now["clicks"] - base["clicks"]
    trend = 0.0
    ctl = rec.get("control")
    if ctl and ctl.get("clicks"):
        trend = snap["totals"]["clicks"] / ctl["clicks"] - 1.0
    expected = base["clicks"] * (1 + trend)
    adj = now["clicks"] - expected
    delta = {"clicks": raw, "clicks_vs_trend": round(adj, 1), "site_trend_pct": round(trend * 100, 1),
             "impressions": now["impressions"] - base["impressions"],
             "position": round(now["position"] - base["position"], 1),
             "ctr_pp": round((now["ctr"] - base["ctr"]) * 100, 2)}
    bar = max(3, 0.15 * base["clicks"])
    if base["clicks"] < 5 and abs(adj) < 5:
        return "no change", "baseline under 5 clicks; too small to call", delta
    if adj >= bar:
        return "worked", "+%.1f clicks beyond the site trend (bar %.1f)" % (adj, bar), delta
    if adj <= -bar:
        return "backfired", "%.1f clicks against the site trend (bar %.1f)" % (adj, bar), delta
    return "no change", "within %.1f clicks of the site trend" % bar, delta


def cmd_verify(a):
    root = C.state_root(a.state)
    cfg = C.load_config(root, a.site)
    d = C.site_dir(root, a.site)
    path = os.path.join(d, "outcomes.jsonl")
    recs = C.load_jsonl(path)
    stem, snap = C.latest(root, a.site, "gsc")
    if not snap:
        sys.exit("no gsc snapshot to verify against")
    _, hs = C.latest(root, a.site, "health")
    today = C.today(a.today)
    wait = cfg["thresholds"]["verify_min_days"]
    changed = 0
    for r in recs:
        if r["status"] != "open":
            continue
        age = (today - datetime.date.fromisoformat(r["date"])).days
        snap_end = datetime.date.fromisoformat(snap["window"]["end"])
        if age < wait:
            print("%-14s wait %d more days" % (r["id"], wait - age))
            continue
        if r["kind"] not in CRAWL_KINDS and (snap_end - datetime.date.fromisoformat(r["date"])).days < wait:
            print("%-14s latest snapshot ends %s, too soon after the change; measure again" % (r["id"], snap_end))
            continue
        if r["kind"] in CRAWL_KINDS:
            verdict, why, delta = judge_crawl(r, hs)
        else:
            verdict, why, delta = judge(r, snap, cfg["thresholds"])
        r.update({"status": "verified", "verdict": verdict, "why": why, "delta": delta,
                  "verified_on": today.isoformat(), "verified_snapshot": stem})
        changed += 1
        print("%-14s %-12s %s  (%s)" % (r["id"], verdict.upper(), r["target"], why))
    if changed:
        with open(path, "w", encoding="utf-8") as fh:
            for r in recs:
                fh.write(C.json.dumps(r, ensure_ascii=False) + "\n")
    print("verified %d action(s) against %s" % (changed, stem))


def main():
    C.utf8_stdout()
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0], epilog=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    com = argparse.ArgumentParser(add_help=False)
    com.add_argument("--state"); com.add_argument("--today", help="pretend today is this date")
    sub = ap.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("add", parents=[com]); p.add_argument("site"); p.add_argument("--target", required=True)
    p.add_argument("--kind", required=True, choices=sorted(LANES)); p.add_argument("--note", default="")
    p.set_defaults(fn=cmd_add)
    p = sub.add_parser("list", parents=[com]); p.add_argument("site"); p.set_defaults(fn=cmd_list)
    p = sub.add_parser("verify", parents=[com]); p.add_argument("site"); p.set_defaults(fn=cmd_verify)
    a = ap.parse_args()
    a.fn(a)


if __name__ == "__main__":
    main()
