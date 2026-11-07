---
title: Unit economics
type: original-analysis
sources: [other/cloud-and-saas.md, a16z/metrics.md]
date_checked: 2026-11-07
related_skills: [startup-idea-evaluator, fundraising-strategist, startup-proposal-generator]
tool: startup-kit unit-economics --arpu --gross-margin --churn --cac
---

# Unit economics

## Formulas (as implemented in `startup-kit`)

| Metric | Formula | Notes |
|---|---|---|
| Gross profit per customer-month | ARPU × gross margin | Use contribution margin if variable support costs are material |
| Expected lifetime (months) | 1 / monthly churn | Churn must be > 0. Never assume zero churn |
| LTV (gross-margin) | ARPU × GM / churn | Undiscounted. Say so |
| LTV : CAC | LTV / CAC | Heuristic target ≥ 3× (BVP 2019, SaaS) |
| CAC payback | CAC / (ARPU × GM) | Heuristic 6–18 months for SMB SaaS (BVP 2019) |
| Marketplace contribution per order | AOV × take rate − payment fees − incentives − support | Per side if both sides are subsidised |

## Rules

1. Pre-revenue unit economics are **assumptions**. Present them as a *target model* with a sensitivity table, never as achieved results.
2. Show **paid CAC** separately from blended CAC.
3. For creator, subscription and membership products, model **both** the platform's unit economics and the **creator's** economics. Creators churn if their payout economics don't work.
4. Payment fees in emerging markets can be material. Include gateway fees with evidence.
5. Run the sensitivity table (the calculator outputs churn × CAC) and state which assumption the business is most sensitive to. That assumption becomes a validation priority.
