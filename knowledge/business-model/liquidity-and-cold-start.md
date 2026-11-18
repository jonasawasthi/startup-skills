---
title: Marketplace liquidity and the cold-start problem
source: NFX; a16z (Andrew Chen); Lenny Rachitsky
urls:
  - https://www.nfx.com/post/19-marketplace-tactics-for-overcoming-the-chicken-or-egg-problem
  - https://a16z.com/books/the-cold-start-problem/
  - https://www.lennysnewsletter.com/p/how-to-kickstart-and-scale-a-marketplace
sources:
  - {title: "19 Tactics to Solve the Chicken-or-Egg Problem and Grow Your Marketplace", url: "https://www.nfx.com/post/19-marketplace-tactics-for-overcoming-the-chicken-or-egg-problem", author: James Currier, published: 2019-07, verification: read-at-source}
  - {title: "The Cold Start Problem", url: "https://a16z.com/books/the-cold-start-problem/", author: Andrew Chen, published: 2021, verification: url-verified (book page; book not read)}
  - {title: "How to kickstart and scale a marketplace business", url: "https://www.lennysnewsletter.com/p/how-to-kickstart-and-scale-a-marketplace", author: Lenny Rachitsky, published: 2019-11-20, verification: read-at-source}
authors: [James Currier, Andrew Chen, Lenny Rachitsky]
date_checked: 2026-11-08
type: attributed-summary + original-analysis
verification: read-at-source (NFX, Rachitsky); url-verified (Chen book page)
related_skills: [business-model-designer, gtm-strategy-maker]
---

# Marketplace liquidity and the cold-start problem

See also: [GTM marketplace cold start](../gtm/marketplace-cold-start.md), [marketplace business models](marketplace-business-models.md).

## Attributed

- **NFX (Currier, 2019)** lists 19 tactics, starting with "Get the hardest side first", usually the more valuable side, found by testing sales and onboarding; once that side reaches critical activity, the other side becomes easier to attract. Others include appealing tightly to a niche, subsidising the most valuable side, building a SaaS tool for one side, connecting the two sides by hand, and setting geographic, time or demand constraints.
- **Rachitsky (2019)** found that nearly every marketplace he studied constrained its launch by geography or category to reach critical mass; TaskRabbit focused on liquidity in its most popular categories.
- **Chen, *The Cold Start Problem* (2021)** is a book on starting networks; only its a16z page was checked.

## Original synthesis: liquidity is measured, not declared

| Not liquidity | Liquidity signals |
|---|---|
| Registered sellers or buyers | Share of listings or suppliers with a sale in a period (sell-through) |
| Listings or courses published | Share of demand requests that end in a completed transaction |
| Sign-ups, followers, waitlists | Repeat transactions by the same buyers |
| Matches or enquiries | Time to first sale for a new supplier |

**Rules used by the engine.** The funnel holds measured counts only; ratios are computed only when both counts exist; "emerging" or "achieved" liquidity needs measured completed transactions and a dataset; "achieved" also needs a repeat or sell-through rate. "This side brings the other" is an assumption to test, not a mechanism.

**Choosing the first side.** The founder's choice (often supply first) is a hypothesis about which side is harder. Write down the smallest market where liquidity could exist (one exam, one city, one category) and the measure that would show it.
