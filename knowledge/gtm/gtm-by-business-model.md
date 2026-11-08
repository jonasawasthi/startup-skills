---
title: GTM by business model
type: original-analysis
sources: [gtm/channels-and-distribution.md, gtm/marketplace-cold-start.md, gtm/product-led-growth.md, gtm/pricing-and-monetization.md, gtm/metrics-and-retention.md]
date_checked: 2026-11-07
verification: original analysis; draws on the attributed files listed in sources
related_skills: [gtm-strategy-maker]
---

# GTM by business model

The GTM engine reads `business_model.type` and adapts the KPI set, the channel guards and the required sections. The table below states its defaults. These are starting points for reasoning, not rules about what works.

| Model (`type`) | Likely first channels | North-star candidates | Required sections | Engine guards |
|---|---|---|---|---|
| `b2b-saas` | Founder-led sales, partnerships, content | Weekly active accounts; net new ARR | ICP with buyer/user split; sales process | PLG needs `self_serve: true` |
| `enterprise` | Founder-led sales, partnerships, events | Qualified pipeline; signed contracts | Buying committee; procurement; pilots | Paid ads and affiliates flagged as weak fits |
| `consumer-app` | Community, social, referral (after retention), creators/influencers | Weekly active users; D30 retention | Activation event; retention cohort plan | Direct sales to consumers flagged; paid ads before retention flagged |
| `marketplace` | Founder-led supply acquisition, niche community, partnerships | Transactions with a successful match per week | Side priority; atomic network; liquidity; trust and safety | Multi-geography or multi-category launches without justification; take rate without a defence |
| `creator-platform` | Founder-led creator onboarding, creator referrals, creators' own audiences | Creator GMV; creators with ≥1 sale | Supply vs demand split; creator activation; payouts | As marketplace; demand-side paid ads before creator activation flagged |
| `education` | Teacher/creator partnerships, community, content/SEO, WhatsApp-style groups | Paid enrolments; completion; repeat purchase | Learner vs payer roles; outcomes evidence | Completion and outcome claims need evidence |
| `devtool` | Developer-led, docs/SEO, open source, community | Weekly active projects; time to first call | Docs and DX plan; free tier | Outbound before developer adoption flagged |
| `services` | Founder-led sales, referrals, partnerships | Billable utilisation; repeat clients | Capacity plan | Scaling channels beyond delivery capacity flagged |
| `ecommerce` | Social, influencers, paid (with contribution margin), email | Repeat purchase rate; contribution per order | Unit economics per order | Paid ads without contribution margin flagged |

## Hybrid models

Many startups are hybrids. A creator platform is a marketplace with a SaaS tool for creators, and an education business may also be a marketplace of teachers. Set `type` to the model that **earns the revenue**, and use `secondary_types` for the others. The engine merges the guards of every listed type.

## Stage adaptation

| Stage | GTM emphasis | What not to do yet |
|---|---|---|
| Idea / pre-launch | Customer discovery, a waitlist with qualification, manual onboarding | Paid scaling, PR, a broad launch |
| Private beta | Activation, the first cohort, hand-delivered value | Referral incentives, affiliates |
| Early revenue | One channel to repeatability; pricing experiments | More than three primary channels |
| Growth | Loops, scaling channels, new segments and geographies | Entering many geographies at once |
