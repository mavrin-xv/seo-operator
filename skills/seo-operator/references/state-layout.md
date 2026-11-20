# State layout

One folder per site under the state root. The root is `--state`, else `$SEO_STATE_DIR`, else `./.seo` in the working directory. Keep it out of git if the site is private (`.seo/` is in the repo's `.gitignore`).

```
.seo/
  acme-coffee/
    config.json            settings, edited by hand
    truth.md               facts copy may use, with source and date
    radar.md               topic queue: NOW / NEXT / HOLD / DROP
    needs-you.md           the owner's to-do list, "- [ ]" items
    gsc/2026-11-17.json    Search Console snapshot, named by window end
    health/2026-11-18.json crawl snapshot, named by crawl date
    candidates/2026-11-20.json   the ranked board
    outcomes.jsonl         the ledger, one action per line
    runs.jsonl             one line per session
    reports/2026-11-20.md  the report shown to the owner
```

`scripts/seo_state.py init` creates the folder from `templates/` and never overwrites an existing file.

## config.json

Template: `templates/config.json`.

| Key | Meaning |
|---|---|
| `site`, `domain` | slug and bare domain |
| `start_url` | where the crawl starts |
| `gsc_property` | `sc-domain:acme-coffee.com` or a URL-prefix property |
| `hosts` | hosts treated as this site; rows for other hosts are dropped |
| `brand_terms` | lower-case terms; queries containing one are brand queries |
| `money_paths` | path prefixes that get the x1.5 boost |
| `exclude_paths` | path prefixes dropped from every snapshot (cart, account) |
| `ctr_skip_paths` | paths never given a CTR action (default `["/"]`) |
| `thresholds` | `ttfb_ms`, `html_kb`, `min_impressions`, `strike_position`, `ctr_max_position`, `cooldown_days`, `verify_min_days`, `prune_days` |
| `effort`, `recover` | overrides for the scoring tables, by kind |

## gsc snapshot

```json
{"window": {"start": "2026-10-21", "end": "2026-11-17", "days": 28}, "source": "csv",
 "totals": {"clicks": 734, "impressions": 25845, "ctr": 0.0284, "position": 6.7},
 "pages":   [{"key": "/menu/cold-brew", "clicks": 71, "impressions": 4050, "ctr": 0.0175, "position": 5.6}],
 "queries": [{"key": "how to make cold brew", "clicks": 41, "impressions": 4400, "ctr": 0.0093, "position": 7.6}],
 "ctr_gap": [{"key": "...", "expected_ctr": 0.031, "clicks_left": 156.6}],
 "strike":  [{"key": "...", "position": 7.6}]}
```

Page keys are bare paths without the trailing slash, so `/menu/cold-brew/` and `/menu/cold-brew` are one row.

## health snapshot

Top-level keys: `site`, `start`, `crawled`, `complete`, `cap`, `counts`, `speed`, `robots`, `soft_404`, `issues`, `pages`. Each issue list is either a list or `null` (not measured, for example orphans on a capped crawl). `not_checked` lists URLs that answered 401, 403, 429 or failed, whose checks did not run.

## outcomes.jsonl

One JSON object per line:

| Field | Set by | Meaning |
|---|---|---|
| `id` | add | `<date>-<n>` |
| `date`, `target`, `kind`, `lane`, `note` | add | what was done and where |
| `baseline` | add | clicks, impressions, CTR, position of the target in the latest snapshot, or `null` |
| `baseline_snapshot`, `baseline_window_days` | add | which snapshot, and its window length |
| `control` | add | site totals from the same snapshot |
| `status` | add, verify | `open` then `verified` |
| `verdict`, `why`, `delta` | verify | see `verify.md` |
| `verified_on`, `verified_snapshot` | verify | when and against what |

The ledger is append and verify only. Do not edit or delete lines by hand.

## runs.jsonl

`{"date": "2026-10-22", "at": "...", "picked": "/menu/cold-brew", "note": "..."}`. `picked` is `none` on a session that found nothing worth an hour.

## Working notes

- `truth.md`: a table of Fact, Source, Verified. Copy may only use numbers that appear here.
- `radar.md`: topics and pages under consideration, in NOW, NEXT, HOLD and DROP, each with the query evidence.
- `needs-you.md`: actions the owner must take (deploys, approvals, facts). The report lists the open ones.
