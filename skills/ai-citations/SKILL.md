---
name: ai-citations
description: Measures whether AI assistants (ChatGPT, Perplexity, Gemini, Claude and others) cite or mention a brand for the questions its buyers ask, and compares two rounds to say what was gained, lost or held. It records each answer as cited, mentioned, absent or error, computes share of model per engine, lists which competitor names appeared instead, and refuses to compare rows where a round failed. Use when the user asks "does ChatGPT recommend us", "AI visibility", "are we cited in AI answers", "GEO tracking", "share of model", or wants to know if content changes moved AI answers.
---

# AI citations

Track how AI assistants answer the questions that lead to a sale, the same way the `seo-operator` loop tracks clicks: a fixed prompt set, dated rounds, and a comparison that treats failed checks as unknown, not as losses.

## Inputs

- 10 to 30 prompts a buyer would type, written in their words ("best cold brew coffee subscription", "wholesale coffee for cafes downtown"). Mix discovery, comparison and how-to prompts.
- The engines to check, and how: by hand in each product, or with an API the owner already pays for.
- The brand name and its domain; the competitor names to watch.

## Steps

1. **Fix the prompt set.** Write it once in a file and keep it. Changing prompts between rounds makes the rounds incomparable. Rules for choosing prompts: `references/measurement.md`.
2. **Run a round.** Ask every prompt on every engine, in a clean session (logged out or a fresh chat, no memory, same country). Record one row per answer: `engine, prompt, status, cited_url, competitors`.
   - CITED: your URL is a linked source.
   - MENTIONED: the brand is named, not linked.
   - ABSENT: neither.
   - ERROR: no answer, a refusal, a rate limit, a timeout.
   Run each prompt 2 or 3 times if you can; repeated rows are combined and the best state counts.
3. **Save the round** as `aeo/round-<date>.csv` in the state folder.
4. **Compare two rounds.** `python3 scripts/aeo_diff.py aeo/round-2026-10-20.csv aeo/round-2026-11-17.csv`. Read the totals first, then the LOST rows, then the new competitor names.
5. **Act on what moved.** LOST on a prompt with a page: audit that page (`page-audit`) and check the crawl (`site-health`: is the search crawler blocked?). ABSENT everywhere: the site has no page that answers the prompt; send it to `query-research`. A competitor that keeps appearing: read the pages the engine cites for them.
6. **Log content changes** in the `seo-operator` ledger as usual. AI answers move slower and noisier than clicks; compare rounds 4+ weeks apart.

## Gates

- Same prompts, same engines, same session conditions in both rounds.
- ERROR rows are never counted as ABSENT. The script reports them as INDETERMINATE and leaves them out of share of model.
- One flip on one prompt is noise. Report the totals and the share per engine; call a change only when it repeats across prompts or rounds.
- Do not use a third-party account, key or agent you were not given. If no API is available, the rounds are done by hand.
- No claims of "AI ranking" from one round. A single round is a baseline.

## Output

```
LOST (1)
  perplexity  CITED     -> MENTIONED wholesale coffee for cafes downtown
GAINED (3)
  chatgpt     MENTIONED -> CITED     how to make cold brew at home
  ...
share of model (CITED + 0.5 x MENTIONED over answers observed)
  chatgpt       17% (3) ->   50% (3)
  all           25% (8) ->   39% (9)
note: 1 pair(s) not compared because a round had no usable answer
```

Then two or three lines: what moved, the likely reason, the next action. Example rounds and output: `examples/acme-coffee/aeo/round-2026-10-20.csv`, `examples/acme-coffee/aeo/round-2026-11-17.csv`, `examples/acme-coffee/aeo/diff.txt`.

## Failure modes

| Trap | What it looks like | Instead |
|---|---|---|
| Logged-in checks | the assistant remembers you work at the brand | clean session, no memory |
| Changing the prompts | round 2 has "better" prompts | fix the set; add new prompts as a separate group |
| Errors read as losses | half the checks timed out, "visibility halved" | INDETERMINATE, excluded from the share |
| One answer as truth | one prompt flipped, a new strategy follows | totals across prompts and rounds |
| Counting mentions as citations | "we were named" treated like a linked source | MENTIONED is half a point |
| Ignoring crawler access | content rewritten while the search bot is blocked at the CDN | run `site-health` first |
