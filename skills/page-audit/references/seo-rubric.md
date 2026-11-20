# SEO rubric (30 of 100 points)

This axis answers: will Google rank this page for the queries it is meant to win, and will the snippet earn the click? It covers classic on-page work: title and H1, intent match, query coverage, internal links, trust signals and basic technical hygiene you can read off the page.

It carries less weight than GEO because much of it overlaps (a page that answers clearly and cites sources usually ranks better too), and because ranking also depends on things a single-page audit cannot see, such as links from other sites.

## 1. Score from facts, not impressions

Run `scripts/page_facts.py` first. For this axis you need: title and its length, description and its length, H1 count and text, the outline, word count, internal and external link counts, JSON-LD types and dates. Every sub-score cites one of those facts or a quoted line.

If you have Search Console queries for the page, have them open. Intent and coverage are judged against what people type, not against what the writer guessed.

## 2. Sub-dimensions

| # | Dimension | Pts | Full | Half | Zero |
|---|---|---|---|---|---|
| 1 | Title, H1 and description | 6 | Title 35-65 characters with the primary query near the start; H1 promises the same thing; description 120-160 characters with one specific detail | Title or H1 vague, or description missing | Title is a slogan, H1 is unrelated, no description |
| 2 | Intent match | 6 | The format fits the query type: steps for "how to", a table for "x vs y", prices in text for "pricing", an order path for "buy" | Intent right, format wrong (a comparison written as prose) | Page answers a different question than the query asks |
| 3 | Query coverage | 5 | Primary query plus the related terms and sub-questions people search, used naturally in headings and body | Primary query present, sub-questions missing | No clear primary query, or the same phrase repeated until it reads badly |
| 4 | Internal links | 4 | 3+ internal links with descriptive anchors, including one to the money page that fits (for a cold brew guide: `/subscriptions`) | 1-2 links, or anchors like "click here" | No internal links; the page is an island |
| 5 | Experience and trust | 4 | Named author, first-hand detail ("we steep every batch 18 hours"), a visible date, sources for claims | Some of these | Anonymous, undated, no first-hand detail |
| 6 | Depth for the intent | 3 | Covers what the top results cover plus something they lack (your own data, a real mistake and its fix) | Covers the basics only | Thinner than the results it competes with |
| 7 | On-page hygiene | 2 | Exactly one H1, short paragraphs that read on a phone, valid JSON-LD that matches the page, no duplicated block from another page on the site | One issue | Several issues |

Sum the rows for the SEO score out of 30. Give any integer within a row when the page sits between columns and say why.

Character ranges and link counts are starting rules of thumb, not studied limits. A navigational page can be short; a guide competing with long guides cannot.

## 3. Notes per dimension

**Title and H1.** Google writes its own title link often, and it builds that link partly from the H1 and prominent text. A title the H1 contradicts is the most common reason the shown title differs from the one you wrote. For deeper title work on a page that already gets impressions, hand off to the serp-copy skill.

**Intent.** Look at the query, then at what already ranks. If every top result for "cold brew ratio" is a short answer with a table, a 3,000-word story will lose no matter how good it is.

**Coverage.** For `/blog/how-to-make-cold-brew`, related terms a reader expects: ratio, grind size, steep time, fridge vs room temperature, concentrate, dilution, how long it keeps. Missing sub-questions are the cheapest gains in the whole audit.

**Internal links.** Every informational page should hand readers to the next step. A cold brew guide that never mentions bean subscriptions wastes its traffic. Anchors say what is behind the link ("our cold brew bean subscription"), not "learn more".

**Experience.** First-hand detail is the hardest thing to fake and the easiest for a real business to add: what you measured, what went wrong, what you changed.

## 4. Deductions

Apply after summing, floor the axis at 0.

| Pattern | Deduct |
|---|---|
| Primary phrase repeated so often it reads as stuffing | 3 |
| Title and H1 promise different things | 2 |
| A paragraph copied word for word from another page on the same site | 2 |
| No date on content where freshness matters (prices, seasonal offers) | 1 |

## 5. Hard fails

Set the verdict to REWRITE or BLOCK regardless of points:

- The page carries a noindex tag or a canonical pointing elsewhere while it is meant to rank.
- Hidden text or content shown to crawlers but not to people.
- The title or description states a price, date or count the page does not support.
- The page targets the same query as another page on the site with the same intent and nothing separates them (two pages competing, one should merge into the other).

## 6. How to report

Report as `SEO NN/30`, then one strength, one moderate issue and one critical miss with counts or quotes. Each fix names the location, the problem, the exact replacement and the dimension it lifts.

Example fix: "Title is 72 characters and lists three near-identical phrases separated by pipes. Replace with 'How to Make Cold Brew at Home: Ratio and 18-Hour Steep' (54 characters). Dimension 1, about +3."

Items you cannot verify from a draft (live canonical, Core Web Vitals, rendered JSON-LD) go on a "not checked" line, never into the score as a pass.
