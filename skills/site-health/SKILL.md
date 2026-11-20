---
name: site-health
description: Checks the technical health of a website and says what is broken, in order of cost. It crawls the site and sitemap, then probes the live site for the failures a crawl report hides, such as soft 404s, robots.txt groups per crawler, AI crawlers blocked at the CDN, redirect chains and pages that render only in JavaScript. It also finds near-duplicate pages where only a town or product name was swapped. Use when the user asks for a technical SEO audit, "why is this page not indexed", "are AI bots blocked", "check robots.txt", "find broken links", or after a migration or redesign.
---

# Site health

Find what stops search engines and AI assistants from reading the site, and fix it in cost order. Every check ends in FAIL, ok, or not checked with a reason. A check that could not run is never reported as fine.

## Inputs

- The site's home URL, and the state folder if the `seo-operator` loop runs on this site.
- Optional: specific URLs to trace (old URLs after a migration, a money page).
- Optional: a folder of page files (markdown or HTML) to test for near-duplicates.

## Steps

1. **Crawl.** `python3 ../seo-operator/scripts/seo_crawl.py <site> --max 300` writes `health/<date>.json` (from the repo root: `skills/seo-operator/scripts/seo_crawl.py`). On a site with more pages than the cap, raise `--max` or accept that orphans are reported as not measured.
2. **Probe the live site.** `python3 scripts/site_probe.py https://acme-coffee.com/ --snapshot .seo/acme-coffee/health/2026-11-18.json --url https://acme-coffee.com/old-page`. The probe adds the checks a crawl cannot make (soft 404, robots groups per crawler, edge blocks, JavaScript-only pages, redirect chains) and reads the snapshot's issue lists. Check IDs and what each one means: `references/check-ids.md`.
3. **Read AI crawler rows by job.** Search and user-fetch crawlers must be allowed: blocking them removes the site from AI answers. Training crawlers are a policy choice for the owner. Which bot does what: `references/ai-crawlers.md`.
4. **Check for swapped-name pages** when the site has many location or product pages: `python3 scripts/overlap.py pages/ --names "Downtown,Riverside,Uptown"`. Pairs above the threshold (default 0.30 of the smaller page's sentences shared) are near-duplicates. Merge them or give each page its own facts.
5. **Order the fixes** by cost to traffic:
   1. site-wide blocks (robots `Disallow: /` for a search bot, an edge block, noindex on the home page);
   2. money pages broken, redirected, or noindexed;
   3. canonicals to bad targets, noindex pages in the sitemap, sitemap URLs not 200;
   4. internal links to redirects and redirect chains;
   5. orphans, depth, missing descriptions, missing schema;
   6. speed and weight, only after 3 crawls agree.
6. **Write the fix list** with the exact change per item (the line to remove from robots.txt, the link to repoint). If the `seo-operator` loop runs, register each fix: `seo_register.py add <site> --target /path --kind link-fix` (or `sitemap`, `schema`, `internal-link`, `speed`). Link-fix and sitemap actions verify from the next crawl.

## Gates

- Report "not checked" with the reason for every check that could not run (a 403 to the probe, a timeout, a capped crawl). Never fold it into "ok".
- An edge block counts only when the bot gets 401, 403, 429 or 503 and the browser request gets 200 on the same URL in the same run.
- Do not call orphans zero on a capped crawl.
- A user-agent string can be spoofed by anyone, and the CDN may treat a real crawler differently from this probe. Confirm a suspected edge block in the CDN's bot logs or firewall events before you change rules.
- Robots rules are read per group: a bot with its own group ignores the `*` group entirely.

## Output

```
FAIL (1)
  internal_links_to_redirects  1 page(s), first: https://acme-coffee.com/wholesale
Checked, fine (31)
  soft_404                     made-up URL answers 404
  robots_groups                GPTBot (training): blocked via own group
  ai_blocked_at_edge           OAI-SearchBot gets 200 (browser 200)
  ...
Not checked (0)
```

Then the fix list in cost order, one line each: check, URL, exact change, who applies it. Full example: `examples/acme-coffee/site-probe.txt` (run against the fixture site in `examples/acme-coffee/site`).

## Failure modes

| Trap | What it looks like | Instead |
|---|---|---|
| Allowed in robots, blocked at the CDN | robots.txt is fine, yet AI answers never cite the site | `ai_blocked_at_edge` compares bot and browser status |
| Blocking all AI bots at once | one rule for GPTBot, OAI-SearchBot and ChatGPT-User | split by job; block training if the owner wants, keep search and user-fetch |
| Soft 404 | deleted pages answer 200 with "not found" text | the made-up URL probe catches it; return 404 or 410 |
| JavaScript-only page | raw HTML has a few words, content arrives by script | server-render or pre-render the main text |
| Trailing-slash redirect on every link | `/wholesale` links to `/wholesale/` with a 301 | link to the final URL directly |
| Fixing speed from one crawl | one slow run after a deploy | wait for 3 crawls |
| Swapped-name pages | 20 town pages share most sentences | merge, or give each page real local facts |
