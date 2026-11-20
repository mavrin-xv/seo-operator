#!/usr/bin/env python3
"""Measure: turn Search Console data into a dated snapshot the operator can rank.

Three inputs, same output (<state>/<site>/gsc/<end-date>.json):

  --pages-csv / --queries-csv   the "Pages" and "Queries" tables exported from
                                the Search Console Performance report (CSV)
  --pages-json / --queries-json a JSON list of rows from any tool:
                                [{"key"|"page"|"query": ..., "clicks", "impressions", "ctr", "position"}]
  --api                         the Search Console API, with an OAuth access
                                token in $GSC_ACCESS_TOKEN (for example from
                                `gcloud auth print-access-token`) and the
                                property from config.json

The snapshot holds totals, pages, queries, and two derived lists the selector
reads: ctr_gap (pages losing clicks against the expected CTR for their
position) and strike (queries at positions 4-20 with real impressions).

Examples:
    python3 seo_measure.py acme-coffee --pages-csv Pages.csv --queries-csv Queries.csv --end 2026-11-18
    GSC_ACCESS_TOKEN=... python3 seo_measure.py acme-coffee --api --days 28
"""
import argparse
import csv
import datetime
import json
import os
import sys
import urllib.parse
import urllib.request

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import seo_common as C  # noqa: E402

API = "https://www.googleapis.com/webmasters/v3/sites/%s/searchAnalytics/query"


def num(v):
    if v is None or v == "":
        return 0.0
    if isinstance(v, (int, float)):
        return float(v)
    v = str(v).strip().replace(",", "")
    if v.endswith("%"):
        return float(v[:-1]) / 100.0
    return float(v)


def to_path(key, hosts):
    """Pages become bare paths so every layer joins on the same key."""
    if "://" not in key:
        return key
    rest = key.split("://", 1)[1]
    host, _, path = rest.partition("/")
    if hosts and host not in hosts:
        return None
    path = "/" + path.split("#")[0]
    return path.rstrip("/") or "/"


def norm_rows(rows, kind, hosts, exclude):
    out = []
    for r in rows:
        key = r.get("key") or r.get("page") or r.get("query")
        if key is None:
            keys = r.get("keys")
            key = keys[0] if keys else None
        if key is None:
            sys.exit("row without a key/page/query field: %r" % r)
        if kind == "pages":
            key = to_path(key, hosts)
            if key is None or any(key.startswith(x) for x in exclude):
                continue
        clicks, impr = num(r.get("clicks")), num(r.get("impressions"))
        ctr = num(r.get("ctr")) if r.get("ctr") not in (None, "") else (clicks / impr if impr else 0.0)
        out.append({"key": key, "clicks": int(clicks), "impressions": int(impr),
                    "ctr": round(ctr, 4), "position": round(num(r.get("position")), 1)})
    return out


def read_csv(path):
    """Search Console exports name the first column 'Top pages' or 'Top queries'."""
    with open(path, encoding="utf-8-sig", newline="") as fh:
        rows = list(csv.DictReader(fh))
    out = []
    for r in rows:
        lower = {k.strip().lower(): v for k, v in r.items() if k}
        first = next(iter(r.values()))
        out.append({"key": first, "clicks": lower.get("clicks"), "impressions": lower.get("impressions"),
                    "ctr": lower.get("ctr"), "position": lower.get("position")})
    return out


def read_json(path):
    with open(path, encoding="utf-8") as fh:
        data = json.load(fh)
    return data.get("rows", data) if isinstance(data, dict) else data


