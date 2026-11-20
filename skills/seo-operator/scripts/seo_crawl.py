#!/usr/bin/env python3
"""Crawl: the technical vitals of a site in one dated snapshot.

Reads the sitemap (following a sitemap index one level), walks internal links
from the start URL, and records per page: status, redirect hops, time to first
byte, HTML weight, title, description, canonical, meta robots and X-Robots-Tag,
H1 count, H2 count, JSON-LD types, internal links, click depth and inbound
links. It also reads robots.txt for search, user-fetch and training crawlers,
and probes one made-up URL for a soft 404.

Writes <state>/<site>/health/<date>.json. --diff compares the last two.

Orphans are only counted when the crawl covered the whole sitemap; on a capped
crawl the field is null ("not measured"), never 0.

Examples:
    python3 seo_crawl.py acme-coffee --start https://acme-coffee.com/ --max 300
    python3 seo_crawl.py acme-coffee --diff
"""
import argparse
import datetime
import json
import os
import random
import re
import string
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from concurrent.futures import ThreadPoolExecutor

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import seo_common as C  # noqa: E402

# Some CDNs reject the stock urllib agent (Cloudflare answers 403 with error
# 1010), which reads like an auth failure. A browser agent avoids that.
UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/128.0 Safari/537.36")
SKIP_EXT = (".pdf", ".png", ".jpg", ".jpeg", ".svg", ".webp", ".gif", ".zip", ".xml",
            ".css", ".js", ".ico", ".woff", ".woff2", ".mp4", ".json", ".txt")
FACET_KEYS = ("category", "page", "tag", "sort", "filter", "q", "search", "utm_source")
BOTS = {  # token: job. Search and user-fetch rows decide visibility; training rows do not.
    "Googlebot": "search", "Bingbot": "search", "OAI-SearchBot": "search",
    "Claude-SearchBot": "search", "PerplexityBot": "search",
    "ChatGPT-User": "user-fetch", "Claude-User": "user-fetch", "Perplexity-User": "user-fetch",
    "GPTBot": "training", "ClaudeBot": "training", "Google-Extended": "training", "CCBot": "training",
}


class Hops(urllib.request.HTTPRedirectHandler):
    def __init__(self):
        self.hops = 0

    def redirect_request(self, req, fp, code, msg, headers, newurl):
        self.hops += 1
        return super().redirect_request(req, fp, code, msg, headers, newurl)


def fetch(url, timeout=25, ua=UA):
    """(status, final_url, ttfb_ms, body, headers, hops). Never raises; status 0 = transport error."""
    h = Hops()
    opener = urllib.request.build_opener(h)
    req = urllib.request.Request(url, headers={"User-Agent": ua, "Accept": "text/html,*/*"})
    t0 = time.time()
    try:
        r = opener.open(req, timeout=timeout)
        ttfb = int((time.time() - t0) * 1000)
        body = r.read(2_000_000)
        return r.status, r.geturl(), ttfb, body, dict(r.headers), h.hops
    except urllib.error.HTTPError as e:
        return e.code, url, int((time.time() - t0) * 1000), b"", dict(e.headers or {}), h.hops
    except Exception as e:  # noqa: BLE001 - a crawl must not die on one page
        return 0, url, int((time.time() - t0) * 1000), str(e).encode("utf-8", "ignore")[:200], {}, h.hops


def is_facet(u):
    q = urllib.parse.urlparse(u).query
    keys = [k.lower() for k, _ in urllib.parse.parse_qsl(q)] if q else []
    return any(k in FACET_KEYS or k.endswith("_page") for k in keys)


def canon_key(u):
    """One key per URL: no fragment, lower-case host, consistent encoding.

    The trailing slash is kept: /menu and /menu/ are two URLs, and when a site
    links one while serving the other, that redirect is a finding."""
    sp = urllib.parse.urlsplit(u)
    path = urllib.parse.quote(urllib.parse.unquote(sp.path), safe="/%:@&=+$,~")
    path = path or "/"
    query = urllib.parse.quote(urllib.parse.unquote(sp.query), safe="=&%:@+$,~")
    return urllib.parse.urlunsplit((sp.scheme, sp.netloc.lower(), path, query, ""))


