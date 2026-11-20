# Contributing

Issues and pull requests are welcome.

- **Bug:** include the command, the script's output, and the snapshot file if it matters, with your domain and paths replaced by example ones.
- **New check:** add it to `site_probe.py` with an ID, a FAIL rule and a "not checked" reason, document it in `skills/site-health/references/check-ids.md`, and show its output on the fixture site.
- **Scoring changes:** show the board before and after on `examples/acme-coffee/state`, and explain the new number in `docs/scoring.md`.
- **New action kind:** add its effort, recovery and stake rule in `seo_select.py`, and its verify rule in `seo_register.py`.
- Scripts stay standard-library only.
- Plain English in docs. No invented benchmarks; example companies are fictional.

By contributing you agree your work is released under the MIT license.
