---
title: Revenue architecture and monetisation
source: a16z; Stripe; Strategyzer
urls:
  - https://a16z.com/16-startup-metrics/
  - https://docs.stripe.com/revenue-recognition
  - https://docs.stripe.com/connect/merchant-of-record
  - https://www.strategyzer.com/library/the-business-model-canvas
sources:
  - {title: "16 Startup Metrics", url: "https://a16z.com/16-startup-metrics/", author: "Jeff Jordan, Anu Hariharan, Frank Chen, Preethi Kasireddy", published: 2015-08-21, verification: read-at-source}
  - {title: "Revenue Recognition", url: "https://docs.stripe.com/revenue-recognition", author: Stripe, verification: url-verified}
  - {title: "Determine and configure the merchant of record (MoR)", url: "https://docs.stripe.com/connect/merchant-of-record", author: Stripe, verification: url-verified}
  - {title: "Business Model Canvas – Download the Official Template", url: "https://www.strategyzer.com/library/the-business-model-canvas", author: Strategyzer, verification: read-at-source}
authors: [Jeff Jordan, Anu Hariharan, Frank Chen, Preethi Kasireddy]
date_checked: 2026-11-08
type: attributed-summary + original-analysis
verification: read-at-source (a16z, Strategyzer); url-verified (Stripe pages)
related_skills: [business-model-designer, startup-proposal-generator, fundraising-strategist]
---

# Revenue architecture and monetisation

See also: [pricing and willingness to pay](pricing-and-willingness-to-pay.md), [cost structure](cost-structure.md), [unit economics](../frameworks/unit-economics.md), [a16z metrics](../a16z/metrics.md).

## Attributed (a16z, "16 Startup Metrics", 2015)

- **Bookings vs revenue.** Bookings are the value of a contract and the customer's obligation to pay; revenue is recognised as the service is delivered or ratably over a subscription. Letters of intent and verbal agreements are neither.
- **GMV vs revenue.** For marketplaces, revenue is only the portion of GMV the marketplace keeps.
- **Recurring vs total revenue.** Annual recurring revenue should exclude one-time and professional-service fees.
- **Gross profit** includes the costs of manufacturing, delivering and supporting the product; founders should be ready to explain what is in and out.
- **Blended vs paid CAC.** Blended CAC includes organic users and does not show whether paid acquisition works.

Stripe's documentation covers revenue recognition and merchant-of-record configuration for its own products; it is listed for the concepts, not as a statement about availability anywhere.

## Original synthesis: describing a revenue stream

| Field | Question |
|---|---|
| Payer | Which segment pays? (Often not the user.) |
| Value | What exactly are they paying for? |
| Mechanism | one-time · subscription · transaction fee · commission · usage · licensing · service fee · advertising · bundle · tiered · hybrid |
| Billing | When and how often? |
| Structure | Who pays whom, through which channel, and what is held back (refund holds, payouts)? |
| Recognition | Gross (principal, seller of record) or net (agent)? Confirm with an accountant |
| Dependencies | Which payment, payout, tax and legal items must work first? |
| Stage | proposed → tested → available → generating → repeatable |

**Stage discipline.** A proposed price is a hypothesis. *Tested* means real customers saw the offer; *available* means they can actually pay today; *generating* means money arrived; *repeatable* means repeat or retained payments were measured. Revenue is never computed from a proposed price multiplied by an assumed volume.
