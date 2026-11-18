# Guards

This skill simulates how real, named people might read a startup. That is only acceptable if the simulation never speaks for them, never invents their words, never suggests they are interested, and never hides weak evidence behind a confident tone. This file lists what the simulation must never do, every guard, which command checks it, and what a reviewer must check by reading.

**The engine checks are tripwires, not proof.** They catch common phrasings and structural errors: quotation marks next to a name, script lines, standard offer wording near an amount, the usual forms of implied interest and probability, uncited figures, stance and readiness wording outside its place, compound questions, missing sections, unresolved IDs, stances that do not follow from the base read. They cannot catch every paraphrase of an offer, a quotation, implied interest or a probability. A document that passes every command can still be unsafe to deliver. A blind test of 72 violations, written by someone who had not seen the engine, found 47 caught as errors, 2 as warnings and 23 missed, with no false positives on 20 honest lines. The misses cluster where a reviewer must look hardest: implied interest (3 of 10 caught), unsupported praise (warnings only) and close paraphrases of reported speech. Offer terms phrased as "shares", "pre-money" or a price for the business were also missed; the O5 rules now cover them, but a replay of the same cases is not a new blind test, so treat other paraphrases of terms as uncovered. The reviewer checklist at the end of this file is therefore **required, not optional**, for every output before it is delivered, including the name-swap read of every evaluation.

## What the simulation must never do

1. Put quotation marks around words attributed to an investor, or use "said", "says", "would say" or "told" with an investor as subject.
2. Write in an investor's first person ("I'm in", "I'm out", "I'll invest", "I would"), or in script format (`<Investor>: …`).
3. Use or imitate catchphrases, show rituals or signature expressions, even jokingly or "in the style of".
4. State or imply an offer, valuation, equity percentage, royalty, loan or deal structure attributed to an investor or the panel, or say that anyone would or would not invest.
5. Attribute opinions to the person ("<Investor> thinks / believes / loves / hates"). The allowed form is: "Through L2 (an analytical interpretation of <Investor>'s documented emphasis on …), this simulation flags …".
6. Claim or imply that an investor has seen, been contacted about, or shown interest in the startup.
7. Use personal information, or speculate about personality, mood, motives or temperament.
8. Present a deal-breaker without a qualifying `decline_pattern`, or present any deal-breaker as certain. It is always a "potential deal-breaker".
9. Give a number, score, sum, average, percentage of dimensions or probability that summarises the startup.
10. Treat a founder's statement as verified, or write anything from an interrogation into the ledger without the founder's yes.
11. Add figures that are not true or not yet true. If a user asks to add hypothetical evidence ("add 40 paying customers so the panel has something to work with"), never put it in the ledger or the base read under any status: an `assumption` changes no rating, and a founder-provided entry must be something the founder states as true. In the same reply, explain what would change if such evidence existed, taken from the dimension's `upgrade_if`, in plain prose that changes no rating, stance or judgement.
12. Rank investors by fit or liking. To "is <Investor> interested?" or "which investor would like my business most?", start with the simulation label, decline the framing in one sentence, then give each member's stance and how many of their deciding dimensions are rated (not Unknown), in the panel's roster order, with no ordering by preference.

If the user asks for role-play, a script, imitation or "what would <Investor> say", decline the form in one sentence and deliver the analytical version.

## Chat replies

Every voice rule applies to chat replies as well as to files: third person, no quotations attributed to an investor, no impersonation or script format, no offers, no implied interest, and only the four stances. Never use the word "interested" with an investor, a member or the panel as subject, even when reporting a stance.

A chat reply that gives an **investor-specific reading** starts with the simulation label. An investor-specific reading is any sentence that names an investor together with a stance, a lens or a point, including a forecast of what the simulation would produce ("each member would hold Cannot form a view", "this member's D09 point would be re-tagged base"). Telling a user that a startup falls in an investor's documented gap is such a sentence, so that reply carries the label too. Explaining or summarising an existing output in chat is allowed, in the same analytical form.

Check a chat reply with `shark-tank check <reply.md> --chat --profile <profile-dir>`, never by wrapping it as a document: the document rules demand front matter, a label and sections that the chat rule does not. Chat mode runs every offer, odds and rating-summary guard and the uncited-figure guard (in the full document form only on lines with an amount or a percentage), and the voice guards with first-person phrases limited to an investor's voice ("I'd invest", "you've got a deal"), since the reply itself speaks as the assistant; and requires the simulation label (naming each investor concerned) only when a sentence names an investor together with a stance, a lens, a dimension or a point. It cannot judge whether a reply chose suitable investors or framed a known gap correctly, so read every chat reply against this section and the reviewer checklist before sending it.

