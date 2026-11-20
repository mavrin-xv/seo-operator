#!/usr/bin/env python3
"""Probe a live site for the technical failures a crawl report hides.

Each check has an ID (see references/check-ids.md) and ends in one of three
states: FAIL, ok, or not checked (with the reason). A check that could not run
is never reported as passing.

Live checks (network, read-only GET requests):
  soft_404            a made-up URL must not answer 200
  robots_groups       robots.txt per crawler: search, user-fetch, training rows
  ai_blocked_at_edge  the home page fetched as each crawler vs as a browser;
                      a 403/503 only for bots means the CDN or firewall blocks
                      them even when robots.txt allows them
  redirect_chain      every URL given with --url, hop by hop (loops included)
  js_rendered_content visible words in the raw HTML (a shell page has almost none)

Snapshot checks (no network): --snapshot <health/date.json from seo_crawl.py>
  noindex_in_sitemap, sitemap_non_200, canonical_to_bad_target,
  internal_links_to_redirects, redirect_chains, thin pages

Examples:
    python3 site_probe.py https://acme-coffee.com/
    python3 site_probe.py https://acme-coffee.com/ --url https://acme-coffee.com/old-menu
    python3 site_probe.py --snapshot .seo/acme-coffee/health/2026-11-18.json
Exit codes: 0 no FAIL, 1 at least one FAIL, 2 bad input.

Note: bot user agents here are self-declared. Real crawlers are verified by
reverse DNS or published IP ranges, so a CDN that verifies them can treat
this probe differently from the real crawler. A FAIL is a lead to confirm in
the CDN's firewall log, not proof.
"""
import argparse
import http.client
import json
import random
import re
import string
import sys
import time
import urllib.parse

BROWSER = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
           "(KHTML, like Gecko) Chrome/128.0 Safari/537.36")
BOTS = [  # (robots token, job, user agent string as published by the operator)
    ("Googlebot", "search", "Mozilla/5.0 (compatible; Googlebot/2.1; +http://www.google.com/bot.html)"),
    ("Bingbot", "search", "Mozilla/5.0 (compatible; bingbot/2.0; +http://www.bing.com/bingbot.htm)"),
    ("OAI-SearchBot", "search", "Mozilla/5.0 (compatible; OAI-SearchBot/1.0; +https://openai.com/searchbot)"),
    ("Claude-SearchBot", "search", "Mozilla/5.0 (compatible; Claude-SearchBot/1.0; +https://www.anthropic.com)"),
    ("PerplexityBot", "search", "Mozilla/5.0 (compatible; PerplexityBot/1.0; +https://perplexity.ai/perplexitybot)"),
    ("ChatGPT-User", "user-fetch", "Mozilla/5.0 (compatible; ChatGPT-User/1.0; +https://openai.com/bot)"),
    ("Claude-User", "user-fetch", "Mozilla/5.0 (compatible; Claude-User/1.0; +https://www.anthropic.com)"),
    ("Perplexity-User", "user-fetch", "Mozilla/5.0 (compatible; Perplexity-User/1.0; +https://perplexity.ai/perplexity-user)"),
    ("GPTBot", "training", "Mozilla/5.0 (compatible; GPTBot/1.1; +https://openai.com/gptbot)"),
    ("ClaudeBot", "training", "Mozilla/5.0 (compatible; ClaudeBot/1.0; +https://www.anthropic.com)"),
    ("Google-Extended", "training", None),  # a robots.txt token only, never sent as a user agent
    ("CCBot", "training", "CCBot/2.0 (https://commoncrawl.org/faq/)"),
]
results = []


def add(check, state, detail):
    results.append({"check": check, "state": state, "detail": detail})


