---
title: "<Startup>: simulated evaluation by <Investor>"
doc_type: shark-tank
doc_type_label: Analytical simulation
simulation: true
kind: evaluation
investors: [<investor-id>]
profile: ../startup-profile
date: <YYYY-MM-DD>
confidentiality: confidential
---

> [!SIMULATION] Analytical simulation. Not a statement by, on behalf of, or a prediction of the decisions of <Investor>. Based on public sources as of <profile last_verified> and the startup evidence available on <base-read ledger_snapshot>.

<!-- Label dates: public sources = profile last_verified (oldest when several); startup evidence = the base read's
ledger_snapshot. With no recorded evidence, write: and no recorded startup evidence (in place of the date). -->

<!-- Method: references/individual-evaluation.md. Voice: third person only. No quotation marks in a sentence
that names the investor, no first person, no script format, no offers or deal terms, no statement that the
investor would or would not invest. Check: startup-kit shark-tank check <this file> --profile <profile-dir>
--against <each other evaluation of this startup>. -->

# <Investor>: simulated evaluation of <Startup>

Profile confidence: <high | medium | low> (<confidence_rationale, shortened>) · Programmes: <programme, seasons, panel status> · Profile sources: <count> · Base read of <YYYY-MM-DD>

<!-- Only when most of the startup falls in the profile's known_gaps: add the next line and suggest another investor. -->
<!-- Most of this startup falls outside <Investor>'s documented expertise (<gap domains>); the record gives little basis for reading it. -->

<!-- Low effective confidence only: add the next line and use restricted mode. -->
<!-- Profile confidence: low. Low confidence: investor-specific emphasis is tentative; this section mostly reflects the base read. -->

Lenses applied (analytical interpretations of the documented record):
- L1 <label>: <one line from the interpretation> (<S#, S#>)
- L2 <label>: <one line from the interpretation> (<S#>)

## Stance

<!-- Write exactly one display label, chosen in this order (references/individual-evaluation.md):
Deciding dimensions: critical for the startup or primary for this investor, counted once. A Weak at low confidence
counts as Unknown. Every Weak or Unknown deciding dimension needs a concern row; leaving one out changes nothing.
1. Not persuaded on current evidence: a deciding dimension rated Weak at medium or high confidence.
2. Cannot form a view (insufficient evidence): half or more of the deciding dimensions Unknown. Usual pre-launch.
3. Persuaded on current evidence: every critical and primary dimension Adequate or Strong, no concern on a Weak rating.
4. Conditional on <evidence>: the rest; never a residual label for mostly Unknown evidence.
Mention no other label in this section. -->

**<Stance display label>.** <Two or three sentences in the third person, each tied to a row: for example, the attraction in A1 rests on verified evidence, while C1 and Q1 leave the deciding dimension open.>

## Point trace

<!-- One row per point. A lens worded around the investor's home market is applied to the startup's own market;
say so in the row (Applied to <market>: ...). Points whose judgement depends on a known-gap domain are base.
Lens: a lens id of this investor or base. Evidence: E-IDs with status, or gap.
C rows are ranked: C1 is the top concern. An Unknown on a critical or primary dimension gives a concern worded as
an evidence gap, with gap: in the Evidence column. Label every figure by its source: founder-provided,
company-provided (or by the company's own account), reported, or estimate. Low confidence: Q and R rows use base. -->

| # | Kind | Point | Lens | Dimension (base rating) | Evidence |
|---|---|---|---|---|---|
| A1 | attracts | <What the lens finds attractive, specific to the startup> | L1 | D09 (Strong) | E-021 verified |
| C1 | concern | <The top concern> | L2 | D07 (Weak) | E-033 founder-provided, E-040 estimate |
| C2 | concern | No evidence yet that <the decisive element of a critical or primary dimension> | L1 | D03 (Unknown) | gap: <decisive question> |
| Q1 | question | A question raised through L1: <one question to the founder>? | L1 | D03 (Unknown) | gap: <decisive question> |
| R1 | evidence demanded | <Evidence the lens demands that the ledger lacks> | L1 | D03 (Unknown) | gap |
| B1 | potential deal-breaker | <Only from a lens with a decline pattern; delete the row otherwise> | L2 (decline pattern, S2, S5) | D07 (Weak) | E-040 |
| M1 | recommendation | <Action tied to the upgrade condition and an experiment> | base | D08 (Unknown) | gap |

<!-- If another evaluation of this startup legitimately shares the top concerns, add one line:
Declared convergence: both evaluations centre on <Dxx> because <lens of this investor> and <lens of the other> both derive from <documented emphasis>. -->

## What attracts

<Prose for the A rows, in order. Medium confidence: word each lens point "on the documented record (S#)". If none: None on current evidence.>

## Primary concerns

<Prose for the C rows, C1 first.>

## Questions this lens would raise

- A question raised through L1: <question>?

## Evidence that would be demanded

- <R row, with the dimension it would settle>

## Potential deal-breakers

<B rows, each called a potential deal-breaker and tied to its decline pattern and sources. Otherwise: None identified on current evidence.>

## Recommendations

- <M row: action, the dimension's upgrade condition, and the experiment in the validation-experiment template>

## What would make the business more compelling under these lenses

<Two to four sentences tying the upgrade conditions of the deciding dimensions to the lenses that weigh them.>

## Outside documented expertise

<Points re-tagged base because they fall in the profile's known gaps, or: None.>

## Sources

- Profile sources used: S1 <title> (<publisher>, <date>); S2 <title> (<publisher>, <date>)
- Ledger entries cited: <E-IDs>
