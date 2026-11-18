# Working with the other skills

This skill orchestrates the nine other Startup Skills. It reads their outputs, reuses the shared startup profile and evidence ledger, and hands work back to them. It never redoes their work and never keeps a separate evidence store.

## Shared state rules

- **One profile, one ledger.** Read `outputs/<startup>/startup-profile/` (or `startup-profile/` in the project root): `profile.yaml`, `evidence.yaml` and the narrative files. Every rating cites ledger IDs.
- **Inventory first.** Run `"$TK/bin/startup-kit" shark-tank context <profile-dir>` before anything else. It lists the profile's identity and stage, ledger counts by status, the number of missing-information items, every sibling output folder with paths and dates, and flags outputs older than the ledger's latest update. It writes nothing.
- **Writes are limited to two things.** Your own files in `outputs/<startup>/shark-tank/`, and founder-provided ledger entries through `shark-tank record … --confirmed` after the founder agrees. The only other write is creating an empty profile with `profile init`, and only after the founder agrees (see the last section).
- **Never write** to the narrative profile files (`customers.md`, `business-model.md` and the others), to another skill's output folder, or to existing ledger entries.
- **Simulation outputs are not evidence.** Never record a simulated investor's view in the ledger. The founder may share the outputs inside their own team, with the simulation label intact. They are never presented as an investor's view to anyone, and never placed in decks, proposals, investor emails or public material.
- **Stale inputs.** If `context` flags an output as older than the ledger, say so, use the ledger, and recommend re-running that skill. Never quietly mix old ratings with new evidence.
- **Conflicts.** If a sibling output and the ledger disagree, the ledger wins. Report the conflict and name the skill to re-run.

## What each skill provides, and when to hand off

Hand-offs are recommendations to the user, written in plain words, for example: "The demand evidence is the gap. The customer-discovery-validation skill can design the interviews and the pre-sale test; the panel can be re-run when results are in the ledger."

| Skill | What this skill reads from it | Hand off when | Never duplicate |
|---|---|---|---|
| startup-idea-evaluator | `startup-analysis/<startup>-evaluation.md`: its ten ratings, mapped through the [crosswalk](evaluator-crosswalk.md); its risk register; its experiments. Its [question bank](../../startup-idea-evaluator/references/evaluation-framework.md) is the question source for the base read | The user wants a full idea evaluation, a single verdict ("is this a good idea?"), or the base read records divergences from an older report | The 14-section evaluation report and its verdict. Divergences are reported and the evaluator is re-run; never overridden |
| startup-research | `research/` briefs and the ledger entries they created: market counts, competitors, regulation | D02, D04 or D15 is Unknown because facts are missing, not because the founder has not acted | Market, competitor or regulatory research. Do not research and record these facts here |
| customer-discovery-validation | The discovery spec, hypothesis statuses, problem-solution fit verdict and interview evidence (`source.type: interview`, which can support Strong) | D01 or D03 is Unknown or Weak; a recommended experiment is a customer test | Interview guides, hypothesis registers, experiment cards, fit verdicts. Give it the dimension, the decisive question and the experiment idea |
| business-model-designer | The business model spec: maturity state, revenue stages, costs, stress test, payment and regulatory dependencies | D06 or D07 is Unknown or Weak; J5 names a model or price change | Canvases, model comparison, stress tests |
| gtm-strategy-maker | The GTM spec and analysis: ICP, channel matrix, channel tests, acquisition cost and channel evidence | D08 or D09 is Unknown or Weak; a channel test is recommended | Channel plans, positioning, roadmaps, KPI workbooks |
| pitch-deck-maker | The deck spec, `products.md` statuses (live, built, planned), and `investor-pitch/investor-qa.md`. Its [investor Q&A bank](../../pitch-deck-maker/references/investor-qa.md) supplies question themes for interrogation | The user wants a deck, or wants to turn debrief topics into prepared answers in the Q&A file | Decks and the Q&A file. The debrief lists topics; the deck skill writes the answers |
| fundraising-strategist | `fundraising/readiness.md` for J3; its [negotiation reference](../../fundraising-strategist/references/negotiation.md) for scenario arithmetic; its [investor research](../../fundraising-strategist/references/investor-research.md) protocol for profile maintenance | The user asks whether a real investor fits the startup, wants an investor list, outreach, a raise plan, meeting preparation or term-sheet help | Real-investor fit, target lists, outreach, raise plans. A simulated evaluation is never a fit analysis and never a reason to contact anyone |
| startup-proposal-generator | Nothing required | The user wants a business plan or proposal | Proposals. A proposal must not cite simulated investor views |
| business-document-generator | Its renderer: `startup-kit doc <file.md> --out <dir>`, then `check` and `preview` | The user wants DOCX or PDF of a shark-tank document | Rendering. Run `shark-tank check` first; rendering does not replace it |

