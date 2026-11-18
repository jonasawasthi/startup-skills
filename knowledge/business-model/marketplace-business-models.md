---
title: Marketplace business models
source: Bill Gurley; NFX; a16z; Lenny Rachitsky; Stripe
urls:
  - https://abovethecrowd.com/2013/04/18/a-rake-too-far-optimal-platformpricing-strategy/
  - https://www.nfx.com/post/19-marketplace-tactics-for-overcoming-the-chicken-or-egg-problem
  - https://a16z.com/16-startup-metrics/
  - https://www.lennysnewsletter.com/p/how-to-kickstart-and-scale-a-marketplace
  - https://docs.stripe.com/connect/charges
sources:
  - {title: "A Rake Too Far: Optimal Platform Pricing Strategy", url: "https://abovethecrowd.com/2013/04/18/a-rake-too-far-optimal-platformpricing-strategy/", author: Bill Gurley, published: 2013-04-18, verification: read-at-source}
  - {title: "19 Tactics to Solve the Chicken-or-Egg Problem and Grow Your Marketplace", url: "https://www.nfx.com/post/19-marketplace-tactics-for-overcoming-the-chicken-or-egg-problem", author: James Currier, published: 2019-07, verification: read-at-source}
  - {title: "16 Startup Metrics", url: "https://a16z.com/16-startup-metrics/", author: "Jeff Jordan, Anu Hariharan, Frank Chen, Preethi Kasireddy", published: 2015-08-21, verification: read-at-source}
  - {title: "How to kickstart and scale a marketplace business", url: "https://www.lennysnewsletter.com/p/how-to-kickstart-and-scale-a-marketplace", author: Lenny Rachitsky, published: 2019-11-20, verification: read-at-source}
  - {title: "Understand how charges work in a Connect integration", url: "https://docs.stripe.com/connect/charges", author: Stripe, verification: read-at-source}
authors: [Bill Gurley, James Currier, Jeff Jordan, Lenny Rachitsky]
date_checked: 2026-11-08
type: attributed-summary + original-analysis
verification: read-at-source
related_skills: [business-model-designer, gtm-strategy-maker, startup-idea-evaluator]
---

# Marketplace business models

See also: [a16z marketplaces](../a16z/marketplaces.md), [marketplace analysis framework](../frameworks/marketplace-analysis.md), [liquidity and cold start](liquidity-and-cold-start.md), [payment infrastructure](payment-infrastructure.md).

## Attributed

- **GMV is not revenue.** a16z's "16 Startup Metrics" defines GMV as the total sales volume moving through a marketplace and revenue as only the portion the marketplace keeps as fees: "GMV does not equal revenue!"
- **Take rate (Gurley, 2013).** A high rake raises prices for buyers, pushes suppliers to other channels and leaves a pricing umbrella for a competitor; a lower rake buys broad supplier adoption and a network that is hard to leave. His examples include Booking.com starting with a 10% agency model against 30%+ merchant models, and oDesk cutting its commission from 30% to 10%.
- **Start constrained (Rachitsky, 2019).** Nearly every marketplace he studied limited its initial scope, by geography or category, to reach critical mass faster; examples include OpenTable's 50–100 restaurants per city.
- **Money flow is a design choice (Stripe Connect docs).** With *direct charges* the seller is the business of record and refunds and chargebacks hit the seller's balance; with *destination charges* or *separate charges and transfers* the platform charges the buyer, pays fees, and its own balance is debited for refunds and disputes. These describe Stripe's product, which is not available in every country.

## Original synthesis: what a marketplace model must state

1. **Sides, separately.** Supply (sellers, creators, teachers, providers, vendors) and demand (buyers, learners, businesses), each with its acquisition, value, price and subsidy.
2. **The funnel, measured.** Registered → active → available supply; registered → active → actual demand; matches → completed → repeat transactions. Each step is a different number; none substitutes for the next.
3. **The money.** GMV, the platform's revenue (commission or fees), seller earnings (owed to sellers), payment costs and who bears them, refunds, disputes, payout timing.
4. **Leakage.** Why the parties keep transacting through the platform after they have met; a high take rate makes leakage more likely.
5. **Configuration.** Two-sided, three-sided, service, digital-product, education, managed or hybrid with SaaS; each shifts where the operating cost and the trust problem sit.
