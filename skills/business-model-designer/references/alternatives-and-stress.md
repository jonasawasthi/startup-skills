# Alternatives and stress tests

Background: [patterns and archetypes](../../../knowledge/business-model/patterns-and-archetypes.md), [business model innovation](../../../knowledge/business-model/business-model-innovation.md), [validation and evidence](../../../knowledge/business-model/validation-and-evidence.md).

## Generating alternatives

Start from the job and the payer, not from a favourite pattern. Useful variations:

- **Who pays**: the user, the buyer, the other side of a marketplace, an advertiser, a sponsor.
- **What they pay for**: access (subscription), outcome (commission, success fee), usage, ownership (one-time), service time.
- **When**: upfront, per use, after delivery, on renewal.
- **Scope**: one product first vs an ecosystem; one segment vs several.
- **Operating model**: self-serve, managed, services-first ("make a product first, then open a marketplace").

Two to four alternatives are enough. Each needs all twelve fields: description, target customers, value proposition, revenue architecture, cost implications, operational complexity, capital requirements, distribution requirements, dependencies, risks, validation requirements and strategic trade-offs.

## Comparing without fake numbers

- Use the seven default criteria (customer fit; clarity of who pays and for what; operational complexity; capital requirements; distribution requirements; dependency risk; validation burden) or define your own under `comparison.criteria`, **each with a named scale and a definition for every level**.
- Every rating has a `why` and, where possible, evidence. A rating without valid evidence is shown as a *judgement*.
- No weights, scores, totals or rankings: the engine rejects them. The recommendation is argued in `decision_reason`, not computed.
- Exactly one `recommended` model (or none yet); others are `viable` or `reject`, each with a reason. A recommendation lists what must be tested before the founder commits; recommending a model *to test* is different from declaring it validated.

## Stress tests

### Computed thresholds (from recorded inputs only)

| Result | Formula |
|---|---|
| Contribution per transaction | price × take rate − platform-borne payment fee − delivery cost − support cost |
| Lowest viable price | (delivery + support) ÷ (take rate − platform fee rate) |
| Highest payment fee rate | take rate − (delivery + support) ÷ price |
| Highest support cost | price × take rate − payment fee − delivery cost |
| Break-even transactions per month | fixed costs ÷ contribution per transaction |
| Highest affordable CAC | contribution per transaction × purchases per customer |
| Purchases to repay CAC | CAC ÷ contribution per transaction |
| Founder capacity gap | hours required − hours available |

For a SaaS or direct model, set `take_rate` to 1 (the company keeps the price). Missing inputs are listed; an explicit 0 must carry a status and a reason.

### Scenarios

Founder-defined changes with a rationale: `{multiply: 2}`, `{add: -1}`, `{set: 299}`. Name them (base, downside, best, or by cause, e.g. "VAT on the whole price"). They are what-ifs: no probabilities, no "likely", no forecasts. A scenario cannot change an input that has no base value.

### The thirteen stress cards

Weak willingness to pay · high acquisition costs · low retention · insufficient transaction volume · high payment processing costs · low marketplace liquidity · high seller churn · high support costs · poor margins · partner dependency · regulatory constraints · international payment limitations · founder capacity limitations.

Each card shows its computed threshold (or "qualitative" with the missing inputs), the linked assumptions, unverified dependencies, and the founder's mitigation (`stress.mitigations.<card>`).