def norm(base, href):
    if not href or href.startswith(("#", "mailto:", "tel:", "javascript:", "data:")):
        return None
    return canon_key(urllib.parse.urldefrag(urllib.parse.urljoin(base, href))[0])


def path_of(u):
    return urllib.parse.urlsplit(u).path.rstrip("/") or "/"


def sitemap_urls(start, cap):
    out, seen, queue = [], set(), [urllib.parse.urljoin(start, "/sitemap.xml")]
    while queue and len(out) < cap:
        sm = queue.pop(0)
        if sm in seen:
            continue
        seen.add(sm)
        st, _, _, body, _, _ = fetch(sm)
        if st != 200 or not body:
            continue
        try:
            root = ET.fromstring(body)
        except ET.ParseError:
            continue
        locs = [e.text.strip() for e in root.iter() if e.tag.split("}")[-1] == "loc" and e.text]
        if root.tag.split("}")[-1] == "sitemapindex":
            queue.extend(locs[:50])
        else:
            out.extend(locs)
    return out[:cap]


TITLE_RE = re.compile(br"<title[^>]*>(.*?)</title>", re.I | re.S)
META_RE = re.compile(br"<meta\b[^>]*>", re.I)
LINK_RE = re.compile(br"<link\b[^>]*>", re.I)
ATTR_RE = re.compile(br"([a-zA-Z:_-]+)\s*=\s*(?:\"([^\"]*)\"|'([^']*)'|([^\s\"'>]+))")
H1_RE = re.compile(br"<h1[^>]*>(.*?)</h1>", re.I | re.S)
H2_RE = re.compile(br"<h2[^>]*>", re.I)
LD_RE = re.compile(br"<script[^>]+application/ld\+json[^>]*>(.*?)</script>", re.I | re.S)
A_RE = re.compile(br"<a\b[^>]*?\bhref\s*=\s*(?:\"([^\"]+)\"|'([^']+)'|([^\s\"'>]+))", re.I)
TAG_RE = re.compile(br"<[^>]+>")
BODY_RE = re.compile(br"<body[^>]*>(.*)</body>", re.I | re.S)
STRIP_RE = re.compile(br"<(script|style|noscript)\b.*?</\1>", re.I | re.S)


def attrs(tag):
    """Attribute order is not fixed (some builders put content= before name=)."""
    """Values may be double-quoted, single-quoted or bare (minified HTML drops quotes)."""
    return {m[0].decode("ascii", "ignore").lower(): m[1] or m[2] or m[3] for m in ATTR_RE.findall(tag)}


def clean(b, cap=300):
    return TAG_RE.sub(b" ", b or b"").decode("utf-8", "ignore").strip()[:cap]


def meta(body, name):
    for tag in META_RE.findall(body):
        a = attrs(tag)
        if a.get("name", b"").decode("utf-8", "ignore").lower() == name:
            return clean(a.get("content", b""))
    return ""


def link_href(body, rel):
    for tag in LINK_RE.findall(body):
        a = attrs(tag)
        if a.get("rel", b"").decode("utf-8", "ignore").lower() == rel:
            return a.get("href", b"").decode("utf-8", "ignore")
    return ""


def schema_types(body):
    types = []
    for blob in LD_RE.findall(body):
        try:
            d = json.loads(blob.decode("utf-8", "ignore"))
        except ValueError:
            continue
        items = d if isinstance(d, list) else d.get("@graph", [d]) if isinstance(d, dict) else []
        for item in items:
            if isinstance(item, dict) and item.get("@type"):
                t = item["@type"]
                types.extend(t if isinstance(t, list) else [t])
    return sorted(set(types))


def word_count(body):
    m = BODY_RE.search(body)
    text = STRIP_RE.sub(b" ", m.group(1) if m else body)
    return len(clean(text, 10_000_000).split())


