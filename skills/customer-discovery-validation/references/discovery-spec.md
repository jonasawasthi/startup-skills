# Discovery spec and notes format

`startup-kit discovery <action> <spec.yaml>` reads this file. Paths are relative to the spec. Every evidence ID must exist in the shared ledger.

```yaml
discovery:
  company: Acme
  profile: ../startup-profile          # shared profile + ledger (or evidence: path/to/evidence.yaml)
  stage: pre-seed
  notes_dir: interviews                # one Markdown notes file per interview (format below)
  objectives: [...]                    # research objectives
  methodology: "..."                   # written after the research; appears in the report
  summary: "..."                       # executive summary, written from the findings (checked by the claim guard)
  next_steps: [...]
  illustrative: "..."                  # set only for fictional examples; shown as the cover disclaimer

business_model: {type: marketplace}    # same vocabulary as the GTM engine; marketplace models need supply + demand segments

segments:
  - id: S1
    name: ...
    side: supply | demand | customer | other
    market: b2b | b2c | b2b2c | b2g
    problem_area: "month-end payment reconciliation"   # used in interview questions
    roles: {user: ..., buyer: ..., decision_maker: ..., influencers: [...], beneficiary: ...}
    profile: "demographics or firmographics"
    jobs: ["When <circumstance>, I want to <progress>, so I can <outcome>"]
    needs: [...]
    early_adopter_signals: [...]
    scores: {pain: 1-5, access: 1-5, willingness_to_pay: 1-5, reachable_size: 1-5}
    why: "rationale for the scores"   # required with scores
    criteria: [participant criteria]
    recruitment: "..."
    evidence: [E-...]

hypotheses:
  - id: H1
    category: problem | customer | market | solution | pricing | distribution | behavioral | retention
    segment: S1
    dimension: existence | frequency | severity | urgency | dissatisfaction | demand-for-alternatives |
               solution-relevance | behaviour-change | purchase-commitment      # optional; feeds the fit assessment
    statement: ...
    why_it_matters: ...
    supporting: [E-...]
    contradicting: [E-...]
    conflict_note: ...                 # required to mark it supported while contradicting evidence exists
    themes: [S1/problem:theme]         # optional link to coded interview themes
    risk: high | medium | low
    confidence: high | medium | low    # declared; compared with the computed evidence strength
    validation_method: ...
    success_criteria: ...
    status: untested | testing | supported | contradicted | inconclusive
    next_action: ...

experiments:
  - id: X1
    name: ...
    hypothesis: H1
    type: interviews | landing-page | waitlist | prototype | concierge | wizard-of-oz | paid-pilot | pre-order |
          pricing | ab-test | smoke-test | manual-service | retention | survey
    objective: ...
    target_customer: ...
    method: ...
    resources: ...
    duration: ...
    cost: ...
    steps: [...]
    success: {metric: prepaid, op: ">=", value: 3}     # or text; structured criteria are evaluated
    failure: {metric: prepaid, op: "<=", value: 0}
    threshold_basis: heuristic | benchmark | founder   # benchmark also needs benchmark_source or evidence
    evidence_to_collect: ...
    biases: ...
    decision_rule: {success: ..., failure: ..., inconclusive: ...}
    results: {status: planned | running | complete, measured: {prepaid: 3}, evidence: [E-...], outcome: optional}

surveys:
  - {id: SV1, file: surveys/x.csv, segment: S2, sample: active-users | waitlist | friends-family | mixed | unknown,
     pmf_column: "How would you feel if you could no longer use X?"}

pmf:
  inputs: {activated: {value: 14, evidence: [E-001]}, ...}   # GTM metric inputs plus organic_signups, repeat_users, active_users
  survey: {very_disappointed: 7, somewhat_disappointed: 4, not_disappointed: 1, sample: active-users, evidence: [E-..]}
  cohorts: [{name: 2026-09, size: 40, active: [40, 22, 18], evidence: [E-..]}]
```

## Interview notes

```markdown
---
interview: I-01
segment: S1
date: 2026-09-14
participant: M-01            # pseudonymous code
role: Cooperative manager
method: in person
consent: true
transcript: transcripts/I-01.txt   # optional; quotes are checked against it
evidence: E-010                     # optional; otherwise matched by the ledger entry's source.ref
---

- [problem:payment-reconciliation] Month-end reconciliation took two full days
  > "Last month it took me two full days"
- [problem:payment-reconciliation -] (a denial: the participant does not have this problem)
- [interpretation] What the interviewer thinks this means (never evidence)
```

Codes: `problem`, `job`, `alternative`, `behavior`, `trigger`, `spend`, `wtp`, `commitment`, `objection`, `unmet-need`, `outcome`, `decision`, plus `interpretation`. Themes are free-form kebab-case keys, so recurrences across interviews line up.

## Ledger conventions

- **Interview:** `source.type: interview`, `source.ref` set to the notes path relative to the ledger, `status: reported`. Written by `analyze --record`.
- **Survey:** `source.type: dataset` with `signal: stated`.
- **Optional `signal:`** (`stated | observed | committed | paid`) records strength in the willingness-to-pay sense. Only `committed` or `paid` evidence can support pricing or purchase-commitment hypotheses.

## What the engine checks

| Area | Errors | Warnings |
|---|---|---|
| Notes | Missing front-matter fields; unknown codes; quotes not found in the transcript; missing transcript files; quotes without an observation | Consent not recorded; participant looks like a real name; no observations |
| Provenance | Evidence IDs not in the ledger | Interview or survey not recorded in the ledger |
| Segments | Invalid side; scores outside 1–5, or without a rationale; marketplace without both supply and demand segments | Missing user or buyer; B2B without a decision-maker; no jobs |
| Hypotheses | Missing fields or invalid values; *supported* without customer evidence; *supported* with contradictions and no conflict note; pricing or commitment *supported* without committed or paid evidence; *supported* after a failed experiment; *contradicted* without evidence; the same ID on both sides | Conflicts; high declared confidence on weak evidence; linked themes denied more often than confirmed |
| Experiments | Missing any of the 13 fields; invalid type; identical success and failure criteria; numeric thresholds without a basis; benchmarks without a source; completed with no evidence; measured result missing the criterion metric; declared outcome contradicts the measurement | Interest-only method for a willingness-to-pay hypothesis; success measured as interviews completed; no inconclusive branch |
| PMF | Negative inputs; numerator above denominator; survey without counts or evidence | Fewer than about 40 survey responses; sample not recent active users |
