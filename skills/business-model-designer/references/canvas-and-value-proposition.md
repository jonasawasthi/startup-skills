# Canvas and value proposition: how to fill them honestly

Background: [Business Model Canvas](../../../knowledge/business-model/business-model-canvas.md) and [Value Proposition Canvas](../../../knowledge/business-model/value-proposition-canvas.md).

## The nine blocks, and the question each answers

| Block | Question | Typical evidence |
|---|---|---|
| Customer Segments | Who receives value? Who pays? (Name user, buyer and decision-maker separately; for marketplaces, each side) | Interviews, usage data |
| Value Propositions | What job gets done, which pain is relieved, for each segment? | Interviews, behaviour, retention |
| Channels | How does each segment find, buy and receive the offer? | Measured acquisition by channel |
| Customer Relationships | How are customers acquired, kept and grown (self-serve, done-with-you, community)? | Retention and support data |
| Revenue Streams | Who pays, for what, by which mechanism? | Payments, contracts (signal: committed or paid) |
| Key Resources | What assets make delivery possible? | Codebase, contracts, licences |
| Key Activities | What must the company do well? | Operating records |
| Key Partnerships | Whom does it depend on (providers, banks, distributors)? | Signed agreements |
| Cost Structure | What does it cost to deliver, and what drives each cost? | Invoices, quotes, provider price pages |

The right-hand blocks (segments, value, channels, relationships, revenue) are **customer-facing**: evidence there must come from customers. The left-hand blocks are **internal**: a codebase, a contract or an invoice is good evidence there, a founder's statement is still `founder`.

## Labelling each item

| Basis | Use when | Never |
|---|---|---|
| `evidence` | A verified or reported ledger entry from a source other than the founder supports it (customer evidence on customer-facing blocks) | For desk research about a market, a founder's belief, a waitlist, or an `assumption` entry |
| `founder` | The founder says so and it is plausible, e.g. "we onboard teachers ourselves" | To dress up a guess as a fact |
| `hypothesis` | It needs testing; link the discovery hypothesis (`hypothesis: H3`) | Without a validation route |
| `recommendation` | It is your advice; give the rationale | As a description of what exists |
| `unknown` | Nobody knows yet | Leave a block empty instead |

## Value Proposition Canvas

- One canvas **per segment**. In a marketplace, supply and demand each get their own; they rarely share pains.
- Jobs, pains and gains come from interviews or observed behaviour. Without them they are hypotheses, ideally linked to the discovery register; never write them as findings.
- A product's *existence* may cite the codebase. A pain reliever's *effect* is customer-facing.
- Give pains and gains ids and make every pain reliever say which pain it `addresses`. Unaddressed pains are shown; that is a design gap, not a failure.

### Fit ladder (computed)

1. *Conceptual fit only*: no customer evidence for jobs, pains or gains.
2. *Customer evidence exists, but no evidence-backed pain is addressed.*
3. *Problem side evidenced*: addressed pains are backed by customer evidence; the value map is untested.
4. *Early evidence of fit*: value-map items are also backed by customer evidence (usage, commitment, payment).

Even step 4 is early: fit is confirmed by behaviour over time, not by a canvas.

## Common mistakes the engine catches

- An `evidence` item that cites an `assumption`, `estimate` or `unverified` ledger entry.
- An `evidence` item that rests only on founder statements.
- A quotation in an item without an interview entry behind it.
- A missing block (record `unknown` instead).
- Contradicting evidence: it is shown next to the item in every output, never dropped.