def api_rows(prop, dim, start, end):
    token = os.environ.get("GSC_ACCESS_TOKEN")
    if not token:
        sys.exit("--api needs an OAuth access token in GSC_ACCESS_TOKEN")
    body = json.dumps({"startDate": start, "endDate": end, "dimensions": [dim],
                       "rowLimit": 25000, "dataState": "final"}).encode()
    req = urllib.request.Request(API % urllib.parse.quote(prop, safe=""), data=body, method="POST",
                                 headers={"Authorization": "Bearer " + token,
                                          "Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=60) as r:
        data = json.load(r)
    return [{"key": row["keys"][0], "clicks": row["clicks"], "impressions": row["impressions"],
             "ctr": row["ctr"], "position": row["position"]} for row in data.get("rows", [])]


def derive(pages, queries, th, brand):
    lo, hi = th["strike_position"]
    gap = []
    for p in pages:
        if p["impressions"] < th["min_impressions"]:
            continue
        exp = C.expected_ctr(p["position"])
        left = p["impressions"] * exp - p["clicks"]
        if left > 0:
            gap.append(dict(p, expected_ctr=round(exp, 4), clicks_left=round(left, 1)))
    gap.sort(key=lambda x: -x["clicks_left"])
    strike = [q for q in queries
              if lo <= q["position"] <= hi and q["impressions"] >= th["min_impressions"]
              and not any(b and b.lower() in q["key"].lower() for b in brand)]
    strike.sort(key=lambda x: -x["impressions"])
    return gap[:25], strike[:25]


def main():
    C.utf8_stdout()
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0], epilog=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("site")
    ap.add_argument("--state")
    ap.add_argument("--pages-csv"); ap.add_argument("--queries-csv")
    ap.add_argument("--pages-json"); ap.add_argument("--queries-json")
    ap.add_argument("--api", action="store_true")
    ap.add_argument("--end", help="last day of the window (default: today minus 2, Search Console lag)")
    ap.add_argument("--days", type=int, default=28)
    a = ap.parse_args()

    root = C.state_root(a.state)
    cfg = C.load_config(root, a.site)
    th = cfg["thresholds"]
    end = C.today(a.end) if a.end else datetime.date.today() - datetime.timedelta(days=2)
    start = end - datetime.timedelta(days=a.days - 1)

    if a.api:
        src = "api"
        praw = api_rows(cfg["gsc_property"], "page", start.isoformat(), end.isoformat())
        qraw = api_rows(cfg["gsc_property"], "query", start.isoformat(), end.isoformat())
    elif a.pages_csv or a.pages_json:
        src = "csv" if a.pages_csv else "json"
        praw = read_csv(a.pages_csv) if a.pages_csv else read_json(a.pages_json)
        qraw = (read_csv(a.queries_csv) if a.queries_csv else
                read_json(a.queries_json) if a.queries_json else [])
    else:
        sys.exit("give --pages-csv, --pages-json or --api (see --help)")

    pages = norm_rows(praw, "pages", cfg.get("hosts") or [], cfg.get("exclude_paths") or [])
    queries = norm_rows(qraw, "queries", [], [])
    if not pages:
        sys.exit("no page rows after filtering hosts and exclude_paths; nothing written")

    clicks = sum(p["clicks"] for p in pages)
    impr = sum(p["impressions"] for p in pages)
    pos = sum(p["position"] * p["impressions"] for p in pages) / impr if impr else None
    gap, strike = derive(pages, queries, th, cfg.get("brand_terms") or [])
    snap = {
        "site": a.site, "source": src,
        "window": {"start": start.isoformat(), "end": end.isoformat(), "days": a.days},
        "totals": {"clicks": clicks, "impressions": impr,
                   "ctr": round(clicks / impr, 4) if impr else 0.0,
                   "position": round(pos, 1) if pos else None,
                   "note": "sum of exported page rows; Search Console totals can be higher"},
        "pages": sorted(pages, key=lambda p: -p["impressions"]),
        "queries": sorted(queries, key=lambda q: -q["impressions"]),
        "ctr_gap": gap, "strike": strike,
    }
    path = os.path.join(C.site_dir(root, a.site), "gsc", end.isoformat() + ".json")
    C.write_json(path, snap)
    print("saved %s" % path)
    print("window %s..%s (%d days), %d pages, %d queries, %d clicks, %d impressions"
          % (start, end, a.days, len(pages), len(queries), clicks, impr))
    print("ctr gaps %d, striking-distance queries %d" % (len(gap), len(strike)))
    if len(pages) >= 1000 and src == "csv":
        print("note: the Search Console UI exports at most 1,000 rows; the long tail is missing")


if __name__ == "__main__":
    main()