def get(url, ua=BROWSER, timeout=20):
    """One request, no redirect following: (status, location, body)."""
    u = urllib.parse.urlsplit(url)
    conn_cls = http.client.HTTPSConnection if u.scheme == "https" else http.client.HTTPConnection
    conn = conn_cls(u.netloc, timeout=timeout)
    path = (u.path or "/") + ("?" + u.query if u.query else "")
    try:
        conn.request("GET", path, headers={"User-Agent": ua, "Accept": "text/html,*/*"})
        r = conn.getresponse()
        body = r.read(1_500_000)
        return r.status, r.getheader("Location"), body
    finally:
        conn.close()


def follow(url, ua=BROWSER, max_hops=10):
    hops, seen = [], set()
    cur = url
    for _ in range(max_hops):
        if cur in seen:
            return hops, "loop"
        seen.add(cur)
        st, loc, body = get(cur, ua)
        hops.append((cur, st))
        if st in (301, 302, 303, 307, 308) and loc:
            cur = urllib.parse.urljoin(cur, loc)
            continue
        return hops, body
    return hops, "too many hops"


def visible_words(body):
    m = re.search(rb"<body[^>]*>(.*)</body>", body, re.I | re.S)
    b = m.group(1) if m else body
    b = re.sub(rb"<(script|style|noscript|template)\b.*?</\1>", b" ", b, flags=re.I | re.S)
    return len(re.sub(rb"<[^>]+>", b" ", b).decode("utf-8", "ignore").split())


def robots_groups(start):
    try:
        st, _, body = get(urllib.parse.urljoin(start, "/robots.txt"))
    except OSError as e:
        add("robots_groups", "not checked", "robots.txt unreachable: %s" % e)
        return
    if st in (401, 403, 429):
        add("robots_groups", "not checked", "robots.txt answered %d to a browser agent" % st)
        return
    if st != 200:
        add("robots_groups", "ok", "no robots.txt (HTTP %d): every crawler is allowed" % st)
        return
    text = body.decode("utf-8", "ignore")
    groups, cur, agent_run = {}, [], False
    for line in text.splitlines():
        line = line.split("#", 1)[0].strip()
        if ":" not in line:
            continue
        k, v = [x.strip() for x in line.split(":", 1)]
        if k.lower() == "user-agent":
            cur = cur if agent_run else []
            cur.append(v.lower())
            groups.setdefault(v.lower(), [])
            agent_run = True
        else:
            agent_run = False
            for ua in cur:
                groups[ua].append((k.lower(), v))
    for token, job, _ in BOTS:
        # A crawler obeys its own group if one exists, otherwise the * group.
        # The two never combine.
        rules = groups.get(token.lower(), groups.get("*", []))
        via = "own group" if token.lower() in groups else "* group" if "*" in groups else "not mentioned"
        blocked = any(k == "disallow" and v == "/" for k, v in rules)
        if blocked and job != "training":
            add("robots_groups", "FAIL", "%s (%s) is disallowed via %s: pages cannot appear in that product"
                % (token, job, via))
        else:
            add("robots_groups", "ok", "%s (%s): %s via %s" % (token, job, "blocked" if blocked else "allowed", via))
    if "BEGIN Cloudflare Managed" in text:
        add("robots_groups", "ok", "robots.txt carries a CDN-managed block; its rules are applied "
            "at the edge too, so check the CDN bot settings")


def edge_block(start):
    try:
        base, _, _ = get(start)
    except OSError as e:
        add("ai_blocked_at_edge", "not checked", "home page unreachable: %s" % e)
        return
    for token, job, ua in BOTS:
        if not ua:
            continue
        try:
            st, _, _ = get(start, ua)
        except OSError as e:
            add("ai_blocked_at_edge", "not checked", "%s: %s" % (token, e))
            continue
        if st != base and st in (401, 403, 429, 503):
            add("ai_blocked_at_edge", "FAIL" if job != "training" else "ok",
                "%s gets %d while a browser gets %d%s" % (token, st, base,
                "" if job != "training" else " (training crawler, a policy choice)"))
        else:
            add("ai_blocked_at_edge", "ok", "%s gets %d (browser %d)" % (token, st, base))
        time.sleep(0.2)