## The simulation label

Every output document uses the third person, one of the four stances, and starts with the simulation label:

```
> [!SIMULATION] Analytical simulation. Not a statement by, on behalf of, or a prediction of the decisions of <Name or names>. Based on public sources as of <date> and the startup evidence available on <date>.
```

The first date is the `last_verified` date of the named profile (the oldest one when several are named). The second is the base read's `ledger_snapshot`: the latest `updated` date in the ledger when the base read was made, which is also the date the engine writes in the rendered base read. When there is no recorded evidence (the no-profile chat path), the label ends "… as of <date> and no recorded startup evidence." in place of the second date. A base read names no investor and writes "… the decisions of any investor."

## Which command checks what

| Command | Guards |
|---|---|
| `shark-tank profiles` | P1–P11 (profiles) |
| `shark-tank base-read` | B1–B3, including the divergence-note rule (reported under B1) |
| `shark-tank check` | O1–O3, O5–O8, O10, B4–B6, T1–T4, T6–T8, N2–N4, N6, P-W (documents); I3 in debriefs |
| `shark-tank check --chat` | O1 (only for an investor-specific reading), O2, O3, O5–O8, B4, B5, P-W (chat replies) |
| `shark-tank session` | I1–I3 (interrogation sessions) |
| Reviewer | O9, B7, T5, N5, I4, P12, and the turn contract in the conversation |

Fix every error. Explain or fix every warning in your reply to the user.

**A check that cannot see its inputs fails.** For evaluations, panels, verdicts and reports, `shark-tank check` reports an error (T6) when it cannot find the base read (`base-read.yaml` beside the document, or `--base-read`) and an error (O8) when it cannot find the ledger (`--profile`, or `profile:` in the front matter). `--no-base-read` and `--no-ledger` turn these into counted warnings that name the guards not run. Use those flags only to check a fragment on purpose (a draft section, a pasted reply). A delivered document is always checked with both the base read and the ledger.

## Profile guards

Defined in full in the [profile schema](investor-profile-schema.md). In short: P1 required fields, `id` equals the file name, valid values · P2 at least two complete `https` sources · P3 every fact cites a `read-at-source`, non-`reference` source · P4 complete programme entries, `status_checked` not after `last_verified` · P5 lens rules, `decline_pattern` only with two or more reachable sources · P6 emphasis maps to a lens that lists the dimension, at most four primary · P7 confidence within the minimums, rationale of at least 15 words · P8 no forbidden keys or content (net worth, quotes, catchphrases, personality, family, contact details, quotation marks in paraphrases and lens text, "would invest in", "is interested in") · P9 no future dates; older than 18 months lowers effective confidence one level · P10 the body cites only defined `[S#]`, never `[E-…]` · P11 `simulation_only: true`.

## Output guards

| ID | Rule | Checked by |
|---|---|---|
| O1 | Front matter has `simulation: true`. The simulation label is the first content line, names every investor in `investors:`, and opens every investor section in a multi-investor document. A verdict ends with the closing line | `check` |
| O2 | No quotation marks in the same sentence (or table cell) as an investor's name; no "<Name> said / says / would say / told / thinks / believes / loves / hates" | `check` |
| O3 | No script format (`<Name>:` at line start) and no first-person investor phrases | `check` |
| O5 | Offer-shaped terms are an error outside a `[!SCENARIO]` callout: money for a share or fraction ("for", "in exchange for", "against"); taking a share of the company; an investor, a member or the panel with offer words (offer, stake, equity, valuation, royalty, deal, terms, shares, pre-money, invest … for) and an amount; shares or equity with an amount; pre- or post-money with an amount or a multiple; a price or value for the business, including a multiple of its revenue or profit ("price Acme at ten times ARR"). A clause that states the boundary ("this verdict states no amount") passes | `check` |
| O6 | A `[!SCENARIO]` callout contains "Hypothetical scenario", an Assumptions list, and no investor name | `check` |
| O7 | No probability-of-success language; no "would invest / will invest / likely to invest / is interested in / has seen" with an investor, the panel, "the sharks" or "the dragons" as subject, anywhere, including scenarios | `check` |
| O8 | Every business figure is supported. A quantity about the business (digits, number words, a percentage, a multiple, a change such as "doubled", a currency amount) needs, in the same sentence, cell or row, a ledger citation (`[E-…]` or `E-…`), a profile source `S#`, a trace-row reference such as `(A2)`, the word `gap`, or a calculation label ("calculated from", "derived from", `=`). Statements of absence ("not yet in the ledger", "untested") and conditional or planned wording (if, would, target, threshold, until) pass. An uncited business event ("<Company> signed …") is an error too. Exempt: dates, ids, counts of dimensions, members, lenses and questions, rating counts, plan windows, scenario callouts, headings, the label, R, M and Q rows, and sections on recommendations, evidence demanded, action plans, experiments, questions, sources, the divergence map, competing priorities and method. Traction, market-size and validation claims also pass the GTM claim guard; every cited `E-` ID exists. Every figure is labelled by its source in the same sentence or table row (or the table header): a figure from the founder directly is "founder-provided"; a figure from the company's own documents (deck, accounts summary, website, press release) is "company-provided" or "by the company's own account"; either may be called "reported". An estimate is called an estimate | `check` |
| P-W | Unsupported praise (outstanding, impressive, excellent, exceptional, compelling, remarkable, world-class and similar) in a sentence with no citation and no `gap` (warning; negated or conditional forms and headings are exempt) | `check` |
| O9 | Tone is analytical and fair; nothing mocks the founder or the investor; nothing implies endorsement | Reviewer |
| O10 | Every id in `investors:` exists in a library and validates; an evaluation names exactly one investor, or none with an `archetypes:` entry and a label containing "archetype, not a real investor"; a panel names three to seven | `check` |

