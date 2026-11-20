#!/usr/bin/env python3
"""Select: rank every possible action on one scale and print the board.

    score = clicks_at_stake x RECOVER[kind] / EFFORT[kind]

clicks_at_stake comes from the latest gsc snapshot (CTR gaps, striking-distance
queries) or a flat floor for technical issues from the latest health snapshot.
EFFORT is operator hours, RECOVER the share of the stake a fix usually wins
back. Both tables are starting guesses; tune them in config.json under
"effort" and "recover" once your own outcomes.jsonl has verdicts.

Skipped on purpose:
  * a target acted on in the same lane within cooldown_days (60)
  * speed work until at least 3 health snapshots exist (one fast reading after
    a deploy is usually the CDN cache warming, not a real gain)
  * CTR work below position ctr_max_position (15): rank sets CTR there
  * CTR work on ctr_skip_paths (default the home page, whose CTR is set by
    brand searches, not by its snippet)

Money pages (paths starting with an entry in money_paths) get x1.5.

Writes <state>/<site>/candidates/<date>.json and prints the top N.
An empty board is a valid result: log it with seo_state.py log --picked none.
"""
import argparse
import datetime
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import seo_common as C  # noqa: E402

EFFORT = {"title-meta": 0.25, "link-fix": 0.15, "internal-link": 0.5, "schema": 0.4,
          "content": 3.0, "speed": 4.0, "sitemap": 0.3}
RECOVER = {"title-meta": .35, "link-fix": 1.0, "internal-link": .25, "schema": .10,
           "content": .30, "speed": .15, "sitemap": .20}
LANE = {"title-meta": "ctr", "content": "content", "link-fix": "links", "internal-link": "links",
        "schema": "aeo", "speed": "tech", "sitemap": "tech"}


def cooled(outcomes, target, lane, today, days):
    for o in outcomes:
        if o.get("target") == target and o.get("lane") == lane:
            d = datetime.date.fromisoformat(o["date"])
            if (today - d).days < days:
                return True
    return False


def build(cfg, gsc, health, n_health, outcomes, today):
    th = cfg["thresholds"]
    effort = dict(EFFORT, **(cfg.get("effort") or {}))
    recover = dict(RECOVER, **(cfg.get("recover") or {}))
    money = cfg.get("money_paths") or []
    cands, skipped = [], []

    def add(kind, target, stake, why, evidence):
        lane = LANE[kind]
        if cooled(outcomes, target, lane, today, th["cooldown_days"]):
            skipped.append({"kind": kind, "target": target, "reason": "cooldown"})
            return
        boost = 1.5 if any(target.startswith(m) for m in money) else 1.0
        score = stake * recover[kind] / effort[kind] * boost
        cands.append({"kind": kind, "lane": lane, "target": target, "score": round(score, 1),
                      "clicks_at_stake": round(stake, 1), "effort_h": effort[kind],
                      "money_page": boost > 1, "why": why, "evidence": evidence})

    ctr_skip = cfg.get("ctr_skip_paths", ["/"])
    if gsc:
        for p in gsc["ctr_gap"]:
            if p["key"] in ctr_skip:
                skipped.append({"kind": "title-meta", "target": p["key"],
                                "reason": "in ctr_skip_paths (brand searches set a home page's CTR)"})
                continue
            if p["position"] <= th["ctr_max_position"]:
                add("title-meta", p["key"], p["clicks_left"],
                    "CTR %.1f%% vs %.1f%% expected at position %.1f"
                    % (p["ctr"] * 100, p["expected_ctr"] * 100, p["position"]),
                    {k: p[k] for k in ("impressions", "clicks", "position")})
        for q in gsc["strike"][:15]:
            gain = q["impressions"] * max(0.0, C.expected_ctr(5) - q["ctr"])  # top-5 CTR
            if gain < 5:
                continue
            add("content", "query: " + q["key"], gain,
                "query at position %.1f with %d impressions; top-5 would earn ~%.0f more clicks"
                % (q["position"], q["impressions"], gain),
                {k: q[k] for k in ("impressions", "clicks", "position")})

    if health:
        iss, imp = health["issues"], {}
        if gsc:
            imp = {p["key"]: p["impressions"] for p in gsc["pages"]}
        for b in iss["broken"]:
            add("link-fix", C_path(b["url"]), 20, "returns %s; internal pages linking to it: %d" % (b["status"], b["inbound"]),
                {"status": b["status"]})
        for r in iss["internal_links_to_redirects"]:
            add("link-fix", C_path(r), 10, "internal links point at a redirect", {})
        if iss["orphans"]:
            for u in iss["orphans"][:20]:
                add("internal-link", C_path(u), 15, "no internal page links here", {})
        if n_health >= 3:
            slow = iss["slow"]
            if len(slow) >= 10:
                add("speed", "site-wide", 8 * len(slow),
                    "%d pages over %d ms TTFB in the latest of %d crawls" % (len(slow), th["ttfb_ms"], n_health),
                    {"p50": health["speed"]["ttfb_p50"], "p90": health["speed"]["ttfb_p90"]})
        elif iss["slow"]:
            skipped.append({"kind": "speed", "target": "site-wide",
                            "reason": "only %d health snapshot(s); need 3" % n_health})
        for u in iss["no_description"][:20]:
            add("title-meta", C_path(u), 12, "no meta description", {})
        for u in iss["no_schema"]:
            if imp.get(C_path(u), 0) >= 100:
                add("schema", C_path(u), 18, "no JSON-LD on a page with %d impressions" % imp[C_path(u)], {})
        off = iss["not_in_sitemap"]
        if len(off) >= 5:
            add("sitemap", "sitemap.xml", 5 * len(off), "%d indexable pages missing from the sitemap" % len(off), {})

    best = {}
    for c in cands:  # one row per target and kind: keep the strongest reason
        k = (c["kind"], c["target"])
        if k not in best or best[k]["score"] < c["score"]:
            best[k] = c
    board = sorted(best.values(), key=lambda c: -c["score"])
    uniq = {(x["kind"], x["target"], x["reason"]): x for x in skipped}
    return board, list(uniq.values())


