---
title: "<Startup>: simulated investor panel"
doc_type: shark-tank
doc_type_label: Analytical simulation
simulation: true
kind: panel
investors: [<id-1>, <id-2>, <id-3>]
profile: ../startup-profile
date: <YYYY-MM-DD>
confidentiality: confidential
---

> [!SIMULATION] Analytical simulation. Not a statement by, on behalf of, or a prediction of the decisions of <Investor A>, <Investor B> and <Investor C>. Based on public sources as of <earliest profile last_verified> and the startup evidence available on <base-read ledger_snapshot>.

<!-- Label dates: public sources = profile last_verified (oldest when several); startup evidence = the base read's
ledger_snapshot. With no recorded evidence, write: and no recorded startup evidence (in place of the date). -->

<!-- Method: references/panel.md. Three to seven members. Write every member's evaluation-<id>.md first, then
this report. Check: startup-kit shark-tank check <this file> --profile <profile-dir> --against <each evaluation>.
Do not begin any heading with a member's name except under Member summaries. Label every figure by its
source: founder-provided, company-provided (or by the company's own account), reported, or estimate. -->

# <Startup>: simulated panel of <YYYY-MM-DD>

## 1. Panel and method

| Member | Programmes and panel status | Effective profile confidence | Evaluation |
|---|---|---|---|
| <Investor A> | <programme, seasons, status as of status_checked date; flag if older than six months> | <high / medium / low> | [evaluation-<id-1>.md](evaluation-<id-1>.md) |

Base read of <YYYY-MM-DD> (ledger snapshot <YYYY-MM-DD>). <Evidence profile line exactly as rendered in base-read.md, including the Unknown count.>

Each member was evaluated independently from the shared base read and that member's own profile. The moderator is the skill's neutral voice and adds no business opinion.

## 2. Base read summary

| Dimension | Rating | Confidence | Decisive evidence | Upgrade if |
|---|---|---|---|---|
| D01 Problem severity | <rating> | <confidence> | <E-IDs or gap> | <condition> |

D11 and D15: Strong means the risk is low or well controlled.

## 3. Initial positions

<!-- Locked after stage 2. Stances must match each evaluation file. -->

| Investor | Stance | Top attraction | Top concern | Lenses |
|---|---|---|---|---|
| <Investor A> | <stance display label, copied from the evaluation> | <A1, dimension, or none on current evidence> | <C1, dimension; may be an evidence-gap concern> | <L1, L2> |

## 4. Divergence map

<!-- The rating is shared, so every member who covers a dimension treats it in the same direction. Cells give the
member's role (deciding, considered, not covered, outside expertise) and, for Unknown or Weak dimensions, the
evidence that member's lens demands. Divergent only when the dimension leads members to different stances, is in one
member's deciding set and not another's in a way that changes a stance, or falls in one member's documented gap.
Different evidence demanded that changes no stance is not divergent: list it under Competing priorities. -->

| Dimension (rating) | <Investor A> | <Investor B> | <Investor C> | Result |
|---|---|---|---|---|
| D07 (Weak) | deciding (critical), L2 | deciding (critical), L1 | deciding (critical), base | convergent |
| D03 (Unknown) | deciding (critical), L1: demands paid pilots | deciding (critical), L3: demands repeat orders | deciding (critical), base | convergent (different evidence, same stance) |
| D09 (Weak) | deciding (primary), L1: demands retailer terms | considered, L3 | outside expertise | divergent (stances differ) |
| Stance | <stance> | <stance> | <stance> | <convergent or divergent> |

## 5. Discussion

<!-- One of three forms. Exchanges only for divergence of stance or deciding set. If the only divergences are gap
re-tags, a note instead: No exchanges: the panel converges on all critical dimensions. <Dxx> is outside <Investor>'s documented expertise (<domain>), so that member's
point is base; this changes no stance. If nothing is divergent, this sentence alone:
The panel converges on all critical dimensions; the evidence leaves no basis for disagreement. -->

| # | Dimension | Investor | Lens | Evidence or gap | Point | Resolution |
|---|---|---|---|---|---|---|
| X1a | D09 | <id-1> | L1 | E-021 | <Third person: why D09 decides this member's stance, or what evidence this lens demands> | |
| X1b | D09 | <id-2> | <L3, or base if no lens of this member covers D09> | E-022 | <Third person: why D09 does not decide this member's stance, or the different evidence this lens demands> | <resolved: name the evidence / persists / becomes founder question> |

## 6. Competing priorities

| Investor | What the primary lenses put first | Source in the profile |
|---|---|---|
| <Investor A> | <for example margin before growth; evidence this member demands on shared Unknown dimensions> | <dimension_emphasis primary: D07 → L2> |

## 7. Disagreements explained

| Exchange | Dimension | Class | Profile field that causes it | What would resolve it |
|---|---|---|---|---|
| X1 | D09 | <different-priorities (deciding sets differ) / evidence-gap (an Unknown deciding dimension)> | <emphasis, lens evidence_demanded or known_gaps of each member> | <specific evidence, founder question or experiment> |

## 8. Final positions

| Investor | Initial stance | Final stance | Cause |
|---|---|---|---|
| <Investor A> | <stance> | <stance> | Unchanged |

## 9. Consensus

<Unanimous, majority, split or no consensus, with counts of members: for example, 3 of 3 members are Not persuaded on current evidence; on D07 all members list a concern. When most members cannot form a view, say so plainly and name the shared gaps: for example, 4 of 5 members cannot form a view on current evidence; the shared gaps are D03 and D07. No mood words.>

## 10. Member summaries

### <Investor A>: evaluation summary

> [!SIMULATION] Analytical simulation. Not a statement by, on behalf of, or a prediction of the decisions of <Investor A>. Based on public sources as of <profile last_verified> and the startup evidence available on <base-read ledger_snapshot>.

<Two or three sentences in the third person: stance, the row that decides it, and a link to the evaluation file.>

## 11. Consolidated assessment

<Three to five sentences leading to the verdict. Link verdict.md, or append the verdict sections from the verdict template here, including the judgements table and the closing line.>

## 12. Sources

- Profile sources by member: <Investor A>: S1, S3; <Investor B>: S2, S4
- Ledger entries cited: <E-IDs>