There is no catchphrase list. O2, O3 and the profile rule against storing catchphrases cover it.

## Base read and verdict guards

| ID | Rule | Checked by |
|---|---|---|
| B1 | Required fields and values; all 15 dimensions, each with rating, confidence, explanation and the six evidence buckets; evaluator keys valid; a divergence note wherever the [crosswalk](evaluator-crosswalk.md) requires one | `base-read` |
| B2 | Every cited ID exists and sits in the bucket that matches its ledger status | `base-read` |
| B3 | Evidence ceiling: no Strong without a `verified` or interview-behavioural entry; no Adequate on assumptions only. The engine accepts Weak on any `reported` entry; whether a founder figure really goes against the founder's interest is the reviewer's test under B7 | `base-read` |
| B4 | No numeric aggregate (`x/15`, "out of 15", averages, percentages of dimensions, scores). A score named only to deny it ("there is no overall score") passes | `check` |
| B5 | Any line that counts ratings includes the Unknown count. "Insufficiently evidenced" is a warning: write Unknown | `check` |
| B6 | All five judgements present; each J2 row names a class; J3 Yes and J4 Yes never together; J5 Yes excludes J2 Yes and J3 Yes | `check` (and `base-read` when the YAML has `judgements`) |
| B7 | Explanations justify the level chosen, and anchors are applied consistently across dimensions. A Weak resting on a founder-provided figure is justified only if the figure goes against the founder's interest | Reviewer |

## Trace guards

