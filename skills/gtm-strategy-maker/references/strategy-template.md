# GTM strategy template (Markdown+)

Copy the skeleton below into `outputs/<startup>/gtm/<startup>-gtm-strategy.md`. Each `##` section can also be published as a standalone document (`doc_type: gtm-plan`). Cite ledger IDs inline as `[E-012]`. Paste the engine's tables from `<spec>-analysis.md`; don't retype the numbers.

~~~~markdown
---
title: Go-to-market strategy
subtitle: <one line: beachhead, first channel, first metric>
company: <Company>
author: <Company> founding team
date: <Month YYYY>
version: "1.0"
doc_type: gtm-strategy
confidentiality: Confidential
profile: ../startup-profile
---

# Executive summary

Five to eight sentences: the beachhead segment, why now, the positioning in one line, the two or three primary
channels, the first 90-day objective, the one metric that matters, and the three assumptions that must be tested first.
State the evidence base honestly ("pre-launch: no customer data yet").

> [!KEY] What we know vs what we assume: two short lists, with ledger IDs.

# 1. Starting point
Company, stage, business model (with hybrids), products and their **status**, team and GTM capacity, GTM budget, and existing assets (audiences, relationships, content).

# 2. Market and segmentation
Category definition. A segment table (segment | size evidence or "unsized" | pain intensity | access | WTP evidence | status).
The beachhead and why it was chosen. Geographic opportunities and the entry sequence. Market-size figures **only** from `market-size`.

# 3. Ideal customer profiles and personas
For each ICP: firmographics or demographics, trigger events, the jobs to be done, current alternatives and spend, the user/buyer/influencer/beneficiary split, how they buy, early-adopter signals, and evidence or *hypothesis* on every row. Personas follow the same rule.

# 4. Positioning and messaging
Positioning components (alternatives → differentiated capabilities → value → best-fit customers → category), the positioning statement (labelled an internal record), elevator pitch, homepage messaging, landing-page structure, the feature → benefit → proof table, objection handling, and messaging by segment.

# 5. Competitive GTM intelligence
| Alternative | Target customer | Positioning | Pricing | Channels | Partnerships | Geography | Observed (source, date) | Interpretation |

# 6. Customer acquisition strategy
The engine's channel matrix. Then one playbook per primary channel (why, execution, resources, cost, leading indicators, success metrics, risks, experiment). Then why the other channels are not chosen now.

# 7. Launch strategy and calendar
The phases that apply, each with objective, audience, positioning, campaign, channels, assets, partners, feedback loop, activation and follow-up. A content calendar table (week | channel | asset | owner | goal).

# 8. Marketplace strategy                 <!-- marketplace and creator models only -->
Side priority (engine table) and the reasoning. Supply acquisition, demand acquisition, the cold-start tactics chosen, atomic network, geographic and category concentration, liquidity targets, matching, trust and safety, quality, transaction frequency, repeat usage, network effects, take rate and its defence, supply and demand retention.

# 9. Pricing and monetisation
Model and value metric. Price points marked **researched** or **hypothesis**. Competitor and substitute prices (sourced). Packaging and upgrade path. Monetisation experiments.

# 10. Growth system and experiments
AARRR definitions for this business, the growth loop(s) written as sentences, and an experiment backlog (hypothesis | metric | threshold | cost | duration | kill | priority).

# 11. KPI dashboard
The engine's metrics tables (computed, plus formulas with missing inputs). The north-star metric, the leading indicators and the measurement plan (tools and events to instrument). Refer to the KPI workbook.

# 12. Execution roadmap
30 / 60 / 90 days, then 6 and 12 months. For each phase: objectives, priorities, tasks, deliverables, dependencies, owner, resources, budget assumptions, KPIs, success criteria. Include the engine's capacity table.

# 13. Risks, assumptions and validation plan
| Assumption | Ledger ID | Status | Why it matters | Test | Kill / pivot signal | Owner | By |
Risks by category (market, channel, product readiness, regulatory, team capacity, competition).

# 14. Missing information
The founder's checklist: from `profile missing` and the engine's findings.
~~~~

## Writing rules

- Lead every section with the decision, then the evidence.
- In a table, put status in its own column, so assumptions stay visible when rows are skimmed.
- Report small numbers with their base: "5 of 14 pilots (36%)".
- Targets read as targets: "Target: 100 paid purchases by week 10." Never "We will get 100 purchases."