def robots_report(start):
    st, _, _, body, _, _ = fetch(urllib.parse.urljoin(start, "/robots.txt"))
    rb = body.decode("utf-8", "ignore") if st == 200 else ""
    groups, cur, last_was_agent = {}, [], False
    for line in rb.splitlines():
        line = line.split("#", 1)[0].strip()
        if ":" not in line:
            continue
        k, v = [x.strip() for x in line.split(":", 1)]
        if k.lower() == "user-agent":
            if not last_was_agent:
                cur = []
            cur.append(v.lower())
            groups.setdefault(v.lower(), [])
            last_was_agent = True
        else:
            last_was_agent = False
            for ua in cur:
                groups[ua].append((k.lower(), v))
    def state(rules):
        return "BLOCKED" if any(k == "disallow" and v == "/" for k, v in rules) else "allowed"
    bots = {}
    for bot, job in BOTS.items():
        rules = groups.get(bot.lower())
        if rules is not None:
            bots[bot] = {"job": job, "state": state(rules), "via": "own group"}
        elif "*" in groups:
            bots[bot] = {"job": job, "state": state(groups["*"]), "via": "* group"}
        else:
            bots[bot] = {"job": job, "state": "allowed", "via": "not mentioned"}
    managed = "BEGIN Cloudflare Managed" in rb
    return {"found": st == 200, "status": st,
            "sitemap_declared": bool(re.search(r"^\s*Sitemap:", rb, re.I | re.M)),
            "cdn_managed_block": managed, "bots": bots}


def soft_404(start):
    junk = "".join(random.choice(string.ascii_lowercase) for _ in range(12))
    url = urllib.parse.urljoin(start, "/%s-page-that-should-not-exist" % junk)
    st, _, _, body, _, _ = fetch(url)
    return {"url": url, "status": st, "soft_404": 200 <= st < 300 and b"<html" in body[:4000].lower()}


