# Decision queue: NOW, NEXT, HOLD, DROP

Every query family gets one status in `radar.md`, with the evidence on the same line. The queue keeps the plan short: a family is either worth the next hour, waiting for a reason, or gone.

## Statuses

| Status | Means | Evidence required |
|---|---|---|
| NOW | work on it this cycle | Search Console rows at positions 4 to 20 with real impressions, or a money page with a snippet gap, and a clear fit with what the business sells |
| NEXT | worth doing after the NOW items | demand shown (rows or typed suggestions) and fit, but a smaller stake or a missing input |
| HOLD | blocked by something specific | the blocker named: a fact the owner must supply, a page template that must pass the programmatic gate, a season |
| DROP | not worth building | the reason: no fit, served better by another page, intent the business cannot meet |

## How to decide

Ask in order and stop at the first "no":

1. **Does it fit what the business sells?** A roaster can answer "how to make cold brew"; it should not chase "coffee machine repair". No fit is DROP.
2. **Is there demand you can point to?** Search Console rows, a typed autocomplete suggestion, or questions customers ask in email or reviews. None is HOLD with "needs evidence".
3. **Does a page already exist?** If yes, the work is improving that page (NOW or NEXT, routed to `page-audit` or `serp-copy`), not a new one.
4. **Can one page answer the family?** If the plan needs a page per town or product, HOLD it until the programmatic gate passes.
5. **How much is at stake?** Use the `seo-operator` board score when the family maps to an existing page. For a new page, compare the family's impressions with the families already in NOW.

## Line format

```
| cold brew at home | 4 queries, positions 7-15, 8,450 impressions (gsc 2026-11-17) | NOW | 2026-11-18 |
| cold brew near me | 1,850 impressions at 6.7; needs one page per shop | HOLD: pseo gate | 2026-11-18 |
| espresso vs drip  | 1,350 impressions at 12.0; no product to sell on it | DROP: no fit | 2026-11-18 |
```

## Review rhythm

- Each measure: move families whose evidence changed. A HOLD whose blocker cleared moves to NEXT.
- Keep NOW to 3 families or fewer. More than that and none of them gets finished.
- DROP is kept, not deleted, so the same idea is not re-proposed next month without new evidence.
