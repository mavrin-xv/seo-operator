#!/usr/bin/env python3
"""Sort Search Console queries into intent buckets and show where the clicks are.

Buckets (first match wins, in this order):
  brand          contains a brand term (--brand, repeatable)
  near-me        "near me", "nearby", "open now", "closest"
  town+service   contains a town from --towns and a service word
  informational  starts with how / what / why / when / can / is / does / best way,
                 "best X for", or contains vs / recipe / guide / ideas / ratio / tips
  service        everything else (the commercial core)

Per bucket: queries, impressions, clicks, CTR and impression-weighted
position (a plain average lets 1-impression queries at position 90 drown out
the queries that matter). Then the top queries per bucket, and the
striking-distance list (positions 4-20 with impressions over --min-impr).

Input: the Queries.csv export from the Search Console UI (Top queries,
Clicks, Impressions, CTR, Position) or any CSV with query, clicks,
impressions, position columns.

Examples:
    python3 query_buckets.py Queries.csv --brand acme
    python3 query_buckets.py Queries.csv --brand acme --towns "portland,salem" --format json
Exit codes: 0 ok, 2 bad input.
"""
import argparse
import csv
import json
import re
import sys

NEAR = re.compile(r"\b(near me|nearby|open now|closest|near by)\b", re.I)
INFO = re.compile(r"^(how|what|why|when|where|can|is|are|does|do|should|which|best way)\b|"
                  r"\b(vs|versus|recipe|guide|ideas|meaning|difference|tips|ratio|tutorial)\b|^best .+ for\b",
                  re.I)


def num(v):
    v = (v or "0").strip().replace(",", "")
    return float(v[:-1]) / 100 if v.endswith("%") else float(v or 0)


def read(path):
    with open(path, encoding="utf-8-sig", newline="") as fh:
        rows = list(csv.reader(fh))
    if not rows:
        sys.exit(2)
    head = [h.strip().lower() for h in rows[0]]

    def col(*names):
        for n in names:
            for i, h in enumerate(head):
                if h == n or h.startswith(n):
                    return i
        return None
    qi = col("query", "top queries", "queries")
    qi = 0 if qi is None else qi
    ci, ii, pi = col("clicks"), col("impressions"), col("position")
    if None in (ci, ii, pi):
        print("CSV needs clicks, impressions and position columns", file=sys.stderr)
        sys.exit(2)
    out = []
    for r in rows[1:]:
        if len(r) <= max(qi, ci, ii, pi) or not r[qi].strip():
            continue
        out.append({"query": r[qi].strip(), "clicks": num(r[ci]), "impressions": num(r[ii]),
                    "position": num(r[pi])})
    return out


def bucket(q, brands, towns):
    s = q.lower()
    if any(b in s for b in brands):
        return "brand"
    if NEAR.search(s):
        return "near-me"
    if towns and any(re.search(r"\b%s" % re.escape(t), s) for t in towns):
        return "town+service"
    if INFO.search(s):
        return "informational"
    return "service"


def main():
    for s in (sys.stdout, sys.stderr):
        try:
            s.reconfigure(encoding="utf-8")
        except (AttributeError, ValueError):
            pass
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0], epilog=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("csv")
    ap.add_argument("--brand", action="append", default=[], help="brand term (repeatable)")
    ap.add_argument("--towns", default="", help="comma-separated towns or areas you serve")
    ap.add_argument("--top", type=int, default=5)
    ap.add_argument("--min-impr", type=int, default=50, help="impressions floor for striking distance")
    ap.add_argument("--format", choices=("text", "json"), default="text")
    a = ap.parse_args()
    try:
        rows = read(a.csv)
    except OSError as e:
        print("cannot read %s: %s" % (a.csv, e), file=sys.stderr)
        sys.exit(2)
    brands = [b.lower() for b in a.brand]
    towns = [t.strip().lower() for t in a.towns.split(",") if t.strip()]
    order = ["brand", "near-me", "town+service", "informational", "service"]
    agg = {b: {"queries": 0, "impressions": 0.0, "clicks": 0.0, "_wpos": 0.0, "top": []} for b in order}
    for r in rows:
        b = bucket(r["query"], brands, towns)
        r["bucket"] = b
        g = agg[b]
        g["queries"] += 1
        g["impressions"] += r["impressions"]
        g["clicks"] += r["clicks"]
        g["_wpos"] += r["position"] * r["impressions"]
        g["top"].append(r)
    total_imp = sum(g["impressions"] for g in agg.values()) or 1
    for b, g in agg.items():
        g["ctr"] = round(g["clicks"] / g["impressions"], 4) if g["impressions"] else 0
        g["position_weighted"] = round(g["_wpos"] / g["impressions"], 1) if g["impressions"] else None
        g["share_of_impressions"] = round(g["impressions"] / total_imp, 3)
        g["top"] = sorted(g["top"], key=lambda r: -r["impressions"])[:a.top]
        del g["_wpos"]
    strike = sorted([r for r in rows if 4 <= r["position"] <= 20 and r["impressions"] >= a.min_impr
                     and r["bucket"] != "brand"], key=lambda r: -r["impressions"])
    if a.format == "json":
        print(json.dumps({"buckets": agg, "striking_distance": strike}, indent=1, ensure_ascii=False))
        return
    print("%-14s %7s %9s %7s %6s %8s %6s" % ("bucket", "queries", "impr", "clicks", "CTR", "pos(w)", "share"))
    for b in order:
        g = agg[b]
        if not g["queries"]:
            continue
        print("%-14s %7d %9.0f %7.0f %5.1f%% %8s %5.0f%%" % (
            b, g["queries"], g["impressions"], g["clicks"], g["ctr"] * 100,
            g["position_weighted"], g["share_of_impressions"] * 100))
    for b in order:
        if agg[b]["top"]:
            print("\n%s: top by impressions" % b)
            for r in agg[b]["top"]:
                print("  %6.0f impr  %4.0f clicks  pos %5.1f  %s" % (r["impressions"], r["clicks"], r["position"], r["query"]))
    print("\nstriking distance (positions 4-20, %d+ impressions, brand excluded): %d" % (a.min_impr, len(strike)))
    for r in strike[:15]:
        print("  pos %5.1f  %6.0f impr  [%s]  %s" % (r["position"], r["impressions"], r["bucket"], r["query"]))
    if not brands:
        print("\nnote: no --brand given, brand searches are mixed into the other buckets")


if __name__ == "__main__":
    main()
