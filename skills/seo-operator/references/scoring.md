# Scoring: how the board is built

`scripts/seo_select.py` puts every possible action on one scale so a title rewrite, a broken link and a new section can be compared.

```
score = clicks_at_stake x RECOVER[kind] / EFFORT[kind]     (x 1.5 on a money page)
```

- **clicks_at_stake**: monthly clicks the problem costs, from the latest Search Console snapshot, or a flat floor for technical issues the data cannot price.
- **RECOVER**: the share of those clicks a fix of this kind usually wins back.
- **EFFORT**: operator hours, including the review and the deploy.

Both tables are starting guesses. Once your ledger has 10 or more verdicts of one kind, set your own values in `config.json` under `"effort"` and `"recover"`. Example: if 6 of 8 title rewrites worked, keep RECOVER for title-meta; if 1 of 8 did, cut it.

## Default tables

| Kind | Effort (h) | Recover | Lane | Stake comes from |
|---|---|---|---|---|
| title-meta | 0.25 | 0.35 | ctr | `ctr_gap` rows: clicks the page would earn at the expected CTR for its position |
| link-fix | 0.15 | 1.0 | links | broken page: 20; internal links to a redirect: 10 |
| internal-link | 0.5 | 0.25 | links | orphan page: 15 (top 20 orphans only) |
| schema | 0.4 | 0.10 | aeo | no JSON-LD on a page with 100+ impressions: 18 |
| content | 3.0 | 0.30 | content | striking-distance query: impressions x (CTR at position 5 minus current CTR) |
| speed | 4.0 | 0.15 | tech | 8 per slow page, only with 10+ slow pages and 3+ crawls |
| sitemap | 0.3 | 0.20 | tech | 5 per indexable page missing from the sitemap, only with 5+ |

## Expected CTR curve

`seo_common.expected_ctr(position)` interpolates a conservative curve of organic CTR by position. It is a planning curve, not a measurement of your site: CTR depends on brand, SERP features and intent. Replace it with your own median CTR by position once you have 3 months of data.

## Rules that keep the board honest

| Rule | Why |
|---|---|
| CTR rows only at position 15 or better (`ctr_max_position`) | below that, rank sets CTR and a snippet change cannot move it |
| `ctr_skip_paths` (default `/`) | a home page's CTR is set by brand searches, not by its snippet |
| strike queries: top 15, gain under 5 clicks dropped | keeps long-tail noise off the board |
| 60-day cooldown per target and lane | two changes on one page in one window make both unverifiable |
| speed waits for 3 crawls | one fast crawl after a deploy is often a warm cache |
| one row per kind and target | the strongest reason wins; duplicates are dropped |
| brand queries never in strike | you already rank for your name; the gap is elsewhere |

## Reading the board

- The top row is a suggestion with its arithmetic, not an order. Skip it when the owner's context rules it out and say why in the run log.
- Floors for technical rows are deliberately modest. A broken money page still lands near the top because of the x1.5 boost and RECOVER 1.0.
- An empty board means nothing is worth an hour. Log `--picked none` and spend the hour elsewhere.

## Worked example (Acme Coffee, 2026-11-20)

`/blog/how-to-make-cold-brew` sits at position 7.2 with 8,300 impressions, 99 clicks, and a CTR of 1.2% against 3.1% expected. The clicks at stake are 156.6 (the snapshot's exact expected clicks minus actual). 156.6 x 0.35 / 0.25 = 219.2.

`/wholesale` is a link-fix with a floor of 10: 10 x 1.0 / 0.15 = 66.7, x 1.5 for a money page = 100.

`/subscriptions`: 35.8 clicks at stake x 0.35 / 0.25 = 50.1, x 1.5 = 75.2.

Full board: `examples/acme-coffee/board-2026-11-20.txt`.
