---
title: Growth metrics, AARRR and retention
source: Dave McClure (500 Startups); a16z; Y Combinator
urls:
  - https://www.slideshare.net/dmc500hats/startup-metrics-for-pirates-long-version
  - https://a16z.com/16-startup-metrics/
  - https://a16z.com/16-more-startup-metrics/
  - https://www.ycombinator.com/library/KT-consumer-startup-metrics
  - https://www.ycombinator.com/library/LV-how-to-improve-cohort-retention
sources:
  - {title: "Startup Metrics for Pirates", url: "https://www.slideshare.net/dmc500hats/startup-metrics-for-pirates-long-version", author: Dave McClure, published: 2007, verification: url-verified}
  - {title: "16 Startup Metrics", url: "https://a16z.com/16-startup-metrics/", author: Andreessen Horowitz, published: 2015-08-21, verification: url-verified}
  - {title: "16 More Startup Metrics", url: "https://a16z.com/16-more-startup-metrics/", author: Andreessen Horowitz, verification: url-verified}
  - {title: "Consumer Startup Metrics", url: "https://www.ycombinator.com/library/KT-consumer-startup-metrics", author: Tom Blomfield, published: 2024-01-06, verification: url-verified (description read)}
  - {title: "How To Improve Cohort Retention", url: "https://www.ycombinator.com/library/LV-how-to-improve-cohort-retention", author: David Lieb, published: 2024-08-29, verification: url-verified (description read)}
authors: [Dave McClure, Andreessen Horowitz, Tom Blomfield, David Lieb]
date_checked: 2026-11-07
type: attributed-summary + original-analysis
verification: url-verified
related_skills: [gtm-strategy-maker, startup-idea-evaluator, pitch-deck-maker]
---

# Growth metrics and retention

See also: [a16z metrics](../a16z/metrics.md) and [unit economics](../frameworks/unit-economics.md).

## Attributed

- **AARRR (McClure, 2007).** The "pirate metrics" divide the customer lifecycle into Acquisition, Activation, Retention, Referral and Revenue. Each stage gets a few measurable conversion steps.
- **a16z metric definitions (2015).** These clarify commonly misused metrics: bookings vs revenue, gross vs net, CAC blended vs paid, and the cohort view of retention.
- **Consumer metrics (Blomfield, YC, 2024)** covers the metrics that matter most for consumer startups. **Cohort retention (Lieb, YC, 2024)** explains how to define cohorts, track active users and choose the right time frame for measuring retention.

## Metric formulas used by the engine

The engine computes a metric only when every input exists. Otherwise it lists the missing inputs and the formula, and never fills a gap with a benchmark.

| Metric | Formula | Inputs |
|---|---|---|
| Activation rate | activated ÷ sign-ups | `signups`, `activated` |
| Visitor → sign-up | sign-ups ÷ visitors | `visitors`, `signups` |
| Purchase conversion | first-time buyers ÷ activated | `activated`, `new_customers` |
| Blended CAC | sales and marketing spend ÷ new customers | `acquisition_spend`, `new_customers` |
| ARPU (period) | revenue ÷ active customers | `revenue`, `active_customers` |
| Churn (period) | customers lost ÷ customers at start | `customers_lost`, `customers_start` |
| LTV (subscription) | ARPU × gross margin ÷ churn | `arpu`, `gross_margin`, `churn` |
| LTV (transactional) | AOV × contribution margin × expected purchases | `aov`, `contribution_margin`, `purchases_per_customer` |
| LTV : CAC | LTV ÷ CAC | as above |
| CAC payback (months) | CAC ÷ (ARPU × gross margin) | `cac`, `arpu`, `gross_margin` |
| Repeat purchase rate | customers with ≥2 purchases ÷ customers | `repeat_customers`, `customers` |
| Take rate | net revenue ÷ GMV | `net_revenue`, `gmv` |
| Liquidity | listings with a sale ÷ live listings | `listings_with_sale`, `listings_live` |
| Cohort retention | active in period n ÷ cohort size | a cohort table |

## How the GTM skill applies this (original synthesis)

- **Pick one key metric per stage.** Pre-launch: problem interviews and committed early adopters. Beta: activation and the first retention cohort. Launch: weekly growth in the key metric, shown with its base number.
- **Leading indicators predict lagging ones.** For example, the share of creators who publish a paid product in their first 7 days predicts creator GMV at 90 days. Every channel experiment names one leading indicator.
- **Benchmarks are context, not inputs.** A benchmark can appear next to a measured value, labelled with its source, but it is never used as a substitute for a missing measurement.
- **Small numbers stay small.** Report "3 of 12 (25%)", never "25% conversion" alone.
