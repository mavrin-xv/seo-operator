#!/usr/bin/env python3
"""Compare two rounds of AI-answer checks and say what moved.

You (or a script) ask each AI assistant the same prompts on two dates and
record one row per answer. This script compares the rounds and reports, per
engine and prompt:

  GAINED         absent before, mentioned or cited now (or mentioned -> cited)
  LOST           the reverse
  HELD           cited both times
  NO CHANGE      same state both times (absent/absent, mentioned/mentioned)
  INDETERMINATE  either round has no row, an error, or a refusal: not compared

Share of model = (CITED + 0.5 x MENTIONED) / answers observed, per engine
and overall. Errors and missing rows do not count as observed, so a round
where half the checks failed is not read as a drop.

Input CSV columns: engine, prompt, status, cited_url, competitors
  status       CITED (your URL is a source), MENTIONED (named, not linked),
               ABSENT, ERROR (no answer, refusal, rate limit)
  competitors  optional, semicolon-separated names that appeared instead

AI answers vary between runs of the same prompt. One flip on one prompt is
noise; read the totals, and run each prompt 2-3 times per round if you can
(rows with the same engine and prompt are combined: the best state wins).

Examples:
    python3 aeo_diff.py round-2026-10-20.csv round-2026-11-17.csv
    python3 aeo_diff.py before.csv after.csv --format json
Exit codes: 0 ok, 2 bad input.
"""
import argparse
import csv
import json
import sys

RANK = {"ABSENT": 0, "MENTIONED": 1, "CITED": 2}


def read(path):
    try:
        with open(path, encoding="utf-8-sig", newline="") as fh:
            rows = list(csv.DictReader(fh))
    except OSError as e:
        print("cannot read %s: %s" % (path, e), file=sys.stderr)
        sys.exit(2)
    if rows and not {"engine", "prompt", "status"} <= set(rows[0]):
        print("%s needs columns engine, prompt, status" % path, file=sys.stderr)
        sys.exit(2)
    out = {}
    for r in rows:
        k = (r["engine"].strip(), r["prompt"].strip())
        st = r["status"].strip().upper()
        cur = out.get(k)
        if st not in RANK:
            out.setdefault(k, {"status": "ERROR", "competitors": set()})
            continue
        comp = set(c.strip() for c in (r.get("competitors") or "").split(";") if c.strip())
        if cur is None or cur["status"] == "ERROR" or RANK[st] > RANK[cur["status"]]:
            out[k] = {"status": st, "competitors": comp | (cur or {}).get("competitors", set())}
        else:
            cur["competitors"] |= comp
    return out


def share(rnd, engine=None):
    obs = [v["status"] for (e, _), v in rnd.items() if v["status"] in RANK and (engine is None or e == engine)]
    if not obs:
        return None, 0
    pts = sum(1.0 if s == "CITED" else 0.5 if s == "MENTIONED" else 0 for s in obs)
    return round(pts / len(obs), 3), len(obs)


def main():
    for s in (sys.stdout, sys.stderr):
        try:
            s.reconfigure(encoding="utf-8")
        except (AttributeError, ValueError):
            pass
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0], epilog=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("before")
    ap.add_argument("after")
    ap.add_argument("--format", choices=("text", "json"), default="text")
    a = ap.parse_args()
    b, n = read(a.before), read(a.after)
    rows = []
    for k in sorted(set(b) | set(n)):
        s0 = b.get(k, {}).get("status", "MISSING")
        s1 = n.get(k, {}).get("status", "MISSING")
        if s0 not in RANK or s1 not in RANK:
            v = "INDETERMINATE"
        elif RANK[s1] > RANK[s0]:
            v = "GAINED"
        elif RANK[s1] < RANK[s0]:
            v = "LOST"
        elif s1 == "CITED":
            v = "HELD"
        else:
            v = "NO CHANGE"
        new_comp = sorted(n.get(k, {}).get("competitors", set()) - b.get(k, {}).get("competitors", set()))
        rows.append({"engine": k[0], "prompt": k[1], "before": s0, "after": s1, "verdict": v,
                     "new_competitors": new_comp})
    engines = sorted(set(e for e, _ in set(b) | set(n)))
    som = {e: {"before": share(b, e), "after": share(n, e)} for e in engines}
    som["all"] = {"before": share(b), "after": share(n)}
    count = {}
    for r in rows:
        count[r["verdict"]] = count.get(r["verdict"], 0) + 1
    if a.format == "json":
        print(json.dumps({"rows": rows, "share_of_model": som, "counts": count}, indent=1, ensure_ascii=False))
        return
    order = ["LOST", "GAINED", "INDETERMINATE", "HELD", "NO CHANGE"]
    for v in order:
        sel = [r for r in rows if r["verdict"] == v]
        if not sel:
            continue
        print("%s (%d)" % (v, len(sel)))
        for r in sel:
            extra = "  new names: %s" % ", ".join(r["new_competitors"]) if r["new_competitors"] else ""
            print("  %-11s %-9s -> %-9s %s%s" % (r["engine"], r["before"], r["after"], r["prompt"], extra))
    print("\nshare of model (CITED + 0.5 x MENTIONED over answers observed)")
    for e in engines + ["all"]:
        (s0, n0), (s1, n1) = som[e]["before"], som[e]["after"]
        f = lambda s: "-" if s is None else "%.0f%%" % (s * 100)
        print("  %-11s %5s (%d) -> %5s (%d)" % (e, f(s0), n0, f(s1), n1))
    if count.get("INDETERMINATE"):
        print("\nnote: %d pair(s) not compared because a round had no usable answer" % count["INDETERMINATE"])


if __name__ == "__main__":
    main()
