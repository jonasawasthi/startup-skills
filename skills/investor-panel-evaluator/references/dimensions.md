# Dimensions and the base read

The **base read** is the single business judgement in this skill. Rate the startup once, on 15 dimensions, before any investor is involved. Every investor evaluation, panel and verdict reads the same base read. An investor never re-rates a dimension.

The base read is stored as `outputs/<startup>/shark-tank/base-read.yaml` (start from the [template](../assets/templates/base-read.yaml)) and checked and rendered with:

```bash
"$TK/bin/startup-kit" shark-tank base-read outputs/<startup>/shark-tank/base-read.yaml \
  --profile outputs/<startup>/startup-profile --out outputs/<startup>/shark-tank/base-read.md
```

How the 15 dimensions relate to the startup-idea-evaluator's 10 is defined in the [crosswalk](evaluator-crosswalk.md). Which dimensions are critical depends on the business type and stage ([business types and stages](business-types-and-stages.md)).

## Scale

The scale is the house scale from the evaluator's [scoring rubric](../../startup-idea-evaluator/references/scoring-rubric.md). Do not invent another one.

| Rating | YAML value | Meaning |
|---|---|---|
| **Strong** | `strong` | Evidence of the required status (see the ceiling) supports it. Few open questions remain on the decisive question |
| **Adequate** | `adequate` | Plausible, with some evidence. Important questions remain |
| **Weak** | `weak` | Evidence points against it, or a critical gap is confirmed |
| **Unknown** | `unknown` | The decisive question cannot be answered from the ledger. This is a task, not a judgement |

Where a reader might take Unknown as neutral, write "Unknown (not enough evidence to judge)". Never use another name for it.

Each rating carries a **confidence**: `high`, `medium` or `low`. Confidence says how sure you are of *this rating* given the evidence. It is not a second rating.

For **D11 Operational complexity** and **D15 Legal and regulatory risks**, Strong means the risk is low or well controlled, and Weak means it is high or uncontrolled. State this in every table that shows these two dimensions.

## The evidence ceiling

Every dimension has one **decisive question** (listed below). The best evidence that answers it sets the highest rating you may give.

| Best evidence on the decisive question | Highest supporting rating | Weak allowed? |
|---|---|---|
| At least one `verified` entry (accounts, primary data, contracts, the codebase, official sources, a reproducible calculation from sourced inputs), or `reported` behavioural evidence with `source.type: interview` recorded through customer discovery | Strong | Yes |
| `reported` entries (founder or company figures) or `estimate` entries with a shown method | Adequate | Yes |
| Only `assumption`, `unverified` or `contradicted` entries, or nothing | Unknown | Only under the asymmetry rule |

**Asymmetry rule.** Evidence against the business is accepted at a lower bar than evidence for it. Weak is allowed on `verified` evidence, or on founder-provided evidence that goes against the founder's own interest. A founder-reported negative margin justifies Weak. A founder-reported positive margin justifies Adequate at most. The reason: a founder has no incentive to overstate weakness, and a false Strong misleads the founder more than a false Weak.

The engine (`shark-tank base-read`) accepts Weak on any `reported` entry, because it cannot tell whether a founder figure goes against the founder's interest. That test is the reviewer's, under B7 in [guards](guards.md).

**Half an anchor is not the anchor.** When a founder-provided figure covers only part of an anchor (cash and burn but no model for D12; a channel but no cost for D08; a list of requirements but no source for D15), the dimension stays Unknown, unless the figure itself points against the business, which allows Weak at low confidence.

**When to write Unknown.** Rate a dimension Unknown when any of these holds:

1. No `verified`, `reported` or `estimate` entry addresses the decisive question.
2. The only relevant entries are `assumption`, `unverified` or `contradicted`. If only `contradicted` entries exist, say so in the explanation.
3. The dimension's own Unknown trigger (below) applies.

Every Unknown dimension produces three things: its decisive question, the evidence that would answer it, and, when the dimension is critical, a validation experiment in the [experiment template](../../../knowledge/frameworks/validation-experiments.md).

`shark-tank base-read` rejects Strong without a `verified` or interview-behavioural entry, and Adequate that rests on assumptions only.

## Evidence basis per rating

Every dimension lists its evidence in six buckets. Write `none` (or an empty list in YAML) for an empty bucket. Never leave a bucket out.

