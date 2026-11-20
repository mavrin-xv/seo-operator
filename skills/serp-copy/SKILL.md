---
name: serp-copy
description: Writes title tags and meta descriptions that win the click for the queries a page already ranks for. It drafts several variants by angle, lints them for the mistakes that make Google rewrite or skip a snippet, such as the keyword twice, a title that disagrees with the H1, a keyword string, or a number with no source, scores them out of 100, and ships one so the change can be measured. Use when a page has impressions but a low click rate, when the user asks to "rewrite the title", "write a meta description", "improve CTR", or "my page ranks but nobody clicks".
---

# SERP copy

Turn impressions into clicks on a page that already ranks. The title and description are an ad that runs thousands of times a month for free; most sites leave them as defaults.

## Inputs

- The page URL, its current title, description and H1.
- The queries the page ranks for, with impressions, position and CTR (Search Console, "Queries" filtered to the page). With the `seo-operator` loop, the page's `ctr_gap` row says how many clicks are at stake.
- The facts the copy may use: `truth.md` in the state folder (start from `templates/truth.md`). A number not in it does not go in the copy.
- The brand name as it should appear.

## Steps

1. **Read the queries.** Find the primary query (most impressions at a position of 15 or better) and the intent behind the top 5: do people want a how-to, a price, a place, a comparison? The snippet must answer that intent, not the page's internal name.
2. **Write 3 to 5 variants, one angle each.** Angles: the direct answer, a specific proof from `truth.md`, the outcome for the reader, the comparison, the local or audience fit. Method and examples: `references/serp-copy.md`.
3. **Put them in a CSV** with columns page, variant, title, description, h1, brand, primary (example: `examples/acme-coffee/titles.csv`, including the current copy as a variant).
4. **Lint.** `python3 scripts/serp_lint.py titles.csv --facts truth.md`. Any hard fail removes the variant. The script also gives each variant up to 30 automatic points.
5. **Judge the remaining 70 points** by hand: intent match, proof, distinct from the other results on the page, reads like something a person would click. Scoring table: section 6 of `references/serp-copy.md`. Look at the live results page for the primary query before you judge "distinct".
6. **Ship one variant.** Keep the H1 aligned with the new title; Google rewrites titles that disagree with the page. Change nothing else on the page in the same window.
7. **Register it.** With the loop: `MSYS_NO_PATHCONV=1 python3 ../seo-operator/scripts/seo_register.py add <site> --target /path --kind title-meta --note "old: ... new: ..."`. Keep both titles in the note so the verdict teaches something either way.

## Gates

- No hard fails in the shipped variant.
- Every number and claim traces to `truth.md`. "Award-winning" without the award is out.
- The primary query (or its closest natural form) is in the title, early.
- Brand appears once, at the end, unless the query is a brand query.
- One snippet change per page per 60 days, so the verdict is clean.

## Output

```
/blog/how-to-make-cold-brew current  [FAIL]  auto 12/30  title 72, desc 0
    How to Make Cold Brew | Cold Brew Recipe | Cold Brew Guide | Acme Coffee
    fail: keyword_string
/blog/how-to-make-cold-brew A  [PASS]  auto 30/30  title 54, desc 125
    How to Make Cold Brew at Home: Ratio and 18-Hour Steep
/blog/how-to-make-cold-brew B  [FAIL]  auto 15/30  title 56, desc 110
    fail: generic_adjectives (best, ultimate)
```

Then a table of the passing variants with the judged points, the pick and why, the exact title and description to ship, and the ledger line. Full example: `examples/acme-coffee/serp-lint.txt`.

## Failure modes

| Trap | What it looks like | Instead |
|---|---|---|
| Keyword string | "Cold Brew, Cold Brew Coffee, Best Cold Brew" | one natural phrase, then a reason to click |
| Invented proof | "Rated #1 by 10,000 customers" | only numbers from `truth.md` |
| Title and H1 disagree | title "Cold Brew Guide", H1 "Our Story" | align them, or Google picks its own title |
| Rewriting the home page | the home title "fixed" for CTR | brand searches drive it; leave it |
| Length chasing | stuffing to 60 characters | 45 to 60 is a range, not a target; the angle matters more |
| Changing three things at once | title, H1 and intro all rewritten | one change per window, or the verdict means nothing |
| Generic adjectives | "premium, delicious, perfect" | one specific fact beats three adjectives |
