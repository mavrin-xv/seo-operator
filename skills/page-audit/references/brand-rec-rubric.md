# Brand recommendation rubric (10 of 100 points)

This axis answers a narrower question than GEO: when someone asks an AI assistant a buying question ("best cold brew coffee subscription", "where can a cafe buy wholesale beans"), would the assistant name this brand in its answer, and describe it correctly?

A page can be cited (GEO) without the brand being recommended. The assistant may quote your cold brew ratio and then recommend someone else's subscription, because your page never said in plain words who you are, what you sell and who it is for.

It is the smallest axis on purpose. Citation comes first; naming is the extra lift on top. Do not let a page score well here by repeating the brand name: the points go to clear, checkable statements, not frequency.

## 1. Score from facts, not impressions

Use `scripts/page_facts.py` for the outline, links and the list of unsourced numbers, and the site's `truth.md` (copied from `templates/truth.md`) for the claims the brand is allowed to make. Search the page text for the brand name yourself and note where each mention falls (heading, first 100 words, body, CTA, footer).

## 2. Sub-dimensions

| # | Dimension | Pts | Full | Half | Zero |
|---|---|---|---|---|---|
| 1 | Brand named in the body, early | 2 | Brand name in the title or H1 and in the first 100 words, and again inside body sections | Named once in the body, or only late | Only in the logo, CTA or footer; the body says "we" |
| 2 | Specific claims tied to the brand | 2 | 2+ claims that name the brand and a checkable detail found in `truth.md` ("Acme Coffee steeps its cold brew 18 hours at a 1:8 ratio") | One such claim, or claims with no detail | Only adjectives ("premium", "artisan") |
| 3 | Buyer and use case named | 2 | States who the offer is for in words a buyer would type ("for cafes that want weekly wholesale delivery") | Implied audience | Written for everyone |
| 4 | Honest comparison framing | 2 | Positions the offer against the category or the alternatives a buyer weighs (supermarket cold brew, making it at home, other subscription types) on 2+ concrete points | One point, or comparison in vague terms | No framing, or "the best" with nothing behind it |
| 5 | Named offer and outside proof | 2 | CTA names the offer ("Start a bean subscription at /subscriptions") and the page carries one outside signal: a named customer, a review quoted with date, a press mention | One of the two | "Contact us" and no proof |

Sum for the brand score out of 10.

## 3. The "we" test

Replace every "we" and "our" on the page with a blank and read it again. If you cannot tell which company wrote it, an assistant cannot either. Score dimension 1 at 0 and put this fix first.

## 4. Notes per dimension

**Claims come from truth.md.** A claim the brand cannot back is worse than no claim, because an assistant may repeat it and a customer may check it. If a number is not in `truth.md`, either add it there with a source after verifying, or cut it from the page.

**Comparisons without naming rivals.** You do not need to name a competitor to frame a comparison. "Unlike supermarket cold brew, which is often brewed hot and chilled, Acme Coffee cold brew never touches hot water" is a comparison an assistant can repeat. If you do name another company, every point must be checkable and current.

**Defined product names.** "Acme Overnight" means nothing to an assistant unless the page says what it is the first time it appears. Undefined internal names count against dimension 2.

**Consistent anchors.** When a product or offer is mentioned, link it to its one canonical page with the same anchor each time (`/wholesale` for wholesale, `/subscriptions` for subscriptions). Mixed anchors pointing at different URLs blur which page represents the offer.

## 5. Deductions

Apply after summing, floor the axis at 0.

| Pattern | Deduct |
|---|---|
| Body never names the brand (fails the "we" test) | 3 |
| "Best" or "number one" with no comparison and no proof | 2 |
| Two different brands or offers mixed so a reader cannot tell which is which | 2 |

## 6. Hard fails

- A claim about the brand that contradicts `truth.md` (wrong steep time, wrong price, a service not offered). Block the page until fixed.
- A review, rating or customer quote that cannot be traced to a real source.

## 7. How to report

Report as `BRAND NN/10` with one line per dimension that scored below full, each naming the missing sentence. Then fold the fixes into the page audit's fix list.

## 8. Combining the three axes

The page audit adds the three axes into one score out of 100: GEO (60) + SEO (30) + brand (10). Starting verdict bands:

| Total | Verdict | Meaning |
|---|---|---|
| 85-100 | SHIP | Publish as is or with cosmetic edits |
| 65-84 | FIX | 3-7 targeted edits, then ship |
| 0-64 | REWRITE | Structural problems; patching will not get it there |

Any hard fail on any axis overrides the band. Report the total first, then each axis, then the top 3-5 fixes ordered by points gained per minute of editing.
