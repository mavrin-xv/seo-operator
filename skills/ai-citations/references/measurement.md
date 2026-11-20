# Measuring AI answers

AI answers change between runs of the same prompt, between days, and between users. The method below does not remove that noise; it keeps it from being read as a result.

## Choosing prompts

| Type | Example (Acme Coffee) | Why it matters |
|---|---|---|
| Discovery | "best cold brew coffee subscription" | the buyer has not picked a brand yet |
| Comparison | "Acme Coffee vs Northwind Roasters" | the buyer is choosing |
| Local | "wholesale coffee for cafes downtown" | intent tied to a place |
| How-to | "how to make cold brew at home" | the page can be cited as a source |
| Problem | "why does my cold brew taste bitter" | entry point to the brand's knowledge pages |

- Write prompts the way buyers type them, not with the brand's internal terms.
- Keep 10 to 30. Fewer and one flip swings the share; more and nobody runs the rounds.
- Store the set in one file and version it. A new prompt starts its own history.

## States

| State | Rule | Points |
|---|---|---|
| CITED | your domain appears as a linked source in the answer | 1 |
| MENTIONED | the brand is named in the text with no link to your domain | 0.5 |
| ABSENT | neither | 0 |
| ERROR | no answer, refusal, rate limit, timeout, login wall | not counted |

Share of model = (CITED + 0.5 x MENTIONED) / answers observed, per engine and overall. Errors are not observed answers.

## Verdicts between rounds

| Verdict | Rule |
|---|---|
| GAINED | the state went up (absent to mentioned or cited, mentioned to cited) |
| LOST | the state went down |
| HELD | cited both times |
| NO CHANGE | the same non-cited state both times |
| INDETERMINATE | a round has no row, or an error, for this engine and prompt |

`scripts/aeo_diff.py` also lists competitor names that appear in the newer round for a prompt and did not in the older one.

## Session conditions

Keep these the same in both rounds and write them in the round file name or a note:

- logged out, or a fresh account with memory and personalisation off;
- the same country (answers differ by location, especially local prompts);
- the same product surface (the web app and an API can answer differently);
- the same model setting where the product lets you choose.

## Cadence

- A round every 4 weeks is enough for most sites. Content changes take weeks to reach answers.
- Run each prompt 2 or 3 times per round when you can; the diff combines repeated rows and keeps the best state, which reduces flip noise.
- Compare a round with the one before, and every few months with the first one, to see the slower trend.

## Reading the result

- Read the overall share first, then per engine, then the LOST list.
- A change on one prompt in one engine is a lead to look at, not a finding.
- When an engine cites a competitor for a prompt you lose, open the cited page. It usually answers the question in its first paragraph with a specific fact; that is the fix to try on your own page (`page-audit`).
