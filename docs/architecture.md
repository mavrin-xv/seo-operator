# Architecture

The pack is seven skills and fifteen standard-library Python scripts. There is no server and no database: the memory for each site is a folder of JSON and markdown files, so an agent, a person or a scheduled job can read it.

## Data flow

```
 inputs                    scripts                       state (.seo/<site>/)
 ------                    -------                       --------------------
 Search Console CSV/API -> seo_measure.py            ->  gsc/<window end>.json
 the live site          -> seo_crawl.py              ->  health/<date>.json
 the live site          -> site_probe.py             ->  printed checks (FAIL / ok / not checked)
 gsc + health + config  -> seo_select.py             ->  candidates/<date>.json (the board)
 a change you made      -> seo_register.py add       ->  outcomes.jsonl (baseline + control)
 21+ days later         -> seo_register.py verify    ->  outcomes.jsonl (verdict)
 everything above       -> seo_report.py             ->  reports/<date>.md
 one session            -> seo_state.py log          ->  runs.jsonl
```

The other skills read the same state where it helps and produce one change each:

| Skill | Reads | Produces | Registered as |
|---|---|---|---|
| site-health | the crawl, the live site | a fix list in cost order | link-fix, sitemap, schema, internal-link, speed |
| serp-copy | the page's queries, `truth.md` | one title and description | title-meta |
| page-audit | one page or draft | a score and exact edits | content |
| query-research | the Queries export, autocomplete | `radar.md` statuses | (new pages, judged by hand) |
| llms-txt-mirror | the crawl, the pages | `llms.txt`, `.md` mirrors | not ranked; checked by lint |
| ai-citations | dated prompt rounds | verdicts and share of model | not in the click ledger |

## Design rules

- **Memory in files.** Every session starts with `seo_state.py show`. Nothing important lives only in a chat.
- **One scale.** Every action, technical or editorial, is priced in clicks per operator-hour so they can be compared. See [scoring.md](scoring.md).
- **Verify against the trend.** A change is judged by how far the page moved beyond what the site-wide change predicts, after 21 days, on the same window length.
- **Unknown is not zero.** A capped crawl reports orphans as `null`; a probe that was refused reports "not checked"; an AI answer that failed is INDETERMINATE; a missing number in the report says "not measured".
- **Read-only on the site.** The scripts only send GET requests. Changes to the live site are made by the owner or by an agent the owner gave access to.
- **No dependencies.** Python 3.9+ standard library. The only external endpoints are the site itself, the Search Console API when `--api` is used, and Google's public suggest endpoint for `suggest.py`.

## Snapshot keys

Search Console rows are keyed by bare path (no host, no trailing slash, no query string). Rows for hosts outside `config.json` `hosts` and paths under `exclude_paths` are dropped at measure time, so every later step sees the same page set.

The crawl normalises internal URLs the same way and keeps the redirect target (`final`) for every redirected URL. That is how `llms_txt.py` lists a redirected page at its final address and how `seo_register.py verify` decides that a link-fix is fixed.

## Scheduling

The loop is meant for a weekly session with a person in it. Measure and crawl can run on a schedule (they only read); select, act and register need judgement. `site_probe.py` exits 1 on any FAIL, so a daily scheduled run can alert only when something breaks.
