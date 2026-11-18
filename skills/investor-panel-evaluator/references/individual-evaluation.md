# Individual investor evaluation

An individual evaluation reads the shared [base read](dimensions.md) through one investor's profile. It never re-rates a dimension. Each point it makes is a row that names one lens (or `base`) and the startup evidence (or the gap) behind it, so every difference between two investors can be traced to a profile field.

Write it to `outputs/<startup>/shark-tank/evaluation-<investor-id>.md` from the [template](../assets/templates/evaluation.md), then run:

```bash
"$TK/bin/startup-kit" shark-tank check outputs/<startup>/shark-tank/evaluation-<investor-id>.md \
  --profile outputs/<startup>/startup-profile
```

Add `--against <other evaluation>` for every other evaluation of the same startup, so the pairwise checks run (see [guards](guards.md)). The check reads `base-read.yaml` from the same folder to confirm that the stance follows from the base read (T6); if the base read is elsewhere, pass `--base-read <file>`.

## Selecting the investor

1. List the library: `"$TK/bin/startup-kit" shark-tank profiles` (add `--library DIR` for a private library, see [maintaining investors](maintaining-investors.md)). The table shows each profile's id, name, regions, programmes with panel status, declared and effective confidence, source count and lenses.
2. Match the user's request to an `id`. Users may name a person, give a name variant, or describe the investor by programme and a company they founded. If two profiles could match, ask which one. Never guess between namesakes.
3. Show the chosen profile's lenses and emphasis with `shark-tank profiles --id <id>` before writing.
4. If the profile fails validation, do not use it. Say why in one sentence and offer an archetype (below).
5. If the person is not in any library, say so. Offer an archetype, or offer to add a profile by following [maintaining investors](maintaining-investors.md). Never improvise a profile from memory.

The index of shipped profiles is [investors/README.md](../investors/README.md).

## Procedure

1. **Load.** Read the base read (build it first if it does not exist) and the profile. Use the profile's *effective* confidence from `shark-tank profiles`, which already includes the staleness downgrade. In the simulation label, the public-sources date is the profile's `last_verified` and the startup-evidence date is the base read's `ledger_snapshot` (see [guards](guards.md#the-simulation-label)).
2. **Generate candidate points per lens.** For each lens, for each dimension it lists, look up the base-read rating:
   - Strong or Adequate: a candidate **attraction**, applying the lens's `attracted_by` to the cited evidence.
   - Weak: a candidate **concern**, applying `concerned_by`. If the lens has a `decline_pattern` that is allowed at the profile's confidence (see the table below) *and* the Weak rating rests on `verified` or founder-against-interest evidence, the concern may also become a **potential deal-breaker**.
   - Unknown: a candidate **question** and **evidence demanded**, taken from the lens's `evidence_demanded`, filtered to what the ledger does not already hold. If the dimension is also critical for the startup or `primary` for this investor, add a **concern** as well, worded as an evidence gap ("No evidence yet that …") with `gap:` in the Evidence column. A missing answer on a dimension that matters most is a concern in its own right, not only a question.
3. **Add base points.** Every critical dimension rated Weak or Unknown that no lens covers is added as a `base` point. Any investor would see it, so it is not investor-specific.
4. **Order** the points: `primary` emphasis first, then `secondary`, then critical dimensions, then dimension number.
5. **Apply known gaps.** `known_gaps` are recorded as industries or domains (for example "consumer retail", "regulated financial services"), not as dimensions. A gap applies to a lens point when the judgement in that point depends on knowledge of the gap's domain: retail terms and sell-through for someone with no documented retail record, licensing for someone with no documented regulated-sector record. Points about general business mechanics, such as cash and runway, unit-economics arithmetic or the team's delivery record, are not affected by a domain gap. Re-tag each affected point `base` and list it under "Outside documented expertise".
   - **When most of the startup falls inside the gaps** (more than half of the lens-tagged points have been re-tagged `base` under this step), say so plainly in the header: "Most of this startup falls outside <Investor>'s documented expertise (<gap domains>); the record gives little basis for reading it." Tell the user this investor's record gives little basis for reading this startup and suggest choosing another investor whose documented expertise touches the sector. Still write the evaluation if the user wants it. `shark-tank check` then reports T2 (lens share) as a warning, not an error.
6. **Derive recommendations** from the concerns and questions. Each recommendation maps to the dimension's `upgrade_if` and to an experiment in the [experiment template](../../../knowledge/frameworks/validation-experiments.md). The same mapping gives "What would make the business more compelling under these lenses".
7. **Choose the stance** (below).
8. **Apply the confidence limits** (below), write the file, and run `shark-tank check`.

