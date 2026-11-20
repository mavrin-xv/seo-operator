# AGENTS.md

Guidance for an AI agent working with or on this repo.

## Using the pack
- Skills: `seo-operator` (the loop), `site-health`, `serp-copy`, `page-audit`, `query-research`, `llms-txt-mirror`, `ai-citations`. Each `SKILL.md` lists its inputs, gates and output.
- Start every SEO session with `seo_state.py show <site>`; the state folder is the memory. Read `needs-you.md` before picking an action.
- Scripts are Python 3.9+, standard library only, each with `--help`. Run them for counts, scores and verdicts; do not redo the arithmetic in the prompt.
- Register every change with `seo_register.py add` in the same session. Never edit or delete ledger lines.
- Changes to a live site go through the owner unless they gave you access. Write the exact change in `needs-you.md`.
- Copy uses only facts from `truth.md`. Never invent numbers, reviews or sources.
- In Git Bash, set `MSYS_NO_PATHCONV=1` before any argument that starts with `/`, and use a relative `SEO_STATE_DIR`.

## Changing the pack
- Keep `SKILL.md` under 500 lines; detail goes in `references/`.
- Script changes: re-run the examples and update the outputs in `examples/acme-coffee/`:
  ```
  cd skills/seo-operator/scripts && SEO_STATE_DIR=../../../examples/acme-coffee/state python3 seo_select.py acme-coffee --today 2026-11-20
  python3 skills/serp-copy/scripts/serp_lint.py examples/acme-coffee/titles.csv --facts examples/acme-coffee/truth.md
  python3 skills/page-audit/scripts/page_facts.py examples/acme-coffee/page.md
  python3 skills/query-research/scripts/query_buckets.py examples/acme-coffee/gsc-export/2026-11-17/Queries.csv --brand acme --towns downtown
  python3 skills/llms-txt-mirror/scripts/llms_txt.py lint examples/acme-coffee/llms.txt
  python3 skills/llms-txt-mirror/scripts/mirror_lint.py examples/acme-coffee/mirror.md
  python3 skills/ai-citations/scripts/aeo_diff.py examples/acme-coffee/aeo/round-2026-10-20.csv examples/acme-coffee/aeo/round-2026-11-17.csv
  ```
- Live checks (`seo_crawl.py`, `site_probe.py`) run against the fixture site: `python3 -m http.server 8799 --bind 127.0.0.1 --directory examples/acme-coffee/site`.
- Fail visibly: a check that could not run reports "not checked" with the reason, never "ok".
