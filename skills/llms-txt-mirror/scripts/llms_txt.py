#!/usr/bin/env python3
"""Draft an llms.txt from a crawl, or lint one you already have.

    build  --snapshot health/<date>.json --name "Acme Coffee" --summary "..."
           Groups every indexable 200 page by its first path segment, writes
           "- [Title](url): description" lines, puts money pages first under
           their own section and sends the blog, legal and tag pages to
           "## Optional" (the spec's section an agent may skip when short on
           context). Prints to stdout; review it before publishing, because
           a crawl title is not always the name a human would give the page.
    lint   llms.txt
           Checks the format from llmstxt.org: one H1 first, an optional
           blockquote summary, H2 sections of "- [name](url): notes" lists,
           absolute URLs, no duplicate URLs, no headings below H2.

Examples:
    python3 llms_txt.py build --snapshot .seo/acme-coffee/health/2026-11-18.json \\
        --name "Acme Coffee" --summary "Small-batch roaster with cold brew and subscriptions." \\
        --base https://acme-coffee.com --money /subscriptions --money /wholesale > llms.txt
    python3 llms_txt.py lint llms.txt
Exit codes: 0 ok, 1 lint errors, 2 bad input.
"""
import argparse
import json
import re
import sys
import urllib.parse

OPTIONAL = ("blog", "news", "tag", "tags", "category", "author", "legal", "privacy", "terms", "cookies",
            "careers", "press")
LINK = re.compile(r"^- \[([^\]]+)\]\(([^)\s]+)\)(: .+)?$")


def cmd_build(a):
    with open(a.snapshot, encoding="utf-8") as fh:
        snap = json.load(fh)
    pages = snap["pages"].values() if isinstance(snap["pages"], dict) else snap["pages"]
    base = (a.base or "").rstrip("/")
    groups, money, seen = {}, [], set()
    for p in pages:
        # a redirect that lands on a 200 page is listed under its final URL
        if p.get("status") != 200 or "noindex" in (p.get("robots") or "").lower():
            continue
        path = urllib.parse.urlsplit(p.get("final") or p["url"]).path or "/"
        if path in seen:
            continue
        seen.add(path)
        url = base + path if base else p["url"]
        title = (p.get("h1") or p.get("title") or path).split(" | ")[0].strip()
        desc = (p.get("description") or "").strip()
        line = "- [%s](%s)%s" % (title, url, ": " + desc if len(desc) >= 20 else "")
        if path == "/":
            continue
        if any(path.startswith(m) for m in a.money):
            money.append(line)
            continue
        seg = path.strip("/").split("/")[0]
        groups.setdefault(seg, []).append(line)
    out = ["# %s" % a.name, ""]
    if a.summary:
        out += ["> %s" % a.summary, ""]
    if a.notes:
        out += [a.notes, ""]
    if money:
        out += ["## %s" % a.money_title, ""] + sorted(money) + [""]
    for seg in sorted(g for g in groups if g not in OPTIONAL):
        out += ["## %s" % seg.replace("-", " ").capitalize(), ""] + sorted(groups[seg]) + [""]
    opt = [l for g in sorted(groups) if g in OPTIONAL for l in sorted(groups[g])]
    if opt:
        out += ["## Optional", ""] + opt + [""]
    short = sum(1 for l in out if l.startswith("- [") and "): " not in l)
    print("\n".join(out).rstrip() + "\n")
    if short:
        print("note: %d entries have no description; add one line each by hand" % short, file=sys.stderr)


def cmd_lint(a):
    try:
        with open(a.file, encoding="utf-8") as fh:
            lines = fh.read().splitlines()
    except OSError as e:
        print("cannot read %s: %s" % (a.file, e), file=sys.stderr)
        sys.exit(2)
    errs, warns, urls = [], [], {}
    body = [l for l in lines if l.strip()]
    if not body or not body[0].startswith("# "):
        errs.append("line 1 must be the H1 with the site or project name")
    if sum(1 for l in lines if re.match(r"^# ", l)) > 1:
        errs.append("more than one H1")
    if len(body) > 1 and not body[1].startswith(">"):
        warns.append("no blockquote summary after the H1 (optional in the spec, but agents read it first)")
    section, n_links = None, 0
    for i, l in enumerate(lines, 1):
        if l.startswith("## "):
            section = l[3:].strip()
            continue
        if re.match(r"^#{3,} ", l):
            errs.append("line %d: headings below H2 are not part of the format" % i)
        if l.startswith("- ") and section:
            m = LINK.match(l)
            if not m:
                errs.append("line %d: list items must be '- [name](url): notes'" % i)
                continue
            n_links += 1
            u = m.group(2)
            if not re.match(r"https?://", u):
                errs.append("line %d: URL must be absolute: %s" % (i, u))
            if u in urls:
                warns.append("line %d: duplicate URL (first on line %d)" % (i, urls[u]))
            urls.setdefault(u, i)
            if not m.group(3):
                warns.append("line %d: no description after the link" % i)
    if not n_links:
        errs.append("no H2 section with links")
    for e in errs:
        print("error  " + e)
    for w in warns:
        print("warn   " + w)
    print("%s: %d links, %d errors, %d warnings" % (a.file, n_links, len(errs), len(warns)))
    sys.exit(1 if errs else 0)


def main():
    for s in (sys.stdout, sys.stderr):
        try:
            s.reconfigure(encoding="utf-8")
        except (AttributeError, ValueError):
            pass
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0], epilog=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    b = sub.add_parser("build", help="draft llms.txt from a crawl snapshot")
    b.add_argument("--snapshot", required=True)
    b.add_argument("--name", required=True)
    b.add_argument("--summary", default="")
    b.add_argument("--notes", default="", help="a plain paragraph after the summary")
    b.add_argument("--base", help="public origin to use instead of the crawled one")
    b.add_argument("--money", action="append", default=[], help="path prefix listed first (repeatable)")
    b.add_argument("--money-title", default="Products and services")
    b.set_defaults(fn=cmd_build)
    l = sub.add_parser("lint", help="check an llms.txt against the format")
    l.add_argument("file")
    l.set_defaults(fn=cmd_lint)
    a = ap.parse_args()
    a.fn(a)


if __name__ == "__main__":
    main()