def crawl(site, start, cap, workers, th):
    host = urllib.parse.urlparse(start).netloc.lower()
    seeds = [s for s in sitemap_urls(start, cap * 2) if not is_facet(s)]
    from_sitemap = set(canon_key(s) for s in seeds)
    pages, edges = {}, {}
    home = canon_key(start)
    depth = {home: 0}
    queue, seen = [home] + sorted(from_sitemap), set()

    def one(url):
        st, final, ttfb, body, hdr, hops = fetch(url)
        rec = {"url": url, "status": st, "final": final, "ttfb_ms": ttfb,
               "bytes": len(body), "hops": hops, "redirected": hops > 0 or canon_key(final) != url}
        xrt = {k.lower(): v for k, v in hdr.items()}.get("x-robots-tag", "")
        if st == 200 and b"<html" in body[:4000].lower():
            h1 = H1_RE.findall(body)
            rec.update({
                "title": clean(TITLE_RE.search(body).group(1)) if TITLE_RE.search(body) else "",
                "description": meta(body, "description"),
                "canonical": link_href(body, "canonical"),
                "robots": " ".join(x for x in (meta(body, "robots"), meta(body, "googlebot"), xrt) if x),
                "h1_count": len(h1), "h1": clean(h1[0], 160) if h1 else "",
                "h2_count": len(H2_RE.findall(body)), "schema": schema_types(body),
                "words": word_count(body),
            })
            links = []
            for m in A_RE.findall(body):
                u = norm(final, (m[0] or m[1] or m[2]).decode("utf-8", "ignore"))
                if u and urllib.parse.urlparse(u).netloc.lower() == host \
                        and not u.lower().endswith(SKIP_EXT) and not is_facet(u):
                    links.append(u)
            rec["internal_links"] = len(links)
            edges[url] = sorted(set(links))
        return rec

    with ThreadPoolExecutor(max_workers=workers) as ex:
        while queue and len(pages) < cap:
            batch = []
            while queue and len(batch) < workers * 2 and len(pages) + len(batch) < cap:
                u = queue.pop(0)
                if u not in seen:
                    seen.add(u)
                    batch.append(u)
            if not batch:
                break
            for rec in ex.map(one, batch):
                pages[rec["url"]] = rec
                d = depth.get(rec["url"], 99)
                for child in edges.get(rec["url"], []):
                    if child not in depth or depth[child] > d + 1:
                        depth[child] = d + 1
                    if child not in seen:
                        queue.append(child)

    inbound = {}
    for src, outs in edges.items():
        for dst in outs:
            if dst != src:
                inbound.setdefault(dst, set()).add(src)
    for u, rec in pages.items():
        rec["depth"] = depth.get(u)
        rec["inbound"] = len(inbound.get(u, ()))
        rec["in_sitemap"] = u in from_sitemap

    full = not queue and len(pages) < cap
    ok = [p for p in pages.values() if p["status"] == 200 and "title" in p]
    not_checked = [p for p in pages.values() if p["status"] in (401, 403, 429) or p["status"] == 0]
    broken = [p for p in pages.values() if p["status"] >= 400 and p not in not_checked]
    redirects = [p for p in pages.values() if p["redirected"] and 200 <= p["status"] < 400]
    chains = [p for p in redirects if p["hops"] >= 2]
    linked_redirects = [p for p in redirects if p["url"] in inbound]
    orphans = [p["url"] for p in ok if p["inbound"] == 0 and p.get("depth") != 0] if full else None
    by_key = {p["url"]: p for p in pages.values()}

    def bad_canonical(p):
        c = p.get("canonical")
        if not c:
            return None
        t = by_key.get(canon_key(urllib.parse.urljoin(p["url"], c)))
        if t and (t["status"] != 200 or t["redirected"] or "noindex" in t.get("robots", "")):
            return {"url": p["url"], "canonical": c, "target_status": t["status"]}
        return None

    issues = {
        "broken": [{"url": p["url"], "status": p["status"], "inbound": len(inbound.get(p["url"], ()))}
                   for p in broken],
        "redirects": [{"url": p["url"], "to": p["final"], "hops": p["hops"]} for p in redirects],
        "redirect_chains": [{"url": p["url"], "to": p["final"], "hops": p["hops"]} for p in chains],
        "internal_links_to_redirects": [p["url"] for p in linked_redirects],
        "orphans": orphans,
        "deep": [p["url"] for p in ok if (p.get("depth") or 0) >= 4],
        "slow": sorted([{"url": p["url"], "ttfb_ms": p["ttfb_ms"]} for p in ok
                        if p["ttfb_ms"] > th["ttfb_ms"]], key=lambda x: -x["ttfb_ms"]),
        "heavy": sorted([{"url": p["url"], "kb": round(p["bytes"] / 1024)} for p in ok
                         if p["bytes"] > th["html_kb"] * 1024], key=lambda x: -x["kb"]),
        "no_description": [p["url"] for p in ok if not p.get("description")],
        "bad_h1": [p["url"] for p in ok if p.get("h1_count", 0) != 1],
        "no_schema": [p["url"] for p in ok if not p.get("schema")],
        "not_in_sitemap": [p["url"] for p in ok if not p["in_sitemap"] and "noindex" not in p.get("robots", "")],
        "sitemap_non_200": [{"url": p["url"], "status": p["status"], "redirected": p["redirected"]}
                            for p in pages.values() if p["in_sitemap"] and (p["status"] != 200 or p["redirected"])],
        "noindex_in_sitemap": [p["url"] for p in ok if p["in_sitemap"] and "noindex" in p.get("robots", "")],
        "canonical_to_bad_target": [x for x in (bad_canonical(p) for p in ok) if x],
        "thin_or_js_rendered": [p["url"] for p in ok if p.get("words", 0) < 50],
        "not_checked": [{"url": p["url"], "status": p["status"]} for p in not_checked],
    }

    def pct(vals, q):
        s = sorted(vals)
        return s[min(len(s) - 1, int(len(s) * q))] if s else None

    counts = {k: (None if v is None else len(v)) for k, v in issues.items()}
    counts.update({"pages": len(pages), "ok": len(ok), "sitemap_urls": len(from_sitemap)})
    return {
        "site": site, "start": start, "crawled": datetime.datetime.now().isoformat(timespec="seconds"),
        "complete": full, "cap": cap, "counts": counts,
        "speed": {"ttfb_p50": pct([p["ttfb_ms"] for p in ok], .5),
                  "ttfb_p90": pct([p["ttfb_ms"] for p in ok], .9),
                  "html_kb_p50": round((pct([p["bytes"] for p in ok], .5) or 0) / 1024, 1),
                  "html_kb_p90": round((pct([p["bytes"] for p in ok], .9) or 0) / 1024, 1)},
        "robots": robots_report(start), "soft_404": soft_404(start), "issues": issues,
        "pages": by_path(pages),
    }


