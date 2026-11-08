# Marketplace models

Background: [marketplace business models](../../../knowledge/business-model/marketplace-business-models.md), [multi-sided platforms](../../../knowledge/business-model/multi-sided-platforms.md), [liquidity and cold start](../../../knowledge/business-model/liquidity-and-cold-start.md).

## Configurations

| Type | Example shape | Design emphasis |
|---|---|---|
| two-sided | Sellers and buyers | Which side first; take rate vs leakage |
| three-sided | Restaurants, couriers, diners | Each side's economics; who subsidises whom |
| service | Tutors, contractors | Scheduling, quality, off-platform leakage |
| digital-product | Templates, courses, downloads | Discovery, refunds, piracy |
| education | Teachers and learners | Teacher-led demand, completion, exam seasons |
| managed | Platform vets or delivers the service | Higher take rate, higher operating cost |
| hybrid-saas | Software for one side plus a marketplace | SaaS revenue first, marketplace later (NFX tactic: "Build a SaaS tool for one side of the market") |

## What every marketplace spec must describe

1. **Sides**: each side is a separate segment with its own acquisition, value, what it pays and any subsidy. A supply segment cannot appear as demand.
2. **Matching**: how demand finds supply.
3. **Trust and safety**: verification, reviews, moderation, KYC.
4. **Transaction flow**: from checkout to delivery to completion.
5. **Payments**: collection, payout and settlement, refunds, disputes and who bears payment fees, each linked to a dependency.
6. **Leakage**: why transactions stay on the platform once both sides have met.
7. **Cold start**: which side first, and the smallest market where it can work.
8. **Network effects**: same-side or cross-side, and the evidence (usually none yet).
9. **Multi-sided pricing**: who pays, who is free, who is subsidised.

## The funnel holds measured counts only

registered supply → active supply → available supply → registered demand → active demand → actual demand → matches → completed transactions → repeat transactions

- The engine checks the order (active ≤ registered; completed ≤ matches; repeat ≤ completed).
- Ratios (activation, match rate, completion, repeat share, sell-through) are computed only when both counts exist, and carry the weaker status.
- Registrations are not active participants; listings are not demand; a match is not a completed transaction.

## Liquidity claims

`liquidity.status` is `not-measured`, `not-yet`, `emerging` or `achieved`. *Emerging* or *achieved* needs measured completed transactions and measured liquidity evidence (a dataset); *achieved* also needs a measured repeat or sell-through rate. A count of sellers is never liquidity.

## Supply does not create demand by itself

`brings_other_side: true` on a side is an assumption. Link it to an assumption or hypothesis, or cite measured evidence. NFX's first tactic is to get the harder side first, but which side is harder is itself something to test.

## Money: GMV, platform revenue, seller earnings

- Measured `platform_revenue` gives the realised take rate and seller earnings (GMV − platform revenue).
- Without it, the design take rate gives *design* figures, labelled with the take rate's status.
- Seller earnings are owed to sellers; a refund hold makes the platform hold other people's money, which can raise regulatory questions (see [payments and regulation](payments-and-regulation.md)).

## Take rate

A high rake invites leakage and competitors; a low rake needs volume (Gurley, *A Rake Too Far*). The take rate is a design choice until sellers accept it; register that as a `pricing` assumption.
