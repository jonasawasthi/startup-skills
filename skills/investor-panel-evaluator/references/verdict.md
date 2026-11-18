# Investment verdict

The verdict answers **five separate judgements** about the startup. A television verdict collapses "good business", "investable" and "ready" into one yes or no; founders need them apart. Each judgement is answered on its own, from gates over the [base read](dimensions.md)'s critical-dimension table, and may be "Not yet determinable".

Write the verdict to `outputs/<startup>/shark-tank/verdict.md` from the [template](../assets/templates/verdict.md), or as the last section of a [panel report](panel.md). Check it with:

```bash
"$TK/bin/startup-kit" shark-tank check outputs/<startup>/shark-tank/verdict.md --profile outputs/<startup>/startup-profile
```

## Structure

1. Simulation label and basis: base-read date, ledger snapshot, the investors or panel whose evaluations it draws on
2. Overall business assessment: the evidence profile line, the critical-dimension table, three to five sentences
3. Strongest opportunities, with evidence IDs
4. Biggest weaknesses, with evidence IDs
5. Critical unanswered questions: the decisive questions of the critical dimensions rated Unknown
6. The five judgements, as a table: `Judgement | Answer | Reason | Deciding dimensions`
7. Investment readiness: the nine [fundraising-readiness](../../../knowledge/frameworks/fundraising-readiness.md) dimensions rated ready, partly or not ready, with a hand-off to fundraising-strategist for the plan
8. Conditions that would improve the case: the `upgrade_if` conditions of the deciding dimensions
9. Reasons an investor might decline: from the concerns and potential deal-breakers across the evaluations, each with its lens and evidence, framed as reasons and never as predictions. Include both kinds of concern: those on Weak ratings ("the evidence points against …") and evidence-gap concerns on Unknown critical or `primary` dimensions ("there is no evidence yet that …"). For a startup with mostly Unknown dimensions, the gaps are the main reasons
10. Recommended validation experiments, each in the [experiment template](../../../knowledge/frameworks/validation-experiments.md): assumption (ledger ID), experiment, metric and threshold, kill criterion, sample, cost and time, owner
11. Founder action plan: ordered, in 30, 60 and 90 days, each item tied to a gap
12. Optional: a hypothetical scenario, only if the user asked (below)
13. Closing line, exactly: "This assessment reflects the evidence available on <date>. It is not a prediction of success, nor of any investor's decision."

## The five judgements

"Critical" means the critical set for the startup's type and stage ([business types and stages](business-types-and-stages.md)). Answers are `Yes`, `No` or `Not yet determinable` (in YAML: `yes`, `no`, `not-yet-determinable`).

| ID | Judgement | Question it answers | Yes requires | No when | Not yet determinable when |
|---|---|---|---|---|---|
| J1 | Good business | Can it create and capture value sustainably at its intended scale? | D01, D03, D06 and D07 at least Adequate; D12 not Weak; no critical dimension Weak on `verified` or founder-against-interest evidence | Any of D01, D03, D06, D07 Weak on such evidence | Any of D01, D03, D06, D07 Unknown |
| J2 | Investable business, **always for a named investor class** | Does it fit the return profile of that class? | J1 is not No, and the class conditions below hold | J1 is No, or the class dimensions are Weak with evidence | The class dimensions are Unknown |
| J3 | Investment-ready business | Could it go through a diligence process now? | J2 Yes for at least one class; no critical dimension Unknown; D15 not Weak; fundraising readiness Progress, Plan, Legal and corporate, and Diligence hygiene at least "partly" | Any requirement fails. List the gaps | Rarely used. Usually No with the gap list |
| J4 | Needs further validation | Are decisive questions still open? | Any critical dimension is Unknown, or a critical Adequate rests only on estimates or founder-provided figures | Otherwise: no critical dimension is Unknown, and each critical rating rests on at least one `verified` entry or interview evidence | Not used |
| J5 | Should not proceed in its current form | Does the evidence show the current form fails? | A critical dimension is Weak on `verified` or founder-against-interest evidence, with no credible mitigation inside the current segment, model or channel. Name which form fails and what change (segment, model, channel, price) would re-open the case | Otherwise | Not used |

**A Weak rating decides a judgement only at medium or high confidence.** Wherever this table or the rules below say Weak, a Weak rating held at low confidence counts as Unknown for the judgement, and the reason cell says so ("D13 is Weak at low confidence, so it does not decide this"). A judgement must not rest on a rating the base read itself holds loosely.

### J2 investor classes

Write one J2 row per class you assess, with the class in the Judgement cell, for example `J2 Investable business (venture)`. Assess at least one class. Never name a person in a J2 row.

| Class | Yes requires |
|---|---|
| `venture` | D02, D10 and D13 at least Adequate, and `ambition: venture` |
| `operator-strategic` | D09 or D11 Adequate or better where operator help matters, and D12 Adequate or better |
| `debt-or-revenue-based` | D12 Strong or Adequate, with `verified` revenue |

