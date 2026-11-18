---
name: investor-panel-evaluator
description: Runs a simulation of how investors from Shark Tank (US, India, Nepal, Australia) and Dragons' Den (UK) would read a startup. It rates the business once on 15 dimensions from the evidence ledger, then reads that through each investor's sourced profile and lenses, so differences are traceable. It offers individual evaluations, a moderated panel of 3–7, one-question-per-turn founder interrogation, and a verdict separating good, investable and investment-ready. It never speaks for or imitates real people, never states offers, valuations or that anyone would invest, and gives no scores or probabilities. Use when someone asks what a named programme investor or panel would make of their startup (even its business model), wants a mock Shark Tank or Dragons' Den panel, or wants to be grilled as these programmes question founders. Not for a general idea evaluation (startup-idea-evaluator), or whether a real investor, even a programme investor, is a fit to approach or how to reach them (fundraising-strategist).
license: MIT
compatibility: The engine, guards and DOCX/PDF outputs need Python 3.9+ and the Startup Skills toolkit (bin/startup-kit; run scripts/setup.sh). Investor profiles ship with the skill; adding or re-verifying one needs a web search or fetch tool. A simulation for analysis and practice only; not investment, legal or financial advice.
metadata:
  author: Jonas Awasthi
  version: "1.0.0"
  repository: https://github.com/jonasawasthi/startup-skills
  collection: startup-skills
---

# Investor Panel Evaluator

Show a founder how the documented priorities of well-known programme investors would bear on their startup, and why those investors would differ, without ever putting words in a real person's mouth. Rate the business once from evidence; let each investor's sourced lenses decide only what matters more and what gets asked.

## Setup

```bash
TK="$(cd "${CLAUDE_SKILL_DIR}" && cd -P ../.. && pwd)"; "$TK/bin/startup-kit" doctor
```

If the toolkit is missing (this skill was copied on its own), work in Markdown with the same templates, run every guard in [guards](references/guards.md) by reading, and tell the user that the engine checks were not run.

**Shared state.** Find the startup profile (`startup-profile/` in the project root, or `outputs/<startup>/startup-profile/`) and run `"$TK/bin/startup-kit" shark-tank context <profile-dir>` before asking anything. It lists the ledger by status and every other skill's outputs, with stale flags. Write only to `outputs/<startup>/shark-tank/`. Write to the ledger only through `shark-tank record … --confirmed`, after the founder agrees. Never edit the narrative profile files or another skill's outputs. How each of the nine other skills feeds in and receives hand-offs is in [integration](references/integration.md).

## Modes

| Mode | The user says, for example | Output | Method |
|---|---|---|---|
| Base read | "How strong is the evidence?" (always built first) | `base-read.yaml`, `base-read.md` | [dimensions](references/dimensions.md), [types and stages](references/business-types-and-stages.md) |
| Individual evaluation | "How would <Investor> read this?" | `evaluation-<investor-id>.md` | [individual evaluation](references/individual-evaluation.md) |
| Panel | "Run a panel of the current <programme> investors" | `panel-<YYYY-MM-DD>.md` plus one evaluation per member | [panel](references/panel.md) |
| Interrogation | "Grill me", "question me like the panel would" | `interrogation/<session-id>.yaml`, `-debrief.md` | [interrogation](references/interrogation.md) |
| Verdict | "Is this investable?", "what is the overall result?" | `verdict.md` or the panel report's last section | [verdict](references/verdict.md) |
| Summary report | "Give me one document with everything" | `summary-<YYYY-MM-DD>.md` (`kind: report`), organised by the founder's topics, adding nothing new | [verdict](references/verdict.md#founder-summary-report) |

### Choosing investors

- List the library with `"$TK/bin/startup-kit" shark-tank profiles` (id, name, regions, programmes and panel status, effective confidence, sources, lenses). Show one profile's lenses with `--id <id>`. The index is [investors/README.md](investors/README.md).
- The user can choose by name, by programme ("the current Dragons' Den panel": profiles with `panel_status: current`; for an `unconfirmed` line-up the latest aired season, for a `dormant` programme its last panel, each labelled; a named programme is the roster, so proceed without confirming), by region, or by asking for a mix of perspectives (propose profiles whose `primary` emphasis differs).
- Prefer investors whose documented expertise touches the startup's sector; never say that any profiles "will do". When a named panel is used, say which members' documented gaps cover the startup's sector (with the simulation label, since that names an investor with a point); if most of the startup falls in an investor's `known_gaps`, suggest another.
- If a name could match two profiles, ask which. If a person has no profile or the profile fails validation, say so, and offer an unnamed archetype or the steps in [maintaining investors](references/maintaining-investors.md). Never build a profile from memory, and do not research one mid-request unless the user asks.
- A panel has three to seven validated profiles. Former, unconfirmed and dormant members are allowed and labelled. Whenever a programme's panel is listed, show each status with its `status_checked` date ("current as of <date>"), and flag any status checked more than six months ago for re-verification.
- Private profiles: pass `--library <dir>` to `profiles`, `queue` and `check`.

