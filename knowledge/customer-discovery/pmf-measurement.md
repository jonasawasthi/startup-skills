---
title: Measuring product-market fit
source: First Round Review (Rahul Vohra); Sean Ellis; Y Combinator
urls:
  - https://review.firstround.com/how-superhuman-built-an-engine-to-find-product-market-fit/
  - https://pmfsurvey.com/
  - https://www.ycombinator.com/library/LV-how-to-improve-cohort-retention
sources:
  - {title: "How Superhuman Built an Engine to Find Product Market Fit", url: "https://review.firstround.com/how-superhuman-built-an-engine-to-find-product-market-fit/", author: Rahul Vohra, published: 2018-11-12, verification: read-at-source}
  - {title: "Product/Market fit survey by Sean Ellis and GoPractice", url: "https://pmfsurvey.com/", author: "Sean Ellis, GoPractice", verification: url-verified}
  - {title: "How To Improve Cohort Retention", url: "https://www.ycombinator.com/library/LV-how-to-improve-cohort-retention", author: David Lieb, published: 2024-08-29, verification: url-verified (description read)}
authors: [Rahul Vohra, Sean Ellis, David Lieb]
date_checked: 2026-11-08
type: attributed-summary + original-analysis
verification: read-at-source (First Round Review); url-verified (others)
related_skills: [customer-discovery-validation, gtm-strategy-maker]
---

# Measuring product-market fit

See also: [PMF signals (GTM)](../gtm/product-market-fit-signals.md), [YC PMF](../yc/product-market-fit.md) and [metrics and retention](../gtm/metrics-and-retention.md).

## Attributed

- **The Ellis question** asks how users would feel if they could no longer use the product. As Vohra reports it, Ellis found that startups with fewer than about 40% "very disappointed" users usually struggled to grow.
- **Vohra (2018)** surveyed only recently active users (at least twice in the previous two weeks), and found about 40 responses enough for a *directional* reading. He then segmented to the high-expectation customers and tracked the score over time.
- **Cohort retention (Lieb, YC, 2024)** covers defining cohorts, defining an active user, and choosing the time frame in which to measure retention.

## How the skill applies this (original synthesis)

- **Signals, not verdicts.** The engine reports *early PMF signals*, and never says "product-market fit achieved". Demonstrated PMF needs retention that flattens across cohorts, repeat use or purchase, organic demand, and economics that work, sustained over time.
- **The survey needs its context.** The engine refuses to compute the very-disappointed share without the response counts, and warns when:
  - fewer than 40 people responded (a heuristic from Vohra's account, not a statistical rule);
  - the respondents were not recent active users;
  - the sample came from friends, family or a waitlist.
- **Metrics only from measured inputs.** Activation, repeat usage, retention, referral, organic share, paid conversion and churn are computed by the shared GTM metrics engine, which shows formulas and missing inputs instead of estimates. Inputs are validated: a numerator larger than its denominator, or a negative count, is an error.
- **Vanity metrics are excluded:** sign-ups, page views, downloads and waitlist size are reported as context, never as PMF signals.
