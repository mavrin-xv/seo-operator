# SERP copy: titles and meta descriptions for a CTR gap

Use this method when a page already shows up in Google (real impressions, average position roughly 2-15) but gets fewer clicks than its position should earn. The fix is the snippet: the `<title>` and the meta description. A page at position 35 does not have a snippet problem; it has a ranking problem, and this method will not help it.

## 1. What the two fields do

The title is the ad for the result. Google builds the title link from your `<title>`, and also from the H1, prominent text on the page and anchor text pointing at it. It rewrites titles often, especially when the title and the H1 disagree or the title is padded. Your job is to hand Google the clearest accurate option, so that when it does rewrite, it rewrites toward your meaning.

The meta description is not a ranking factor. Google uses it when it describes the page well for the query, and replaces it with page text otherwise. Write it with care on money pages and high-impression pages; elsewhere, a competent one is enough.

Spend most of the time on the title.

## 2. Inputs

Collect these before writing a word:

| Input | Where from | Why |
|---|---|---|
| Queries the page ranks for, with impressions, clicks and position | Search Console, Page x Query, last 28-90 days | Decides the primary query and the intent |
| Current title and description | The live page | The baseline variant |
| H1 | The live page | The title must promise the same thing |
| Facts the brand can state | The site's `truth.md` (from `templates/truth.md`) | The only source for numbers and claims |
| What competitors show | The live results page for the primary query | The variant has to stand out from them |

Strip branded queries when the goal is non-brand clicks. Read the results page itself: an AI overview, a map pack or a video block above the results can explain a low CTR better than the title can.

## 3. Writing the title

Formula, pick the two or three strongest blocks: `[primary query or entity] + [specific qualifier or value] + [proof or freshness] + [brand if useful]`.

1. Put the primary query, or a natural close form of it, in the first 40 characters.
2. Give one reason to click that the page delivers: a ratio, a time, a price, a scope, a free tool.
3. Brand last by default. First only when people search the brand itself.
4. Length: 45-60 characters ideal, 35-65 acceptable when the extra words carry meaning.
5. Keep the H1 aligned. If the new title promises something the H1 does not, change the H1 too or pick another variant.
6. No year unless the results page rewards freshness and the page is updated every year.
7. One separator style per title (a colon or a pipe, not both mixed with dashes).

## 4. Writing the description

Formula: `[what is on the page for this intent] + [the decisive detail] + [a light next step where natural]`.

- 120-160 characters. Google cuts by pixel width, so treat the range as a guide.
- Never open by repeating the title; the description expands its promise.
- Use the searcher's words; matched terms are shown in bold.
- A next step only where it fits the intent ("See subscription plans", "Get the wholesale price list"). Never "click here".

## 5. Variants and hard fails

Write 3-5 variants that differ by angle, not five rewordings of one idea. Angles that work for Acme Coffee's `/blog/how-to-make-cold-brew`: the ratio, the steep time, fixing bitter cold brew, cold brew at home vs bought, the question form ("How Long Should Cold Brew Steep?") when the query is a question.

Put the current version and the variants in a CSV shaped like `examples/acme-coffee/titles.csv` and run `scripts/serp_lint.py` on it with `--facts` pointing at the site's `truth.md`. Sample output: `examples/acme-coffee/serp-lint.txt`.

Reject a variant outright, do not soften it, when any of these holds:

| Hard fail | Example |
|---|---|
| Primary query twice in the title | "Cold Brew Guide: Make Cold Brew Easily" |
| Brand twice | "Acme Coffee Cold Brew \| Acme Coffee" |
| Title and H1 promise different things | Title about wholesale, H1 about home brewing |
| A number not in `truth.md` | "Steep 12 Hours" when the spec sheet says 18 |
| Keyword string: 3+ separators | "Cold Brew \| Recipe \| Guide \| Acme Coffee" |
| Boilerplate (brand, separators, site tagline) over half the title | "Acme Coffee \| Small-Batch Roasters \| Cold Brew" |
| 2+ generic adjectives | "The Best Ultimate Cold Brew Guide" |
| Description repeats the title | Description opening with the title text word for word |

## 6. Scoring

Each surviving variant gets a score out of 100. 30 points are automatic and come from `scripts/serp_lint.py`; 70 points are judged by you (or a model) reading the variant next to the queries and the competitors' snippets.

Automatic, 30 points:

| Check | Pts | Full marks when |
|---|---|---|
| Title length | 10 | 45-60 characters (partial inside 35-65) |
| Description length | 8 | 120-160 characters |
| Primary query early | 7 | The primary query appears in the first 40 characters |
| No year | 3 | No year in the title |
| No mixed separators | 2 | One separator style only |

Judged, 70 points:

| Criterion | Pts | Full marks when |
|---|---|---|
| Intent match | 25 | A searcher sees at a glance that this result answers the query they typed, in the format they want |
| Specific proof from truth.md | 20 | The variant carries a concrete detail that is in `truth.md` and on the page (the 1:8 ratio, the 18-hour steep) |
| Distinct from competitors' snippets | 15 | Next to the top results, it offers a reason to pick it that the others do not |
| Reads as a sentence a person would click | 10 | Natural phrase, no jargon, no list of keywords |

Score each judged row with a one-line reason. A variant with a hard fail scores 0 regardless of the sum. If two variants land within 5 points of each other, prefer the one closer to the H1.

## 7. Ship one and register it

1. Ship the top variant. Keep the runner-up written down as the next challenger.
2. Check every claim in it against the page one last time. If the page does not support it, change the copy or improve the page; never ship the mismatch.
3. Register the change in the same session with the seo-operator skill's ledger script, so it can be verified later:

```
python3 seo_register.py add <site> --target /blog/how-to-make-cold-brew --kind title-meta --note "A: ratio + 18-hour steep; was keyword string"
```

4. Change nothing else on that page while the test runs, or you will not know what moved the number.

## 8. Verify after 21+ days

Wait at least 21 days after Google has recrawled the page. Then run the verify step (`seo_register.py verify <site>`), which compares clicks and CTR for the page against its baseline at a comparable average position. CTR is read next to position: a CTR rise with a position drop is not a win, and a position change alone is not a snippet result.

Then look at the title Google renders for the main queries. If Google keeps rewriting it, the cause is usually on the page (H1, prominent text, boilerplate), and that is the next fix.

Outcome: keep the winner, revert to the old copy, or ship the challenger as the next test. Apply a winning pattern to other pages only when they share the same template and intent.
