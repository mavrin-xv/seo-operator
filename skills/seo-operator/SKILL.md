---
name: seo-operator
description: Runs SEO for a site you own as a repeating loop instead of a one-off audit. It keeps per-site memory in a state folder, measures Search Console and crawl vitals, ranks every possible action on one scale of expected clicks per operator-hour, does the best one, logs it in a ledger and checks weeks later, against the site-wide trend, whether it worked. Use when the user says "do SEO for my site", "what should I fix on the site this week", "why is organic traffic down", "did that title change work", "SEO report", or pastes Search Console exports.
---

# SEO operator

Spend the next hour of SEO work on the action with the most clicks behind it, write down what you did, and find out later if it worked. The memory lives in files, so the next session starts where this one stopped.

## Inputs

- The site name (a short slug like `acme-coffee`) and its domain.
- Search Console data: the Pages and Queries CSV exports from the Performance report (last 28 days), or JSON rows, or API access with `GSC_ACCESS_TOKEN`.
- Network access to the site for the crawl (read-only GET requests).
- What counts as a money page (pricing, product, sign-up) for `money_paths` in config.json.
- Optional: the owner's facts for `truth.md` (prices, specs, numbers copy may use).

## State folder

Everything the operator knows sits in `<state>/<site>/` (default `./.seo`, or `$SEO_STATE_DIR`, or `--state`). Layout and file formats: `references/state-layout.md`.

| File | Holds |
|---|---|
| `config.json` | domain, hosts, money paths, excluded paths, brand terms, thresholds, effort and recovery overrides |
| `gsc/<date>.json` | one Search Console snapshot per measure |
| `health/<date>.json` | one crawl snapshot per crawl |
| `candidates/<date>.json` | the ranked board from each select |
| `outcomes.jsonl` | the ledger: every action, its baseline and its verdict |
| `runs.jsonl` | one line per session, including sessions that picked nothing |
| `truth.md`, `radar.md`, `needs-you.md` | facts, the topic queue, the owner's to-do list |

Use a relative path for `SEO_STATE_DIR` in Git Bash on Windows; an absolute `$PWD` there turns into a broken `C:\c\...` path.

## Steps

1. **Load memory.** `python3 scripts/seo_state.py show <site>`. If the folder does not exist, run `init <site> --domain <domain>` and fill `config.json` with the owner (money paths, brand terms, hosts). Read `needs-you.md`: an open item blocking the top action changes the plan.
2. **Measure.** `python3 scripts/seo_measure.py <site> --pages-csv Pages.csv --queries-csv Queries.csv` (or `--api`). The window ends two days ago by default, because Search Console lags. Keep the window length the same between runs (28 days), or verify cannot compare them.
3. **Crawl.** `python3 scripts/seo_crawl.py <site> --max 300`, then `--diff` when a previous crawl exists. New broken pages and robots changes print first: they outrank everything else.
4. **Select.** `python3 scripts/seo_select.py <site>`. The board ranks every action by `clicks_at_stake x RECOVER / EFFORT`, x1.5 on money pages. Read the top 3 rows and the skipped list. How the numbers are built: `references/scoring.md`.
5. **Pick one.** Take the top row unless something in `needs-you.md` or the owner's context rules it out; say why when you skip it. If nothing scores above the floor, pick nothing and log it. An empty board is a valid result.
6. **Act.** Do the work with the matching skill:
   - title-meta: `serp-copy` (variants, lint, ship one);
   - content (a striking-distance query): `page-audit` on the page, then rewrite the section that should answer the query;
   - link-fix, internal-link, sitemap, schema, speed: `site-health`;
   - a query with no page: `query-research` to decide build or skip.
   Changes on the live site go through the owner unless they gave you access. Write the exact change in `needs-you.md` when they apply it.
7. **Register.** `python3 scripts/seo_register.py add <site> --target /path --kind <kind> --note "<what changed>"`. This pins the baseline (clicks, impressions, CTR, position) and the site totals as a control. In Git Bash, set `MSYS_NO_PATHCONV=1` first or the `/path` becomes a Windows path.
8. **Log the run.** `python3 scripts/seo_state.py log <site> --picked "/path" --note "..."` (or `--picked none`).
9. **Verify the old ones.** `python3 scripts/seo_register.py verify <site>`. Actions 21+ days old, measured by a snapshot that ends 21+ days after the change, get a verdict: worked, backfired, no change, fixed, still open, or unverifiable. Method: `references/verify.md`.
10. **Report.** `python3 scripts/seo_report.py <site>` writes `reports/<date>.md`: numbers, vitals, the board, the ledger, owner items, and what was not measured. Show it to the owner as is.

## Gates

- No action without a measure and a crawl from the last 7 days.
- One action per hour of work. Two changes on the same page in one window make both unverifiable.
- Every action is registered before the session ends. An action without a baseline can never be judged.
- A verdict needs 21 days and the same window length. Earlier reads are reported as "too soon", not as wins.
- Losers stay in the ledger. Do not delete or rewrite a verdict.
- Numbers in reports come from the snapshot files. If a number is missing, say "not measured".
- A traffic drop goes through `references/traffic-drop.md` before any fix is proposed.
- Programmatic pages (one template, many URLs) pass `references/pseo-gate.md` before any are built.

## Output

Per session, in this order:

```
Board for acme-coffee on 2026-11-20 (top 3)
  1  219.2  title-meta  /blog/how-to-make-cold-brew  (CTR 1.2% vs 3.1% expected at position 7.2)
  2  100.0  link-fix    /wholesale  [money page]  (internal links point at a redirect)
  3   75.2  title-meta  /subscriptions  [money page]
Picked: 1, because ...
Done: <the change>, registered as 2026-11-20-3
Verified: 2026-10-22-1 /menu/cold-brew WORKED (+29.5 clicks beyond the site trend)
Report: .seo/acme-coffee/reports/2026-11-20.md
Needs you: <items>
```

A full run on invented data: `examples/acme-coffee/state/acme-coffee/reports/2026-11-20.md`, boards in `examples/acme-coffee/board-2026-11-20.txt`.

## Failure modes

| Trap | What it looks like | Instead |
|---|---|---|
| Audit dump | 60 findings, no order | the board; one action, the rest wait |
| Home page CTR "fix" | rewriting the home title because its CTR looks low | brand searches set it; `ctr_skip_paths` keeps it off the board |
| Calling it at day 5 | "clicks are up 40% since Monday" | wait for verify; report "too soon" |
| Site trend read as a win | every page is up 20% after a season change | verify subtracts the site-wide trend |
| Speed after one fast crawl | TTFB halved after deploy | the cache was warm; speed waits for 3 crawls |
| Capped crawl read as complete | "0 orphan pages" from a 300-page crawl of a 2,000-page site | orphans are null on a capped crawl |
| Editing the ledger | deleting a backfired row | the ledger is append and verify only |
| UI export cap | a 1,000-row CSV taken as the whole site | measure prints a note at 1,000 rows; use the API for big sites |
