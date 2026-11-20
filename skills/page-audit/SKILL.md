---
name: page-audit
description: Audits one page or one draft before it ships and scores it out of 100 on three axes, GEO (whether AI assistants can quote it) 60, classic SEO 30, and brand recommendation 10. It scores from countable facts pulled by a script (outline, question headings, answer length under each heading, lists, tables, schema, links, unsourced numbers) rather than impressions, and returns the fixes in order of points. Use when the user pastes a blog draft or landing copy, asks to "audit this page", "check this article for SEO", "will ChatGPT cite this", or "review the copy from our writer".
---

# Page audit

Score one page on whether search engines can rank it and AI assistants can quote it, then hand back the few edits worth the most points. This is the single-page mode; site-wide work belongs to `seo-operator`.

## Inputs

- The page: a URL, an HTML file, or a markdown or text draft.
- The primary query the page should win, and 2 to 5 secondary ones.
- The facts the page may claim (`truth.md`, or the owner's source list).
- The brand and what it sells, for the brand recommendation axis.

## Steps

1. **Pull the facts.** `python3 scripts/page_facts.py page.md` (or a URL). It prints title and description lengths, word count, the outline, H1 count, question headings, the first-paragraph length under each H2, lists, tables, JSON-LD types, links, dates, and sentences with a number but no source. Score from this output.
2. **Score GEO, 60 points.** Does each section open with a direct answer of 40 to 80 words? Are the headings the questions people ask? Are claims sourced and dated? Is there a table or list where the content is a comparison or steps? Rubric: `references/geo-rubric.md`.
3. **Score SEO, 30 points.** Title and H1 match the primary query, one H1, description present, internal links to and from related pages, schema that fits the page type, depth that matches the intent. Rubric: `references/seo-rubric.md`.
4. **Score brand recommendation, 10 points.** Would an assistant asked "which coffee subscription should I get" have a reason to name this brand from this page: a clear category statement, who it is for, specific differentiators, proof? Rubric: `references/brand-rec-rubric.md`.
5. **Check the hard fails** in each rubric. One hard fail caps the page at "fix before shipping", whatever the total.
6. **Write the fix list** ordered by points recovered per minute of editing. Give the exact replacement text for the top fixes, not advice.

## Gates

- Every score cites a line from the `page_facts.py` output or the page itself.
- A number without a source in the same sentence is a finding, never ignored. Either add the source from the facts file or cut the number.
- Do not invent sources, studies or quotes to fix a finding. If the fact is not known, the fix is "ask the owner" and it goes to `needs-you.md`.
- Do not reward length. A 600-word page that answers the query beats a 3,000-word page that circles it.

## Output

```
Page audit: /blog/how-to-make-cold-brew (draft)
Total 58/100   GEO 33/60   SEO 18/30   Brand 7/10
Hard fails: 1 unsourced claim ("3 times smoother")
Top fixes (points per minute)
  1  +6  cut or source "3 times smoother than hot coffee"
  2  +5  expand the steep-time answer to 40-80 words (now 20)
  3  +4  add a ratio table (coffee grams, water ml, strength)
  4  +3  write a description, 120-160 characters
```

Then each axis table with points and the evidence line, and the rewritten passages. Sample input and facts: `examples/acme-coffee/page.md`, `examples/acme-coffee/page-facts.txt`.

## Failure modes

| Trap | What it looks like | Instead |
|---|---|---|
| Scoring by feel | "reads well, 8/10" | every point cites a fact line |
| Rewarding word count | longer draft scores higher | score answers per question, not words |
| Fixing claims with fake sources | "according to a recent study" | source it from the facts file or cut it |
| Keyword density advice | "use the keyword 12 times" | match the query in title, H1 and first answer; then write for the reader |
| Schema for its own sake | FAQ schema on a page with no FAQ | only schema that describes what the page shows |
| Generic advice list | 25 tips, none specific | 3 to 5 fixes with exact replacement text |
