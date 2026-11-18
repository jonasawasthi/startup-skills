# Marketplace and multi-sided GTM

Background: [cold start](../../../knowledge/gtm/marketplace-cold-start.md), [marketplace analysis](../../../knowledge/frameworks/marketplace-analysis.md), [a16z metrics](../../../knowledge/a16z/marketplaces.md).

## Decision sequence

1. **Name the sides** and what each one gets. Creator platforms are usually supply (creators, teachers) and demand (fans, learners). Some also have a third side: payment partners, advertisers or institutions.
2. **Pick the side to prioritise** with the engine's side score (difficulty + brings the other side + standalone value). Write the reasoning in plain words, and say what would change the decision.
3. **Define the atomic network**, the smallest unit that works on its own (for example, "one teacher, their existing students and one paid course"). Every early tactic should create more of these units.
4. **Concentrate**: one geography and one category at launch. Expansion criteria are explicit, for example "expand when ≥ 60% of listings sell within 30 days for two consecutive months (target)".
5. **Choose two or three cold-start tactics** that fit: hard side first, single-player tool value, manual matchmaking, seeding with existing audiences, or constrained launches. Reject the rest with a reason.
6. **Liquidity plan**: the target, the measurement (sell-through, time to first sale, fill rate), and what to do if it is missed.
7. **Trust and safety before scale**: identity or KYC for sellers, content rules, refunds and disputes, payout holds, fraud signals.
8. **Quality**: a minimum listing standard, onboarding review, ratings (only when there is volume), and how bad supply is removed.
9. **Frequency and repeat usage**: how often a buyer has a reason to come back, and the mechanism (subscriptions, a series, new releases, follow notifications).
10. **Network effects**: which kind (same-side, cross-side, local) and the evidence to watch for (newer cohorts retaining better, retention by location).
11. **Take rate**: the level, what the platform does to earn it, and the disintermediation defence (payments, protection, tools, discovery, payouts).
12. **Retention, per side**: supply retention (still publishing or selling after 60/90 days) and demand retention (repeat purchase rate).

## Creator and education platforms

- **Supply brings demand.** Each creator's audience is the first demand channel. Creator activation (first paid product published, first sale) is usually the binding constraint, more than learner acquisition.
- **Creator onboarding** is a funnel: identified → contacted → onboarded → first product published → first sale → second product. Measure every step.
- **Learner activation** happens at the first lesson or first paid purchase. Retention is completion and a second purchase.
- **Cross-product discovery** (from one product's buyers to another product) only uses products that are `live`. A `built` product can be offered to beta users who are told it is a beta.
- **Services such as consulting or bookings** are an extra monetisation hypothesis. They need their own readiness (scheduling, payments, cancellation) and their own experiment.

## Output table

| Element | Decision | Evidence / status | Metric | Target (hypothesis) |
|---|---|---|---|---|
| Side to prioritise | | | | |
| Atomic network | | | | |
| Launch geography / category | | | | |
| Cold-start tactics | | | | |
| Liquidity | | | | |
| Trust and safety | | | | |
| Take rate and defence | | | | |
| Supply retention | | | | |
| Demand retention | | | | |
