---
title: Marketplace cold start and liquidity
source: NFX; Andrew Chen (a16z); Lenny's Newsletter
urls:
  - https://www.nfx.com/post/19-marketplace-tactics-for-overcoming-the-chicken-or-egg-problem
  - https://a16z.com/books/the-cold-start-problem/
  - https://www.lennysnewsletter.com/p/atomic-network
sources:
  - {title: "19 Tactics to Solve the Chicken-or-Egg Problem and Grow Your Marketplace", url: "https://www.nfx.com/post/19-marketplace-tactics-for-overcoming-the-chicken-or-egg-problem", author: James Currier, published: 2019-07, verification: read-at-source}
  - {title: "The Cold Start Problem", url: "https://a16z.com/books/the-cold-start-problem/", author: Andrew Chen, verification: read-at-source}
  - {title: "The Atomic Network", url: "https://www.lennysnewsletter.com/p/atomic-network", author: "Andrew Chen (book excerpt, via Lenny Rachitsky)", published: 2021-12-09, verification: read-at-source}
authors: [James Currier, Andrew Chen]
date_checked: 2026-11-07
type: attributed-summary + original-analysis
verification: read-at-source
related_skills: [gtm-strategy-maker, startup-idea-evaluator]
---

# Marketplace cold start

See also: [a16z marketplace metrics](../a16z/marketplaces.md), [marketplace analysis](../frameworks/marketplace-analysis.md), [network effects](../other/network-effects.md).

## Attributed

- **NFX: 19 tactics (Currier, 2019)**, paraphrased in groups:
  - *Choose the side*: recruit the harder-to-attract side first, pay the most valuable side to join, or change the behaviour of only one side.
  - *Shrink the market*: target a tight niche and repeat, launch in a limited geography, constrain the offer to one simple value proposition, or limit activity to set times.
  - *Seed supply without a network*: aggregate existing public data, build one side as an email list, or anchor on one large participant.
  - *Single-player value*: sell one side a software tool, give software to a third party that brings one side, or launch a standalone product and open the marketplace later.
  - *Manual work*: match and fulfil early transactions by hand, and run meetups.
  - *Structure*: pick markets where users are both buyers and sellers, restrict access to create scarcity, make a previously paid offering free, or (with care) pay early participants with tokens.
- **The Cold Start Problem (Chen).** The book explains how networked products overcome the cold start, drawing on Chen's time at a16z and Uber. In the excerpt published by Lenny's Newsletter (2021), the **atomic network** is the smallest network that is stable and dense enough to stand on its own. Build one, then repeat the playbook for adjacent networks. Density matters more than market size at the start.

## Which side first? (original synthesis)

The GTM engine (`gtm analyze`, `marketplace:` block) scores each side on:

- **acquisition difficulty** (1–5): how hard and costly the side is to recruit;
- **brings the other side**: does each participant import the other side? (Creators bring their audiences; teachers bring their students.)
- **standalone value**: does this side get value before the other side arrives? ("Come for the tool, stay for the network.")

Priority = difficulty + 2 if it brings the other side + 1 if it has standalone value. The output always shows the arithmetic and the reasoning, so the founder can disagree with a specific input rather than with an opaque verdict.

## Concentration rules

- Launch in **one geography and one category** unless there is a specific reason not to, and record that reason (`justification:`). The engine warns about multi-geography or multi-category launches without one.
- Define the **atomic network** concretely, for example "one teacher, 30 of their students and one paid course". Define the **liquidity target** too, for example "70% of listed courses make at least one sale in 30 days".
- **Trust and safety** must exist before scale: identity checks, refunds, dispute handling, content moderation and payout holds.
- **Take rate** needs a disintermediation defence (payments, protection, tools, discovery). A take rate with no reason to stay on the platform invites off-platform deals.

## Liquidity metrics

| Metric | Formula | Needs |
|---|---|---|
| Listing sell-through (liquidity) | listings with ≥1 sale in period ÷ listings live | sales by listing |
| Supply utilisation | suppliers with ≥1 sale ÷ active suppliers | sales by supplier |
| Fill / match rate | requests matched ÷ requests | request log |
| Time to first sale | median days from listing to first sale | timestamps |
| Repeat buyer rate | buyers with ≥2 purchases ÷ buyers | order history |
| Take rate | net revenue ÷ GMV | revenue, GMV |
| Supplier concentration | GMV share of top 10% of suppliers | GMV by supplier |
