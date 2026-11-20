#!/usr/bin/env python3
"""Pull the countable facts out of one page so the audit scores evidence, not vibes.

Input: a URL, a local .html file, or a .md/.txt draft (a copywriter's doc
exported as text). Output: title and description with lengths, the heading
outline, word count, question headings, the first-answer length under each
H2, lists and tables, JSON-LD types, internal vs external links, dates,
named numbers, and a list of claims with a number but no link or source
nearby. The rubric in references/geo-rubric.md reads these facts.

Examples:
    python3 page_facts.py https://acme-coffee.com/blog/how-to-make-cold-brew
    python3 page_facts.py draft.md --format json
Exit codes: 0 ok, 2 could not read the input.
"""
import argparse
import html
import json
import re
import sys
import urllib.parse
import urllib.request

UA = "Mozilla/5.0 (compatible; page-facts/0.1)"


def load(src):
    if re.match(r"https?://", src):
        req = urllib.request.Request(src, headers={"User-Agent": UA})
        with urllib.request.urlopen(req, timeout=20) as r:
            return r.read().decode("utf-8", "ignore"), True
    with open(src, encoding="utf-8") as fh:
        text = fh.read()
    return text, src.lower().endswith((".html", ".htm"))


def md_to_blocks(text):
    """Markdown or plain text -> (headings, paragraphs, lists, tables)."""
    heads, paras, lists, tables, buf = [], [], 0, 0, []
    in_list = False
    for line in text.splitlines():
        m = re.match(r"^(#{1,6})\s+(.*)", line)
        if m:
            heads.append((len(m.group(1)), m.group(2).strip()))
            if buf:
                paras.append((len(heads) - 1, " ".join(buf)))
                buf = []
            continue
        if re.match(r"^\s*([-*+]|\d+[.)])\s+", line):
            lists += 0 if in_list else 1
            in_list = True
        else:
            in_list = False
        if line.strip().startswith("|") and "---" in line:
            tables += 1
        if line.strip():
            buf.append(line.strip())
        elif buf:
            paras.append((len(heads), " ".join(buf)))
            buf = []
    if buf:
        paras.append((len(heads), " ".join(buf)))
    return heads, paras, lists, tables


def strip(s):
    return html.unescape(re.sub(r"<[^>]+>", " ", s)).strip()


def html_facts(doc, base):
    f = {}
    m = re.search(r"<title[^>]*>(.*?)</title>", doc, re.I | re.S)
    f["title"] = strip(m.group(1)) if m else ""
    m = re.search(r"<meta\s[^>]*name\s*=\s*[\"']?description[\"']?[^>]*>", doc, re.I)
    d = re.search(r"content\s*=\s*(\"[^\"]*\"|'[^']*'|[^\s>]+)", m.group(0), re.I) if m else None
    f["description"] = html.unescape(d.group(1).strip("\"'")) if d else ""
    f["jsonld_types"] = sorted(set(re.findall(r'"@type"\s*:\s*"([^"]+)"', " ".join(
        re.findall(r"<script[^>]*ld\+json[^>]*>(.*?)</script>", doc, re.I | re.S)))))
    body = re.sub(r"<(script|style|noscript|template|svg)\b.*?</\1>", " ", doc, flags=re.I | re.S)
    heads = [(int(lv), strip(t)) for lv, t in re.findall(r"<h([1-6])[^>]*>(.*?)</h\1>", body, re.I | re.S)]
    # paragraph text grouped by the heading that precedes it
    paras, idx = [], 0
    for tag in re.finditer(r"<h[1-6][^>]*>.*?</h[1-6]>|<p[^>]*>(.*?)</p>", body, re.I | re.S):
        if tag.group(0)[:2].lower() == "<h":
            idx += 1
        elif strip(tag.group(1) or ""):
            paras.append((idx, strip(tag.group(1))))
    host = urllib.parse.urlsplit(base).netloc if base else ""
    internal = external = 0
    for h in re.findall(r"<a\s[^>]*href\s*=\s*[\"']?([^\"'\s>]+)", body, re.I):
        if h.startswith(("#", "mailto:", "tel:", "javascript:")):
            continue
        n = urllib.parse.urlsplit(urllib.parse.urljoin(base or "http://x/", h)).netloc
        if n in (host, "x"):
            internal += 1
        else:
            external += 1
    f.update(heads=heads, paras=paras, lists=len(re.findall(r"<(ul|ol)\b", body, re.I)),
             tables=len(re.findall(r"<table\b", body, re.I)), internal_links=internal,
             external_links=external, text=strip(body))
    return f


