---
title: Cost structure and operating models
source: Strategyzer; a16z; Stripe
urls:
  - https://www.strategyzer.com/library/the-business-model-canvas
  - https://a16z.com/16-startup-metrics/
  - https://docs.stripe.com/connect/charges
sources:
  - {title: "Business Model Canvas – Download the Official Template", url: "https://www.strategyzer.com/library/the-business-model-canvas", author: Strategyzer, verification: read-at-source}
  - {title: "16 Startup Metrics", url: "https://a16z.com/16-startup-metrics/", author: "Jeff Jordan, Anu Hariharan, Frank Chen, Preethi Kasireddy", published: 2015-08-21, verification: read-at-source}
  - {title: "Understand how charges work in a Connect integration", url: "https://docs.stripe.com/connect/charges", author: Stripe, verification: read-at-source}
authors: [Strategyzer, Jeff Jordan, Anu Hariharan]
date_checked: 2026-11-08
type: original-analysis + attributed-summary
verification: read-at-source
related_skills: [business-model-designer, startup-proposal-generator]
---

# Cost structure and operating models

See also: [revenue architecture](revenue-architecture.md), [unit economics](../frameworks/unit-economics.md).

## Attributed

- Strategyzer notes that the cost and revenue blocks only hold if the other blocks are right; costs follow from the resources, activities and partnerships the model needs.
- a16z's definition of gross profit includes the costs of delivering and supporting the product, not only hosting.
- Stripe's Connect documentation shows that who pays payment fees, refunds and chargebacks depends on how charges are structured (platform or connected account). Fee bearing is a design choice to record, not a detail.

## Original synthesis: a cost checklist

| Type | Fixed or variable | Notes |
|---|---|---|
| Personnel | fixed | Founder time is a cost even when unpaid; record it as unknown rather than zero |
| Infrastructure and platform | mostly fixed, steps up with scale | Hosting, video delivery, storage |
| Direct delivery | variable | Per order, per lesson streamed, per unit shipped |
| Payment processing | variable | Share of each payment; record who bears it |
| Payouts and settlement | variable | Per payout or per transfer |
| Refunds and chargebacks | variable | A cost and a cash-timing issue |
| Customer acquisition | variable or semi-variable | Per customer acquired; blended vs paid |
| Support and operations | semi-variable | Often the cost founders underestimate |
| Compliance and administration | fixed | Legal review, accounting, tax filings, licences |
| Partner costs | either | Revenue shares, integration fees |
| Marketplace incentives | variable | Subsidies, guarantees, launch credits for one side |

**Rules.** Separate known (invoice, quote, contract) from estimated (with a source or calculation) and assumed; never fill an unknown with a plausible number; add totals only across compatible units; show contribution after variable costs before talking about margins.