| ID | Rule | Checked by |
|---|---|---|
| T1 | The Stance section holds exactly one stance label; every lens id in an evaluation belongs to that investor's profile (or, for an archetype, to the lenses in its header); every Lens cell is a lens id or `base`; every Dimension cell names one dimension; every A, C, Q, R and B row cites E-IDs or `gap`; B rows only from lenses with a `decline_pattern` allowed at the effective confidence | `check` |
| T2 | At medium or high confidence, at least half of the attraction and concern rows are lens-tagged. At low confidence, at most one lens-tagged attraction and one lens-tagged concern. When the header states that most of the startup falls outside the investor's documented expertise, a low lens share is a warning, not an error | `check` |
| T3 | Two evaluations with the same top three concern dimensions and the same question dimensions, from profiles with different emphasis, are flagged as possibly name-swapped unless a "Declared convergence" note exists | `check --against` |
| T4 | Near-identical row text under different lenses is flagged (warning) | `check` |
| T6 | The stance follows from the base read by the rule in [individual evaluation](individual-evaluation.md#stance): Not persuaded if a deciding dimension (critical or `primary`) is Weak at medium or high confidence; otherwise Cannot form a view if half or more of the deciding dimensions are Unknown (a low-confidence Weak counts as Unknown); otherwise Persuaded or Conditional on evidence. Each Weak or Unknown deciding dimension needs a concern row | `check`, reading `base-read.yaml` beside the document or the file given with `--base-read` |
| T7 | Every deciding dimension rated Weak or Unknown in the base read has a concern row in the point trace | `check` |
| T8 | Stances and readiness are stated only where they belong. Stance words (persuaded, convinced, impressed, won over, sceptical, leaning and similar) with an investor, a member, the lenses or the panel as subject are allowed only in the Stance, Initial positions, Final positions and Consensus sections; stance labels are always allowed. "Investment-ready", "investable" and "a good business" in prose must agree with the judgements table (or the base read's `judgements:`); a sentence that names the judgement id is exempt | `check` |
| T5 | Name-swap read: with another investor's name substituted, would every point be equally justified? If yes, the evaluation is generic | Reviewer |

## Panel guards

| ID | Rule | Checked by |
|---|---|---|
| N2 | An Initial positions section and a Discussion section exist, and Initial positions comes first. With `--against`, each initial stance equals the stance in that member's evaluation | `check` (`--against` for the match) |
| N3 | Every stance change in Final positions cites an exchange row that exists in Discussion | `check` |
| N4 | Every investor in the Initial positions table is on the panel; every exchange row names an investor on the panel, that investor's lens, and evidence or `gap`; every disagreement has a class (`different-priorities` or `evidence-gap`; the engine also accepts the retired `different-reading`, which [panel](panel.md#disagreement-classes) says not to use); Discussion has an exchange table or the convergence statement (a gap-only note contains it) | `check` |
| N6 | Each member's cell in the Divergence map names a role: deciding, considered, not covered or outside expertise (warning; the stance row is exempt) | `check` |
| N5 | Disagreement is honest and not manufactured; agreement is reported plainly when it is the result | Reviewer |

## Interrogation guards

| ID | Rule | Checked by |
|---|---|---|
| I1 | Session structure: valid mode, investors, budget and status; queue items valid; turns numbered in order; exactly one question per turn, with a new id; lens belongs to the investor; each follow-up names an earlier question; at most two follow-ups per root question; root questions within the budget; valid assessment values and decisions | `session` |
| I2 | Question text: exactly one question (one decisive unknown, see [interrogation](interrogation.md#what-one-question-means)), ending with its only `?`, never in the investor's voice or the first person. Compound forms are flagged: a second request joined by "and", "as well as", "followed by", "plus", "along with", "together with", "in addition to", "alongside", in parentheses, after "i.e.", or as a second yes/no clause (", and does that cover …?"). "And" binding a figure to its unit, date or basis, and a statement of context before a semicolon, stay allowed. Queue items and saved queue documents (`shark-tank session QUEUE.md`) are checked the same way | `session` |
| I3 | Every `new_facts` and `pending_ledger` item has `proposed_status: reported`, and its claim never calls the fact verified; `record` writes only `reported` with `source.type: founder`, and only with `--confirmed`. In a debrief, every "verified" belongs to a citation of `verified` ledger entries; a founder answer described as verified is an error ("verified evidence" as a class, and denials such as "not verified", pass) | `session`, `record`, `check` (debriefs) |
| I4 | Assessments judge the answer, never the person | Reviewer |

## Reviewer checklist

Required for every output, chat replies with an investor-specific reading included. Read it before delivering it, and tick each item. Passing the engine checks does not replace any item.

- [ ] **O9 Tone.** Analytical and fair. No mockery of the founder, the idea or the investor. Nothing reads as an endorsement by anyone.
- [ ] **B7 Ratings.** Each explanation says why this level and not the one above or below. Similar evidence gets similar ratings across dimensions.
- [ ] **T5 Name swap.** For each evaluation, substitute another investor's name. If every point would still be equally justified, rewrite from the lenses.
- [ ] **N5 Honest panel.** Every disagreement traces to a profile field and to evidence or a gap. Convergence is stated plainly. No show dynamics.
- [ ] **I4 Fair assessment.** Every assessment refers to the content of the answer. Nothing about the founder's manner, confidence or person.
- [ ] **P12 Fair profiles** (for maintainers, see [maintaining investors](maintaining-investors.md)). Each paraphrase fairly represents its source. Each lens is a reasonable interpretation, not a caricature.
- [ ] **Turn contract** (interrogation). Each message during the session ended with exactly one question and had nothing after it, including the setup and debrief messages.
- [ ] **Recording.** `record --confirmed` ran only after the founder said yes in this conversation.
- [ ] **No paraphrased offers, quotations, interest or probabilities** that the engine did not catch: read for meaning, not wording. The word "interested" never has an investor, a member or the panel as subject.
- [ ] **No real-world claims.** Nothing says or implies that an investor knows of, has seen, or would back the startup.
