---
name: llms-txt-mirror
description: Makes a site readable for AI agents and assistants by building an llms.txt index from a crawl and writing markdown mirrors (clean .md twins) of the pages that matter, then linting both against the llms.txt format and a fixed mirror layout. It lists money pages first, drops noindex and redirected URLs, moves blog and legal pages under Optional, and rejects mirrors with relative links, leftover site chrome or numbers without a source. Use when the user asks for "llms.txt", "make the site readable for ChatGPT or Claude", "markdown version of our pages", "agent-ready docs", or "AI-friendly site".
---

# llms.txt and markdown mirrors

Give agents a short map of the site (llms.txt) and a clean markdown copy of each key page, so an assistant reading the site gets the facts without the menus, cookie banners and scripts.

Neither file is a ranking factor in Google, and no AI vendor has committed to reading llms.txt. Build them because they are cheap, they help agents that do fetch them, and writing them forces the facts into one place. Do not promise traffic from them.

## Inputs

- A crawl snapshot from `seo_crawl.py` (the `seo-operator` skill), or the list of pages to include.
- The site name, a one-line summary of what it sells and to whom, and the money pages.
- For mirrors: the page itself and the facts it states, with sources.

## Steps

1. **Draft llms.txt from the crawl.** `MSYS_NO_PATHCONV=1 python3 scripts/llms_txt.py build --snapshot .seo/acme-coffee/health/2026-11-18.json --name "Acme Coffee" --summary "Small-batch coffee roaster: ..." --base https://acme-coffee.com --money /subscriptions --money /menu --money /wholesale`. Pages are grouped by first path segment, money pages first; the home page and noindex pages are skipped; a URL that redirects is listed at its final address; blog, news and legal pages go under "## Optional".
2. **Finish it by hand.** Replace auto notes with one plain line per page: what the page answers, with a specific fact. Cut pages an agent would never need. The format: `references/llms-txt-spec.md`.
3. **Lint it.** `python3 scripts/llms_txt.py lint llms.txt`. Fix every error (H1 first, one H1, `- [name](url): notes` lines, absolute URLs, no H3) and clear the warnings (duplicates, missing notes).
4. **Write mirrors for the pages in llms.txt**, starting with money pages and the pages AI answers should quote. Use the article or landing layout in `references/mirror-format.md`. Every number in Key Numbers links its source.
5. **Lint each mirror.** `python3 scripts/mirror_lint.py mirror.md --canonical https://acme-coffee.com/blog/how-to-make-cold-brew/`. Errors block shipping; warnings need a reason to keep.
6. **Publish** llms.txt at the site root and each mirror at a predictable URL (the page path plus `index.md`, or `.md` appended), and say which convention in llms.txt. Link the HTML page to its mirror with `<link rel="alternate" type="text/markdown" href="...">`.
7. **Keep them in sync.** When a page's facts change, the mirror changes in the same deploy. A stale mirror is worse than none, because agents quote it.

## Gates

- llms.txt lint: 0 errors.
- Mirror lint: 0 errors, and every warning either fixed or explained.
- No fact in a mirror that is not on the HTML page or in the facts file.
- No noindex, redirected or private page in llms.txt.
- Absolute URLs only. An agent reads these files out of context.

## Output

The two files and their lint lines:

```
llms.txt: 5 links, 0 errors, 0 warnings
mirror.md: 246 words, 0 errors, 0 warnings
```

Examples: the raw build `examples/acme-coffee/llms.draft.txt`, the finished `examples/acme-coffee/llms.txt`, a mirror `examples/acme-coffee/mirror.md` and its lint `examples/acme-coffee/mirror-lint.txt`.

## Failure modes

| Trap | What it looks like | Instead |
|---|---|---|
| Dumping the sitemap | 400 links in llms.txt | the pages an agent needs, with a line each |
| Redirected URLs | `/wholesale` listed while it 301s to `/wholesale/` | list the final URL |
| HTML-to-markdown dump | nav, footer and cookie text in the mirror | write the mirror from the page's facts in the fixed layout |
| Relative links | `[pricing](/subscriptions)` | absolute URLs |
| Frontmatter | YAML block at the top | H1 first; metadata goes in "Article Metadata" |
| Promising rankings | "llms.txt will grow AI traffic" | it is a readability aid; measure citations with `ai-citations` |
| Stale mirror | price changed on the page, not in the mirror | change both in one deploy |
