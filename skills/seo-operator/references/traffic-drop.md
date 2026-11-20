# Traffic drop: an ordered checklist

Load this when someone says "organic clicks dropped". Work the steps in order and stop to write down what each one shows. Most false alarms die in step 1, and most real drops with a fast fix are found in step 2. Do not touch the site until you know which step the cause sits in.

For every suspected cause keep one row: cause, evidence, verdict (**proven**, **present** or **hypothesis only**). Report only proven causes as the cause.

## 1. Measurement first

Rule out a broken measurement before believing the drop.

| Check | What to look for | If it explains the drop |
|---|---|---|
| Data delay | Search Console data runs about 2-3 days behind, and the last day or two are often incomplete | Re-compare with a window that ends 3+ days ago |
| Partial windows | Comparing 28 days to a window that includes a half day, or 28 days to 30 | Compare equal, complete windows, same weekdays |
| Weekday mix | A window with one weekend fewer than the one before | Compare week over week on full weeks |
| Property or host change | A move from http to https, www to bare domain, or a new domain-level property; data split across two properties | Add the properties together, or read the domain property |
| Filters | A country, device, page or query filter left on in the report or export | Clear filters, re-pull |
| Export caps | Row limits in exports drop the long tail of queries and pages | Use property totals for clicks and impressions, rows only for which page or query |
| Analytics vs Search Console | An analytics tool dropped (consent banner, tag removed) while Search Console did not | Not an SEO drop; fix the tag |

Never add impressions across page-by-query rows to get a total. Use the property totals.

## 2. Site-wide technical

A sudden cliff across the whole site, on a specific date, usually has a technical cause. Check what changed on or shortly before that date: deploys, CMS settings, CDN or hosting changes.

- **robots.txt**: a `Disallow: /` or a blocked section shipped by accident; also check the CDN's bot settings, which can refuse crawlers that robots.txt allows.
- **noindex**: a meta robots or `X-Robots-Tag` noindex left on from staging, often site-wide.
- **Canonicals**: every page canonicalised to the homepage, or to a URL that redirects or errors.
- **Redirects**: a migration with missing or chained redirects; old URLs returning 404.
- **Outages**: server errors or timeouts in the crawl stats report; a few hours of 5xx at the wrong moment shows up as a dip.
- **Sitemap**: removed, empty, or listing URLs that redirect or are noindexed.
- **Rendering**: content moved behind JavaScript so the raw HTML is empty.

Use `scripts/seo_crawl.py` to re-crawl and compare against the last saved crawl. Read the rendered HTML of the pages that dropped, not the CMS editor.

If nothing on the site changed, the drop came from outside. Do not roll back changes on a hunch.

## 3. Google update vs seasonality vs demand

Compare three numbers for the drop window against the window before it, and against the same window last year if you have it: impressions, average position, CTR.

| Impressions | Position | CTR | Most likely cause |
|---|---|---|---|
| Down | Steady | Steady | Demand fell: season, weather, news, or ads paused (brand searches fall when ads stop) |
| Down | Worse | Steady or down | Rankings fell: a Google update, a stronger competitor, or a page change |
| Steady | Steady | Down | The results page changed: an AI overview, map pack, ads or a video block now sits above you; or Google rewrote your title |
| Down | Better | Varies | Lost queries, not lost rank: Google stopped showing you for broad queries and the remaining ones rank higher; or the query is now answered by a different feature |
| Down | Down | Down, same date as a confirmed update | A core or spam update; read what it targeted |

Seasonality check for Acme Coffee: cold brew queries fall every autumn. A drop in October that matches last October's shape is the season, not a problem.

Check the date against public Google update announcements before calling it an update. A drop that started a week before the announced rollout was something else.

## 4. Page-level and query-level breakdown

Find where the loss sits before choosing a fix.

1. Split branded and non-branded queries. Recovery is judged on non-branded only.
2. Rank pages by clicks lost (previous window minus current). Usually a few pages hold most of the loss.
3. For each top loser, list its queries with impressions and position in both windows.
4. **Trend-adjust** each page: compute the site-wide change in clicks for the same windows, apply it to the page's previous clicks to get its expected clicks, and compare the page's actual clicks against that expectation. A page down 20% on a site down 20% has no page-specific problem; a page down 50% on a site down 10% does.
5. For each query that dropped, check which of your pages Google now shows. If a different page of yours took over the query, two pages are competing; fix with titles, headings and internal links, not by canonicalising one page to the other.
6. Look at the live results page for the top lost queries and note what sits above you now.

Snapshot both windows with `scripts/seo_measure.py` so the comparison is saved, not redone by hand.

## 5. Recovery actions

Match the action to the proven cause.

| Proven cause | Action |
|---|---|
| Measurement artefact | No site change; fix the comparison and note it |
| Technical (step 2) | Revert or fix the setting, request indexing for the key pages, resubmit the sitemap |
| Demand or season | No site change; set expectations and plan seasonal content earlier next year |
| Results page changed | Rework the snippet (serp-copy skill) and make the page quotable for AI answers (page-audit skill) |
| Rankings fell after an update | Audit the losers against what the update targeted; fix claims not backed by the site's `truth.md`, thin templated pages, outdated content; improve the pages, do not delete winners in a panic |
| Pages competing for one query | Pick one page to win, align titles and internal links to it, merge if they serve the same intent |

Use `scripts/seo_select.py` to rank the recovery actions against the rest of the queue, so a drop does not crowd out a higher-value fix elsewhere.

Recovery after an update is often slow and may wait for the next update. Do not promise a date.

## 6. What to log

- The cause table from the top of this file, with verdicts.
- The comparison windows used, their exact dates, and the filters (none, or which).
- Each action shipped, registered in the ledger with `scripts/seo_register.py` (kind `other`, `content`, `title-meta` or the fitting one) so its effect is verified against the site trend later.
- A fixed cohort to watch weekly: 20-60 non-branded money queries with impressions, weighted position, clicks and the winning page; brand impressions on their own line.
- A "not checked" list: anything you could not see (crawl stats without access, rendered HTML not fetched, last year's data missing).

Summarise with `scripts/seo_report.py`. Recovery is declared when the non-branded cohort is back near its pre-drop level after trend adjustment, not when one day looks good.
