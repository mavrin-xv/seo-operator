# Verify: did the change work?

`scripts/seo_register.py verify <site>` judges every open action. It runs in each session, so old actions get their verdict without anyone remembering them.

## When an action can be judged

All three must hold:

1. The action is at least `verify_min_days` old (default 21).
2. The latest Search Console snapshot ends at least 21 days after the change. A snapshot pulled today can still end before the change, because of the lag and the window; then the script prints "too soon after the change; measure again".
3. The snapshot window has the same length as the baseline window. A 28-day baseline against a 90-day reading is "unverifiable".

Why 21 days: Google needs to recrawl the page, and a title change shows up in clicks over the following weeks. A shorter wait mostly measures noise and weekday mix.

## The trend-adjusted comparison

A page that gained 20% while the whole site gained 20% did nothing. So the script compares the page against what the site trend predicts:

```
site_trend = site_clicks_now / site_clicks_at_baseline - 1
expected   = page_clicks_at_baseline x (1 + site_trend)
adjusted   = page_clicks_now - expected
bar        = max(3, 15% of page_clicks_at_baseline)
```

| Result | Verdict |
|---|---|
| adjusted >= bar | worked |
| adjusted <= -bar | backfired |
| between | no change |
| baseline under 5 clicks and adjusted within 5 either way | no change (too small to call) |

Example from `examples/acme-coffee/state/acme-coffee/outcomes.jsonl`: `/menu/cold-brew` had 38 clicks at baseline. The site grew 9.2%, so it was expected at 41.5. It reached 71, so adjusted = +29.5 against a bar of 5.7: worked.

The control is the sum of the exported page rows on the same snapshot, not the Search Console headline total, so both sides of the comparison use the same source.

## Crawl-verified kinds

`link-fix` and `sitemap` actions are judged from the latest crawl, not from clicks:

| Kind | fixed | still open |
|---|---|---|
| link-fix | the target is no longer broken or redirected in the crawl | it still answers with an error or a redirect |
| sitemap | no indexable pages are missing from the sitemap | some still are |

If no crawl ran after the change, the verdict is "unverifiable: no crawl after the change". Run `seo_crawl.py` and verify again.

## unverifiable

| Why | What to do |
|---|---|
| no baseline was pinned | the target had no row when registered (a new page). Judge it by its first 28 days instead, by hand |
| window lengths differ | re-measure with the baseline's window length |
| target is not in the latest data | the page lost all impressions or moved URL. Check the crawl before calling it a loss |

## What the verdicts are for

- **Tune the tables.** After 10 verdicts of one kind, the share that worked is your own RECOVER. Put it in `config.json`.
- **Learn what fails.** A backfired title is a lesson about the audience. Keep the old and new title in the note so the next writer sees both.
- **Report honestly.** The report counts worked, backfired, no change and unverifiable side by side. A run of "no change" verdicts is information: the board is pointing at problems a snippet cannot fix.

## Limits

- One page and one change per window. If two changes hit the same page, the verdict belongs to both and to neither.
- Seasonal sites: the site trend covers most of it, but a page with its own season (a holiday guide) can still swing. Compare with the same window last year when you have it.
- Small pages stay noisy. Under about 5 clicks a month, the verdict is a hint, not a result.
