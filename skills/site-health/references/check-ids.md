# Check IDs

Every check ends in one of three states: **FAIL**, **ok**, or **not checked** (with the reason). Live checks come from `scripts/site_probe.py`; snapshot checks read the crawl file written by `seo_crawl.py`.

## Live checks

| ID | What it does | FAIL when | Fix |
|---|---|---|---|
| `soft_404` | requests a random path that cannot exist | it answers 200 | return a real 404 or 410 for unknown paths |
| `robots_groups` | parses robots.txt into groups and finds the group each crawler obeys (its own, else `*`) | a search or user-fetch crawler hits `Disallow: /` | remove the rule, or move it to training crawlers only |
| `ai_blocked_at_edge` | fetches the home page with each crawler's user agent and with a browser's | the bot gets 401, 403, 429 or 503 while the browser gets 200 (search and user-fetch bots) | allow verified crawlers in the CDN or firewall bot settings |
| `js_rendered_content` | counts visible words in the raw HTML of the home page | under 50 words | server-render or pre-render the main content |
| `redirect_chain` | follows each `--url` hop by hop | 2+ hops | point the first URL straight at the final one |
| `redirect_loop` | same | a URL repeats | break the loop in the redirect rules |

A training crawler blocked in robots.txt is reported as ok with "blocked": the owner chose it. The probe also notes when robots.txt looks managed by the CDN (some CDNs inject AI-bot rules), so the owner knows where the rule lives.

## Snapshot checks

| ID | Read from the crawl | FAIL when |
|---|---|---|
| `noindex_in_sitemap` | pages in the sitemap with a noindex tag or header | any |
| `sitemap_non_200` | sitemap URLs that answer an error or a redirect | any |
| `canonical_to_bad_target` | canonicals pointing at a 4xx, a redirect, or a noindex page | any |
| `internal_links_to_redirects` | pages linked internally that answer a redirect | any |
| `redirect_chains` | internal URLs with 2+ hops | any |
| `thin_or_js_rendered` | crawled pages with almost no visible words | any |
| `orphans` | sitemap pages no crawled page links to | reported only on a complete crawl; `null` on a capped one |

## not checked

| Typical reason | Meaning |
|---|---|
| robots.txt unreachable, or answered an error to a browser agent | robots groups cannot be read |
| home page unreachable, or one bot request failed | the edge comparison for that bot is unknown |
| made-up URL answered a redirect or another non-404 code | soft 404 needs a manual look |
| `not in this snapshot` | the crawl file has no list for this check (an older crawl) |
| crawl was capped | orphans cannot be counted |
| `crawl_access`: URLs answered 401/403/429 or failed | their per-page checks did not run |

Google-Extended has no fetch agent of its own (it is a robots token only), so it appears in the robots rows but not in the edge rows.

## Exit codes

`0` no FAIL, `1` at least one FAIL, `2` bad input. Use the exit code in a scheduled job to alert only on change.