| Bucket (rendered label) | YAML key | Ledger entries it holds |
|---|---|---|
| Verified | `verified` | `status: verified` |
| Founder-provided | `reported` | `status: reported` with `source.type: founder`. Other `reported` entries (a company press release, a partner's statement) go here too, and the explanation names their source type |
| Estimates | `estimate` | `status: estimate` |
| Assumptions | `assumption` | `status: assumption` |
| Unverified or disputed | `disputed` | `status: unverified` or `contradicted` |
| Unknowns | `unknowns` | Open questions, written as text. They have no ledger entry |

Each dimension also states the ceiling applied, what would raise the rating (`upgrade_if`) and what would lower it (`downgrade_if`). The upgrade condition names checkable evidence ("three months of sell-through data with returns from one retailer"), never effort ("more marketing").

Rendered, one dimension reads like this (fictional figures):

```
D07 Unit economics: Adequate (confidence: medium) [critical]
Explanation: Contribution is positive on a sourced bill of materials and a reported price, but the
  return rate is assumed, so the decisive figure cannot reach Strong.
Evidence basis
  Verified:               E-031 supplier quote, bill of materials per unit
  Founder-provided:       E-033 retail price (reported)
  Estimates:              E-040 contribution after returns (calculation, method shown)
  Assumptions:            E-041 return rate (owner: founder)
  Unverified or disputed: none
  Unknowns:               cost of acquiring a retail customer; warranty cost
Ceiling applied:          Adequate (depends on a reported price and an assumed return rate)
Upgrade if:               three months of sell-through data with returns from one retailer
Downgrade if:             measured returns above the assumed rate, or a higher quote at the next order quantity
```

## The 15 dimensions

Each specification gives what the dimension measures, its decisive question, the evidence that can answer it, the anchors for each rating, and its own Unknown trigger. The anchors describe evidence patterns. The ceiling above always applies on top of them.

The evaluator's [question bank](../../startup-idea-evaluator/references/evaluation-framework.md) (sections A–I) is the source of detailed questions for each dimension. Do not copy it here.

### D01 Problem severity
- **Measures:** how frequent, costly and urgent the problem is for a defined customer.
- **Decisive question:** what does the problem cost a specific customer today, and what do they already do or pay about it?
- **Evidence:** problem interviews describing recent, specific incidents; current spend on workarounds or competitors; a quantified cost (hours × wage, losses, fines); complaint or search data.
- **Strong:** recent, costly incidents and existing spend or workarounds, recorded as `verified` or interview evidence (`source.type: interview`), across enough interviews in the defined segment that the pattern does not rest on one or two accounts.
- **Adequate:** the cost is quantified only from `reported` or `estimate` entries (founder figures, desk estimates), or the interview evidence comes from a small sample (one or two conversations) or a single sub-segment. Either condition alone caps the rating at Adequate.
- **Weak:** customers cannot recall incidents, tolerate the problem, or the cost is trivial (nice to have).
- **Unknown if:** the only evidence is the founder's description of the problem, or opinion surveys without incidents.

### D02 Market opportunity
- **Measures:** size, growth and timing of the market the business can actually reach, relative to its stated ambition.
- **Decisive question:** how large is the bottom-up serviceable market built from sourced factors, and why is now the time?
- **Evidence:** `startup-kit market-size` output ([method](../../../knowledge/frameworks/tam-sam-som.md)); official statistics; dated industry sources; a specific timing change (regulation, cost, technology, behaviour).
- **Strong:** a calculator SAM built mostly from verified factors, large enough for the stated ambition, with a sourced timing change.
- **Adequate:** calculator output from a mix of verified and estimated factors, and a plausible timing argument.
- **Weak:** the bottom-up SAM is too small for the ambition or is declining, or the timing evidence points against.
- **Unknown if:** only top-down figures exist, or there is no sizing. Never use a TAM that the calculator did not produce.
- **Market:** take the market for D02 and D15 from `geography` in `profile.yaml`. If that field is empty, take it from the ledger entries (where customers, pilots or registrations are) and say in the explanation that the market was taken from the ledger. Ask the founder only if the ledger does not establish it.
- **Note:** "large enough" depends on the ambition recorded in the base read (`venture`, `growth`, `lifestyle`, `unknown`). A small SAM is not Weak for a lifestyle business. It matters for *investable* (J2), not for *good business* (J1).

### D03 Customer demand
- **Measures:** whether customers want *this solution*, shown by what they do. D01 is about the problem; D03 is about the product.
- **Decisive question:** what have customers done (paid, committed, returned, re-ordered) that shows they want this product?
- **Evidence:** payments, pre-orders with deposits, signed letters of intent with a price, paid pilots, retention cohorts, repeat purchase rate, usage analytics.
- **Strong:** verified payments plus retention or repeat purchase.
- **Adequate:** reported sales, deposits, priced letters of intent, or pilot usage.
- **Weak:** low conversion at the price, churn, pilots that do not convert, or interest that collapses when price is discussed.
- **Unknown if:** the only evidence is likes, followers, survey intent or a free waitlist. Name a free waitlist as an *interest signal*. It never counts as customers.

### D04 Competitive landscape
- **Measures:** what customers use today (including doing nothing or a manual workaround), how well it serves them, and the room left.
- **Decisive question:** what do target customers use today, and what evidence shows they would switch?
- **Evidence:** a sourced competitor table (pricing pages, filings, reviews) built with the [competitive analysis](../../../knowledge/frameworks/competitive-analysis.md) method; substitutes and the status quo; switching evidence; incumbent responses.
- **Strong:** a sourced map that includes the status quo, and evidence of dissatisfaction or switching in the target segment.
- **Adequate:** a sourced map and a plausible underserved segment.
- **Weak:** well-resourced alternatives serve the segment well, or an incumbent can bundle the feature, with evidence.
- **Unknown if:** there is no map, only an unsourced founder list, or a "no competitors" claim. Treat "no competitors" as unresearched, never as Strong.

### D05 Product differentiation
- **Measures:** how much better the product is on the criteria customers actually use to buy.
- **Decisive question:** on which buying criterion is it materially better, for whom, and shown how?
- **Evidence:** comparative tests, benchmarks, switching behaviour, customer feedback from interviews, product status per feature.
- **Strong:** a `live` product with verified evidence of a large advantage on a buying criterion (a head-to-head result, switching).
- **Adequate:** a `built` or `live` product with a reported or estimated advantage.
- **Weak:** parity, or an advantage on criteria customers do not weigh.
- **Unknown if:** the differentiating features are `planned` or `proposed` only. Product status rules apply: code proves *built* at most ([evidence standards](../../../knowledge/frameworks/evidence-standards.md)).

### D06 Business model
- **Measures:** how value is captured: who pays whom, how much, for what, through which revenue streams.
- **Decisive question:** who pays how much for what, and has anyone paid that price?
- **Evidence:** invoices or payment records, pricing tests, willingness-to-pay interviews, comparables, business-model-designer outputs (maturity, revenue stages).
- **Strong:** verified payments at the stated price, and payer and user incentives aligned.
- **Adequate:** pricing supported by pre-sales or credible comparables.
- **Weak:** the payer is misaligned with the value, there is evidence of disintermediation, or the price is below cost.
- **Unknown if:** no price has been tested with any customer. A price page or a payment flow that is configured but has not taken a live payment is not a tested price.

### D07 Unit economics
- **Measures:** contribution per unit, order or customer after all variable costs, and how sensitive it is.
- **Decisive question:** is contribution positive after all variable costs (and after acquisition cost, where relevant), and which input is it most sensitive to?
- **Evidence:** `startup-kit unit-economics` output for subscriptions ([method](../../../knowledge/frameworks/unit-economics.md)); accounts; supplier quotes; cohort data; payment fees, returns, logistics.
- **Per-unit products:** the `unit-economics` command models subscriptions. For a product sold per unit, show the contribution arithmetic in a table (price, then each variable cost: bill of materials or cost of goods, landed freight and duty, channel margin, payment fees, returns and warranty, fulfilment), with every input cited to the ledger and its status. Record the result in the ledger: as `status: estimate` (`source.type: calculation`) when any input is reported, estimated or assumed; as `status: verified` with `source.type: calculation` only when every input is verified. Say which in the explanation.
- **Strong:** verified from accounts or cohorts, and positive under conservative inputs.
- **Adequate:** an estimate from sourced inputs, positive, with the sensitivity shown.
- **Weak:** negative, or positive only under optimistic inputs.
- **Unknown if:** price, variable cost or (for subscription and marketplace models) acquisition cost or churn is missing or assumption-only, so the calculation cannot run on non-assumption inputs.

### D08 Customer acquisition
- **Measures:** how customers are won, at what cost, and whether that can be repeated.
- **Decisive question:** which channel produced the existing customers (or which will be tested first), at what cost per customer?
- **Evidence:** channel attribution, ad account exports, sales pipeline data, channel tests from gtm-strategy-maker.
- **Strong:** a repeatable channel with verified acquisition cost inside the payback target.
- **Adequate:** a reported acquisition cost from an early channel, or a small tested sample.
- **Weak:** acquisition cost above target or rising, or acquisition depends on founder effort that cannot be repeated.
- **Unknown if:** the plan is a category ("marketing", "social media", "virality", "word of mouth") with no channel, cost or conversion figure, or the channel is set up (an ad account, a referral feature, a partner agreement) but has not yet produced a customer.

### D09 Distribution
- **Measures:** the commercial route by which the product reaches the customer, who controls it, and what it takes (margin, terms, exclusivity). D08 is the cost of creating demand; D09 is the route and its gatekeepers.
- **Decisive question:** what route gets the product to customers, who controls that route, and what does it cost?
- **Evidence:** retail listings, distributor or partner contracts, margin stacks, platform dependencies (app stores, marketplaces), sales-team capacity.
- **Strong:** secured routes (verified contracts or listings) with known margins and no dependence on a single gatekeeper.
- **Adequate:** an early route in place (reported) and a credible plan for the next one.
- **Weak:** dependence on one gatekeeper with evidence of risk, or a margin stack that removes the profit.
- **Unknown if:** no route is identified, or the route exists only as configuration, an integration that has not processed a live transaction, or an unsigned plan. Such a route is not operating, and the rating stays Unknown until it has run. For software sold directly online, D09 assesses platform dependence and the sales motion. The same entry may be cited in D08 and D09 only if it answers each dimension's own decisive question.

### D10 Scalability
- **Measures:** whether volume can grow without a proportional rise in cost, people or quality problems.
- **Decisive question:** what breaks at ten times the current volume, and what does growth cost?
- **Evidence:** an inventory of manual processes, margin trend against volume, capacity limits (production, staff, suppliers), a codebase scan.
- **Strong:** evidence that margin holds or improves with volume, and key processes are automated or contracted.
- **Adequate:** bottlenecks identified, with a credible plan.
- **Weak:** growth needs proportional founder or staff time, or a capacity limit is evidenced.
- **Unknown if:** nothing is known about operations above the current volume.

### D11 Operational complexity (Strong means well controlled)
- **Measures:** how hard the business is to run week to week: supply chain, inventory, fulfilment, staff, support, quality.
- **Decisive question:** what must go right every week, and is it under control at the current volume?
- **Evidence:** on-time delivery, defect and return rates, supplier contracts and backups, support load, stock-outs. Use the operational category of the [risk register](../../../knowledge/frameworks/risk-register.md).
- **Strong:** processes work at the current volume, with evidence, and critical suppliers have backups.
- **Adequate:** known, manageable complexity, with some evidence.
- **Weak:** evidenced failures (stock-outs, defects, delays), a single supplier with no backup, or the founder as a single point of failure.
- **Unknown if:** operations are not described, or they are designed but have not yet run at any volume (a supplier agreed but no order delivered, a fulfilment process not yet used).

### D12 Financial sustainability
- **Measures:** runway, burn, working capital, and whether the business reaches its next milestone or profitability before cash runs out.
- **Decisive question:** how many months of runway exist, and does the plan reach the next milestone inside them?
- **Evidence:** accounts, bank statements (founder documents), `startup-kit model` output.
- **Strong:** verified accounts show profitability, or runway that covers the next milestone with margin to spare.
- **Adequate:** reported cash and burn, and a model that shows a plausible path.
- **Weak:** runway shorter than the time to the next milestone, or a working-capital trap (inventory, receivables).
- **Unknown if:** cash or burn is not provided, or founder-provided cash and burn exist but no model does. In that case the rating stays Unknown unless the figures themselves show the runway ends before the next milestone; then it is Weak at low confidence (against the founder's interest).

### D13 Defensibility
- **Measures:** what stops others from copying the business as it succeeds.
- **Decisive question:** which specific moat exists or is building up, and what evidence shows it?
- **Evidence:** granted IP, exclusive contracts, network-effect data, switching-cost evidence, brand or data advantages with metrics ([defensibility](../../../knowledge/a16z/defensibility.md)).
- **Strong:** a named moat with evidence (a granted patent, an exclusive contract, a measured network effect).
- **Adequate:** a named moat with a path to evidence (a filed patent, an early data advantage).
- **Weak:** easily copied, or incumbents can bundle it.
- **Unknown if:** a moat is asserted without a type or any evidence ("first-mover advantage" alone).

### D14 Founder execution capability
- **Measures:** evidence that this team can deliver this plan. Evidence only: never personal traits, never speculation.
- **Decisive question:** what has this team already shipped, sold or run that is relevant here?
- **Evidence:** shipped product, repository history, launches, sales achieved, milestones met against plan, relevant prior roles (founder-provided or public).
- **Strong:** verified relevant execution, and the critical skill gaps are covered.
- **Adequate:** reported relevant experience and some shipping evidence.
- **Weak:** a critical skill is missing with no plan, or missed milestones are evidenced.
- **Unknown if:** there is no information on the team. Interrogation answers inform this dimension only through what was said (founder-provided), never through impressions of the founder.

### D15 Legal and regulatory risks (Strong means well controlled)
- **Measures:** licences, certifications, product safety, data protection, sector rules, IP ownership, corporate hygiene, cross-border constraints.
- **Decisive question:** which permissions, certifications or legal structures does the business need, and does it have them?
- **Evidence:** licences and certificates, legal opinions, regulator sources for the startup's own market (set as in D02), IP assignment, the cap table. For cross-border questions use the [emerging markets](../../../knowledge/frameworks/emerging-markets.md) checklist.
- **Strong:** required licences or certifications obtained (verified), or regulation demonstrably light, with sources.
- **Adequate:** requirements identified from sources, with a plan, cost and timeline.
- **Weak:** a required licence is missing with an uncertain path, or the model operates in a grey zone.
- **Unknown if:** the requirements have not been researched. Always add: "not legal advice; confirm with qualified counsel".

## Using an existing evaluator report

If `outputs/<startup>/startup-analysis/<startup>-evaluation.md` exists, set `imported_from` and `imported_date` in the base read, record the evaluator's ratings behind each dimension in its `evaluator` map (keys: `problem-severity`, `market`, `timing`, `customer-clarity`, `differentiation`, `business-model`, `distribution`, `defensibility`, `founder-market-fit`, `execution-risk`; for example `evaluator: {business-model: adequate}` on D06 and D07), and follow the rules in the [crosswalk](evaluator-crosswalk.md): carried and primary dimensions start from the evaluator's rating, the ceiling still applies, Unknown stays Unknown, and every departure needs a `divergence_note` naming the report, its date, both ratings and the ledger IDs. `shark-tank base-read` checks that a divergence note exists wherever the crosswalk requires one. List all divergences in the rendered base read and recommend re-running the evaluator. Never override it silently.

Without an evaluator report, build the base read from the profile and ledger directly. No other skill's output is required.

## Aggregation

There is **no numeric aggregate**. Never write a sum, an average, a percentage of dimensions, "x/15", a star rating or a colour scale that summarises dimensions. Never put a count of ratings in the same sentence as "chance", "likely", "probability" or "odds".

The base read ends with two things:

1. **The evidence profile line.** The engine renders it in a fixed form, and it always shows the Unknown count, even when it is zero:
   `Base read (15 dimensions): Strong 2 · Adequate 5 · Weak 2 · Unknown 6. Critical dimensions: D01 Adequate, D03 Unknown, D07 Weak, D14 Adequate, D15 Adequate.`
   Any other sentence that summarises ratings must also state the Unknown count.
2. **The critical-dimension table:** dimension, rating, confidence, the decisive evidence, and the upgrade condition. The [five judgements](verdict.md) use only gates over this table.

## The base-read file

| Field | Content |
|---|---|
| `startup` | Startup slug, as in `outputs/<startup>/`. A slug only; put anything else in `note` |
| `note` | Optional free text a reader must know about the base read as a whole: that the company and figures are fictional, that the type is provisionally `regulated`, or that the market was taken from the ledger. Never evidence or ratings |
| `as_of` | Date the base read was written |
| `ledger_snapshot` | The latest `updated` date in `evidence.yaml` when the base read was written. If the ledger changes later, `shark-tank context` flags the base read as stale |
| `business_type` | One primary type and an optional secondary ([types](business-types-and-stages.md)) |
| `stage` | `pre-launch`, `launched-pre-revenue`, `early-revenue`, `trading` or `scaling` |
| `ambition` | `venture`, `growth`, `lifestyle` or `unknown`, as the founder states it (founder-provided) |
| `imported_from`, `imported_date` | Optional evaluator report path and its date |
| `dimensions` | All 15, D01 to D15. Each has `rating`, `confidence`, `critical`, `explanation`, `evidence` (the six buckets), `ceiling`, `upgrade_if`, `downgrade_if`, `evaluator` (a map of evaluator dimension keys to ratings, or omitted) and `divergence_note` (or `null`) |
| `judgements` | Optional. The five judgements in the same form as the [verdict](verdict.md); checked when present. The verdict document is where they are normally written |

The explanation has two to four sentences: what the evidence shows, and why this level and not the one above or below. Cite ledger IDs as `E-…` in the bucket lists. A founder-sourced figure in the explanation is labelled "founder-provided" or "reported" in the same sentence.

Rebuild the base read, never patch it, when the ledger changes. Keep the old file under a dated name if earlier evaluations cite it.
