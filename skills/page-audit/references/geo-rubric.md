# GEO rubric (60 of 100 points)

GEO means generative engine optimization: how ready a page is to be lifted into an AI answer (ChatGPT search, Perplexity, Claude, Gemini, Google AI Overviews). The question this axis answers: when someone asks an assistant a question this page covers, can the assistant find a clean, quotable, trustworthy passage here and cite it?

GEO carries the most weight in the page audit because it rewards the same things a hurried human reader wants: the answer first, short self-contained sections, numbers with a source.

## 1. Score from facts, not impressions

Run `scripts/page_facts.py` on the page or draft before scoring. It prints the countable facts this rubric needs:

- word count, number of H1s, the heading outline
- question headings (headings phrased as a question)
- the word count of the first paragraph under each H2
- lists, tables, JSON-LD types, internal and external links
- dates found on the page
- numbers that appear with no source in the same sentence

Every sub-score you give must point at one of those facts or at a quoted sentence. "Structure is good" is not evidence. "5 of 6 H2s open with a 40-80 word answer" is. See `examples/acme-coffee/page-facts.txt` for a real output on `examples/acme-coffee/page.md`.

## 2. Sub-dimensions

| # | Dimension | Pts | Full | Half | Zero |
|---|---|---|---|---|---|
| 1 | Direct answer up front | 10 | The first 100 words answer the page's main question in plain words, with a specific detail (a ratio, a time, a price) | The answer exists but sits in paragraph 3 or later | No explicit answer; the reader has to assemble it |
| 2 | Answer-shaped sections | 8 | Most H2s open with a 40-80 word paragraph that makes sense on its own, without "as mentioned above" | About half do, or openers run long (120+ words) | Sections open with scene-setting or transitions |
| 3 | Question headings | 6 | 3+ headings phrased the way people ask (real queries from Search Console or suggest data) | 1-2 question headings, or questions nobody types | No question headings |
| 4 | Specific, sourced numbers | 10 | Every number in the body has a source or a method in the same sentence; at least one is first-hand (your own test, your own spec sheet) | Numbers present, some unsourced | No numbers, or only vague words ("many", "most people") |
| 5 | External citations | 5 | 2+ links to primary or respected sources, named in the sentence | 1 citation | None, pure assertion |
| 6 | Heading hierarchy and chunk size | 6 | One H1, H2/H3 nest cleanly, sections mostly 100-250 words | Hierarchy fine but sections of 400+ words | One H1 and a wall of paragraphs |
| 7 | Lists and tables | 5 | Steps as a numbered list; any comparison as a table | Lists present, comparisons in prose | Neither |
| 8 | Named terms defined | 4 | Each product name or method name is defined in one sentence the first time it appears ("Acme Overnight is our 18-hour cold brew concentrate") | Terms used, not defined | Generic words only ("our product", "the blend") |
| 9 | Freshness | 3 | Visible updated date within the last 90 days, and the content matches it | Date older than 90 days, content still current | No date, or stale facts |
| 10 | Entity and crawl hygiene | 3 | Article or Product JSON-LD plus Organization, a named author, and no sign that AI crawlers are blocked | One of those missing | No markup, no author, or a crawler block suspected |

Sum the ten rows for the GEO score out of 60. Half credit is a guide; give any integer in the range when the page sits between two columns, and say why.

Word-count and section-length ranges above are starting rules of thumb. Adjust them for the page type: a pricing page needs fewer words than a how-to guide.

## 3. Notes per dimension

**Direct answer.** Test it by covering everything after the first 100 words. If a reader can act on what is left, award full points. For Acme Coffee's `/blog/how-to-make-cold-brew`, full points looks like: "Mix 1 part coarse ground coffee with 8 parts cold water, steep 18 hours in the fridge, then strain."

**Answer-shaped sections.** Read the `first answer under each H2` block in the page facts output. A 20-word opener is too thin to quote; a 150-word opener gets truncated. Aim for 40-80.

**Sourced numbers.** Every line in the `numbers with no source` block costs points here. A number that is not in `templates/truth.md` (copied per site) and has no source is a candidate hard fail (see below). "Most people find cold brew 3 times smoother" is the classic case: delete it or source it.

**Markup.** FAQ and HowTo rich results no longer show for most sites, so do not award points for FAQPage or HowTo markup itself. Award the visible question and answer pairs (dimensions 2 and 3) and keep Article, Product and Organization markup for clear attribution.

**Crawl access.** A page can only be cited if search and user-fetch crawlers can reach it. You usually cannot see robots.txt from a draft, so flag it as "not checked" rather than scoring it as fine.

## 4. Deductions

Apply after summing, floor the axis at 0.

| Pattern | Deduct |
|---|---|
| Stock AI phrasing in the opening (a generic scene-setting line about "the modern world", or an announcement that the post is about to begin) | 3 |
| Marketing prose with no data in any section | 3 |
| Cites only the site's own pages, nothing third-party | 3 |
| Hype words in place of numbers ("lightning fast", "insanely smooth") | 2 |

## 5. Hard fails

A hard fail sets the page verdict to REWRITE or BLOCK regardless of points:

- The main question of the page is never answered on the page.
- A number presented as fact is not in the site's `truth.md` and has no source (an unsupported claim an assistant would repeat).
- The main content is not in the raw HTML (rendered by JavaScript only), so crawlers see an empty page.
- The page is blocked to search crawlers by robots.txt or a noindex tag while it is meant to be found.

## 6. How to report

Report GEO as `GEO NN/60`, then three lines: one strength, one moderate issue, one critical miss, each with its count or quote. Then list fixes that touch GEO, each with:

1. Location: heading name or paragraph number.
2. Problem: what the facts show.
3. Fix: the exact sentence or structure to add or replace.
4. Gain: which dimension and roughly how many points.

Bad fix: "Add more data." Good fix: "Under 'Why does my cold brew taste bitter?' the opener is 18 words. Replace with a 50-word answer naming grind size and steep time past 24 hours, sourced to the kitchen spec sheet. Dimension 2, about +3."

End the report with a "not checked" line for anything you could not see from the draft (robots.txt, rendered markup, live date).
