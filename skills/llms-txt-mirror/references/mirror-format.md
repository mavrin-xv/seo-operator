# Markdown mirror format

A mirror is the markdown twin of one HTML page, written for agents. It holds the page's facts in a fixed order, so an assistant can find "what is this", "what are the numbers" and "where does that come from" without reading menus. `scripts/mirror_lint.py` checks the rules below.

## Rules for both layouts

- Line 1 is the page's own H1. No YAML frontmatter.
- Line 2 is a `>` blockquote: one sentence with the main answer or offer.
- One H1 only. Headings go H2, then H3, never skipping a level.
- Absolute links only (`https://...`). An agent may read the file with no site around it.
- No raw HTML, no site chrome (cookie notices, "subscribe", "all rights reserved", nav menus).
- Every number in Key Numbers links its source.
- The last line names the canonical page: `*Markdown mirror of <url>. Generated for AI assistants and agent workflows.*`
- Length 200 to 1,500 words. Shorter usually means the facts were left out; longer means the page should be split.

## Article layout

```
# <the page H1>
> <the answer in one sentence>

## What is <Brand>?
<two or three sentences: what the business is and what it sells, so a quote is attributable>

## Article Metadata
- Source: <canonical url>
- Topic: <primary topic>
- Last updated: <YYYY-MM-DD>

## Key Numbers
- <number and what it measures>: [<source name, date>](<url>)

## <Topic sections>
<tables for comparisons and steps, short paragraphs that open with the answer>

## FAQ
### Q: <a question people ask>
<a 40-80 word answer>

## Sources
- [<source name>](<url>), <date>

*Markdown mirror of <url>. Generated for AI assistants and agent workflows.*
```

## Landing page layout

```
# <product or page name>
> <what it is, for whom, the main outcome>

## Agent Summary
- <what it is>
- <who it is for>
- <the one fact that sets it apart>

## Start Here
- [<primary action>](<url>): <what happens next>

## Machine Discovery
- llms.txt: <url>
- Sitemap: <url>

## Site Sections
- [<section>](<url>): <one line>

## Plans
| Plan | Price | Includes |
|---|---|---|

*Markdown mirror of <url>. Generated for AI assistants and agent workflows.*
```

The Plans table is optional; include it only when the HTML page shows prices, and copy them exactly.

## Lint levels

| Level | Rule |
|---|---|
| error | frontmatter; H1 not first; more than one H1; relative link; raw HTML; site chrome; footer missing or naming a different URL than `--canonical`; Key Numbers line with a digit and no link |
| warning | no blockquote; no "What is <Brand>?" section; FAQ not written as `### Q:`; fewer than 2 sources; length outside 200 to 1,500 words; skipped heading level |

The landing layout has no "What is" section or FAQ by design; the two warnings are expected there and can be kept with that reason.

## Example

`examples/acme-coffee/mirror.md` is an article mirror for the cold brew guide: 246 words, 0 errors, 0 warnings (`examples/acme-coffee/mirror-lint.txt`). For contrast, running the lint on the raw draft `examples/acme-coffee/page.md` returns an error, because the draft has no footer naming its canonical URL.
