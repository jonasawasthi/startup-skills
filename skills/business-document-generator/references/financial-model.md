# Financial model YAML

The model is driver-based. Every input becomes a blue row on the *Assumptions* sheet, with its status and evidence. The *Monthly*, *Annual* and *Unit economics* sheets contain only formulas. `startup-kit model` also writes `<file>-summary.json` (annual figures and the first month cash goes negative) for use in decks and proposals.

```yaml
model:
  company: Acme
  currency: USD
  start: 2027-01          # first month
  months: 36
  scenario: base          # build conservative/base/ambitious as separate files
  starting_cash: {value: 40000, status: reported}
funding:
  - {label: Seed (amount TBD), month: 3, amount: null}    # null = founder hasn't decided; modelled as 0 and flagged
revenue_streams:
  - name: Subscriptions
    type: subscription
    start_month: {value: 1}
    new_customers_month1: {value: 3, status: assumption}
    new_customers_growth: {value: 0.06, status: assumption}   # monthly growth of new adds
    churn: {value: 0.02, evidence: E-009}
    price: {value: 60, status: assumption}                     # per customer per month
    cogs_pct: {value: 0.15, status: estimate}
  - name: Transaction fees
    type: transaction
    start_month: {value: 13}
    gmv_month1: {value: 50000, status: assumption}
    gmv_growth: {value: 0.05}
    take_rate: {value: 0.004}
    cogs_pct: {value: 0.3}
headcount:
  - {role: Engineer, start_month: {value: 4}, count: {value: 1}, monthly_cost: {value: 2500, status: assumption}}
opex:
  - {name: Cloud and tools, monthly: {value: 600}, growth: {value: 0.03}}
unit_economics:
  cac: {value: 250, status: assumption}
```

Every value can be a plain number or `{value, status | evidence, note}`. Values without evidence default to `assumption`.

**Validation**: the test suite recalculates the workbook with the `formulas` package and compares the results with the Python mirror (`simulate`). Keep scenarios honest: the model is a tool for reasoning about assumptions, not a forecast.