The calculators are shared engine commands, not skills: `startup-kit market-size` (D02), `unit-economics` (D07) and `model` (D12). Use their outputs; never type a market size or a unit-economics figure that they did not produce. `unit-economics` models subscriptions; for a product sold per unit, follow the per-unit rule under D07 in [dimensions](dimensions.md#d07-unit-economics): a contribution table with every input cited, recorded in the ledger as an estimate, or as a verified calculation only when every input is verified.

## Requests that belong elsewhere

| The user asks | Route to |
|---|---|
| "Evaluate my idea", "is this a good business?", "stress-test my startup" (no investor or programme named) | startup-idea-evaluator |
| "Is <real investor> a good fit for us?", "should we pitch <real investor>?", "write to <real investor>" | fundraising-strategist. It researches real investors and never implies interest |
| "How would the <programme> investors see this?", "run a mock Dragons' Den panel", "grill me like a Shark Tank pitch" | This skill |
| "Make my pitch deck" | pitch-deck-maker |

When a request mixes both (for example, a simulated panel and then real outreach), do the simulation, then hand off the outreach with the sentence: "Real investor fit and outreach are handled by the fundraising-strategist skill, which works from public records and makes no assumption of interest."

## How findings flow back

| Finding | Where it goes |
|---|---|
| A fact the founder states during interrogation | `pending_ledger`, then the ledger through `shark-tank record --confirmed` after the founder agrees. Status `reported`, never `verified` |
| A critical dimension that is Unknown | A validation experiment in the [experiment template](../../../knowledge/frameworks/validation-experiments.md), handed to customer-discovery-validation (customer tests) or gtm-strategy-maker (channel tests) |
| A divergence from the evaluator | Listed in the base read, with a recommendation to re-run startup-idea-evaluator |
| A risk the evaluation surfaces | Named with its [risk register](../../../knowledge/frameworks/risk-register.md) category in the verdict, for the evaluator or proposal to pick up. Not written into another skill's file |
| Debrief topics to prepare | Handed to pitch-deck-maker for the Q&A file |
| J3 gaps (legal hygiene, data room) | Handed to fundraising-strategist |

## Running it for a different startup

Everything in this skill is per startup except the investor library.

1. Use the new startup's own profile directory and output folder, `outputs/<other-startup>/shark-tank/`. Never reuse a base read, evaluation, session or verdict from another startup.
2. Run `shark-tank context` on the new profile, then build a new base read with the new startup's type and stage.
3. Reuse the investor profiles as they are. Lenses describe the investor, not any startup.
4. Use the new startup's own market for D02 sources and D15 regulators.

## A startup with none of the other skills' outputs

No other skill is required.

1. **No profile at all.** Ask one question: whether to create an empty profile, and under what name. If the idea has no name, offer a short working name taken from the idea: "Shall I create a startup profile so the evidence can be recorded, under the working name <Short Name> unless another name suits?"
   - **Yes:** run `"$TK/bin/startup-kit" profile init outputs/<startup>/startup-profile --name "<Name>"`, then build the base read with the engine as usual. It will be almost entirely Unknown.
   - **No:** give the same read in chat, following the [base-read template](../assets/templates/base-read.yaml) without the engine (a general description is context, not evidence, so every dimension is Unknown; a specific figure the founder states as true in the conversation may be used only if it is explicitly labelled founder-provided in the reply, and then allows Adequate at most, or Weak at low confidence if it goes against the founder's interest). State that the engine checks were not run, and write no files. The simulation label ends "and no recorded startup evidence" in place of the evidence date.
2. **Empty ledger** (a profile exists). Build the base read with the engine. The founder's description is context, not evidence, and a figure the founder states becomes founder-provided evidence only once it is recorded in the ledger (through interrogation and `record --confirmed`). With no ledger entries every dimension is Unknown, the evidence profile line shows it, and that is the honest result. Investors' stances are then mostly "Cannot form a view (insufficient evidence)", and the verdict is usually J1 Not yet determinable and J4 Yes.
3. **Fastest route to evidence.** Offer founder interrogation. Its answers become founder-provided entries after the founder agrees at the debrief, and the base read can then reach Adequate where they apply.
4. **Better evidence.** Recommend the skill that fits the largest critical gap (table above), then re-run the evaluation.
