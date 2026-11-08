# Revenue, costs and financial architecture

This skill defines the financial *architecture* and its assumptions. Detailed forecasting belongs to the financial model (`startup-kit model`); this skill never projects revenue.

## Revenue stream stages

| Stage | Meaning | Evidence the engine requires |
|---|---|---|
| proposed | Designed, not offered | None; the price is a hypothesis |
| tested | Offer or price shown to real customers | Customer evidence (interview, dataset or a signal) |
| available | Customers can actually pay today | Every linked dependency `verified`, plus verified or reported non-founder evidence of a live checkout |
| generating | Payments received | `signal: paid` evidence, or measured `revenue` (verified or reported) |
| repeatable | Repeat or retained payments measured | `repeat_evidence`: a dataset or paid signal |

A stream below *generating* cannot carry `revenue`. A stated price is never revenue; a waitlist is never a test of price.

## Mechanisms

one-time · subscription · transaction-fee · commission · usage · licensing · service-fee · advertising · bundle · tiered · hybrid. Commission and transaction-fee streams need a `take_rate` (0–1) or a fee.

## Revenue recognition

Record the assumption in words and confirm it with an accountant. When a marketplace is the **seller of record** (principal), it may recognise the gross price as revenue and owe the seller's share as a cost; as an **agent** it recognises only its commission. Either way, GMV is not the platform's share and not its profit. The engine warns on gross recognition in commission streams.

## Cost lines

| Field | Values |
|---|---|
| category | fixed · variable · semi-variable |
| type | delivery · infrastructure · payment-processing · acquisition · support · operations · personnel · compliance · administrative · partner · incentives · other |
| driver | What makes a variable cost grow (per sale, per payout, per teacher) |
| amount | `{value, unit, evidence | status, basis}`; omit when unknown |

Rules: a number needs evidence or a status; an estimate needs its source or calculation (`basis`); a share-of-payment cost is a fraction (0.03, not 3); totals add only known values with a compatible unit, and list the unknowns. The engine warns when personnel, acquisition or infrastructure costs (and, for transaction models, payment processing and support) are missing; founder time is a cost even when unpaid.

## Financial definitions (computed only from complete inputs)

| Metric | Formula |
|---|---|
| Commission revenue | GMV × take rate |
| Net revenue | gross revenue − refunds − discounts |
| Realised take rate | net revenue ÷ GMV |
| Average order value | GMV ÷ orders |
| Revenue per transaction | net revenue ÷ transactions |
| Average revenue per customer | net revenue ÷ customers |
| Recurring revenue share | recurring revenue ÷ net revenue |
| Gross margin | (net revenue − direct costs) ÷ net revenue |
| Contribution margin | (net revenue − variable costs) ÷ net revenue |
| Payment processing cost | payment volume × fee rate |
| Refund rate | refunded orders ÷ orders |
| Seller earnings | GMV − commission revenue − seller-borne fees |

A marketplace funnel's measured `gmv`, `platform_revenue` and `completed_transactions` feed these automatically. `cash_received`, `bookings` and `profit` are reported as supplied, never derived.

## Never confuse

| This | Is not |
|---|---|
| GMV | Platform revenue |
| Revenue | Cash received (prepayments, settlement delays and refund holds differ) |
| Gross revenue | Net revenue |
| Revenue | Profit |
| Seller earnings | Platform earnings (they are owed to sellers until paid out) |
| Bookings | Recognised revenue |

The engine rejects `revenue` equal to `gmv` in a commission or transaction model, `gross_revenue` equal to GMV without `financials.principal: true`, net revenue above GMV, and platform revenue above GMV.
