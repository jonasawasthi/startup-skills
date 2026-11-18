# Founder interrogation

Interrogation mode questions the founder the way a programme investor's documented lenses would, **one question per turn**. Each answer is assessed, may be followed up at most twice, and any fact the founder states becomes a founder-provided ledger candidate. Nothing is written to the ledger until the founder agrees at the debrief.

Questions are *raised through a lens*. They are never spoken by the investor, never quoted, and never in the investor's first person.

## Session file

The session lives in `outputs/<startup>/shark-tank/interrogation/<session-id>.yaml` (start from the [template](../assets/templates/interrogation-session.yaml)). Conversation memory drifts; the file does not. **Read it at the start of every turn and write it at the end of every turn** while a session is active. Validate it after every write:

```bash
"$TK/bin/startup-kit" shark-tank session outputs/<startup>/shark-tank/interrogation/<session-id>.yaml
```

| Field | Content |
|---|---|
| `session` | `<YYYY-MM-DD>-<letter>`, for example `2026-11-14-a` |
| `mode` | `investor` (one profile), `panel` (three to seven profiles) or `archetype` (no profile; `investors: []`) |
| `investors` | Profile ids |
| `budget` | Number of root questions (follow-ups do not count). Default 10. The user may set 5 to 20 |
| `status` | `setup`, `awaiting-answer`, `paused`, `debrief` or `closed` |
| `queue` | Remaining questions: `{id, dimension, lens, investor, tier, text}` |
| `turns` | One entry per question asked: `n` (1, 2, 3 …), `question` `{id, dimension, lens, investor, text, follow_up_of}`, `answer` (the founder's words, verbatim), `assessment` (seven criteria), `decision` (`follow-up`, `move-on`, `stop`), `new_facts` |
| `pending_ledger` | Facts to offer for recording at the debrief: `{id: F1, claim, key, value, unit, turn, proposed_status: reported}` |
| `next_action` | What the next turn does, for example `ask Q1a` or `debrief` |

`shark-tank session` checks: turn numbers run 1, 2, 3 …; each turn has exactly one question whose text contains one `?` and ends with it, with no first person; each follow-up names an earlier question in `follow_up_of`, and a root question has at most two follow-ups; root questions do not exceed `budget`; every `new_facts` and `pending_ledger` item has `proposed_status: reported`.

## The turn contract

These rules apply to **every** assistant message while `status` is `setup`, `awaiting-answer`, `paused` or `debrief`. The one exception is the first-question message at the end of setup, which carries the simulation label and one short rules paragraph before the question instead of the three short lines.

### What one question means

A question asks for **one decisive unknown: one fact or one figure**. "And" may bind a figure to its unit, date or basis ("how many paying customers, as of which date?" is still one figure with its date), never join a second request. A question that needs two figures is two turns: ask for the first, then the second as the next question or a follow-up. Lists of alternatives the founder must choose between count as one question only when the answer is a single choice. `shark-tank session` flags compound questions under I2.

| Compound (do not ask) | One question each |
|---|---|
| Which channel brought in the last ten customers, and what did each cost? | Which channel brought in most of the last ten customers? Then: what did one customer from that channel cost? |
| How much cash is held, and how many months does it last? | How much cash does the company hold today? Then: what is the monthly burn? |


1. The message contains **exactly one question to the founder**, and it is the **last thing in the message**. Nothing follows it: no sign-off, no second question, no "also", no list of options after it. Then stop and wait.
2. Before the question, at most three short lines:
   - a status line: `Simulation · Q<n> of <budget> · <Dxx> · <lens id> (<Investor or archetype label>)`;
   - a neutral acknowledgement of the last answer, or one line of assessment ("Noted as founder-provided; no customer count yet.");
   - nothing else. No lectures, no advice, no batches of questions.
3. No other sentence in the message ends with a question mark. Rhetorical questions count as questions.
4. Offers to record facts are never asked mid-session. They would be a second question. Facts collect in `pending_ledger` and are offered once, at the debrief.
5. The message that sets `status: closed` contains no question, because the session has ended.

Write the question as a lens question: "A question raised through L3: how many retailers have placed a second order?" In the chat, the status line already names the lens, so the question itself may start directly. Never write "<Investor> asks", "<Investor> would ask", or put the question in quotation marks next to a name.

### Messages that are not answers

| The founder | Do this |
|---|---|
| Asks for advice, asks something else, or changes the topic | Deal with it in one sentence, then repeat the pending question as the turn's single question. Do not pause |
| Asks to pause | Set `status: paused` and end with the single question "Shall we continue with the interrogation?" |
| Answers the question and also asks something else (advice, an offer, a forecast) | Record and assess the answer, deal with the other request in one boundary or answer sentence, then ask the next question |
| Answers several questions at once | Attach each extra answer to its queued question, assess it, and mark it answered (it becomes a turn). The next message still asks one question |
| Says stop, end, enough or debrief | Go to the debrief |
| Asks for an offer, a valuation, or what the investor would decide | One sentence on the boundary (see [verdict](verdict.md#offers-valuations-and-scenarios)), then repeat the current question |
| Asks for role-play or imitation | One sentence declining the form, then repeat the current question |
| Returns later ("continue") | Read the session file and resume from `next_action`. If `status` is `paused`, set it to `awaiting-answer` |

A question repeated after an interruption is the same pending question: it adds no turn to the session file and does not count as a follow-up. The cap of two follow-ups per root question is unchanged.

## Setup

Setup follows the turn contract too.

1. **Base read.** If `base-read.yaml` does not exist, build it first, without questions, from the profile and ledger ([dimensions](dimensions.md)). It is fine for most dimensions to be Unknown. If there is no startup profile, follow the no-profile path in [integration](integration.md#a-startup-with-none-of-the-other-skills-outputs).
2. **Who asks.** If the user has not named an investor, a panel or an archetype, ask exactly that one question: "Should the questions come through one investor, a panel of three to seven, or an unnamed investor type?" If the user already named them, skip this turn.
3. **Budget.** Apply the default of 10 silently unless the user has asked for another number. Ask about the budget only if the user raises it.
4. **Queue.** Run the queue and copy it into the session file:
   ```bash
   "$TK/bin/startup-kit" shark-tank queue outputs/<startup>/shark-tank/base-read.yaml --profile outputs/<startup>/startup-profile \
     --investors <id-1>,<id-2> --budget 10 --json
   ```
5. **First question.** In one message: the simulation label, one short paragraph of rules (this is a simulation; one question at a time; answers are recorded as founder-provided, not verified; say "stop" at any time), then the first question. The question is the last thing in the message.

## Question selection

`shark-tank queue` orders the questions deterministically. Always pass `--profile`: tier 3 depends on the ledger status of the evidence behind each rating, so the tiers differ without it.

| Tier | Condition |
|---|---|
| 1 | Critical dimension, Unknown |
| 2 | Critical dimension, Weak |
| 3 | Critical dimension, Adequate resting only on founder-provided or estimate evidence |
| 4 | Non-critical dimension with `primary` emphasis, Unknown or Weak |
| 5 | Other Unknown dimensions |

Ties break by emphasis (`primary`, then `secondary`, then standard), then by dimension number. In panel mode the queue rotates between members within a tier, so every member's lenses are represented; the rotation never overrides the tier order.

For an investor whose effective profile confidence is `low` (restricted mode), the queue attributes every question to `base`, not to a lens. The status line then reads `… · base (<Investor>)`, and the question is written as a base-read question: "A question raised by the base read: …?". The same rule applies in [individual evaluations](individual-evaluation.md#confidence-limits).

The engine gives the tier, dimension, lens, investor and decisive question. **You write the question text.** Build it from the lens's `evidence_demanded` and the dimension's decisive question, and make it specific to the startup: name the product, segment or figure in question. One dimension per question. For themes and wording, draw on the [investor Q&A bank](../../pitch-deck-maker/references/investor-qa.md) and the evaluator's [question bank](../../startup-idea-evaluator/references/evaluation-framework.md). Do not copy their lists into the session.

## Answer assessment

Assess each answer on seven criteria. Each is `clear`, `partial`, `missing` or `n/a` (when the question does not test it).

| Criterion (YAML key) | Clear looks like |
|---|---|
| Specificity (`specificity`) | Names a segment, channel, figure, date or customer, not a category |
| Evidence (`evidence`) | Cites something checkable: data, a document, a named customer, an experiment result |
| Financial understanding (`financial`) | Numbers are internally consistent; knows margin, acquisition cost and runway as relevant |
| Strategic reasoning (`strategic`) | Explains why this choice over the alternatives, with a trade-off |
| Customer understanding (`customer`) | Describes the customer's behaviour and buying process, not only demographics |
| Execution credibility (`execution`) | Describes what has been done and the next concrete steps, with owners and dates |
| Risk awareness (`risk`) | Names what could go wrong and the signal that would show it |

Assess the **answer, never the person**. Never comment on confidence, manner, accent, personality or effort. "We don't know" is a legitimate answer: evidence is `missing`, but risk awareness can be `clear` if the founder names the gap. The dimension stays Unknown and gets a validation task.

## Follow up or move on

| Situation | Decision |
|---|---|
| Specificity or evidence is `missing` or `partial` on the decisive element, and fewer than two follow-ups have been asked on this root question | `follow-up` (one question) |
| Specificity `clear` and evidence at least `partial` | `move-on` |
| Two follow-ups already asked | `move-on`. If still unanswered, record the topic as unresolved |
| An honest "don't know" | `move-on` |
| The answer conflicts with a ledger entry (same `key`, different value) | One clarifying follow-up that names both figures and their sources. Record the conflict at the debrief; never resolve it yourself, and never replace the ledger figure in the base read |

A follow-up's id is the root id plus a letter (`Q3a`, `Q3b`), and `follow_up_of` names the question it follows.

### Vague answers

A category claim ("we will scale through marketing", "everyone needs this", "we have no competitors", "it will go viral") is an **unanchored claim**. The follow-up asks for the single missing anchor, never several. For example, for D08:

- Trading: "Which channel brought in most of the last ten customers?" (the cost per customer is the next follow-up, if needed)
- Pre-launch: "Which one channel will be tested first?" (the budget or target cost per customer is the next follow-up, if needed)

If the second follow-up is still unanchored, close the topic as "unanchored: D08 remains Unknown", and the debrief recommends a channel test.

## New facts from the founder

- Capture every factual statement (a number, a customer, a contract, a certification) as a `new_facts` item with `proposed_status: reported`, and copy it to `pending_ledger` with an id `F1`, `F2` …, its `key`, `value`, `unit` and `turn`.
- Call it "founder-provided" in the session and in the debrief.
- A founder-provided fact can move a dimension from Unknown to **Adequate at most** (the evidence ceiling). A founder-provided figure that goes against the founder's own interest (for example cash and burn that show the runway ends before the next milestone) may instead move a dimension to **Weak, at low confidence** (the asymmetry rule in [dimensions](dimensions.md#the-evidence-ceiling)). During the session either change is only provisional: list it in the debrief as "provisional: applies if the founder agrees to record F1 and the base read is rebuilt". `base-read.yaml` is rebuilt only after `record` has run.
- A fact that conflicts with a ledger entry keeps the same `key`, so the ledger shows the conflict after recording.

## Stopping

Move to the debrief when any of these holds:

- the founder says stop, end or debrief, or asks to stop for any reason;
- the budget of root questions is used;
- tiers 1 to 3 are exhausted;
- three consecutive critical questions are answered "don't know" (the debrief then says that the business needs validation before more questioning is useful).

Never stop with a follow-up silently pending. Close it as "unresolved".

## Debrief

Write `outputs/<startup>/shark-tank/interrogation/<session-id>-debrief.md` from the [template](../assets/templates/debrief.md), run `shark-tank check` on it, and set `status: debrief`. The file has these sections:

1. Session summary: investor, panel or archetype; questions asked; budget used; why it stopped
2. Answer quality by criterion: counts of `clear`, `partial` and `missing` for each criterion, with no total
3. Strongest answers (turn numbers) and why
4. Weakest answers and the specific anchor that was missing
5. Provisional base-read changes: the ratings that would change once the founder agrees to record the pending entries and the base read is rebuilt (dimension, current rating → provisional rating, founder-provided basis). Nothing changes in `base-read.yaml` during the session
6. Remaining critical gaps, each with a validation experiment in the [experiment template](../../../knowledge/frameworks/validation-experiments.md)
7. Pending ledger entries (table)
8. Topics to prepare: three statements describing answers to prepare for next time. Write them as statements, not as questions

The debrief **message** summarises sections 1, 5 and 7 in a few lines and ends with exactly one question:

- if `pending_ledger` has entries: "Shall I record these <n> founder-provided entries in the evidence ledger?";
- if it is empty: "Shall I close the session?"

### Recording

Only after the founder says yes:

```bash
"$TK/bin/startup-kit" shark-tank record outputs/<startup>/shark-tank/interrogation/<session-id>.yaml \
  --profile outputs/<startup>/startup-profile --confirmed
```

`record` appends each pending item as `status: reported`, `source.type: founder`, with the session id in `notes`. It is append-only and idempotent, and never writes `verified`. Never pass `--confirmed` without the founder's yes in this conversation, and never edit `evidence.yaml` by hand from a session.

If the founder says no, record nothing and keep the items in the debrief as "not recorded at the founder's request".

Then set `status: closed`, rebuild the base read if anything was recorded, and send a closing message with no question. Point to the debrief file, and to [integration](integration.md) for the skills that can close the remaining gaps.
