#!/usr/bin/env python3
"""Lint a markdown mirror (the .md twin of an HTML page) before it ships.

A mirror is read by agents and AI crawlers, so it must hold the page's facts
in plain markdown with nothing a parser trips on. Checks:

  errors   no H1 on the first line, YAML frontmatter, more than one H1,
           relative links, raw HTML tags, leftover site chrome (cookie banner,
           "subscribe", "all rights reserved", nav menus), no footer line
           naming the canonical URL, a number in Key Numbers without a link
  warnings no blockquote summary under the H1, no "What is <Brand>?" section,
           FAQ questions not written as "### Q:", fewer than 2 sources,
           length outside --min/--max words (default 200-1500), a heading
           level skipped (H2 straight to H4)

See references/mirror-format.md for the two formats (article and landing page).

Examples:
    python3 mirror_lint.py mirror.md
    python3 mirror_lint.py mirror.md --canonical https://acme-coffee.com/blog/how-to-make-cold-brew/
Exit codes: 0 no errors, 1 errors, 2 bad input.
"""
import argparse
import re
import sys

CHROME = re.compile(r"accept (all )?cookies|cookie (policy|settings)|subscribe to our newsletter|"
                    r"all rights reserved|skip to (main )?content|back to top|toggle navigation|"
                    r"\bmenu\b\s*\|\s*\w+\s*\|", re.I)


def section(lines, name):
    out, on = [], False
    for l in lines:
        if l.startswith("## "):
            on = l[3:].strip().lower().startswith(name)
            continue
        if on:
            out.append(l)
    return out


def main():
    for s in (sys.stdout, sys.stderr):
        try:
            s.reconfigure(encoding="utf-8")
        except (AttributeError, ValueError):
            pass
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0], epilog=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("file")
    ap.add_argument("--canonical", help="the HTML page URL the footer must name")
    ap.add_argument("--min", type=int, default=200)
    ap.add_argument("--max", type=int, default=1500)
    a = ap.parse_args()
    try:
        with open(a.file, encoding="utf-8") as fh:
            text = fh.read()
    except OSError as e:
        print("cannot read %s: %s" % (a.file, e), file=sys.stderr)
        sys.exit(2)
    lines = text.splitlines()
    body = [l for l in lines if l.strip()]
    errs, warns = [], []
    if text.startswith("---"):
        errs.append("YAML frontmatter: start the file with the H1, metadata goes in a section")
    if not body or not body[0].startswith("# "):
        errs.append("first line must be the H1 (the page's own H1)")
    if sum(1 for l in lines if l.startswith("# ")) > 1:
        errs.append("more than one H1")
    in_code = False
    for i, l in enumerate(lines, 1):
        if l.startswith("```"):
            in_code = not in_code
        if in_code:
            continue
        for m in re.finditer(r"\]\(([^)\s]+)\)", l):
            if not re.match(r"(https?://|mailto:|#)", m.group(1)):
                errs.append("line %d: relative link %s (agents read the file out of context)" % (i, m.group(1)))
        if re.search(r"</?(div|span|br|img|script|style|section|nav|button)\b", l, re.I):
            errs.append("line %d: raw HTML tag" % i)
        if CHROME.search(l):
            errs.append("line %d: site chrome left in: %s" % (i, l.strip()[:60]))
    last = body[-1] if body else ""
    if not re.search(r"mirror of\s+https?://", last, re.I):
        errs.append("last line must name the canonical page: *Markdown mirror of <url>. ...*")
    elif a.canonical and a.canonical not in last:
        errs.append("footer names a different URL than --canonical")
    for l in section(lines, "key numbers"):
        if l.startswith("- ") and re.search(r"\d", l) and "](" not in l:
            errs.append("Key Numbers line without a source link: %s" % l.strip()[:60])
    if len(body) > 1 and not body[1].startswith(">"):
        warns.append("no one-line blockquote summary under the H1")
    if not any(re.match(r"## What is .+\?", l) for l in lines):
        warns.append("no '## What is <Brand>?' section (the block agents quote for 'what is X')")
    faq = section(lines, "faq")
    if faq and not any(l.startswith("### Q:") for l in faq):
        warns.append("FAQ questions are not written as '### Q: ...'")
    src = [l for l in section(lines, "sources") if l.startswith("- ")]
    if len(src) < 2:
        warns.append("%d source(s); list at least 2 with dates" % len(src))
    words = len(re.sub(r"[#>*|`\-]", " ", text).split())
    if not a.min <= words <= a.max:
        warns.append("%d words, outside %d-%d" % (words, a.min, a.max))
    prev = 1
    for l in lines:
        m = re.match(r"^(#{1,6}) ", l)
        if m:
            lv = len(m.group(1))
            if lv > prev + 1:
                warns.append("heading level skipped: %s" % l.strip()[:50])
            prev = lv
    for e in errs:
        print("error  " + e)
    for w in warns:
        print("warn   " + w)
    print("%s: %d words, %d errors, %d warnings" % (a.file, words, len(errs), len(warns)))
    sys.exit(1 if errs else 0)


if __name__ == "__main__":
    main()
