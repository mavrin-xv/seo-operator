# llms.txt format

Based on the proposal at llmstxt.org (Jeremy Howard, 2024). The file lives at `/llms.txt` on the site root and is plain markdown in a fixed order.

## Structure

1. **One H1** with the site or project name. Required, and it must be the first line.
2. **A blockquote** with a one-line summary: what it is and for whom. Strongly recommended.
3. **Optional paragraphs or lists** with context an agent needs before it reads anything else (how the URLs are organised, where the markdown twins live). No headings here.
4. **H2 sections**, each a list of links: `- [name](url): notes`. The notes are optional in the proposal; write them anyway, one plain line.
5. **An `## Optional` section** last, for links an agent may skip when its context is short (blog posts, legal pages, changelogs).

No H3 or deeper headings. No tables. No HTML.

## What `scripts/llms_txt.py lint` checks

| Check | Level |
|---|---|
| the first non-empty line is an H1 | error |
| exactly one H1 | error |
| a blockquote follows the H1 | warning |
| every list line in an H2 section matches `- [name](url)` with optional `: notes` | error |
| URLs are absolute (`https://...`) | error |
| no URL listed twice | warning |
| at least one H2 section with links | error |
| no H3 or deeper | error |
| a link line with no notes | warning |

## Writing the notes

| Weak | Better |
|---|---|
| `Our subscriptions page` | `Whole beans every 2 or 4 weeks, pause or skip any time.` |
| `Learn more about wholesale` | `Beans and cold brew kegs for cafes and offices, with a sample box.` |
| `Blog post` | `Ratio, grind and steep time, and how to fix a bitter batch.` |

Each note says what question the page answers, with one fact from the page.

## Related files

- `llms-full.txt`: the proposal allows a second file with the full text of the linked pages. Build it only for documentation-style sites; for a business site, the markdown mirrors do the same job page by page.
- The markdown twins: the proposal suggests serving a page's markdown at the same URL with `.md` appended. Say in the paragraph block which convention the site uses.

## Example

`examples/acme-coffee/llms.txt`:

```
# Acme Coffee

> Small-batch coffee roaster: cold brew, beans by subscription, and wholesale for cafes.

Every page below also has a markdown twin at the same URL plus index.md.

## Products and services

- [Coffee Subscriptions](https://acme-coffee.com/subscriptions/): Whole beans every 2 or 4 weeks, pause or skip any time.

## Optional

- [How to Make Cold Brew at Home](https://acme-coffee.com/blog/how-to-make-cold-brew/): Ratio, grind and steep time, and how to fix a bitter batch.
```
