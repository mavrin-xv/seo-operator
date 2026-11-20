---
name: query-research
description: Turns search demand into a short, ranked list of pages to build, fix or skip. It sorts Search Console queries into intent buckets (brand, near-me, town plus service, informational, service), shows where impressions sit without clicks, lists striking-distance queries, mines Google autocomplete for the questions people type, and files each query family into a decision queue of NOW, NEXT, HOLD or DROP with evidence. Use when the user asks "what should we write about", "keyword research", "what are people searching for", "which pages should we build", or "is there demand for X".
---

# Query research

Decide which pages deserve to exist, from demand you can see, before anyone writes a word. Most content plans start from ideas; this one starts from queries that already show impressions or typed suggestions.

## Inputs

- The Search Console "Queries" export (CSV, last 3 months if you have it; 28 days works).
- The brand terms, and the towns or areas served (for local businesses).
- Seed topics for autocomplete mining (2 to 5).
- The state folder's `radar.md`, if the `seo-operator` loop runs (start from `templates/radar.md`).

## Steps

1. **Bucket the queries.** `python3 scripts/query_buckets.py Queries.csv --brand acme --towns "downtown,riverside"`. Read the share of impressions per bucket and the weighted position. A bucket with a big share and a low CTR is where the work is.
2. **List striking distance.** The same output lists non-brand queries at positions 4 to 20 with 50+ impressions (`--min-impr`). These are pages that exist and nearly win. They go to `seo-operator` as content or title-meta actions before any new page.
3. **Mine autocomplete for gaps.** `python3 scripts/suggest.py "cold brew" --mode questions,comparisons`. This calls Google's public suggest endpoint only, with a delay between probes; keep `--max-probes` low and do not run it in a loop. Suggestions show what people type, not how many: treat them as a list of questions, not as volume.
4. **Group into families.** One family is one intent a single page can answer ("cold brew at home": how to make, ratio, steep time, bitter). Do not make one page per phrasing.
5. **File each family** in `radar.md` with its evidence and a status. Rules for NOW, NEXT, HOLD and DROP: `references/decision-queue.md`.
6. **Check templates before scale.** If a family is "the same page per town or product", it goes through the programmatic gate first (`pseo-gate.md` in the `seo-operator` skill), and `overlap.py` in `site-health` once drafts exist.
7. **Hand off.** NOW families with an existing page go to `page-audit`, then `serp-copy` if the snippet is the gap. NOW families with no page get a one-paragraph brief: the primary query, the questions to answer, the facts needed, the page it links from.

## Gates

- Every NOW item has evidence: Search Console rows (impressions, position) or a typed suggestion plus a reason it fits what the business sells.
- No family is built twice. Search the site (and the crawl's page list) for an existing page before you plan a new one.
- No volume numbers invented from autocomplete. If a paid tool's volume is used, name the tool and the date.
- Brand queries are not content opportunities. Leave them out of the plan.

## Output

```
bucket         queries      impr  clicks    CTR   pos(w)  share
informational        4      8450      59   0.7%      9.6    59%
service              2      1370       7   0.5%      9.2    10%
...
Decision queue
  NOW   cold brew at home      4 queries at positions 7-15, 8,450 impressions, page exists
  NEXT  coffee subscription    950 impressions at 8.6, money page, snippet gap
  HOLD  cold brew near me      needs a location page per shop; pseo gate first
  DROP  espresso vs drip       informational, no product fit
```

Full bucket output: `examples/acme-coffee/query-buckets.txt`.

## Failure modes

| Trap | What it looks like | Instead |
|---|---|---|
| One page per phrasing | "cold brew ratio" and "cold brew recipe" as two posts | one family, one page, all the questions |
| Ideas first | a content calendar with no query evidence | every item cites rows or suggestions |
| Volume from autocomplete | "this gets 10k searches" | suggestions are questions, not counts |
| Ignoring what already ranks | a new post for a query the site holds at position 8 | improve the existing page first |
| Chasing traffic with no fit | high-volume questions the business cannot serve | DROP with the reason |
| Hammering the suggest endpoint | thousands of probes in a loop | a few seeds, a delay, cache the results |
