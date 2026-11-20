# Programmatic SEO gate

Load this before generating any set of pages from one template: town pages (`/cold-brew-in-<town>`), "for <industry>" pages, "<A> vs <B>" matrices, integration pages, glossary terms. The gate decides one of three verdicts before a single page is built:

| Verdict | Meaning |
|---|---|
| GO | Pass all six tests below; build the pilot batch |
| RESHAPE | The idea has merit but fails a test; cut rows, change the template or the dataset, then re-run the gate |
| NO | The pages would differ only by the swapped noun; build one good page instead |

Templated pages are not banned. Google's scaled content policy targets pages made at scale mainly to rank, whatever the method (templates, AI, scraping, people). Thin pages also count against the whole site, not only against themselves, so a bad batch can drag down pages that worked before.

## 1. Demand proof per page

Every row needs evidence that people search for it, before it gets a page.

- Best proof: Search Console already shows impressions for that row's query on an existing page (for example, `/wholesale` gets impressions for "wholesale coffee beans portland").
- Next best: query or suggest data showing the exact wording people type for that row.
- Not proof: "every town has coffee drinkers". Population is not demand.

Rows without demand proof go to a backlog, not into the batch. Merge close variants into one row ("cold brew delivery seattle" and "seattle cold brew delivery" are one intent, one page).

## 2. Unique data per page

Write down the dataset and its source now, and spot-check three rows end to end.

- Each row needs at least 3 facts that are true only for that row: a delivery day, a price for that area, a cafe partner in that town with permission to name them, local water hardness and how it changes the brew, a dated event.
- Census trivia and Wikipedia sentences about the town do not count.
- Add `source` and `last_verified` columns to the dataset.
- Rows below the bar are dropped from the first version, never padded with filler.

Report one line before building: rows total, rows passing, rows dropped and why.

## 3. Unique content share

Starting rule of thumb: shared boilerplate is at most half of the words a visitor sees on each page, and the row-specific sections come first, above the shared ones.

- Anything that reads the same on every page belongs on the hub page, linked from each row page.
- FAQ questions differ per row because the rows differ, not because a noun was swapped.
- Titles and descriptions vary with real row data, not with the town name alone.

Check it with a sentence-overlap tool across the generated set; any pair of pages sharing about 30% or more of their sentences fails.

## 4. No doorway pages

The doorway test: write the one-paragraph answer for two rows. If the two answers differ only by the swapped word, the set is one page pretending to be many.

Stronger version: would a reader who read page 3 learn something on page 7 they could not get from page 3? If no dataset could make that true, the verdict is NO regardless of search volume.

Other doorway signs:

- pages reachable only through the sitemap, never linked from the site
- pages for towns you do not deliver to or a service you do not offer there
- one business address repeated as if it were a local office in each town
- "x vs y" and "y vs x" as two pages (they are one intent, one page)

## 5. Pilot before scaling

Do not launch the full set.

1. Build the hub plus a pilot of 10-20 rows, picking the rows with the strongest data.
2. The pilot should not grow the site's indexed page count by more than roughly 2-3 times. On a 40-page site, that caps the pilot well below a hundred pages.
3. Link every pilot page from the hub and from at least one relevant existing page.
4. Register the pilot as one action in the ledger (`seo_register.py add <site> --target /cold-brew-in --kind content`) so the result is measured, not guessed.
5. Wait 4-8 weeks, then read Search Console: how many pilot pages are indexed, how many have impressions, and what the "Crawled, currently not indexed" count looks like.
6. Release the next batch (20-50 pages) only when most of the pilot is indexed and earning impressions. If many pages sit as crawled but not indexed, stop and improve quality before adding volume.

After generating any batch, sample 5 random pages (not the 5 best) and check the doorway test, the 3 unique facts, the boilerplate share, and varied titles. A failed sample means fixing the template or the dataset, never hand-patching the pages you sampled.

## 6. Index bloat risk

Each extra low-value page costs crawl attention and dilutes the site's quality signals. Watch for:

- indexed page count rising much faster than pages with impressions
- the pilot pages pulling impressions away from an older page that used to rank for the same query (two of your pages competing)
- thousands of near-empty filter or parameter URLs created as a side effect of the template

Keep generated pages out of the sitemap until they pass the sample check.

## 7. Kill criteria

Decide these before launch and write them next to the ledger entry:

| Signal | Action |
|---|---|
| 0 impressions after 60 days indexed | Enrich with real data, merge into the hub with a redirect, or remove (410 or redirect) |
| Most pilot pages "Crawled, currently not indexed" after 8 weeks | Stop the rollout; fix the template and dataset |
| Overlap check fails after 3 rounds of template fixes | Cut scope to the rows that pass |
| Pilot pages take impressions from an existing page for the same query | Merge, keep the stronger page |
| Site-wide impressions fall after launch while unrelated pages hold steady | Pull the batch back and investigate before anything else |

Register every prune as its own ledger action so the effect is measured like any other change.

## 8. What tends to pass

Sets that carry facts a generic writer could not produce: integration pages built from real setup steps, comparison tables built from collected data, location pages with real local delivery, pricing and partner details, glossary entries with first-hand examples. For Acme Coffee, `/wholesale/<city>` pages with the actual delivery day, minimum order and named partner cafes in that city can pass; `/cold-brew-in-<town>` with a paragraph about the town's history cannot.
