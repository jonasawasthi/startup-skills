# Crosswalk: startup-idea-evaluator dimensions and the 15-dimension base read

The base read uses the same scale as the [startup-idea-evaluator rubric](../../startup-idea-evaluator/references/scoring-rubric.md): **Strong / Adequate / Weak / Unknown**, each with a confidence (high / medium / low). Ratings are never added up and are never probabilities. The base read splits the evaluator's 10 dimensions into 15, because an investor panel asks about economics, operations, cash and regulation separately.

This file is the exact mapping. It exists so the two skills never hold competing judgements about the same startup.

## Mapping, from the 15 dimensions back to the evaluator

| Base-read dimension | Evaluator dimension it comes from | Relationship | What to do when an evaluator report exists |
|---|---|---|---|
| D01 Problem severity | Problem severity | **Carried** | Start from the evaluator's rating |
| D02 Market opportunity | Market + Timing | **Merged** | Start from the lower of the two. If one is Unknown, start from the other and say so. State both source ratings in the explanation |
| D03 Customer demand | Customer clarity (partly) | **Derived** | Rate afresh. Customer clarity asks *who* the customer is; D03 asks what customers have *done*. D03 may not be Strong while Customer clarity is Weak, unless a divergence note explains it |
| D04 Competitive landscape | None (report section 4, question bank D) | **New** | Rate afresh from the evaluator's competitor evidence. The evaluator has no rating for this |
| D05 Product differentiation | Differentiation | **Carried** | Start from the evaluator's rating |
| D06 Business model | Business model | **Split, secondary** | Rate afresh on who pays, how much and for what. It may not be more than one level away from the evaluator's Business model rating without a divergence note |
| D07 Unit economics | Business model | **Split, primary** | Start from the evaluator's Business model rating. The evaluator's Strong anchor for Business model is "unit economics work under conservative assumptions", so this is where that rating lands |
| D08 Customer acquisition | Distribution | **Split, primary** | Start from the evaluator's Distribution rating. Its Strong anchor is "a repeatable channel with CAC evidence, or a built-in loop", which is acquisition |
| D09 Distribution | Distribution | **Split, secondary** | Rate afresh on the commercial route and who controls it (retailers, distributors, platforms). It may not be more than one level away from the evaluator's Distribution rating without a divergence note |
| D10 Scalability | Execution risk (partly) | **Derived** | Rate afresh. Use the evaluator's execution-risk evidence about scope and capacity |
| D11 Operational complexity | Execution risk (partly) | **Derived** | Rate afresh. Use the evaluator's risk register (operational category) |
| D12 Financial sustainability | Execution risk (partly) | **Derived** | Rate afresh. The evaluator's "achievable with the current team and capital" covers capital only in passing; cash, burn and runway need their own evidence |
| D13 Defensibility | Defensibility | **Carried** | Start from the evaluator's rating |
| D14 Founder execution capability | Founder–market fit | **Carried** | Start from the evaluator's rating. Add evidence of delivery against plan if the ledger has it |
| D15 Legal and regulatory risks | None (report section 3 "Regulatory considerations", risk register) | **New** | Rate afresh from the evaluator's regulatory notes and risk register. The evaluator has no rating for this |

## Mapping, from the evaluator's 10 dimensions forward

| Evaluator dimension | Base-read dimensions |
|---|---|
| Problem severity | D01 (carried) |
| Customer clarity | D03 (derived). The segment definition is also used by D01 and D08 |
| Market | D02 (merged with Timing) |
| Timing | D02 (merged with Market) |
| Differentiation | D05 (carried). D04 uses the same competitor evidence but is a separate rating |
| Business model | D07 (primary), D06 (secondary) |
| Distribution | D08 (primary), D09 (secondary) |
| Defensibility | D13 (carried) |
| Founder–market fit | D14 (carried) |
| Execution risk | D10, D11, D12 (all derived) |

Two base-read dimensions, D04 and D15, have no evaluator rating behind them. Every evaluator dimension maps to at least one base-read dimension.

## Rules

1. **Carried** and **primary** dimensions start from the evaluator's rating. Change one only when a ledger entry newer than the evaluator report, or more specific to the dimension, supports the change. Record the change as a divergence note that cites the entry.
2. **The evidence ceiling still applies.** A carried rating that the ceiling does not allow (for example Strong with no verified evidence) is lowered, and the divergence note says why. See [dimensions](dimensions.md).
3. **Unknown carries over as Unknown.** Never turn an evaluator Unknown into a rating without new evidence.
4. **A divergence note** names the evaluator report and its date, both ratings, and the ledger IDs that justify the difference. The base read lists all divergences together and recommends re-running the evaluator. It never silently overrides it.
5. **The ledger is the single source of truth.** Both skills read and cite the same `evidence.yaml`. Neither report is evidence for the other; only ledger entries are.
6. **No evaluator report is required.** Without one, build the base read from the profile and ledger directly, using the evaluator's [question bank](../../startup-idea-evaluator/references/evaluation-framework.md) for questions.

## Verdicts

The evaluator gives one verdict: Pursue, Pursue with changes, Validate before building, or Do not pursue as framed. This skill gives [five separate judgements](verdict.md). They are cross-referenced, never relabelled:

| Evaluator verdict | Usually corresponds to |
|---|---|
| Validate before building | "Needs further validation": Yes |
| Do not pursue as framed | "Should not proceed in its current form": Yes |
| Pursue / Pursue with changes | No fixed correspondence. A business can be worth pursuing and still not be investable or investment-ready |

If the two disagree (for example the evaluator says Pursue and this skill finds "should not proceed in its current form"), report the disagreement with the evidence that changed, and recommend re-running the evaluator.