## Workflow

1. **Inventory.** Run `shark-tank context`. If no profile exists, follow the no-profile path in [integration](references/integration.md#a-startup-with-none-of-the-other-skills-outputs). Ask only for what is missing and changes the read: business type, stage and ambition if unclear.
2. **Base read.** Copy the [template](assets/templates/base-read.yaml) to `outputs/<startup>/shark-tank/base-read.yaml`. Set type, stage and the critical set. Rate all 15 dimensions under the evidence ceiling. If an evaluator report exists, follow the [crosswalk](references/evaluator-crosswalk.md). Then run `"$TK/bin/startup-kit" shark-tank base-read <base-read.yaml> --profile <profile-dir> --out <base-read.md>` and fix every error.
3. **Choose investors** as above. Naming people or a programme counts as naming the roster: list the members used and proceed without asking. Confirm only when the user gave neither.
4. **Evaluate** each investor independently from the base read and their own profile ([template](assets/templates/evaluation.md)). Run `shark-tank check <evaluation> --profile <profile-dir> --against <every other evaluation of this startup>`. `check` fails if it cannot find the base read or the ledger; `--no-base-read` and `--no-ledger` are only for checking a fragment on purpose, never for a delivered document.
5. **Panel** (if asked): lock the initial positions, map divergence, discuss only real divergence, and report ([template](assets/templates/panel-report.md)). Run `shark-tank check <panel> --profile <profile-dir> --against <each member evaluation>`.
6. **Interrogation** (if asked): follow the session file and turn contract in [interrogation](references/interrogation.md). Build the queue with `shark-tank queue <base-read.yaml> --profile <profile-dir> --investors <ids> --budget <n> --json`, validate the session with `shark-tank session <file>` after every turn, and record facts only with `shark-tank record <session> --profile <profile-dir> --confirmed` after the founder says yes.
7. **Verdict:** five judgements, readiness, experiments and the action plan ([template](assets/templates/verdict.md)). Run `shark-tank check`.
8. **Review every document; never skip this step.** Read it against the reviewer checklist in [guards](references/guards.md), including the name-swap read of every evaluation. The engine checks catch common phrasings and structural errors only; passing them is not proof that a document is safe to deliver.
9. **Files** if the user wants them: `"$TK/bin/startup-kit" doc <file.md> --out <dir>`, then `check` and `preview`, and look at the pages.
10. **Hand off** the gaps to the skill that closes them ([integration](references/integration.md)).

## Non-negotiable rules

- **Simulation label first.** Every document starts with the `[!SIMULATION]` label, and every investor section in a multi-investor document starts with one. Never present the output as the person's view.
- **Third person, no impersonation.** No first person, no script format, no quotation marks in a sentence that names an investor, no catchphrases, no "<Investor> thinks". Questions are raised *through a lens*: "A question raised through L3: …?". Decline role-play or imitation in one sentence and give the analytical version.
- **No offers and no implied interest.** Never state or imply an offer, valuation, equity, royalty or deal term attributed to an investor or the panel, or that anyone would invest, is interested, or has seen the startup. Scenarios only on request, in a `[!SCENARIO]` callout, by investor class, never by name.
- **Four stances only:** Persuaded on current evidence; Conditional on evidence; Not persuaded on current evidence; Cannot form a view (insufficient evidence). Never "in" or "out". Precedence: a deciding dimension (critical, or `primary` for the investor) rated Weak at medium or high confidence means Not persuaded; otherwise, half or more of the deciding dimensions Unknown (a Weak at low confidence counts as Unknown) means Cannot form a view, never a softened "Conditional on evidence". Every Weak or Unknown deciding dimension has a concern row.
- **Never "interested".** Do not use the word with an investor, a member or the panel as subject, including when reporting a stance.
- **One base read.** Rate the business once: Strong, Adequate, Weak or Unknown, each with confidence. Investors never re-rate. No numbers, scores, sums, percentages of dimensions or probabilities. Any rating summary shows the Unknown count.
- **Evidence ceiling.** Strong needs verified or interview-behavioural evidence; founder-provided or estimated evidence allows Adequate at most; assumptions alone mean Unknown.
- **Every investor point is traceable** to a lens (or `base`) and to ledger evidence or a named gap. Differences between investors come only from profile fields.
- **Real people's information** comes only from their validated profile: public, professional, sourced and dated. Nothing personal.
- **Chat counts too.** Every voice rule applies to chat replies. A reply in which any sentence names an investor together with a stance, a lens or a point (including a forecast of what the simulation would produce) starts with the simulation label.
- **Interrogation:** exactly one question per turn, last in the message, nothing after it, including setup and debrief. Founder statements are founder-provided, never verified, and reach the ledger only after the founder agrees.

## Failure handling

| Situation | Response |
|---|---|
| No startup profile | Ask once whether to create an empty one with `profile init`, and under what name (offer a short working name from the idea if it has none). Yes: create it and build the base read (almost entirely Unknown). No: give the same read in chat from the template, with the label ending "and no recorded startup evidence", say the engine checks were not run, write no files ([integration](references/integration.md#a-startup-with-none-of-the-other-skills-outputs)) |
| Empty ledger | Build the base read anyway (mostly Unknown); expect most stances to be "Cannot form a view"; offer interrogation to gather founder-provided facts |
| User asks to add figures that are not true or not yet true ("add 40 paying customers") | Never add them to the ledger or the base read under any status. In the same reply, explain in prose what would change if such evidence existed, from `upgrade_if`, without changing any rating, stance or judgement ([guards](references/guards.md)) |
| User asks for scores, an overall score, a ranking of dimensions or a probability of a deal | One sentence stating what the simulation does not do (it gives no scores, rankings or probabilities); then the ratings with confidence, the Unknown count, the judgements and the panel stance |
| Most panel members cannot form a view | Report it plainly with counts and the shared gaps; it is a legitimate result, not a reason to change stances |
| Requested investor has no profile, or it fails validation | Say so; offer an archetype, or the steps to add a profile. Never improvise one |
| User asks for a script, role-play or "what would <Investor> say" | Decline the form in one sentence; deliver the analytical evaluation |
| User asks what an investor would offer, or for a valuation | One sentence on the boundary; offer a labelled scenario from the founder's own ask |
| User asks whether a real investor fits, or wants outreach | Hand off to fundraising-strategist |
| "Is <Investor> interested?" or "which investor would like my business most?" | Simulation label first, then one sentence declining the framing. Then each member's stance and how many of their deciding dimensions are rated, in the panel's roster order. Never order or rank investors by fit or liking |
| User asks whether the output comes from the programme or the person | Repeat the notice below in one sentence |
| Panel of fewer than three or more than seven | Ask the user to add or drop members (one question) |
| Sibling outputs are older than the ledger | Use the ledger, name the stale output, recommend re-running that skill |
| Base read diverges from an evaluator report | Add divergence notes; recommend re-running the evaluator; never override it silently |
| Founder's answer contradicts the ledger | One clarifying follow-up naming both figures; show the conflict at the debrief |
| `shark-tank check` reports errors | Rewrite the flagged rows from the lenses and evidence; never delete the label or the gap to pass |
| Toolkit missing | Use the templates by hand, run the guards by reading, and say the engine checks were not run |

## Validation checklist

- [ ] `shark-tank context` was run first, and no question re-asked something the profile or ledger holds.
- [ ] `shark-tank base-read`: 0 errors. All 15 dimensions, six buckets each, ceiling respected, Unknown count shown.
- [ ] Every evaluation and the panel report pass `shark-tank check` with `--against` the other evaluations: 0 errors.
- [ ] The verdict passes `shark-tank check`; all five judgements; J2 names a class; closing line present.
- [ ] Interrogation: `shark-tank session` 0 errors after every turn; one question per message; `record --confirmed` only after the founder's yes.
- [ ] Reviewer checklist in [guards](references/guards.md) ticked: tone, ratings, name swap, honest panel, fair assessment.
- [ ] Every chat reply read against "Chat replies" in [guards](references/guards.md) before sending; when it names an investor or gives figures, save it and run `shark-tank check <reply.md> --chat --profile <profile-dir>` (never wrap it as a document).
- [ ] No real investor's name appears outside the label, headers, rows and tables this skill defines; nothing implies interest or an offer.
- [ ] If files were generated, `doc`, `check` and `preview` pass and the pages were inspected.

## Not affiliated

This skill is independent work. It is not affiliated with, endorsed by or sponsored by Shark Tank, Dragons' Den, their broadcasters or format owners, or any person profiled. Names are used only to identify the public record being analysed.

## Templates and examples

Templates are in [assets/templates/](assets/templates/): `base-read.yaml`, `evaluation.md`, `panel-report.md`, `verdict.md`, `interrogation-session.yaml`, `debrief.md`, `summary-report.md`, and `investor-profile.md` for maintainers. The profile format is in [investor-profile-schema](references/investor-profile-schema.md); adding, updating and verifying investors is in [maintaining investors](references/maintaining-investors.md).

Two finished examples, both with fictional companies: [Fieldnote](../../examples/fieldnote/shark-tank/README.md) (software; three investors who differ for traceable reasons, with an interrogation session and transcript) and [Ottlebrook](../../examples/ottlebrook/README.md) (a physical-product company where the panel honestly agrees and the verdict says not to proceed in its current form).
