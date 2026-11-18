# Fieldnote: investor-panel-evaluator example

**Fictional example.** Fieldnote is the repository's invented company: offline-first records software for agricultural (dairy) cooperatives, sold as a subscription, at an early-revenue stage. Every figure about it comes from the fictional ledger in [`../startup-profile/evidence.yaml`](../startup-profile/evidence.yaml). The founder answers in the interrogation are scripted, fictional and illustrative. Nothing here asserts that Fieldnote is or is not viable.

The investor profiles used (Steve Baxter, Hem Raj Dhakal, Naomi Simson) are real people's sourced, dated, public profiles from [`skills/investor-panel-evaluator/investors/`](../../../skills/investor-panel-evaluator/investors/). Every document is an analytical simulation of how their *documented lenses* bear on the evidence. None of it is a statement by them, a quotation, or a prediction of their decisions, and nothing says or implies that any of them knows of or would back Fieldnote.

## What this example shows

- A base read built **only** from the existing ledger. Ten of fifteen dimensions are Unknown because the ledger is silent on them, and that is left visible rather than filled in.
- How the same base read produces different evaluations through different profiles, with every row traceable to a lens and to evidence or a gap.
- The stance rule doing its job: on identical evidence, two members **cannot form a view** (half or more of the dimensions critical for the startup or primary for them are Unknown) and one holds the stance **Conditional on evidence** (her primary dimensions are mostly rated).
- A panel that discusses only what changes a stance. Two dimensions do (D06 and D15, each traced to `dimension_emphasis`); the different evidence each lens demands on the shared gaps (D07, D08, D12) is recorded, not debated. Every rating is agreed.
- An interrogation that follows the turn contract, with every question asking for one decisive unknown (two figures are two turns): a vague answer met with follow-ups that each ask for one anchor, an honest "I don't know", a request for a decision, and new founder figures held for the debrief.

## Reading order

| # | File | What it demonstrates |
|---|---|---|
| 1 | [base-read.yaml](base-read.yaml) and [base-read.md](base-read.md) | One rating per dimension under the evidence ceiling; `saas` at `early-revenue`, critical set D01, D03, D07, D08, D12, D14; ambition left `unknown` because no founder statement of it is in the ledger. D06 is the only Strong (verified prepayments, E-017); D01 stays Adequate although interview evidence would allow Strong, because the sample is small |
| 2 | [evaluation-steve-baxter.md](evaluation-steve-baxter.md) | The showcase individual evaluation. Cannot form a view: 4 of 7 critical-or-primary dimensions Unknown. Gap concerns on D10 and D12 come from his primary lenses (L4, L3); D07 and D08 are `base` because no lens of his covers them. Lens readings show why the agent survey counts for little under L1 |
| 3 | [evaluation-hem-raj-dhakal.md](evaluation-hem-raj-dhakal.md) | Same base read, different first question: D15 (licence and regulator confidence) leads. Shows how a known gap (agriculture) is handled when the customer is agricultural but no lens point depends on agricultural knowledge |
| 4 | [evaluation-naomi-simson.md](evaluation-naomi-simson.md) | Conditional on evidence: only 3 of 7 Unknown because D06 (Strong) is one of her primaries. Shows a documented decline pattern that does not apply because D14 is not Weak |
| 5 | [panel-2026-11-15.md](panel-2026-11-15.md) | Initial positions locked from the evaluations; a divergence map giving each member's role (deciding, considered, not covered) and the evidence each lens demands; two single-dimension exchanges, D06 (`different-priorities`: Strong in one member's deciding set keeps her Unknowns below half) and D15 (`evidence-gap`: the Unknown that takes another member to half); D10 and the shared gaps marked convergent because they change no stance; no stance changes |
| 6 | [verdict.md](verdict.md) | The five judgements: J1 Not yet determinable (D07 Unknown), every J2 class Not yet determinable, J3 No, J4 Yes, J5 No. Readiness, experiments in the template, a 30/60/90 plan, and the fixed closing line |
| 7 | [interrogation/transcript.md](interrogation/transcript.md) | The session as a readable conversation, so the turn contract is visible: every assistant message ends with exactly one question, for one fact or figure, and nothing after it |
| 8 | [interrogation/2026-11-15-a.yaml](interrogation/2026-11-15-a.yaml) | The session file the engine validates: seven turns (five root questions, two follow-ups), seven-criterion assessments, cash and monthly spending asked as two questions, the channel (Q4a) and its cost (Q4b) as two follow-ups, and three pending founder-provided facts |
| 9 | [interrogation/2026-11-15-a-debrief.md](interrogation/2026-11-15-a-debrief.md) | Answer quality by criterion with no total; provisional base-read changes (D08 to Adequate at most on a founder-provided channel and cost; D12 stays Unknown because cash and spending without a model are half the anchor); remaining gaps with experiments; the pending ledger entries |

## Where the example stops

The debrief message ends with the single recording question ("Shall I record these 3 founder-provided entries in the evidence ledger?"), and the founder's reply is not scripted. Recording would append to the tracked Fieldnote ledger, which other examples and tests pin, so `shark-tank record ... --confirmed` is never run here and the session file stays at `status: debrief`. The base read is therefore not rebuilt with the interrogation figures.

## Reproduce the checks

From the repository root:

```bash
bin/startup-kit shark-tank context examples/fieldnote/startup-profile
bin/startup-kit shark-tank base-read examples/fieldnote/shark-tank/base-read.yaml \
  --profile examples/fieldnote/startup-profile --out examples/fieldnote/shark-tank/base-read.md

cd examples/fieldnote/shark-tank
K=../../../bin/startup-kit; P=../startup-profile
$K shark-tank check evaluation-steve-baxter.md   --profile $P --against evaluation-hem-raj-dhakal.md --against evaluation-naomi-simson.md
$K shark-tank check evaluation-hem-raj-dhakal.md --profile $P --against evaluation-steve-baxter.md  --against evaluation-naomi-simson.md
$K shark-tank check evaluation-naomi-simson.md   --profile $P --against evaluation-steve-baxter.md  --against evaluation-hem-raj-dhakal.md
$K shark-tank check panel-2026-11-15.md --profile $P --against evaluation-steve-baxter.md \
  --against evaluation-hem-raj-dhakal.md --against evaluation-naomi-simson.md
$K shark-tank check verdict.md --profile $P
$K shark-tank check interrogation/2026-11-15-a-debrief.md --profile $P --base-read base-read.yaml
$K shark-tank session interrogation/2026-11-15-a.yaml
$K shark-tank queue base-read.yaml --investors steve-baxter,hem-raj-dhakal,naomi-simson --budget 10 --profile $P
```

Each check reports 0 errors and 0 warnings. `check` reads `base-read.yaml` beside each document to confirm that every stance follows from the base read and that every deciding Weak or Unknown dimension has its concern row (guard T6). Simulation labels carry the profile's `last_verified` date and the base read's ledger snapshot (2026-11-08). The test `tests/test_shark_tank.py::test_tracked_example_passes_every_engine_check` runs these checks on every document in this folder, and `test_example_ledger_still_valid_and_untouched` confirms the ledger was not modified.
