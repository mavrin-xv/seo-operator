#!/usr/bin/env python3
"""Google autocomplete mining via the public suggest endpoint. Stdlib only, free, no key.

Pulls the suggestions Google shows in the search box for a seed keyword,
expanded across alphabet, question, preposition and comparison probes.
The only network call is suggestqueries.google.com; nothing else is contacted.

Adapted from boringmarketer/boring-marketing-skills (MIT, Copyright (c) 2026
Boring Marketing, LLC; see THIRD_PARTY_NOTICES.md at the repo root)
(`keyword-research/scripts/suggest.py`). Changes from the source:
  - --lang uk: Ukrainian probe sets (Ukrainian alphabet, як/чому/скільки...,
    для/без/ціна..., найкращий/відгуки...), and gl=UA by default.
  - Encoding: requests ie/oe=utf-8 and decodes by the response charset; the
    source fell back to latin-1, which turns Cyrillic into mojibake.
  - --country flag (gl param), UTF-8 stdout on Windows.

Usage:
    python3 suggest.py "кава з собою" --lang uk
    python3 suggest.py "cold brew" --mode questions,comparisons
    python3 suggest.py "зерно для еспресо" --lang uk --mode questions --format lines

Options:
    --mode MODE     all (default) | base | alphabet | questions | prepositions |
                    comparisons. Comma-combine: questions,prepositions
    --lang LANG     en (default) | uk. Sets hl and the probe vocabulary
    --country CC    gl param. Default: UA for uk, none for en
    --format FMT    json (default) | lines
    --delay SECS    Seconds between requests. Default: 0.12
    --max-probes N  Safety cap on number of probes. Default: 60

Exit codes: 0 ok, 1 bad args, 2 network failure on every probe.
"""

import argparse
import json
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request

ENDPOINT = "https://suggestqueries.google.com/complete/search"
USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"

PROBES = {
    "en": {
        "alphabet": "abcdefghijklmnopqrstuvwxyz",
        "questions": ["what", "how", "why", "when", "where", "who", "which",
                      "can", "is", "does", "should", "will"],
        "prepositions": ["for", "with", "without", "vs", "to", "near", "like"],
        "comparisons": ["best {kw}", "{kw} alternatives", "{kw} review", "{kw} pricing"],
    },
    "uk": {
        # Ukrainian alphabet minus letters that almost never start a word (ь, й is kept).
        "alphabet": "абвгґдеєжзиіїйклмнопрстуфхцчшщюя",
        "questions": ["як", "чому", "що", "де", "коли", "хто", "який", "яка",
                      "скільки", "чи", "навіщо", "чим"],
        "prepositions": ["для", "з", "без", "чи", "в", "біля", "ціна", "купити"],
        "comparisons": ["найкращий {kw}", "{kw} відгуки", "{kw} ціна", "{kw} або", "{kw} аналоги"],
    },
}
VALID_MODES = {"all", "base", "alphabet", "questions", "prepositions", "comparisons"}


def build_probes(keyword, modes, lang):
    """Return list of (probe_query, probe_type) preserving order, deduped."""
    p = PROBES[lang]
    probes = []
    want = lambda m: m in modes or "all" in modes
    if want("base"):
        probes.append((keyword, "base"))
    if want("alphabet"):
        probes.extend((f"{keyword} {ch}", "alphabet") for ch in p["alphabet"])
    if want("questions"):
        probes.extend((f"{q} {keyword}", "question") for q in p["questions"])
    if want("prepositions"):
        probes.extend((f"{keyword} {s}", "preposition") for s in p["prepositions"])
    if want("comparisons"):
        probes.extend((t.format(kw=keyword), "comparison") for t in p["comparisons"])
    seen, out = set(), []
    for q, t in probes:
        if q not in seen:
            seen.add(q)
            out.append((q, t))
    return out


def fetch_suggestions(query, lang, country):
    """One suggest request. Returns list of suggestion strings."""
    params = {"client": "firefox", "hl": lang, "q": query, "ie": "utf-8", "oe": "utf-8"}
    if country:
        params["gl"] = country
    req = urllib.request.Request(
        f"{ENDPOINT}?{urllib.parse.urlencode(params)}", headers={"User-Agent": USER_AGENT}
    )
    with urllib.request.urlopen(req, timeout=10) as resp:
        raw = resp.read()
        ctype = resp.headers.get("Content-Type", "")
    m = re.search(r"charset=([\w-]+)", ctype, re.I)
    charsets = [m.group(1)] if m else []
    charsets += ["utf-8", "windows-1251"]
    data = None
    for cs in charsets:
        try:
            data = json.loads(raw.decode(cs))
            break
        except (UnicodeDecodeError, LookupError):
            continue
    if data is None:
        raise json.JSONDecodeError("undecodable response", "", 0)
    if isinstance(data, list) and len(data) >= 2 and isinstance(data[1], list):
        return [s for s in data[1] if isinstance(s, str)]
    return []


def main():
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except (AttributeError, ValueError):
        pass
    ap = argparse.ArgumentParser(description="Google autocomplete miner")
    ap.add_argument("keyword")
    ap.add_argument("--mode", default="all")
    ap.add_argument("--lang", default="en", choices=sorted(PROBES))
    ap.add_argument("--country", default=None)
    ap.add_argument("--format", default="json", choices=["json", "lines"])
    ap.add_argument("--delay", type=float, default=0.12)
    ap.add_argument("--max-probes", type=int, default=60)
    args = ap.parse_args()

    keyword = args.keyword.strip().lower()
    if not keyword:
        print("error: empty keyword", file=sys.stderr)
        return 1
    modes = {m.strip() for m in args.mode.split(",") if m.strip()}
    if not modes or modes - VALID_MODES:
        print(f"error: invalid --mode (valid: {sorted(VALID_MODES)})", file=sys.stderr)
        return 1
    country = args.country if args.country is not None else ("UA" if args.lang == "uk" else "")

    probes = build_probes(keyword, modes, args.lang)[: args.max_probes]
    results = {}  # suggestion -> (probe, probe_type); first probe wins
    errors = 0
    for i, (probe, ptype) in enumerate(probes):
        try:
            for s in fetch_suggestions(probe, args.lang, country):
                s_norm = s.strip().lower()
                if s_norm and s_norm != keyword and s_norm not in results:
                    results[s_norm] = (probe, ptype)
        except (urllib.error.URLError, OSError, json.JSONDecodeError) as e:
            errors += 1
            print(f"warn: probe '{probe}' failed: {e}", file=sys.stderr)
        if i < len(probes) - 1:
            time.sleep(args.delay)

    if errors == len(probes):
        print("error: all probes failed (network/endpoint unavailable)", file=sys.stderr)
        return 2

    if args.format == "lines":
        for s in sorted(results):
            print(s)
    else:
        print(json.dumps({
            "keyword": keyword,
            "lang": args.lang,
            "country": country or None,
            "probes_run": len(probes),
            "probes_failed": errors,
            "unique_suggestions": len(results),
            "suggestions": [{"suggestion": s, "probe": p, "probe_type": t}
                            for s, (p, t) in sorted(results.items())],
        }, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
