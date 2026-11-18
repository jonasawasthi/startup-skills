# Business types and stages

The 15 decisive questions in [dimensions](dimensions.md) never change. What changes with the business type and stage is **what counts as evidence** for a dimension and **which dimensions are critical**. The critical set drives the evidence profile line, the question priority in interrogation and the gates of the [five judgements](verdict.md).

Record the type and stage in the base read (`business_type`, `stage`) and set `critical: true` on each dimension in the resulting critical set.

## Always critical

| Dimension | Why |
|---|---|
| D01 Problem severity | Without a costly problem nothing else matters |
| D03 Customer demand | Behaviour, not opinion, shows the product is wanted |
| D07 Unit economics | A business that loses money per unit does not improve with volume |
| D14 Founder execution capability | Every plan depends on the team delivering it |

**D15 Legal and regulatory risks is a gate for every business.** It blocks J3 (investment-ready) when it is Weak, even where it is not in the critical set. For regulated businesses it is fully critical (see below).

## Business types

A startup may declare one primary type and one secondary type (for example `[marketplace, regulated]`). The critical set is the union of "always critical" and the added dimensions of both types.

| Type | YAML value | Added critical dimensions | Evidence that anchors the key dimensions |
|---|---|---|---|
| SaaS or software | `saas` | D08, D12 | D07: gross margin, acquisition-cost payback, net revenue retention. D03: activation and logo-retention cohorts. D09: platform dependence and sales motion |
| Hardware | `hardware` | D11, D12, D15 | D07: bill of materials, landed cost, contribution after returns and warranty, effect of minimum order quantity. D11: supplier backup, defect rate, lead times. D12: working capital tied up in inventory. D15: certification for each target market (radio, electrical, product safety, or the local equivalent) |
| Consumer goods (packaged goods, food, beauty) | `consumer-goods` | D07, D09 | D09: listings, sell-through per store per week, retailer terms. D07: margin stack after distributor and retailer cuts, trade spend. D15: food or cosmetics licensing and labelling |
| Services or agency | `services` | D10, D11 | D07: utilisation, billable rate against loaded cost. D10: founder dependence, hiring constraint. D13 is usually Weak by nature, and that alone is not a reason for J1 to be `no` |
| Marketplace or platform | `marketplace` | D08 (for both sides), D09 | D03: repeat transactions on both sides, liquidity. D07: take rate and contribution per transaction. D13: measured network effects ([marketplace analysis](../../../knowledge/frameworks/marketplace-analysis.md)) |
| Direct-to-consumer or e-commerce | `d2c` | D07, D08 | D08: blended and paid acquisition cost, repeat purchase. D07: contribution after fulfilment, returns and payment fees |
| Regulated (fintech, health, food safety, education with licensing) | `regulated` | D15 becomes fully critical | D15: licence status and the path to it, from regulator sources |

**Provisionally regulated.** If the ledger records an open question about whether the business needs a licence, a licensed partner or a regulator's approval (for example to hold customer funds, give health advice or sell a food product), add `regulated` as the secondary type until that question is resolved. D15 then joins the critical set. Say in the base read that the classification is provisional and which ledger entry or open question causes it. When the question is answered, rebuild the base read with or without `regulated`.

Use the concepts of the startup's own type only. A hardware startup's report talks about bill of materials, dealers and certification, not liquidity or take rate. If the type is unclear, ask the founder once and record the answer as founder-provided. If the founder does not know, choose the closest type, say why in the base read, and do not add a secondary type.

### Country and programme context

The startup's own market sets the D02 sources, the D15 regulators and the currency. Take them from the startup profile (`profile.yaml` `geography`), never from the investor. If `geography` is empty, take the market from the ledger entries (where the customers, pilots, registrations or sales are) and say in the base read that the market was taken from the ledger. Ask the founder only if the ledger does not establish it. An investor from one programme reading a startup from another country does not change which regulator or statistics office applies. Cross-border questions (payments, foreign investment, data, tax) use the [emerging markets](../../../knowledge/frameworks/emerging-markets.md) checklist and are answered by research, not assumed.

## Stages

Set the stage from evidence about the product and revenue, not from the funding round in `profile.yaml`. Use the first row that matches.

| Stage | YAML value | Matches when | Added critical | Evidence rules |
|---|---|---|---|---|
| Pre-launch | `pre-launch` | No product is `live`, or nobody outside the team uses it | None | No traction fields are filled; outputs say "none yet (pre-launch)". D03 can reach Adequate only with behavioural commitments (deposits, priced letters of intent, paid pilots). D07 can reach Adequate only from sourced inputs: supplier quotes are verified documents, and prices are assumptions until tested. D10 and D12 are often Unknown; that is expected and makes J1 `not-yet-determinable`, not `no` |
| Launched, pre-revenue | `launched-pre-revenue` | A `live` product is used, and nobody has paid | D06 | Usage data from analytics counts as verified when exported. Free usage is not paid demand |
| Early revenue | `early-revenue` | Customers have paid, and there are no accounts or no repeatable channel yet | D08, D12 | Reported revenue caps the dimension at Adequate until accounts or payment exports are provided |
| Trading | `trading` | Regular revenue with at least one year of accounts or equivalent records | D08, D10, D12 | Accounts are expected. If they are missing, that is itself a gap, and J3 names it |
| Scaling | `scaling` | Revenue growth across more than one channel or market | D10, D11, D13 | Cohort and channel data are expected for each dimension |

**Pre-launch rule.** A pre-launch company is evaluated on problem evidence, commitment evidence, founder execution and the quality of its validation plan. It is never given invented traction, and its unknowns become the action plan rather than penalties.

For a pre-launch company, half or more of the critical dimensions are usually Unknown, so most investor evaluations hold the stance "Cannot form a view (insufficient evidence)", with evidence-gap concerns on those dimensions. That is the expected result, not a failure. Do not soften it to "Conditional on evidence"; make the gaps and the experiments that close them the substance of the report.

## Applying the critical set

1. Determine the type and stage. Write both into the base read, with one sentence on why if either is debatable.
2. Take the union: always-critical dimensions, the type's added dimensions (both types if there is a secondary), and the stage's added dimensions. For `regulated`, mark D15 critical.
3. Set `critical: true` on exactly those dimensions. All others are `critical: false`.
4. The critical-dimension table, the evidence profile line, the interrogation queue (tiers 1–3) and the judgement gates all use this set. Never use a different set in a later document for the same base read.

### Illustration (fictional)

Fieldnote, the repository's fictional company, sells offline-first operations software to agricultural cooperatives (field records and farmer payments) as a subscription, with paying pilots. It is `saas` at `early-revenue`. Its critical set is D01, D03, D07, D14 (always), D08 and D12 (SaaS), and D08 and D12 again (early revenue): D01, D03, D07, D08, D12, D14. D15 remains a gate for J3.
