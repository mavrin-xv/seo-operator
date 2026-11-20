#!/usr/bin/env python3
"""Per-site memory for the SEO operator: create it, read it, log a run.

    init  <site> --domain acme-coffee.com [--property sc-domain:acme-coffee.com]
          creates <state>/<site>/ with config.json, the snapshot folders and the
          three working notes (truth.md, radar.md, needs-you.md). Never overwrites.
    show  <site>
          prints what the operator knows: last measure, last crawl, open and
          verified actions, the newest board, and open items in needs-you.md.
    log   <site> --picked "<target>" --note "..."   (or --picked none)
          appends one line to runs.jsonl. A run that picked nothing is logged too.

State folder: --state, else $SEO_STATE_DIR, else ./.seo
"""
import argparse
import datetime
import json
import os
import shutil
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import seo_common as C  # noqa: E402

_HERE = os.path.dirname(os.path.abspath(__file__))
# installed copy: <skills>/seo-operator/templates; repo checkout: <repo>/templates
TEMPLATES = next((p for p in (os.path.join(_HERE, "..", "templates"), os.path.join(_HERE, "..", "..", "..", "templates"))
                  if os.path.isdir(p)), os.path.join(_HERE, "..", "templates"))

NOTES = {
    "truth.md": "# Facts about {site}\n\nEvery fact the copy may use, with its source and the date it was checked.\n\n"
                "| Fact | Source | Verified |\n|---|---|---|\n",
    "radar.md": "# Demand radar for {site}\n\nQuery families worth watching. One line each: family, evidence, status.\n\n",
    "needs-you.md": "# Needs the owner ({site})\n\nDecisions the operator cannot make. Tick when done.\n\n",
}


def cmd_init(a):
    root = C.state_root(a.state)
    d = os.path.join(root, a.site)
    if os.path.exists(os.path.join(d, "config.json")):
        sys.exit("%s already has a config.json; edit it instead" % d)
    for sub in ("gsc", "health", "candidates", "reports"):
        os.makedirs(os.path.join(d, sub), exist_ok=True)
    domain = a.domain.replace("https://", "").replace("http://", "").strip("/")
    cfg = {
        "site": a.site,
        "domain": domain,
        "start_url": "https://%s/" % domain,
        "gsc_property": a.property or "sc-domain:%s" % domain,
        "hosts": [domain, "www." + domain],
        "brand_terms": [a.site.split("-")[0]],
        "money_paths": [],
        "exclude_paths": [],
        "thresholds": dict(C.DEFAULT_THRESHOLDS),
    }
    C.write_json(os.path.join(d, "config.json"), cfg)
    for name, body in NOTES.items():
        src = os.path.join(TEMPLATES, name)
        p = os.path.join(d, name)
        if os.path.exists(p):
            continue
        if os.path.exists(src):
            shutil.copy(src, p)
        else:
            with open(p, "w", encoding="utf-8") as fh:
                fh.write(body.format(site=a.site))
    print("created %s" % d)
    print("next: fill money_paths and brand_terms in config.json, then run seo_measure.py")


def open_items(path):
    if not os.path.exists(path):
        return []
    with open(path, encoding="utf-8") as fh:
        return [l.strip() for l in fh if l.strip().startswith("- [ ]")]


def cmd_show(a):
    root = C.state_root(a.state)
    cfg = C.load_config(root, a.site)
    d = C.site_dir(root, a.site)
    g, gs = C.latest(root, a.site, "gsc")
    h, hs = C.latest(root, a.site, "health")
    b, bs = C.latest(root, a.site, "candidates")
    print("site %s (%s), state %s" % (a.site, cfg["domain"], d))
    if gs:
        t = gs["totals"]
        print("last measure %s: window %s..%s, %s clicks, %s impressions"
              % (g, gs["window"]["start"], gs["window"]["end"], t["clicks"], t["impressions"]))
    else:
        print("last measure: never")
    if hs:
        c = hs["counts"]
        print("last crawl %s: %d pages, broken %d, redirects %d, orphans %s"
              % (h, c["pages"], c["broken"], c["redirects"],
                 "not measured" if c["orphans"] is None else c["orphans"]))
    else:
        print("last crawl: never")
    recs = C.load_jsonl(os.path.join(d, "outcomes.jsonl"))
    counts = {}
    for r in recs:
        k = r.get("verdict") or r.get("status")
        counts[k] = counts.get(k, 0) + 1
    print("actions: %d (%s)" % (len(recs), ", ".join("%s %d" % kv for kv in sorted(counts.items())) or "none"))
    if bs:
        top = (bs.get("candidates") or [])[:3]
        print("board %s, top %d:" % (b, len(top)))
        for r in top:
            print("  score %-6.1f %-13s %s" % (r["score"], r["kind"], r["target"]))
    runs = C.load_jsonl(os.path.join(d, "runs.jsonl"))
    if runs:
        r = runs[-1]
        print("last run %s picked %s" % (r["date"], r.get("picked") or "nothing"))
    items = open_items(os.path.join(d, "needs-you.md"))
    print("needs the owner: %d open" % len(items))
    for i in items[:5]:
        print("  " + i)


def cmd_log(a):
    root = C.state_root(a.state)
    d = C.site_dir(root, a.site)
    picked = None if (a.picked or "").lower() in ("", "none", "nothing") else a.picked
    rec = {"date": C.today(a.today).isoformat(),
           "at": datetime.datetime.now().isoformat(timespec="seconds"),
           "picked": picked, "note": a.note}
    C.append_jsonl(os.path.join(d, "runs.jsonl"), rec)
    print("logged run: picked %s" % (picked or "nothing (a valid result)"))


def main():
    C.utf8_stdout()
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0],
                                 epilog=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    com = argparse.ArgumentParser(add_help=False)
    com.add_argument("--state", help="state folder (default $SEO_STATE_DIR or ./.seo)")
    sub = ap.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("init", parents=[com]); p.add_argument("site"); p.add_argument("--domain", required=True)
    p.add_argument("--property"); p.set_defaults(fn=cmd_init)
    p = sub.add_parser("show", parents=[com]); p.add_argument("site"); p.set_defaults(fn=cmd_show)
    p = sub.add_parser("log", parents=[com]); p.add_argument("site"); p.add_argument("--picked", default="")
    p.add_argument("--note", default=""); p.add_argument("--today"); p.set_defaults(fn=cmd_log)
    a = ap.parse_args()
    a.fn(a)


if __name__ == "__main__":
    main()