def facts(src):
    doc, is_html = load(src)
    if is_html:
        f = html_facts(doc, src if src.startswith("http") else "")
    else:
        heads, paras, lists, tables = md_to_blocks(doc)
        title = next((t for lv, t in heads if lv == 1), "")
        links = re.findall(r"\]\((https?://[^)]+)\)", doc)
        f = {"title": title, "description": "", "jsonld_types": [], "heads": heads, "paras": paras,
             "lists": lists, "tables": tables, "internal_links": len(re.findall(r"\]\((/[^)]*)\)", doc)),
             "external_links": len(links), "text": re.sub(r"[#*_`>|]", " ", doc)}
    words = f["text"].split()
    first_under_h2 = []
    for i, (lv, t) in enumerate(f["heads"]):
        if lv == 2:
            p = next((p for k, p in f["paras"] if k == i + 1), "")
            first_under_h2.append({"h2": t, "first_paragraph_words": len(p.split()),
                                   "is_question": t.rstrip().endswith("?")})
    claims = []
    for _, p in f["paras"]:
        for s in re.split(r"(?<=[.!?])\s+", p):
            if re.search(r"\d+(\.\d+)?\s?(%|x\b|percent|times|hours|minutes|days)", s, re.I) \
                    and not re.search(r"https?://|\]\(|according to|source:|\bper\b", s, re.I):
                claims.append(s.strip()[:160])
    return {
        "source": src, "title": f["title"], "title_len": len(f["title"]),
        "description": f["description"], "description_len": len(f["description"]),
        "word_count": len(words), "outline": ["%s%s" % ("  " * (lv - 1), t) for lv, t in f["heads"]],
        "h1_count": sum(1 for lv, _ in f["heads"] if lv == 1),
        "question_headings": sum(1 for _, t in f["heads"] if t.rstrip().endswith("?")),
        "sections": first_under_h2, "lists": f["lists"], "tables": f["tables"],
        "jsonld_types": f["jsonld_types"], "internal_links": f["internal_links"],
        "external_links": f["external_links"],
        "dates": sorted(set(re.findall(r"\b20\d\d-\d\d-\d\d\b|\b(?:Updated|Published)[: ]+[A-Z][a-z]+ \d{1,2},? 20\d\d",
                                       f["text"]))),
        "numbers_without_source": claims[:20],
    }


def main():
    for s in (sys.stdout, sys.stderr):
        try:
            s.reconfigure(encoding="utf-8")
        except (AttributeError, ValueError):
            pass
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0], epilog=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("source", help="URL, .html file, or .md/.txt draft")
    ap.add_argument("--format", choices=("text", "json"), default="text")
    a = ap.parse_args()
    try:
        r = facts(a.source)
    except (OSError, ValueError) as e:
        print("cannot read %s: %s" % (a.source, e), file=sys.stderr)
        sys.exit(2)
    if a.format == "json":
        print(json.dumps(r, indent=1, ensure_ascii=False))
        return
    print("source       %s" % r["source"])
    print("title        %s (%d chars)" % (r["title"] or "(none)", r["title_len"]))
    print("description  %s" % ("%d chars" % r["description_len"] if r["description_len"] else "(none)"))
    print("words        %d   H1s %d   question headings %d   lists %d   tables %d"
          % (r["word_count"], r["h1_count"], r["question_headings"], r["lists"], r["tables"]))
    print("links        %d internal, %d external   JSON-LD: %s"
          % (r["internal_links"], r["external_links"], ", ".join(r["jsonld_types"]) or "none"))
    print("dates        %s" % (", ".join(r["dates"]) or "none found"))
    print("outline")
    for o in r["outline"]:
        print("  " + o)
    print("first answer under each H2 (40-80 words reads as a quotable answer)")
    for s in r["sections"]:
        print("  %3d words  %s%s" % (s["first_paragraph_words"], s["h2"], "  [question]" if s["is_question"] else ""))
    if r["numbers_without_source"]:
        print("numbers with no source in the same sentence")
        for c in r["numbers_without_source"]:
            print("  - " + c)


if __name__ == "__main__":
    main()
