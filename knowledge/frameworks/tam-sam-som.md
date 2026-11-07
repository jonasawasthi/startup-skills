---
title: Market sizing (TAM / SAM / SOM)
type: original-analysis
date_checked: 2026-11-07
related_skills: [startup-idea-evaluator, startup-research, pitch-deck-maker, startup-proposal-generator]
tool: startup-kit market-size <spec.yaml> --profile <profile-dir>
---

# Market sizing method

## Definitions used across all skills

- **TAM** (total addressable market): annual revenue if *every* customer who could plausibly buy this category bought from you, within a stated geography and year.
- **SAM** (serviceable available market): the part of TAM your product and business model can actually serve (segment, geography, channel, language, regulation).
- **SOM** (serviceable obtainable market): the part of SAM you can realistically capture within a stated period, given competition and your go-to-market capacity.

## Rules

1. **Bottom-up first.** Count customers × price (or × frequency × value × take rate). Top-down figures from reports are *cross-checks* only.
2. **Every factor has evidence or a status.** The calculator inherits the weakest status, so a TAM that rests on one assumption is labelled an assumption.
3. **State the scope**: geography, year, currency, and whether figures are revenue or GMV.
4. **Show the arithmetic** on the slide or in the appendix.
5. **Never fabricate.** If a count is unknown, write the research task to find it ("number of registered cooperatives: query the cooperative registry") and leave the layer *unsized*.
6. **Revenue, not GMV**, unless labelled. A marketplace's TAM in revenue terms is GMV × take rate.
7. **SOM needs a mechanism**: channel capacity × conversion × time. An arbitrary percentage is not a mechanism.

## Spec format (`market.yaml`)

```yaml
title: Creator memberships – Nepal
currency: USD
geography: Nepal
year: 2027
tam:
  label: All creators monetising audiences in Nepal
  factors:
    - {label: Creators with ≥ 10k followers, value: 18000, evidence: E-021}
    - {label: Annual creator revenue via platform, value: 1200, unit: USD/yr, evidence: E-022}
    - {label: Platform take rate, value: 0.1, evidence: E-023}
sam:
  base: tam
  factors:
    - {label: Share with audiences able to pay digitally, value: 0.35, evidence: E-024}
som:
  base: sam
  factors:
    - {label: Share reachable by our creator-partnerships channel in 3 years, value: 0.1, status: assumption}
top_down:
  - {label: National digital payments volume, value: "…", evidence: E-030, note: plausibility check}
```

## Common failure modes

| Failure | Fix |
|---|---|
| "1% of a $50B market" | Replace with a bottom-up count of reachable customers |
| A global TAM for a local product | Size the launch geography; show expansion separately |
| Mixing GMV and revenue | Label clearly; convert with the take rate |
| Stale reports | Record the publication date; ledger flags data older than 18 months |
| Single-source figures | Add a second source or mark *estimate* |