def C_path(u):
    if "://" in u:
        u = "/" + u.split("://", 1)[1].partition("/")[2]
    return u.rstrip("/") or "/"


def main():
    C.utf8_stdout()
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0], epilog=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("site")
    ap.add_argument("--state")
    ap.add_argument("--top", type=int, default=10)
    ap.add_argument("--today", help="pretend today is this date (for reproducible runs)")
    a = ap.parse_args()

    root = C.state_root(a.state)
    cfg = C.load_config(root, a.site)
    d = C.site_dir(root, a.site)
    _, gsc = C.latest(root, a.site, "gsc")
    hs = C.snapshots(root, a.site, "health")
    health = hs[-1][1] if hs else None
    if not gsc and not health:
        sys.exit("nothing measured yet: run seo_measure.py and seo_crawl.py first")
    today = C.today(a.today)
    outcomes = C.load_jsonl(os.path.join(d, "outcomes.jsonl"))
    board, skipped = build(cfg, gsc, health, len(hs), outcomes, today)
    C.write_json(os.path.join(d, "candidates", today.isoformat() + ".json"),
                 {"site": a.site, "date": today.isoformat(), "candidates": board, "skipped": skipped,
                  "inputs": {"gsc": bool(gsc), "health_snapshots": len(hs)}})

    print("board for %s on %s (%d candidates, %d skipped)" % (a.site, today, len(board), len(skipped)))
    if not gsc:
        print("note: no Search Console snapshot, only technical rows are ranked")
    if not board:
        print("nothing worth an hour today. Log it: seo_state.py log %s --picked none" % a.site)
        return
    print("%-4s %-7s %-13s %-7s %s" % ("#", "score", "kind", "lane", "target / why"))
    for i, c in enumerate(board[:a.top], 1):
        print("%-4d %-7.1f %-13s %-7s %s%s" % (i, c["score"], c["kind"], c["lane"], c["target"],
                                              "  [money page]" if c["money_page"] else ""))
        print("%26s %s" % ("", c["why"]))
    for s in skipped[:5]:
        print("skipped %s %s: %s" % (s["kind"], s["target"], s["reason"]))


if __name__ == "__main__":
    main()
