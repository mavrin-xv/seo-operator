# AI crawlers by job

AI companies run separate crawlers for separate jobs. Treat them by job, not by company. The table matches the `BOTS` list in `scripts/site_probe.py`. Check each vendor's crawler documentation before you change rules, because names and agents change.

| Crawler | Company | Job | If blocked |
|---|---|---|---|
| Googlebot | Google | search | the site leaves Google Search, including AI features in Search |
| Bingbot | Microsoft | search | the site leaves Bing and the products built on its index |
| OAI-SearchBot | OpenAI | search | pages stop appearing as sources in ChatGPT search |
| Claude-SearchBot | Anthropic | search | pages stop appearing in Claude's search results |
| PerplexityBot | Perplexity | search | pages stop appearing in Perplexity answers |
| ChatGPT-User | OpenAI | user-fetch | a user's request to read your page fails |
| Claude-User | Anthropic | user-fetch | same, for Claude |
| Perplexity-User | Perplexity | user-fetch | same, for Perplexity |
| GPTBot | OpenAI | training | content is not used to train future models |
| ClaudeBot | Anthropic | training | same |
| Google-Extended | Google | training | a robots token, not a separate fetcher; controls use in Gemini training, not Search |
| CCBot | Common Crawl | training | the page leaves the open web corpus many models train on |

## Rules

- **Search and user-fetch: allow.** Blocking them removes the site from the answers people read. The probe fails these rows.
- **Training: the owner decides.** Blocking is a legitimate policy. The probe reports it as ok with "blocked".
- **Robots groups are exclusive.** A crawler with its own `User-agent:` group follows only that group. If `User-agent: GPTBot` has `Disallow:` empty and `*` has `Disallow: /private`, GPTBot may crawl `/private`.
- **robots.txt is a request, not a wall.** The CDN or firewall is the wall. Some CDNs block AI crawlers by default or offer a one-click switch; that block does not show in robots.txt. `ai_blocked_at_edge` is the check for it.
- **User agents can be faked.** Real crawlers publish IP ranges or support reverse DNS checks. When the CDN treats this probe differently from a real crawler, the CDN's logs are the truth.

## A sample robots.txt (Acme Coffee)

```
User-agent: GPTBot
Disallow: /

User-agent: *
Disallow: /cart
Disallow: /account

Sitemap: https://acme-coffee.com/sitemap.xml
```

Here GPTBot (training) is blocked by choice; every search and user-fetch crawler falls to `*` and may crawl everything except the cart and account pages.