**Lenses worded around one country.** Some lenses are written around the investor's home market (for example expansion beyond one country's cities). Apply the lens's underlying subject (here, reach beyond the home market) to the startup's own geography, and say so in the row: "Applied to <startup's market>: …". Never judge a startup against the investor's home market instead of its own.

A lens may add a **lens reading**: one sentence that says why a rating matters more, or differently, under that lens, with evidence IDs. For example: "Adequate overall; under L2 the retailer margin is the binding question [E-033]." It never changes the rating.

## Confidence limits

| Effective confidence | What the evaluation may contain |
|---|---|
| `high` | Full evaluation. Potential deal-breakers where a lens has a `decline_pattern` |
| `medium` | Full evaluation. Every lens-tagged point is worded "on the documented record (S#)". No potential deal-breaker from a lens that reaches only one source |
| `low` | Restricted mode. Header notice (the check looks for the words "low confidence" near the top): "Profile confidence: low. Low confidence: investor-specific emphasis is tentative; this section mostly reflects the base read." No investor-specific deal-breakers. At most one lens-tagged row under attractions and one under concerns; all other rows are `base`. Every question (Q) and evidence-demanded (R) row is attributed to `base`, as the interrogation queue does for this investor |

The confidence minimums themselves are defined in the [profile schema](investor-profile-schema.md).

## Stance

The stance follows from the base read, not from which rows happen to be written. The **deciding dimensions** are those critical for the startup or `primary` for this investor, each counted once. A Weak rating at `low` confidence counts as Unknown for the stance, as it does for the judgements in [verdict](verdict.md).

**Concern rows are required:** every deciding dimension rated Weak (at medium or high confidence) has a concern row, and every deciding dimension rated Unknown (including a low-confidence Weak) has an evidence-gap concern row with `gap:` in the Evidence column. Leaving a row out does not change the stance; `shark-tank check` computes it from the base read (T6) and flags a missing concern row.

Choose exactly one stance. Write the display label, then two or three sentences in the third person, each tied to a row number.

| Stance (YAML value) | Display label | Choose it when |
|---|---|---|
| `not-persuaded` | Not persuaded on current evidence | At least one deciding dimension is rated Weak at medium or high confidence (its concern row is required) |
| `no-view` | Cannot form a view (insufficient evidence) | Half or more of the deciding dimensions are rated Unknown (low-confidence Weak included). The evidence cannot support a view either way, however good the rest looks. This is the usual stance for a pre-launch company |
| `persuaded` | Persuaded on current evidence | Every critical and every `primary` dimension is Adequate or Strong, and no concern rests on a Weak rating |
| `conditional` | Conditional on evidence | Any other case: most critical and `primary` dimensions are rated, none of them Weak, and one or more is still Unknown. Either write the label as is and name the evidence in the next sentence, or replace "evidence" with the evidence itself ("Conditional on three months of retailer sell-through data"). The condition is the `upgrade_if` of the deciding dimensions |

Check the rows in the order of the table and take the first that applies. Count each dimension once when it is both critical and `primary`. "Conditional on evidence" is never a residual label: if the count of Unknown dimensions reaches half, the stance is `no-view`, and the evaluation says which evidence would let a view form. The Stance section must contain exactly one stance label; do not mention a second label there, even to rule it out. Never write "in", "out", or any phrase that sounds like a decision to invest.

## Output structure

The [template](../assets/templates/evaluation.md) fixes the order:

1. Front matter (`doc_type: shark-tank`, `simulation: true`, `kind: evaluation`, `investors: [<id>]`, `profile:`).
2. The simulation label, as the first content line.
3. Header: profile confidence and its rationale, programmes and panel status, number of profile sources, lenses applied (each "an analytical interpretation of the documented record").
4. Stance.
5. Point trace: one table of every row.
6. Prose sections: What attracts (A rows), Primary concerns (C rows), Questions this lens would raise (Q rows), Evidence that would be demanded (R rows), Potential deal-breakers (B rows, or "None identified on current evidence"), Recommendations (M rows), What would make the business more compelling under these lenses, Outside documented expertise (if any).
7. Sources: the profile's sources used (`S#` with title and date) and the ledger IDs used.

### Point trace rows

| Column | Content |
|---|---|
| `#` | A1… attracts, C1… concern, Q1… question, R1… evidence demanded, B1… potential deal-breaker, M1… recommendation |
| Kind | `attracts`, `concern`, `question`, `evidence demanded`, `potential deal-breaker`, `recommendation` |
| Point | One sentence, specific to the startup |
| Lens | A lens id from this investor's profile (`L2`), or `base`. A deal-breaker also names its decline pattern and sources: `L1 (decline pattern, S2, S5)` |
| Dimension (base rating) | `D09 (Strong)` |
| Evidence | Ledger IDs with their status (`E-021 verified`, `E-033 founder-provided`), or `gap: <decisive question>` |

