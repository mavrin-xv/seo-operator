# Scoring

Three scores appear in this pack. They answer different questions and are never added together.

| Score | Answers | Where |
|---|---|---|
| Board score | which action is worth the next hour | `seo_select.py`, full method in the `seo-operator` skill's `references/scoring.md` |
| Snippet score (out of 100) | which title and description variant to ship | `serp_lint.py` (30 automatic points) plus 70 judged points, in the `serp-copy` skill |
| Page score (out of 100) | is this page ready to rank and be quoted | the `page-audit` rubrics: GEO 60, SEO 30, brand recommendation 10 |

## Board score

```
score = clicks_at_stake x RECOVER[kind] / EFFORT[kind]     (x 1.5 on a money page)
```

Clicks at stake come from Search Console where the data can price the problem (a CTR gap, a striking-distance query) and from modest flat floors where it cannot (a broken page, an orphan). RECOVER and EFFORT are per action kind; the defaults are starting guesses, and the ledger tells you your own after about 10 verdicts per kind.

Worked example on the invented site, `/subscriptions`: position 6.1, CTR 1.5% against 3.9% expected, 35.8 clicks a month at stake. Title rewrite: 35.8 x 0.35 / 0.25 = 50.1; it is a money page, so 75.2.

Rules that keep the board honest: CTR actions only at position 15 or better, never on the home page, a 60-day cooldown per page and lane, speed only after 3 crawls, brand queries excluded from striking distance.

## Verdict bar

A registered action is judged after 21+ days:

```
expected = baseline_clicks x (site_clicks_now / site_clicks_at_baseline)
adjusted = clicks_now - expected
bar      = max(3, 15% of baseline_clicks)
```

`adjusted >= bar` is worked, `adjusted <= -bar` is backfired, anything between is no change. Link fixes and sitemap fixes are judged from the next crawl instead (fixed or still open).

## Snippet score

30 automatic points: title length (10), description length (8), primary query in the first 40 characters (7), no year (3), no mixed separators (2). Hard fails, such as the keyword twice, a number not in the facts file, or two generic adjectives, remove a variant whatever its points.

70 judged points: intent match (25), specific proof from the facts file (20), distinct from the other results on the page (15), reads as a sentence a person would click (10).

## Page score

GEO 60 points for how quotable the page is (direct answers under question headings, sourced and dated claims, tables and lists where they fit). SEO 30 for the basics (title and H1 on the query, one H1, description, internal links, fitting schema). Brand recommendation 10 for whether an assistant would have a reason to name the brand from this page. A hard fail in any axis means "fix before shipping" whatever the total.

All three scores are tools for choosing, not targets. A page at 70 that answers its query is better than a page at 90 written to the rubric.