def by_path(pages):
    """Pages keyed by bare path, the key Search Console rows use. When /x and
    /x/ were both fetched, the one that answered 200 without a redirect wins."""
    out = {}
    for u, p in sorted(pages.items()):
        k = path_of(u)
        if k not in out or (p["status"] == 200 and not p["redirected"]):
            out[k] = p
    return out


def diff(root, site):
    snaps = C.snapshots(root, site, "health")
    if len(snaps) < 2:
        print("need two health snapshots to diff (have %d)" % len(snaps))
        return
    (da, a), (db, b) = snaps[-2], snaps[-1]
    print("diff %s -> %s" % (da, db))
    moved = False
    for k, now in b["counts"].items():
        was = a["counts"].get(k)
        if was != now:
            moved = True
            print("  %-28s %5s -> %5s" % (k, was, now))
    newly = {p["url"] for p in b["issues"]["broken"]} - {p["url"] for p in a["issues"]["broken"]}
    for u in sorted(newly):
        moved = True
        print("  NEW BROKEN: %s" % u)
    for bot, now in b["robots"]["bots"].items():
        was = a["robots"]["bots"].get(bot, {}).get("state")
        if was and was != now["state"]:
            moved = True
            print("  ROBOTS CHANGED: %s %s -> %s" % (bot, was, now["state"]))
    if not moved:
        print("  no change")


def main():
    C.utf8_stdout()
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0], epilog=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("site")
    ap.add_argument("--state")
    ap.add_argument("--start", help="start URL (default: start_url from config.json)")
    ap.add_argument("--max", type=int, default=300, help="page cap (default 300)")
    ap.add_argument("--workers", type=int, default=6)
    ap.add_argument("--date", help="snapshot date for the file name (default today)")
    ap.add_argument("--diff", action="store_true")
    a = ap.parse_args()

    root = C.state_root(a.state)
    if a.diff:
        diff(root, a.site)
        return
    cfg = C.load_config(root, a.site)
    start = a.start or cfg.get("start_url")
    if not start:
        sys.exit("--start is required (or set start_url in config.json)")
    snap = crawl(a.site, start, a.max, a.workers, cfg["thresholds"])
    path = os.path.join(C.site_dir(root, a.site), "health", "%s.json" % C.today(a.date))
    C.write_json(path, snap)
    c, s = snap["counts"], snap["speed"]
    print("saved %s" % path)
    print("pages %d (ok %d, sitemap %d), crawl %s" % (c["pages"], c["ok"], c["sitemap_urls"],
          "complete" if snap["complete"] else "CAPPED at %d, orphans not measured" % a.max))
    print("speed: ttfb p50 %sms p90 %sms, html p50 %skb p90 %skb"
          % (s["ttfb_p50"], s["ttfb_p90"], s["html_kb_p50"], s["html_kb_p90"]))
    skip = {"pages", "ok", "sitemap_urls"}
    print("issues: " + ", ".join("%s %s" % (k, "n/a" if v is None else v)
                                 for k, v in c.items() if k not in skip and v))
    print("soft 404: %s (status %s)" % (snap["soft_404"]["soft_404"], snap["soft_404"]["status"]))
    blocked = [b for b, v in snap["robots"]["bots"].items() if v["state"] == "BLOCKED"]
    print("robots.txt found=%s, blocked: %s" % (snap["robots"]["found"], ", ".join(blocked) or "none"))


if __name__ == "__main__":
    main()