Write questions as questions to the founder raised through a lens: "A question raised through L3: how many retailers have placed a second order?" Never as words spoken by the investor. A Q row names **one thing the lens would need to know**, phrased as one question under the same rule as interrogation ([one question](interrogation.md#what-one-question-means)). If a lens needs two things, write two Q rows.

## Why investors differ: the trace

Two evaluations of the same startup may differ only through these profile fields:

| Field | What it changes |
|---|---|
| `evaluation_lenses` | Which dimensions get attractions, concerns and questions, and what evidence is demanded |
| `dimension_emphasis` | Ordering, and question priority in interrogation |
| `known_gaps` | Which points are re-tagged `base` |
| `decline_pattern` | Which Weak ratings may become potential deal-breakers |

The direction of a point never differs between investors: whether a dimension gives an attraction, a concern or a question follows from its shared rating. Investors differ in which dimensions they cover, which decide their stance, what evidence they demand and where their documented expertise ends. The base read is shared, so any difference that cannot be traced to one of these fields is an error. The Lens column names the field; the Evidence column names the startup evidence.

When two investors' lenses legitimately point at the same dimensions, their outputs will converge. Say so in a **declared convergence** note, for example: "Both evaluations centre on D07 because L1 (<Investor A>) and L4 (<Investor B>) both derive from documented attention to unit margins." Without this note, the pairwise check flags the pair.

## The name-swap check

`shark-tank check` runs four deterministic checks (T1–T4 in [guards](guards.md)): every lens id belongs to this investor; at medium or high confidence at least half of attraction and concern rows are lens-tagged; two evaluations with the same top concern dimensions and question dimensions, from profiles with different emphasis, are flagged unless convergence is declared; and near-identical row text under different lenses is flagged.

Then do the reviewer read (T5): read the evaluation with another investor's name in place of this one. If every point would be equally justified by the other profile, the evaluation is generic. Rewrite it from the lenses.

## What the evaluation must never do

The full list, and how each item is checked, is in [guards](guards.md). In short: no quotation marks or speech verbs with the investor as subject, no first person or script format, no imitation of catchphrases or show rituals, no offers, valuations, equity or deal terms, no statement that the investor would or would not invest, no opinions attributed to the person ("<Investor> thinks…"), no claim that the investor has seen or heard of the startup, nothing personal, and no deal-breaker without a qualifying `decline_pattern`.

The allowed form is: "Through L2 (an analytical interpretation of <Investor>'s documented emphasis on retail margins), this simulation flags …".

If the user asks for role-play, imitation, a script or "what would <Investor> say", decline that form in one sentence ("This skill does not put words in a real person's mouth; here is the analytical version.") and deliver the evaluation.

## Archetypes

An archetype is an unnamed investor type used when no valid profile exists, for example "an operator-investor focused on consumer retail". Use one when a profile fails validation, when the requested person has no profile, or when the user asks for a type rather than a person.

- Name it by type only. The header says "Archetype, not a real investor". It never carries a real person's name, programme seat or likeness.
- Write two to four lenses in the evaluation header in the lens format of the [profile schema](investor-profile-schema.md), with ids `L1`, `L2` … (the trace parser accepts only `L#` or `base` in the Lens column), each with `dimensions`, `attracted_by`, `concerned_by` and `evidence_demanded`. Each archetype lens states the investor class it comes from (`venture`, `operator-strategic`, `debt-or-revenue-based`) instead of `derived_from`.
- Archetypes have no `decline_pattern`, so they produce no potential deal-breakers. Treat them as `medium` for the lens-share rule.
- Front matter has `investors: []` and `archetypes: [<short-label>]`. The simulation label names the archetype and contains the words "archetype, not a real investor", for example: "> [!SIMULATION] Analytical simulation. Not a statement by, on behalf of, or a prediction of the decisions of any investor. The investor here is an archetype, not a real investor: <short-label>. Based on …".
- `shark-tank check` accepts this form. It checks the archetype lenses written in the header in place of a profile, so the Lens column must use only those ids or `base`.
- Archetypes are not panel members. A panel has three to seven validated profiles.

## Running it for a different startup

Nothing in an evaluation carries over to another startup. For a new startup, use its own profile directory and output folder (`outputs/<other-startup>/shark-tank/`), build its own base read, and evaluate again. The investor profiles are reused unchanged; every row, stance and question is rebuilt from the new base read.
