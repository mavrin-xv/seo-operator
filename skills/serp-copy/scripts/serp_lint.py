#!/usr/bin/env python3
"""Lint title and meta description variants before they ship.

Input: a CSV with columns  page, variant, title, description, h1, brand, primary
(primary = the main query the page should win; one row per variant).
Output: per variant the hard fails, the warnings, and the automatic part of
the score (length and structure: 30 of 100 points). The other 70 points
(intent match, proof, distinctness, readability) need a human or model read;
see references/serp-copy.md section 6.

Hard fails (any one blocks the variant):
  keyword_twice      the primary query appears twice in the title
  brand_twice        the brand appears twice in the title
  title_h1_mismatch  title and H1 share under a third of their content words
  unsupported_number a number in the copy that is not in --facts (truth.md)
  keyword_string     three or more separators, reads as a list of keywords
  boilerplate_wide   brand plus separators take more than half the title
  generic_adjectives two or more of: best, top, ultimate, leading, premium...
  desc_repeats_title the description opens with the title

Warnings: title outside 35-65 characters (45-60 ideal), description outside
120-160, primary query not in the first 40 characters, a year in the title,
superlative without proof, pipes and dashes mixed.

Examples:
    python3 serp_lint.py titles.csv
    python3 serp_lint.py titles.csv --facts truth.md --format json
Exit codes: 0 every variant passes hard fails, 1 at least one fails, 2 bad input.
"""
import argparse
import csv
import json
import re
import sys

GENERIC = {"best", "top", "ultimate", "leading", "premium", "amazing", "perfect", "great",
           "awesome", "innovative", "trusted", "#1", "number one", "world-class", "unrivaled"}
SEPS = re.compile(r"\s[|\-:–—·]\s|\s?\|\s?")
STOP = {"the", "a", "an", "and", "or", "for", "to", "of", "in", "on", "with", "at", "by", "your",
        "you", "how", "is", "are", "from", "our", "we"}
NUM = re.compile(r"(?<![\w.])\d[\d,.]*\s?(%|x|k|m|hours?|days?|minutes?|years?|\+)?", re.I)


def words(s):
    return [w for w in re.findall(r"[\w'#]+", s.lower()) if w not in STOP]


def count(hay, needle):
    return len(re.findall(r"(?<!\w)%s(?!\w)" % re.escape(needle.lower()), hay.lower())) if needle else 0


def facts_numbers(path):
    if not path:
        return None
    with open(path, encoding="utf-8") as fh:
        return set(bare(m.group(0)) for m in NUM.finditer(fh.read()))


def bare(n):
    """'18 hours', '18-hour' and '18' all compare as '18'."""
    return re.match(r"[\d,.]*\d", n.strip()).group(0).replace(",", "")


def lint(row, facts):
    t, d, h1 = row.get("title", "").strip(), row.get("description", "").strip(), row.get("h1", "").strip()
    brand, primary = row.get("brand", "").strip(), row.get("primary", "").strip()
    fails, warns, pts = [], [], 0
    if primary and count(t, primary) >= 2:
        fails.append("keyword_twice")
    if brand and count(t, brand) >= 2:
        fails.append("brand_twice")
    tw, hw = set(words(t)) - set(words(brand)), set(words(h1)) - set(words(brand))
    if h1 and tw and len(tw & hw) / max(1, min(len(tw), len(hw))) < 0.34:
        fails.append("title_h1_mismatch")
    if len(SEPS.findall(t)) >= 3:
        fails.append("keyword_string")
    if brand and t:
        tail = len(brand) + 3 * len(SEPS.findall(t))
        if tail > len(t) / 2:
            fails.append("boilerplate_wide")
    gen = [g for g in GENERIC if count(t + " " + d, g)]
    if len(gen) >= 2:
        fails.append("generic_adjectives (%s)" % ", ".join(sorted(gen)))
    if d and t and d.lower().startswith(t.lower()[:30]):
        fails.append("desc_repeats_title")
    if facts is not None:
        for m in NUM.finditer(t + " " + d):
            n = bare(m.group(0))
            f = "unsupported_number (%s)" % n
            if n not in facts and not re.fullmatch(r"20\d\d", n) and f not in fails:
                fails.append(f)

    lt, ld = len(t), len(d)
    if 45 <= lt <= 60:
        pts += 10
    elif 35 <= lt <= 65:
        pts += 6
        warns.append("title %d chars (45-60 ideal)" % lt)
    else:
        warns.append("title %d chars, outside 35-65" % lt)
    if 120 <= ld <= 160:
        pts += 8
    elif ld:
        pts += 3
        warns.append("description %d chars (120-160)" % ld)
    else:
        warns.append("no description")
    if primary:
        pos = t.lower().find(primary.lower())
        if 0 <= pos and pos + len(primary) <= 40:
            pts += 7
        elif pos >= 0:
            pts += 3
            warns.append("primary query starts at char %d; front-load it" % pos)
        else:
            warns.append("primary query not in the title")
    else:
        pts += 3
    if re.search(r"\b20\d\d\b", t):
        warns.append("year in the title: keep it only if it is updated every year")
    else:
        pts += 3
    if "|" in t and re.search(r"\s[-–—]\s", t):
        warns.append("pipes and dashes mixed")
    else:
        pts += 2
    if len(gen) == 1:
        warns.append("superlative '%s': keep only with proof on the page" % gen[0])
    return {"page": row.get("page", ""), "variant": row.get("variant", ""), "title": t,
            "title_len": lt, "desc_len": ld, "auto_points": pts, "auto_max": 30,
            "hard_fails": fails, "warnings": warns, "pass": not fails}


def main():
    for s in (sys.stdout, sys.stderr):
        try:
            s.reconfigure(encoding="utf-8")
        except (AttributeError, ValueError):
            pass
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0], epilog=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("csv")
    ap.add_argument("--facts", help="truth.md or any text file holding the numbers the copy may use")
    ap.add_argument("--format", choices=("text", "json"), default="text")
    a = ap.parse_args()
    try:
        with open(a.csv, encoding="utf-8-sig", newline="") as fh:
            rows = list(csv.DictReader(fh))
    except OSError as e:
        print("cannot read %s: %s" % (a.csv, e), file=sys.stderr)
        sys.exit(2)
    if not rows or "title" not in rows[0]:
        print("CSV needs a header with at least: title (and ideally description, h1, brand, primary)",
              file=sys.stderr)
        sys.exit(2)
    facts = facts_numbers(a.facts)
    res = [lint(r, facts) for r in rows]
    if a.format == "json":
        print(json.dumps(res, indent=1, ensure_ascii=False))
    else:
        for r in res:
            print("%s %s  [%s]  auto %d/30  title %d, desc %d" % (
                r["page"], r["variant"], "PASS" if r["pass"] else "FAIL", r["auto_points"],
                r["title_len"], r["desc_len"]))
            print("    %s" % r["title"])
            for f in r["hard_fails"]:
                print("    fail: %s" % f)
            for w in r["warnings"]:
                print("    warn: %s" % w)
        if facts is None:
            print("\nnote: no --facts file, numbers were not checked against a source")
    sys.exit(0 if all(r["pass"] for r in res) else 1)


if __name__ == "__main__":
    main()
