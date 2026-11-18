# Business model spec format

One YAML file per startup, normally `outputs/<startup>/business-model/<startup>-business-model.yaml`. Paths are relative to the spec. A complete template is in [../assets/templates/business-model-spec.yaml](../assets/templates/business-model-spec.yaml); a worked fictional example is in [examples/fieldnote/business-model/](../../../examples/fieldnote/business-model/fieldnote-business-model.yaml).

**Quote any text that contains a comma, a colon or an `[E-001]` citation inside `{flow: mappings}` and `[flow, lists]`.** An unquoted comma silently splits the text into a stray key; the engine reports every key without a value.

## Sections

| Section | Required | Purpose |
|---|---|---|
| `design` | yes | Header: `company`, `profile` (or `evidence`), `discovery` (path to the discovery spec), `stage`, `date`, `currency`, `geography`, `types`, `recommended`, `claimed_maturity` (optional), `illustrative` (disclaimer), `summary`, `decision`, `next_steps`, `confidentiality` |
| `segments` | no | Only when no discovery spec is linked; same shape as discovery segments (`id`, `name`, `side`, `market`, `roles`) |
| `canvas` | yes | The nine blocks (below) |
| `value_propositions` | recommended | One canvas per segment |
| `revenue_streams` | yes | Streams on the stage ladder |
| `costs` | yes | Cost lines |
| `marketplace` | for marketplaces | Sides, flow, payments, funnel, liquidity |
| `financials` | optional | `inputs` for the financial definitions; `principal: true` only when an accountant confirmed gross recognition |
| `dependencies` | yes when money moves | Payment, payout, banking, tax, legal, regulatory, partner, technology |
| `assumptions` | yes | The register |
| `alternatives` and `comparison` | recommended | Models compared on defined scales |
| `stress` | recommended | Inputs, scenarios, mitigations |

## Canvas

```yaml
canvas:
  customer_segments:            # also: value_propositions, channels, customer_relationships, revenue_streams,
    rationale: Why these segments   #   key_resources, key_activities, key_partnerships, cost_structure
    items:
      - {text: "...", basis: evidence, evidence: [E-010, E-011], contradicting: [E-012]}
      - {text: "...", basis: hypothesis, hypothesis: H3}
      - {text: "...", basis: recommendation, rationale: "..."}
      - {text: "...", basis: unknown}
```

`basis`: `evidence` | `founder` | `hypothesis` | `recommendation` | `unknown`. Rules: `evidence` cites verified/reported, non-founder entries; customer-facing blocks need customer evidence; quotations need an interview entry. An alternative may carry its own `canvas` (`business-model canvas <spec> --model M2`).

## Value propositions

```yaml
value_propositions:
  - segment: S1
    customer_profile:
      jobs:  [{id: J1, text: "...", basis: hypothesis}]
      pains: [{id: P1, text: "...", basis: evidence, evidence: [E-010]}]
      gains: [{id: G1, text: "...", basis: hypothesis}]
    value_map:
      products:       [{text: "...", basis: evidence, evidence: [E-002]}]    # a product's existence may cite code
      pain_relievers: [{id: R1, text: "...", basis: hypothesis, addresses: [P1]}]
      gain_creators:  [{id: C1, text: "...", basis: hypothesis, addresses: [G1]}]
```

## Revenue streams

```yaml
revenue_streams:
  - id: R1
    name: Course sales commission
    payer: D1                     # a segment id
    value: What the payer receives
    mechanism: commission         # one-time | subscription | transaction-fee | commission | usage | licensing |
                                  # service-fee | advertising | bundle | tiered | hybrid
    billing: one-time per purchase
    structure: Who pays whom, when, and what is held back
    recognition: Gross or net; to confirm with an accountant
    price: {value: 999, currency: NPR, evidence: [E-025]}     # or status: assumption
    take_rate: {value: 0.3, evidence: [E-006]}                # commission and transaction-fee streams
    stage: proposed               # proposed | tested | available | generating | repeatable
    evidence: [E-006]
    repeat_evidence: []           # for 'repeatable': dataset or paid signal
    revenue: {value: 120000, evidence: [E-050]}               # only from 'generating' upwards, measured
    dependencies: [D1, D2]
    risks: "..."
```

## Costs

