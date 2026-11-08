# GTM spec format

`startup-kit gtm analyze <spec.yaml>` reads this file, and `startup-kit gtm kpi <spec.yaml>` builds the KPI workbook from it. Paths are relative to the spec. Every `evidence:` ID must exist in the ledger, or the build fails.

```yaml
gtm:
  company: Acme
  profile: ../startup-profile        # ledger + profile.yaml (or evidence: path/to/evidence.yaml)
  stage: pre-seed                    # defaults to profile.yaml stage
  currency: USD

business_model:
  type: creator-platform             # b2b-saas | enterprise | consumer-app | marketplace | creator-platform |
                                     # education | devtool | services | ecommerce
  secondary_types: [education]       # hybrids: guards and KPIs of every type apply
  self_serve: true                   # can users start without talking to anyone?

team:
  people: 1
  hours_per_week: 25                 # per person, available for GTM (not product work)
  roles: [founder]                   # task owners outside this list are flagged as dependencies

budget:
  available: 300000                  # GTM cash for the roadmap horizon (founder-set; never invent)

products:                            # status vocabulary: live | built | in-development | planned | proposed | unknown
  - {name: Workshops, status: built, evidence: [E-011]}

segments:                            # informational; the strategy document carries the detail
  - {name: ..., role: supply | demand | customer, users: ..., buyer: ..., influencers: [...], beneficiary: ..., evidence: [...]}

max_primary_channels: 3              # default 3; >4 triggers a warning
channel_weights: {customer_fit: 0.25, economics: 0.2, speed: 0.15, resources: 0.15, scalability: 0.1}  # optional

channels:                            # candidates, including ones you expect to reject
  - key: founder-led-sales           # catalogue keys: founder-led-sales outbound content seo social community
                                     # referral partnerships influencer email paid-ads affiliate product-led
                                     # developer-led pr events
    side: supply | demand | both
    scores: {customer_fit: 1-5, economics: 1-5, speed: 1-5, resources: 1-5, scalability: 1-5}
    why: "Why this fits the target customer"     # required: scores without a rationale are errors
    evidence: [E-...]                # the evidence score (1–5) is computed from these, never declared
    decision: primary | test-later | not-now     # optional founder override (shown as an override)
    reason: "Why not now"            # for rejected channels
    # required for primary channels:
    execution: [...]
    resources: ...
    cost: ...
    leading_indicators: [...]
    success_metrics: [...]
    risks: [...]
    experiment: {hypothesis: ..., metric: ..., threshold: ..., budget: ..., duration: ..., kill: ...}

pricing:
  model: commission                  # freemium | subscription | one-time | commission | transaction | usage |
                                     # tiered | enterprise | hybrid
  value_metric: "per workshop ticket sold"
  take_rate: {value: 0.30, evidence: [E-006]}   # required for commission/transaction models
  price_points:
    - {name: Typical workshop, price: 25, currency: USD, basis: researched | hypothesis, evidence: [...]}
  competitors:
    - {name: ..., price: ..., evidence: [E-...]}   # unsourced competitor prices are errors
  experiments:
    - {name: ..., tests: [Typical workshop], hypothesis: ..., metric: ..., threshold: ..., duration: ..., kill: ...}

marketplace:                         # required for marketplace and creator-platform models
  sides:
    - {name: Hosts, role: supply, difficulty: 1-5, brings_other_side: true, standalone_value: true,
       why: "...", evidence: [...]}
    - {name: Attendees, role: demand, difficulty: 1-5, brings_other_side: false, standalone_value: false, why: "..."}
  launch: {geographies: [one country], categories: [one category], justification: ""}
  atomic_network: "One host, their existing community, one paid workshop"
  liquidity_target: "≥ 60% of published listings sell once within 30 days (target)"
  trust_safety: [...]
  disintermediation_defence: [...]

metrics:
  currency: USD
  owner: founder
  kpis: [activation_rate, liquidity]     # extra KPIs beyond the model defaults
  inputs:                                # measured values only; null = not measured
    visitors: {value: null}
    signups: {value: 120, evidence: [E-040]}
    churn: {value: 0.04, status: assumption}
  targets: {activation_rate: "≥ 40% (target)"}

cohorts:                                 # optional measured cohorts
  - {name: 2026-09, size: 40, active: [40, 22, 18], evidence: [E-041]}

roadmap:
  phases:                                # consecutive; standard ends: day 30, 60, 90, 180, 365
    - name: First 30 days
      days: 30
      objectives: [...]
      tasks:
        - {id: t1, task: ..., owner: founder, effort_days: 5, cost: 0, depends_on: [], deliverable: ...}
      kpis: [...]
      success_criteria: [...]
      budget: 0                          # extra phase spend beyond task costs

cross_product:
  - {product: Call, opportunity: "...", phase: Months 4–6}   # status is taken from products:
```

## Metric input names

`visitors`, `signups`, `activated`, `new_customers`, `customers`, `active_customers`, `customers_start`, `customers_lost`, `repeat_customers`, `referred_signups`, `revenue`, `net_revenue`, `gmv`, `orders`, `acquisition_spend`, `gross_margin`, `contribution_margin`, `purchases_per_customer`, `churn`, `arpu`, `aov`, `listings_live`, `listings_with_sale`, `active_suppliers`, `suppliers_with_sale`, `enrolments`, `completions`. Use one period (for example, the last 30 days) for all of them.

## What the engine checks

| Area | Errors | Warnings / info |
|---|---|---|
| Evidence | Unknown evidence IDs anywhere in the spec | No profile or ledger configured |
| Channels | Missing or out-of-range scores; scores without `why`; primary channels without all playbook fields or experiment fields | Declared evidence scores (ignored); >4 primary; no primary channel |
| Model guards | Missing `business_model.type` | Outbound to consumers, paid ads or affiliates before retention evidence, referral without a base, PLG without self-serve, slow channels at an early stage, enterprise/devtool mismatches, paid demand before marketplace liquidity |
| Metrics | Non-numeric inputs | Unknown KPI names |
| Pricing | No model; "researched" price without verified/reported evidence; unsourced competitor price; commission without a valid take rate | No value metric; a hypothesis without an experiment |
| Marketplace | Section missing for a marketplace model; side difficulty outside 1–5 | Tie in side priority; more than one geography or category without justification; no atomic network, liquidity target or trust and safety; take rate without a disintermediation defence |
| Roadmap | Effort above capacity; spend above budget; unknown dependencies; no `team.people` | Load above 85%; missing objectives, KPIs or owners; owners outside `team.roles`; non-standard horizons |
| Cross-product | Planned, proposed or unknown products in the first 90 days; status conflicts | In-development products in the first 90 days; built-not-live products (beta only) |

Capacity = people × hours_per_week ÷ 8 × days ÷ 7 person-days. Channel total = Σ(weight × score) ÷ Σ(weights), with evidence weighted 0.15. Side priority = difficulty + 2 (brings the other side) + 1 (standalone value).