def live(start, urls):
    junk = "".join(random.choice(string.ascii_lowercase) for _ in range(12))
    try:
        hops, body = follow(urllib.parse.urljoin(start, "/%s-should-not-exist" % junk))
        st = hops[-1][1]
        if 200 <= st < 300:
            add("soft_404", "FAIL", "a made-up URL answers %d; missing pages look like real ones" % st)
        elif st in (401, 403, 429):
            add("soft_404", "not checked", "made-up URL answered %d" % st)
        else:
            add("soft_404", "ok", "made-up URL answers %d" % st)
    except OSError as e:
        add("soft_404", "not checked", str(e))
    robots_groups(start)
    edge_block(start)
    try:
        hops, body = follow(start)
        if isinstance(body, bytes):
            n = visible_words(body)
            add("js_rendered_content", "FAIL" if n < 50 else "ok",
                "%d visible words in the raw HTML of the home page%s" % (n, "; content likely needs JavaScript"
                                                                          if n < 50 else ""))
    except OSError as e:
        add("js_rendered_content", "not checked", str(e))
    for u in urls:
        try:
            hops, end = follow(u)
        except OSError as e:
            add("redirect_chain", "not checked", "%s: %s" % (u, e))
            continue
        path = " -> ".join("%s [%d]" % h for h in hops)
        if end == "loop":
            add("redirect_loop", "FAIL", path)
        elif len(hops) > 2:
            add("redirect_chain", "FAIL", "%d hops: %s" % (len(hops) - 1, path))
        else:
            add("redirect_chain", "ok", path)


def from_snapshot(path):
    with open(path, encoding="utf-8") as fh:
        snap = json.load(fh)
    iss = snap["issues"]
    for key, check in (("noindex_in_sitemap", "noindex_in_sitemap"), ("sitemap_non_200", "sitemap_non_200"),
                       ("canonical_to_bad_target", "canonical_to_bad_target"),
                       ("internal_links_to_redirects", "internal_links_to_redirects"),
                       ("redirect_chains", "redirect_chains"), ("thin_or_js_rendered", "js_rendered_content")):
        rows = iss.get(key)
        if rows is None:
            add(check, "not checked", "not in this snapshot")
        elif rows:
            first = rows[0] if isinstance(rows[0], str) else rows[0].get("url")
            add(check, "FAIL", "%d page(s), first: %s" % (len(rows), first))
        else:
            add(check, "ok", "none found in %d crawled pages" % snap["counts"]["pages"])
    if iss.get("orphans") is None:
        add("orphans", "not checked", "crawl was capped, so pages nobody links to cannot be counted")
    if iss.get("not_checked"):
        add("crawl_access", "not checked", "%d URLs answered 401/403/429 or failed; their checks did not run"
            % len(iss["not_checked"]))


def main():
    for s in (sys.stdout, sys.stderr):
        try:
            s.reconfigure(encoding="utf-8")
        except (AttributeError, ValueError):
            pass
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0], epilog=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("start", nargs="?", help="home page URL for the live checks")
    ap.add_argument("--url", action="append", default=[], help="URL to trace for redirects (repeatable)")
    ap.add_argument("--snapshot", help="health snapshot JSON from seo_crawl.py")
    ap.add_argument("--format", choices=("text", "json"), default="text")
    a = ap.parse_args()
    if not a.start and not a.snapshot:
        ap.print_usage()
        sys.exit(2)
    if a.start:
        live(a.start, a.url)
    if a.snapshot:
        from_snapshot(a.snapshot)
    if a.format == "json":
        print(json.dumps(results, indent=1, ensure_ascii=False))
    else:
        for title, state in (("FAIL", "FAIL"), ("Checked, fine", "ok"), ("Not checked", "not checked")):
            rows = [r for r in results if r["state"] == state]
            if rows:
                print("%s (%d)" % (title, len(rows)))
                for r in rows:
                    print("  %-28s %s" % (r["check"], r["detail"]))
    sys.exit(1 if any(r["state"] == "FAIL" for r in results) else 0)


if __name__ == "__main__":
    main()