```yaml
costs:
  - {id: C1, name: Hosting, category: fixed, type: infrastructure, amount: {value: 6300, unit: NPR per month, evidence: [E-021]}}
  - {id: C2, name: Gateway fee, category: variable, type: payment-processing, driver: each payment, amount: {value: 0.03, unit: share of payment, status: assumption}}
  - {id: C3, name: Support, category: semi-variable, type: support, driver: per sale}          # unknown: no amount
```

`category`: fixed | variable | semi-variable. `type`: delivery, infrastructure, payment-processing, acquisition, support, operations, personnel, compliance, administrative, partner, incentives, other. An `estimate` needs `basis` (source or calculation) or evidence.

## Marketplace

```yaml
marketplace:
  type: education                 # two-sided | three-sided | service | digital-product | education | managed | hybrid-saas
  applies_to: M3                  # optional: when the marketplace is an alternative, not the recommended model
  sides:
    - {segment: S1, role: supply, acquisition: "...", value: "...", pays: "...", subsidy: "..."}
    - {segment: D1, role: demand, acquisition: "...", value: "...", pays: "...", brings_other_side: false}
  matching / trust_safety / transaction_flow / leakage / network_effects / pricing: text
  cold_start: {first_side: S1, plan: "..."}
  take_rate: {value: 0.3, evidence: [E-006]}
  payments: {collection: {text: "...", dependency: D1}, payout: {text: "...", dependency: D2}, refunds: "...", disputes: "...", fee_bearer: platform}
  funnel:                         # measured counts only, each {value, evidence|status}
    registered_supply: {value: 120, evidence: [E-060]}
    active_supply: ...
    available_supply, registered_demand, active_demand, demand_requests, matches, completed_transactions,
    repeat_transactions, gmv, platform_revenue, listings_live, listings_with_sale
  liquidity: {status: not-measured, evidence: []}   # not-measured | not-yet | emerging | achieved
```

## Dependencies

```yaml
dependencies:
  - id: D1
    name: Learner payment collection by QR
    type: payment                 # payment | payout | banking | regulatory | tax | legal | partner | technology | other
    provider: Fonepay
    country: Nepal
    status: in-progress           # verified | in-progress | unverified | assumed | blocked
    evidence: [E-009]
    question: What must be confirmed?
    confirm_with: [payment-provider, bank]   # legal, tax, payment-provider, bank, regulator, accountant, partner
    confirmed_by: ""              # required for a verified regulatory, tax or legal item
```

## Assumptions

```yaml
assumptions:
  - id: A1
    description: Learners pay NPR 999 by QR
    category: wtp                 # wtp, pricing, revenue, acquisition, retention, costs, margins, volume, liquidity,
                                  # partnerships, payments, operations, regulatory
    why: Every stream depends on it
    impact: high                  # impact if false: high | medium | low
    evidence: [E-025]
    contradicting: []
    conflict_note: ""
    validation: Soft-launch purchases
    status: untested              # untested | testing | supported | contradicted | inconclusive
    hypothesis: H6                # discovery register id
    owner: founder                # used by --record
```

## Alternatives and comparison

```yaml
comparison:                       # optional: custom criteria; otherwise seven defaults with one four-level scale
  criteria:
    - {key: customer_fit, label: Customer fit, scale: {strong: "...", partial: "...", weak: "...", unknown: "..."}}
alternatives:
  - id: M1
    name: "..."
    types: [marketplace, commission, education, b2c]
    fit: Why these types fit
    description / target_customers / value_proposition / revenue / costs / complexity / capital /
    distribution / dependencies / risks / tradeoffs: text
    validation: [What must be tested before committing]
    ratings:
      customer_fit: {level: unknown, why: "...", evidence: [E-017]}
    decision: recommended         # recommended | viable | reject | undecided
    decision_reason: "..."
```

Fields named `score`, `rank`, `total`, `weight` or `points` are rejected anywhere in alternatives or comparison.

## Stress

```yaml
stress:
  inputs:                         # each {value, evidence|status}; fee_bearer is platform | seller
    price, take_rate, payment_fee_rate, fee_bearer, delivery_cost, support_cost, transactions_per_month,
    fixed_costs_month, cac, new_customers_month, purchases_per_customer, founder_hours_per_week,
    hours_required_per_week
  scenarios:
    - {name: downside, changes: {support_cost: {multiply: 2}}, rationale: "..."}   # multiply | add | set
  mitigations: {wtp: "...", volume: "..."}   # keys are the stress card ids
```

Keys named `probability`, `likelihood`, `chance` or `odds` are rejected.
