#!/usr/bin/env python3
"""Report: one markdown page per run, in plain English, from the state folder.

Sections: the numbers (with the change against the previous snapshot of the
same window length), the vitals, the top of the board, what the ledger says
worked and what did not, open items for the owner, and what was not measured.

A missing input is reported as missing. The script never prints "?" or a zero
in place of a number it does not have.

Writes <state>/<site>/reports/<date>.md and prints the path.
"""
import argparse
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import seo_common as C  # noqa: E402
from seo_state import open_items  # noqa: E402


def pct(now, was):
    if was in (None, 0) or now is None:
        return "n/a"
    return "%+.0f%%" % ((now / was - 1) * 100)


def main():
    C.utf8_stdout()
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0], epilog=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("site")
    ap.add_argument("--state")
    ap.add_argument("--today")
    ap.add_argument("--top", type=int, default=5)
    a = ap.parse_args()

    root = C.state_root(a.state)
    cfg = C.load_config(root, a.site)
    d = C.site_dir(root, a.site)
    today = C.today(a.today)
    gs = C.snapshots(root, a.site, "gsc")
    hs = C.snapshots(root, a.site, "health")
    _, board = C.latest(root, a.site, "candidates")
    recs = C.load_jsonl(os.path.join(d, "outcomes.jsonl"))
    out, missing = ["# SEO run: %s, %s" % (cfg["domain"], today), ""], []

    out += ["## Numbers", ""]
    if gs:
        stem, g = gs[-1]
        prev = next((s for _, s in reversed(gs[:-1]) if s["window"]["days"] == g["window"]["days"]), None)
        t, p = g["totals"], (prev or {}).get("totals", {})
        out += ["Window %s to %s (%d days, source: %s)." % (g["window"]["start"], g["window"]["end"],
                                                            g["window"]["days"], g["source"]), "",
                "| Metric | Now | Previous | Change |", "|---|---|---|---|"]
        for k, label in (("clicks", "Clicks"), ("impressions", "Impressions")):
            out.append("| %s | %d | %s | %s |" % (label, t[k], p.get(k, "n/a"), pct(t[k], p.get(k))))
        out.append("| CTR | %.2f%% | %s | |" % (t["ctr"] * 100, "%.2f%%" % (p["ctr"] * 100) if p else "n/a"))
        out.append("| Avg position | %s | %s | |" % (t["position"], p.get("position", "n/a")))
        if not prev:
            out += ["", "No earlier snapshot of the same length, so no change is shown."]
    else:
        missing.append("Search Console: no gsc snapshot. Run seo_measure.py.")
        out.append("No Search Console data yet.")
    out.append("")

    out += ["## Vitals", ""]
    if hs:
        stem, h = hs[-1]
        c, s = h["counts"], h["speed"]
        out += ["Crawl %s, %d pages, %s." % (stem, c["pages"],
                "complete" if h["complete"] else "capped at %d pages" % h["cap"]), "",
                "| Vital | Reading |", "|---|---|",
                "| Speed | TTFB p50 %s ms, p90 %s ms; HTML p50 %s KB (%d crawl%s on file) |"
                % (s["ttfb_p50"], s["ttfb_p90"], s["html_kb_p50"], len(hs), "" if len(hs) == 1 else "s"),
                "| Link health | %d broken, %d redirects, %d chains, orphans %s |"
                % (c["broken"], c["redirects"], c["redirect_chains"],
                   "not measured (capped crawl)" if c["orphans"] is None else c["orphans"]),
                "| Indexing | %d noindex in sitemap, %d sitemap URLs not 200, %d bad canonicals, soft 404 %s |"
                % (c["noindex_in_sitemap"], c["sitemap_non_200"], c["canonical_to_bad_target"],
                   "yes" if h["soft_404"]["soft_404"] else "no"),
                "| Snippets | %d pages without description, %d without exactly one H1 |"
                % (c["no_description"], c["bad_h1"])]
        if gs:
            out.append("| Relevance and click rate | %d CTR gaps, %d striking-distance queries |"
                       % (len(gs[-1][1]["ctr_gap"]), len(gs[-1][1]["strike"])))
        blocked = [b for b, v in h["robots"]["bots"].items() if v["state"] == "BLOCKED" and v["job"] != "training"]
        if blocked:
            out += ["", "robots.txt blocks search or user-fetch crawlers: %s." % ", ".join(blocked)]
        if h["robots"].get("cdn_managed_block"):
            out += ["", "robots.txt contains a CDN-managed block; check the CDN bot settings too."]
        if len(hs) < 3:
            missing.append("Speed is not ranked until 3 crawls exist (have %d)." % len(hs))
        if not h["complete"]:
            missing.append("Orphans: crawl was capped, raise --max to measure them.")
    else:
        missing.append("Technical vitals: no health snapshot. Run seo_crawl.py.")
        out.append("No crawl yet.")
    out.append("")

    out += ["## Best use of the next hour", ""]
    if board and board.get("candidates"):
        out += ["| # | Score | Kind | Target | Why |", "|---|---|---|---|---|"]
        for i, c in enumerate(board["candidates"][:a.top], 1):
            out.append("| %d | %.1f | %s | %s | %s |" % (i, c["score"], c["kind"], c["target"], c["why"]))
        out += ["", "Board from %s. Score = clicks at stake x share usually recovered / operator hours."
                % board["date"]]
    elif board:
        out.append("The board is empty. Nothing is worth an hour today, and that is a valid result.")
    else:
        missing.append("Board: run seo_select.py.")
        out.append("No board yet.")
    out.append("")

    out += ["## Ledger", ""]
    done = [r for r in recs if r["status"] == "verified"]
    openr = [r for r in recs if r["status"] == "open"]
    if recs:
        tally = {}
        for r in done:
            tally[r["verdict"]] = tally.get(r["verdict"], 0) + 1
        out.append("%d actions, %d open, verified: %s." % (
            len(recs), len(openr), ", ".join("%s %d" % kv for kv in sorted(tally.items())) or "none yet"))
        if done:
            out += ["", "| Action | Target | Verdict | Clicks vs trend | Why |", "|---|---|---|---|---|"]
            for r in done[-10:]:
                dl = r.get("delta") or {}
                out.append("| %s %s | %s | %s | %s | %s |" % (
                    r["date"], r["kind"], r["target"], r["verdict"],
                    dl.get("clicks_vs_trend", "n/a"), r["why"]))
    else:
        out.append("No actions registered yet.")
    out.append("")

    items = open_items(os.path.join(d, "needs-you.md"))
    out += ["## Needs the owner", ""] + (items or ["Nothing open."]) + [""]
    out += ["## Not measured", ""] + (["- " + m for m in missing] or ["Everything above had data."]) + [""]

    path = os.path.join(d, "reports", today.isoformat() + ".md")
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as fh:
        fh.write("\n".join(out))
    print("saved %s" % path)


if __name__ == "__main__":
    main()
