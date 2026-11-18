---
title: "<Startup>: simulated investment verdict"
doc_type: shark-tank
doc_type_label: Analytical simulation
simulation: true
kind: verdict
investors: [<ids whose evaluations this verdict draws on>]
profile: ../startup-profile
date: <YYYY-MM-DD>
confidentiality: confidential
---

> [!SIMULATION] Analytical simulation. Not a statement by, on behalf of, or a prediction of the decisions of <Name or names>. Based on public sources as of <earliest profile last_verified> and the startup evidence available on <base-read ledger_snapshot>.

<!-- Label dates: public sources = profile last_verified (oldest when several); startup evidence = the base read's
ledger_snapshot. With no recorded evidence, write: and no recorded startup evidence (in place of the date). -->

<!-- Method: references/verdict.md. Gates use the critical set of the base read only. No offers, valuations or
equity outside a scenario callout; no statement that anyone would invest. Check: startup-kit shark-tank check
<this file> --profile <profile-dir>. -->

# <Startup>: simulated investment verdict

Basis: base read of <YYYY-MM-DD>, ledger snapshot <YYYY-MM-DD>, evaluations by <investors or panel of YYYY-MM-DD>.

## 1. Overall business assessment

<Evidence profile line exactly as rendered in base-read.md, including the Unknown count.>

| Critical dimension | Rating | Confidence | Decisive evidence |
|---|---|---|---|
| D01 Problem severity | <rating> | <confidence> | <E-IDs or gap> |

<Three to five sentences: what the evidence shows about the business as a whole. Label every figure by its source: founder-provided, company-provided (or by the company's own account), reported, or estimate.>

## 2. Strongest opportunities

- <Opportunity, dimension, evidence [E-…]>

## 3. Biggest weaknesses

- <Weakness, dimension, evidence [E-…]>

## 4. Critical unanswered questions

- <Dxx: decisive question of each critical dimension rated Unknown>

## 5. The five judgements

| Judgement | Answer | Reason | Deciding dimensions |
|---|---|---|---|
| J1 Good business | <Yes / No / Not yet determinable> | <gate that decided it> | D01, D03, D06, D07, D12 |
| J2 Investable business (venture) | <Yes / No / Not yet determinable> | <class conditions> | D02, D10, D13 |
| J2 Investable business (operator-strategic) | <Yes / No / Not yet determinable> | <class conditions; delete the row if not assessed> | D09, D11, D12 |
| J2 Investable business (debt-or-revenue-based) | <Yes / No / Not yet determinable> | <class conditions; delete the row if not assessed> | D12 |
| J3 Investment-ready business | <Yes / No / Not yet determinable> | <requirements met or the gap list> | <critical set>, D15 |
| J4 Needs further validation | <Yes / No> | <open decisive questions> | <critical Unknowns> |
| J5 Should not proceed in its current form | <Yes / No> | <if Yes: which form fails and what change would re-open the case> | <dimension> |

<If J1 is Yes and J2 (venture) is No, add: This is not a criticism of the business; it describes fit with one class of investor.>

## 6. Investment readiness

| Readiness dimension | Rating | Evidence |
|---|---|---|
| Story clarity | <ready / partly / not ready> | <evidence> |
| Progress | | |
| Market | | |
| Team | | |
| Plan | | |
| Materials | | |
| Legal and corporate | | |
| Diligence hygiene | | |
| Investor pipeline | | |

For a raise plan, investor list or outreach, use the fundraising-strategist skill.

## 7. Conditions that would improve the case

- <Dxx: upgrade condition from the base read>

## 8. Reasons an investor might decline

- <Reason, with the lens (or base) and evidence it comes from. A reason, not a prediction.>

## 9. Recommended validation experiments

| Assumption (ledger ID) | Experiment | Metric and success threshold | Kill criterion | Sample, duration, cost | Owner and date |
|---|---|---|---|---|---|
| <E-…> | <experiment> | <metric and threshold> | <kill criterion> | <sample, duration, cost> | <owner, date> |

## 10. Founder action plan

| Window | Action | Gap it closes |
|---|---|---|
| 30 days | <action> | <Dxx> |
| 60 days | <action> | <Dxx> |
| 90 days | <action> | <Dxx> |

<!-- Only if the user asked for a scenario. One callout, framed by investor class, no investor name,
figures from the founder's own ask, arithmetic from fundraising-strategist/references/negotiation.md.
> [!SCENARIO] Hypothetical scenario: not an offer, not a valuation, not attributed to any investor.
> A scenario in which <investor class> provides <capital and what else>, using the founder's own ask [E-…].
> <Dilution arithmetic, step by step.>
> Assumptions:
> - <assumption>
-->

This assessment reflects the evidence available on <YYYY-MM-DD>. It is not a prediction of success, nor of any investor's decision.
