# Research and validation when evidence is thin

Background: [customer discovery](../../../knowledge/gtm/customer-discovery.md), [validation experiments](../../../knowledge/frameworks/validation-experiments.md), [PMF signals](../../../knowledge/gtm/product-market-fit-signals.md).

## When there is no customer research

Say so in the executive summary and in section 3. Then deliver:

1. **Discovery plan**: 15–25 interviews per priority segment, the recruitment source for each, a script focused on past behaviour (last time, workaround, cost, who decided), and a recording template. Each interview becomes a ledger entry (`source.type: interview`, `status: reported`).
2. **Smoke tests**: a landing page per segment with one CTA (waitlist, deposit or booking), with traffic from the founder's own channels. Record the visitors, sign-ups and deposits as measured inputs.
3. **Concierge or manual pilot**: deliver the outcome by hand to 3–10 customers, and measure willingness to pay with a real payment.
4. **Decision rule** per assumption: the threshold that continues, changes or stops the plan.

## Evidence needed to validate demand (checklist)

| Assumption | Weak evidence | Strong evidence |
|---|---|---|
| The segment has the problem | Survey agreement | Observed workaround and spend; interview stories with specifics |
| They will pay | Stated price | Deposit, pre-order, completed payment |
| The channel reaches them | Follower counts | Click-through and sign-up rates measured from a test |
| They activate | Sign-ups | The activation event completed |
| They retain | Positive feedback | Cohort retention; repeat purchases |
| Supply joins (marketplace) | Expressed interest | Published listing; first sale |

## Experiment card

| Field | Example |
|---|---|
| Assumption (ledger ID) | Teachers with YouTube audiences will publish a paid course [E-0xx] |
| Hypothesis | ≥ 4 of 10 onboarded teachers publish a paid course within 14 days |
| Method | Founder-led onboarding calls; a done-for-you course setup |
| Metric | Teachers with a published paid course |
| Threshold / kill | ≥ 4 continue; ≤ 1 stop and re-interview |
| Cost and duration | Founder time; 3 weeks |
| Result | (measured: added to the ledger as `verified` from platform data) |
