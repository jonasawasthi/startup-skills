# Multi-investor panel

A panel is three to seven investors who each evaluate the startup independently, after which a neutral moderator compares their evaluations, discusses only where they genuinely diverge, and reports the result. The panel adds no new ratings: it is built on the shared [base read](dimensions.md) and the [individual evaluations](individual-evaluation.md).

Write the report to `outputs/<startup>/shark-tank/panel-<YYYY-MM-DD>.md` from the [template](../assets/templates/panel-report.md), then check it together with every member's evaluation:

```bash
"$TK/bin/startup-kit" shark-tank check outputs/<startup>/shark-tank/panel-<date>.md \
  --profile outputs/<startup>/startup-profile \
  --against outputs/<startup>/shark-tank/evaluation-<id-1>.md --against outputs/<startup>/shark-tank/evaluation-<id-2>.md …
```

## Choosing the panel

| The user asks for | Do this |
|---|---|
| Named people | Use those profiles. Resolve each id as in [individual evaluation](individual-evaluation.md#selecting-the-investor); ask only if a name is ambiguous |
| A programme, or "the current panel" of a programme | Naming the programme names the roster: list the members used and proceed without asking for confirmation. Take the profiles whose entry for that programme has `panel_status: current`. If the programme's latest panel is recorded as `unconfirmed` (the next line-up is not announced), use the members of the latest aired season and label them unconfirmed. If the programme is `dormant`, use its last panel and label it dormant. More than seven: ask which seven or fewer (one question). Fewer than three: say so and offer to add members from the same programme's former panel |
| A region in general | List the matching profiles with their status and confidence, and ask the user to choose three to seven |
| A mix of perspectives | Propose three to five profiles whose `primary` emphasis differs, and say which dimensions each brings |
| An investor type | A panel is made of profiles only. Offer individual archetype evaluations ([individual evaluation](individual-evaluation.md#archetypes)) instead |

Rules for the roster:

- Three to seven members. `shark-tank check` rejects other sizes (O10).
- Show each member's programme, panel status with its `status_checked` date ("current as of <date>"), and effective confidence in the roster. Do the same whenever a programme's panel is listed. A status checked more than six months ago is flagged for re-verification (`shark-tank profiles` warns), and the roster says so. Members whose status is `former`, `unconfirmed` or `dormant` are allowed, and the roster says so.
- Profiles that fail validation are not used, and archetypes are not panel members. If fewer than three valid profiles remain, say so and offer individual evaluations instead.
- Investors from different programmes can sit on one panel. The startup's own market still sets the regulators and sources ([business types and stages](business-types-and-stages.md#country-and-programme-context)).

## Stages

| Stage | What happens | Rule |
|---|---|---|
| 0. Setup | Fix the roster; validate every profile; one base read for all | Roster table with programme, status and confidence |
| 1. Independent evaluations | Evaluate each member with the [individual procedure](individual-evaluation.md), using only the base read and that member's own profile | Write each to its own `evaluation-<id>.md` before stage 2. No member's output is input to another's |
| 2. Initial positions | Copy each stance and its top attraction and top concern (C1, which may be an evidence-gap concern) into the Initial positions table | This table is never edited afterwards. The check compares it with the stage-1 files |
| 3. Divergence map | For each dimension, record each member's role for it (deciding, considered, not covered, outside expertise) and the evidence that member demands. Mark it *convergent* or *divergent* (see [where members can differ](#where-members-can-differ)) | Never record one member as attracted and another as concerned by the same dimension: the rating is shared, so that cannot happen |
| 4. Discussion | Discuss only dimensions that are divergent because of stances or deciding sets: one exchange per divergence, more only if a new evidence ID enters. Gap-only divergences get a note, not an exchange | Each exchange: the first member's lens and evidence (`a` row) → the second member's lens and evidence (`b` row) → resolution |
| 5. Competing priorities | Table of what each member's `primary` lenses put first (for example margin before growth, or growth before margin) | Derived from `dimension_emphasis`, never invented |
| 6. Disagreements explained | Classify every remaining disagreement and say what would resolve it | No unclassified disagreement |
| 7. Final positions | A stance may change only if an exchange row is cited as the cause | "Changed from Conditional to Not persuaded because X2", or "Unchanged" |
| 8. Consensus | Unanimous, majority, split or no consensus, for the stance and for each critical dimension | State counts of members ("4 of 5 members"). No mood words. When most members cannot form a view, say so plainly (below) |
| 9. Consolidated assessment | Hand over to the [verdict](verdict.md) | The verdict is either the last section of the report or `verdict.md` |

## Where members can differ

The business is rated once. Whether a point is an attraction, a concern or a question follows from the shared rating, so every member who covers a dimension treats it in the same direction: a Weak dimension is a concern for all of them, a Strong one an attraction for all of them. Members can differ in only four ways, each traceable to a profile field:

| Difference | Profile field | Example |
|---|---|---|
| **Stance** | All of the below, through the stance rule | One member is Not persuaded, another Cannot form a view |
| **Deciding set**: which dimensions decide the member's stance (critical for the startup, plus the member's `primary` emphasis) | `dimension_emphasis` | D09 is `primary` for one member, so a Weak D09 decides that member's stance; for another it is a secondary concern that does not |
| **Evidence demanded** on the same dimension | `evaluation_lenses[].evidence_demanded` | On an Unknown D07, one lens demands landed cost per unit, another demands repeat-order margin |
| **Documented gap**: the dimension's judgement falls in one member's `known_gaps` | `known_gaps` | A retail-terms point is outside one member's documented record, so that member's point is `base` and listed under Outside documented expertise |

The divergence map is a dimension × member matrix. Each cell gives the member's role for that dimension (`deciding`, `considered`, `not covered` or `outside expertise`) and, where the dimension is Unknown or Weak, the evidence that member's lens demands. Add one row for the stances themselves.

A dimension is **divergent** only when one of these holds:

1. it leads members to different stances (it is Weak or Unknown and decides one member's stance differently from another's);
2. it is in one member's deciding set and not another's, in a way that changes a stance;
3. it falls in one member's documented gap.

Otherwise it is **convergent**. **Different evidence demanded does not by itself make a dimension divergent.** When it changes no stance, record it in the map's evidence column and under Competing priorities, and do not discuss it. A pre-launch panel whose members all cannot form a view, each demanding different evidence on the same Unknown dimensions, is therefore convergent.

Only cases 1 and 2 are discussed in exchanges. When the only differences are gap re-tags (case 3), write a note in the Discussion section instead of an exchange, for example: "No exchanges: the panel converges on all critical dimensions. D09 is outside <Investor C>'s documented expertise (consumer retail), so that member's D09 point is base; this changes no stance." If no dimension is divergent at all, write the convergence statement.

## Rules against manufactured disagreement

- **No quota.** Zero exchanges is a valid result. If the divergence map is all convergent, replace the discussion with: "The panel converges on all critical dimensions; the evidence leaves no basis for disagreement." Then move on.
- **Traceable twice.** A disagreement must trace to a difference between two members' lenses or emphasis *and* to base-read evidence (or a gap) that both sides cite. If you cannot name the profile field responsible, remove the disagreement.
- **Evidence beats emphasis.** A dimension rated Weak on verified evidence cannot be the subject of disagreement about the facts. Members may differ only on how much it matters.
- **No show dynamics.** No bidding, alliances, rivalries, interruptions, personal clashes or members competing for the deal.
- **Low-confidence members** cannot be the only member on one side of a disagreement. If they are, drop that disagreement and say so in the Discussion note. The same applies to a member whose point on the dimension is outside documented expertise. Outside-expertise differences are always recorded in that one place, the Discussion section, never under Disagreements explained.
- **Changes need a cause.** A stance never changes "for consensus". A disagreement that persists is a legitimate result.

### When most members cannot form a view

For a pre-launch company, or any startup whose critical dimensions are mostly Unknown, most or all members will hold "Cannot form a view (insufficient evidence)". That is a legitimate and common result, not a failed panel. Do not upgrade anyone to "Conditional on evidence" to make the panel look decisive. Write the consensus as, for example: "4 of 5 members cannot form a view on current evidence; the gaps they share are D03 and D07." Two members who both cannot form a view, for different gaps, are not in disagreement; list their gaps side by side under Competing priorities. The useful output is then the shared evidence gaps, the founder questions and the experiments that would let a view form.

## Disagreement classes

Two classes remain. The earlier `different-reading` class (different evidence demanded) cannot occur: stances follow from the shared ratings, so different evidence demanded never changes a stance by itself; it belongs under Competing priorities. The engine still accepts the value, but do not use it.

| Class (value) | Meaning | How it resolves |
|---|---|---|
| `different-priorities` | Same rating, different deciding sets: the dimension decides one member's stance (it is `primary` for that member) and not another's, so their stances differ | It does not resolve with evidence. Explain it as a fit question for the founder: which kind of investor's priorities match the business |
| `evidence-gap` | The stances differ because a deciding dimension is Unknown: it pushes one member to Cannot form a view while another, for whom it is not deciding, holds a view | Becomes a founder question and a validation experiment for that dimension |

## The moderator

The moderator is the skill's own neutral voice. It is never one of the members and never a real person.

The moderator:
- builds the divergence map and chooses which divergences to discuss;
- makes sure every exchange row names a member, a lens and evidence or a gap;
- removes points that cannot be traced;
- refuses stance changes without a cause row;
- puts the simulation label at the top of the report and at the top of each member's section;
- writes the consensus statement and the disagreement explanations.

The moderator adds no business opinion beyond the base read and does not break ties.

## Exchange rows

Each exchange takes two rows in the Discussion table: `X1a` for the challenge and `X1b` for the response. The table header is fixed so that `shark-tank check` can read it:

| Column | Content |
|---|---|
| `#` | `X1a` (challenge), `X1b` (response), `X2a` … |
| Dimension | One dimension, `D07` |
| Investor | The member's profile id or exact profile name |
| Lens | A lens id from that member's profile (`L2`), or `base` when the member's stance turns on a dimension none of their lenses covers |
| Evidence or gap | Ledger IDs (`E-018`), or the word `gap` with the decisive question |
| Point | One sentence in the third person |
| Resolution | On the `b` row: `resolved` (name the evidence that settles it), `persists`, or `becomes founder question` |

Write every Point in the third person: "Through L2, D09 decides this member's stance: the reported single-retailer listing [E-018] leaves the route dependent on one gatekeeper." and, for the `b` row, "Through L1, D09 is a secondary point for this member; the stance rests on D07, which is Adequate [E-031]." Never as dialogue. Classify each exchange that ends `persists` or `becomes founder question` under Disagreements explained, in a table with a `Class` column (`different-priorities` or `evidence-gap`).

Final positions use the columns `Investor | Initial stance | Final stance | Cause`. When the stances differ, Cause cites an exchange row (`X2b`); otherwise write "Unchanged".

## Report structure

The [template](../assets/templates/panel-report.md) has these sections in this order. The Initial positions section must come before Discussion.

1. Panel and method: roster, programmes, profile confidence, base-read date, evidence profile line
2. Base read summary: the critical-dimension table
3. Initial positions: the locked table (`Investor | Stance | Top attraction | Top concern | Lenses`)
4. Divergence map: a dimension × member matrix of roles and evidence demanded, convergent or divergent
5. Discussion: exchange rows, or the convergence statement
6. Competing priorities
7. Disagreements explained: class, the profile field that causes it, what would resolve it
8. Final positions, with cause rows for changes
9. Consensus: level, counts, plain wording
10. Member summaries: one short section per member, each opening with a simulation label naming that member
11. Consolidated assessment, leading to the verdict
12. Sources: profile sources by member, ledger IDs used

Each member's evaluation stays in its own file. The panel report links to them and does not repeat their full point traces. If the report has a section per member (for example "Member summaries"), each such heading begins with the member's profile name and its first line is a simulation label naming that member. Do not begin any other heading with an investor's name.

## Illustrations (fictional)

A hardware startup's verified supplier quote and stated retail price give a negative contribution after the retailer's margin, so D07 is Weak on verified evidence. Four members with different lenses all list D07 as a concern, and D07 is critical, so it decides every member's stance. The divergence map shows D07 convergent, the discussion section carries the convergence statement, no exchange rows are written, the consensus is "unanimous (4 of 4): Not persuaded on current evidence", and the verdict answers J5 `yes` for the current price and channel, naming the change that would re-open the case.

A pre-launch software startup has problem interviews (D01 Adequate) and nothing else on its critical dimensions: D03, D07 and D14 are Unknown. Each of three members records gap concerns on those dimensions, and each holds "Cannot form a view (insufficient evidence)". Their lenses demand different evidence on D03 (one asks for paid pilots, another for repeat orders), but that changes no stance, so the divergence map is convergent: the differences go under Competing priorities and no exchange is written. The consensus reads "3 of 3 members cannot form a view on current evidence; the shared gaps are D03, D07 and D14", and the verdict gives J1 Not yet determinable and J4 Yes, with a pre-sale experiment first in the action plan.