**When the class dimensions are mixed**, decide in this order and stop at the first that applies:

0. For `debt-or-revenue-based` only, and before everything else: no `verified` revenue means **No** (see below). This takes precedence over steps 1 to 3, so a pre-launch company is No for this class even when D12 is Unknown.
1. Any class dimension rated Weak, at medium or high confidence, on `verified` or founder-against-interest evidence: **No**.
2. Otherwise, any class dimension rated Unknown: **Not yet determinable**.
3. Otherwise, apply the Yes conditions in the table; if they are not met, **No**.

For `debt-or-revenue-based`, a company with no `verified` revenue is **No**. State it as a fact about its stage ("no verified revenue yet, so outside this class for now"), not as a criticism of the business.

### Allowed and excluded combinations

- **J1 Yes and J2 No (venture)** is common and is **not a criticism**. A profitable two-location clinic with a small serviceable market is a good business that is not venture-investable; it may be operator- or debt-investable. Say so in those words.
- J2 Yes and J3 No: investable but not ready (for example, missing legal hygiene or no data room).
- J1 Not yet determinable and J4 Yes: the usual pre-launch result.
- **J5 Yes excludes J2 Yes and J3 Yes** for the current form. J1 may still be Not yet determinable for a changed form.
- **J3 Yes and J4 Yes never occur together.**

`shark-tank check` rejects a missing judgement, a J2 row without a class, and the two excluded combinations.

### Cross-reference to the evaluator

The judgements map to the evaluator's single verdict only for cross-reference ([crosswalk](evaluator-crosswalk.md#verdicts)): J4 Yes usually corresponds to "Validate before building", and J5 Yes to "Do not pursue as framed". Never relabel one as the other. If they disagree, report the evidence that changed and recommend re-running the evaluator.

## Investment readiness

Rate the nine dimensions of [fundraising readiness](../../../knowledge/frameworks/fundraising-readiness.md) (story clarity, progress, market, team, plan, materials, legal and corporate, diligence hygiene, investor pipeline) as ready, partly or not ready, each with evidence. If `outputs/<startup>/fundraising/readiness.md` exists, use its ratings and cite its date instead of rating again. Readiness feeds J3 only. For a raise plan, target list or outreach, hand off to fundraising-strategist ([integration](integration.md)).

## Offers, valuations and scenarios

- No offer, valuation, equity percentage, royalty, loan or deal term appears anywhere attributed to an investor or the panel.
- Never write that an investor or the panel would, will or is likely to invest, or is interested.
- If the user asks "what would <Investor> offer?", explain the boundary in one sentence ("This simulation cannot state what a real person would offer; it can show a labelled scenario built from your own ask.") and offer a scenario.

A **hypothetical scenario** is written only when the user asks for one. Check J5 first: if it is Yes, the rule against a scenario for the current form applies whatever figures the user gives, and the other rules below are not reached. Rules:

- It sits in one `> [!SCENARIO]` callout whose first line is: "Hypothetical scenario: not an offer, not a valuation, not attributed to any investor."
- It is framed by investor class ("a scenario in which an operator-investor provides capital plus retail access"), never by name. No investor name appears anywhere in the callout.
- It uses only figures the user supplied (for example the founder's own ask, cited from the ledger) or ranges the user specifies. If the ledger holds no ask, ask the founder one question for the amount and what is offered for it, then build the scenario from those figures, labelled founder-provided. If the user gives a percentage but no amount, ask for the amount (one question).
- No scenario for the current form when J5 is Yes. Say why in one sentence (the evidence shows the current form fails) and name the changed form the verdict already describes; a scenario may be built for that changed form only if the user asks.
- It goes in the optional last section of `verdict.md`, or in chat if no verdict exists. In both places it sits inside the `[!SCENARIO]` callout.
- It shows the dilution arithmetic from fundraising-strategist's [negotiation reference](../../fundraising-strategist/references/negotiation.md), without restating that reference.
- It ends with an `Assumptions:` line followed by a `> - ` list of every assumption.

Offer language next to an amount or percentage outside such a callout is an error in `shark-tank check`.

## Founder summary report

Write a summary report when the user wants one document that ties the base read, the evaluations, the panel and the verdict together, organised by the topics the founder cares about (for example demand, economics, the team, the raise), rather than by the skill's own steps. It adds nothing new: every statement in it comes from those documents and keeps their citations, stances and judgements unchanged.

- File: `outputs/<startup>/shark-tank/summary-<YYYY-MM-DD>.md`, from the template `assets/templates/summary-report.md`.
- Front matter `kind: report`, `investors:` listing every investor whose evaluation it draws on. The simulation label comes first.
- Each topic section names the dimensions it covers, states their base-read ratings, and links the source document for detail. Any rating summary includes the Unknown count.
- If it quotes the five judgements, it uses the same table as the verdict and ends with the verdict's closing line.
- Check it with `shark-tank check <summary> --profile <profile-dir>`.
