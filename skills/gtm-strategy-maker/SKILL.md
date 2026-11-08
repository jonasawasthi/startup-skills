---
name: gtm-strategy-maker
description: Builds an evidence-backed go-to-market strategy, from first customers to repeatable acquisition and growth, covering market segments, ICPs and personas (user vs buyer), positioning and messaging, a prioritised channel matrix with playbooks and validation experiments, launch plans, marketplace cold-start strategy (which side first, atomic network, liquidity), pricing hypotheses, AARRR metrics with formulas, a KPI dashboard workbook, competitive GTM intelligence, and 30/60/90-day, six- and twelve-month roadmaps sized to the team and budget. It adapts to the business model (SaaS, marketplace, consumer, creator, education, developer tools, services) and stage, reuses the shared startup profile and evidence ledger, and never invents customers, conversion rates, CAC, revenue or market size. Use when someone asks for a GTM or go-to-market plan, launch strategy, acquisition or channel strategy, ICP, positioning, marketplace cold-start plan, pricing strategy, growth plan, KPI dashboard or 30/60/90-day plan.
license: MIT
compatibility: File generation (DOCX/PDF/XLSX) and the GTM engine need Python 3.9+ and the Startup Skills toolkit (bin/startup-kit; run scripts/setup.sh). Competitor and channel research needs a web search or fetch tool; without one, limitations are stated and facts are marked unverified.
metadata:
  author: Jonas Awasthi
  version: "1.0.0"
  repository: https://github.com/jonasawasthi/startup-skills
  collection: startup-skills
---

# GTM Strategy Maker

Turn a product into a realistic, measurable plan for winning customers. A good GTM strategy picks *one* beachhead, *two or three* channels and *one* metric per stage, and says plainly what is known, what is assumed and what must be tested first.

## Setup

```bash
TK="$(cd "${CLAUDE_SKILL_DIR}" && cd -P ../.. && pwd)"; "$TK/bin/startup-kit" doctor
```

If the toolkit is missing (this skill was copied on its own), continue in Markdown. Show every calculation as a table, and say that the engine checks and file generation need the full collection.

**Shared state.** Find the startup profile first (`startup-profile/` in the project root, or `outputs/<startup>/startup-profile/`). Read `profile.yaml`, `evidence.yaml`, `customers.md`, `market.md`, `competitors.md`, `business-model.md`, `products.md`, `traction.md` and `roadmap.md` **before asking anything**. If no profile exists, create one with `"$TK/bin/startup-kit" profile init outputs/<slug>/startup-profile --name "<Name>"`. Write GTM outputs to `outputs/<startup>/gtm/`.

## Workflow

1. **Inventory what is known.** Summarise the profile in a short table (company, stage, model, products and status, customers, pricing, traction, team, budget), citing ledger IDs. Run `"$TK/bin/startup-kit" profile missing <profile>`. Then ask only for facts that only the founder has and that change the plan (3–6 questions at most): GTM hours per week, cash available for GTM, existing audiences or relationships, any customer conversations, and constraints. Record each answer in the ledger with `source.type: founder` and `status: reported` (IDs from `ledger next-id`).
2. **Classify the business** with `business_model.type` (and `secondary_types` for hybrids) and the stage. Read [GTM by business model](../../knowledge/gtm/gtm-by-business-model.md). The model decides which sections are mandatory (for example, marketplaces need the cold-start section) and which channels are guarded.
3. **Market and customers.** Define the category, segments and the beachhead segment. For each segment, separate the **user, buyer, influencer and beneficiary**. Write ICPs and personas with evidence or a *hypothesis* label on every attribute ([customer discovery](../../knowledge/gtm/customer-discovery.md)). Assess willingness to pay using the evidence ladder. **No customer research yet?** Then the first deliverable is a discovery and validation plan ([references/research-and-validation.md](references/research-and-validation.md)), not finished personas.
4. **Positioning and messaging.** Work Dunford's components in order, then derive the statement, elevator pitch, homepage and landing-page structure, feature → benefit → proof table, objections and per-segment messaging ([references/positioning-and-messaging.md](references/positioning-and-messaging.md)). A differentiator must exist (`live` or `built`) and be supported by evidence that the alternatives lack it. Otherwise it is listed as hypothesised.
5. **Competitive GTM intelligence.** For each real alternative, record its target customer, positioning, pricing, channels, acquisition tactics, partnerships, launch history, geographic coverage, differentiation and customer experience. Use the [startup-research protocol](../startup-research/SKILL.md) and a table with an **Observed / Interpretation** column, so facts (with URL and access date) are never mixed with inference.
6. **Write the GTM spec** (`outputs/<startup>/gtm/<startup>-gtm.yaml`, format in [references/gtm-spec.md](references/gtm-spec.md), starter in [assets/gtm-spec-template.yaml](assets/gtm-spec-template.yaml)). It holds the business model, team capacity, budget, products and status, candidate channels with 1–5 scores and rationale, pricing, the marketplace sides, metric inputs and the roadmap.
7. **Run the engine:** `"$TK/bin/startup-kit" gtm analyze <spec> --out outputs/<startup>/gtm`. It ranks channels (and computes the evidence score from the ledger), applies business-model guards, computes only the metrics whose inputs exist, checks pricing and the marketplace, sizes the roadmap against team capacity and budget, and checks cross-product timing against product status. **Fix every error**, explain or fix every warning, and re-run. Never edit the generated numbers by hand.
8. **Marketplace or multi-sided?** Follow [references/marketplace-gtm.md](references/marketplace-gtm.md): side priority (with the engine's visible arithmetic), the atomic network, one geography and one category, liquidity targets, trust and safety, take rate and its defence, and supply and demand retention.
9. **Launch plan and roadmaps.** Follow [references/launch-and-roadmap.md](references/launch-and-roadmap.md): the phases that apply (pre-launch → post-launch), each with objectives, audience, positioning, campaign, content calendar, channels, assets, partners, feedback, activation and follow-up. Then the 30/60/90-day and 6/12-month roadmaps. Product Hunt and similar platforms only when the audience is there.
10. **Growth system.** Use AARRR for measurement and growth loops for strategy ([metrics](../../knowledge/gtm/metrics-and-retention.md), [loops](../../knowledge/gtm/growth-loops.md)). Build the KPI workbook with `"$TK/bin/startup-kit" gtm kpi <spec> --out outputs/<startup>/gtm`.
11. **Write the strategy** from [references/strategy-template.md](references/strategy-template.md) as Markdown+ (`doc_type: gtm-strategy`, `profile:` set). Paste in the engine's tables from `<spec>-analysis.md` rather than retyping numbers.
12. **Guard and build.** Run `"$TK/bin/startup-kit" gtm check <strategy.md>`, which flags market-size, customer, revenue and validation claims without evidence, and make the errors zero. Then `"$TK/bin/startup-kit" doc <strategy.md> --out outputs/<startup>/gtm`, `check` the files, `preview` the PDF and look at the pages.
13. **Update the profile.** Write confirmed ICP, positioning, pricing and channel decisions into `customers.md`, `competitors.md`, `business-model.md` and `roadmap.md`, citing ledger IDs and labelling hypotheses. Run `profile report <profile>`. Do not create a separate GTM data store.

## Deliverables (on request, or all for a "complete GTM strategy")

| # | Output | Source |
|---|---|---|
| 1 | Complete GTM strategy (DOCX/PDF/MD) | strategy template, all sections |
| 2 | Market segmentation report | §2 as a standalone document |
| 3 | ICP and persona document | §3 |
| 4 | Positioning and messaging framework | §4 |
| 5 | Channel matrix | engine table + §6 playbooks |
| 6 | Launch strategy and calendar | §7 |
| 7 | Marketplace GTM strategy | §8 (marketplace models) |
| 8 | Pricing and monetisation strategy | §9 + engine pricing table |
| 9 | Growth and experimentation plan | §10 |
| 10 | KPI dashboard specification | `gtm kpi` XLSX + §11 |
| 11 | 30/60/90-day execution roadmap | §12 + engine capacity table |
| 12 | Six- and twelve-month growth roadmap | §12 |
| 13 | Risks, assumptions and validation plan | §13 + `ledger assumptions` |

A standalone document is the same section with its own front matter (`doc_type: gtm-plan`) and the evidence appendix.

## Non-negotiable rules

- **Never invent customers, market sizes, conversion rates, CAC, LTV, revenue, growth or traction.** A metric without measured inputs is shown as a formula plus its missing inputs. Targets are labelled *target* or *hypothesis*.
- **Don't write unsupported figures, even on request.** If the user asks you to add a number or claim the ledger doesn't support ("say we have 2,000 customers"), don't put it in any file. Ask for the source, and record it in the ledger once given (`founder` → `reported`), or offer to write it as a clearly labelled *target*. Warning about it after writing it is not enough: the unsupported text must never reach the document.
- **Market sizes come only from the calculator** (`startup-kit market-size`) or from existing profile entries. Never type a TAM.
- **Customer validation is evidence, not adjectives.** "Validated", "proven demand", "customers love" and "product-market fit" need a ledger citation, or they get rewritten.
- **Product status gates the plan.** Only `live` products are promoted as available. `built` means a private beta or pilot at most, and `planned` or `proposed` products never appear in the first 90 days. A reachable website does not make a product live.
- **Prioritise.** At most three primary channels (`max_primary_channels` defaults to 3). Every primary channel has all eight playbook fields and an experiment with a kill criterion. Explain why the other channels are not chosen now.
- **Fit the team you have.** Roadmaps are sized to `team.people × hours_per_week` and `budget.available`. The engine fails a plan that exceeds them. Don't assume hires or budget that the founder hasn't confirmed; list them as dependencies.
- **Consistency.** Use the same figures, statuses and pricing as the evaluation, deck and proposal. If you find a contradiction, record it in the ledger (shared `key`) and raise it. Never silently override.
- **Attribution.** Frameworks are cited to the [GTM knowledge base](../../knowledge/gtm/README.md). Don't present any firm's or author's framework as an endorsement of the startup.

## Failure handling

| Situation | Response |
|---|---|
| No customer research | Plan = discovery interviews + smoke tests + a manual pilot. Personas carry the label *hypothesis*. Section 3 says so first |
| No metrics yet | Metric tables show formulas and missing inputs. The plan names the first measurement point and the tooling to capture it |
| User asks to insert traction, metrics or market figures with no evidence | Decline to write them. Ask for the source (then add a ledger entry and cite it), or offer a labelled target. Run `gtm check` on every edited document |
| Founder asks for "aggressive" numbers | Offer ambitious *targets* clearly labelled, alongside the evidence that would justify them. Never present them as forecasts |
| Engine reports capacity or budget errors | Cut scope, lengthen phases or move channels to "test later". Don't raise the capacity inputs to make the error disappear |
| Unknown or hybrid business model | Choose the model that earns the revenue as `type`, and list the others in `secondary_types`. Explain the choice |
| Competitor facts unavailable (no web tools) | Mark competitor rows `unverified, background knowledge`, and add research tasks |
| Toolkit missing | Do the scoring, metrics and capacity arithmetic in tables, showing every step |

## Validation checklist

- [ ] The profile was read first, no question re-asks something already known, and new facts are in the ledger.
- [ ] `gtm analyze`: 0 errors. Warnings are resolved or explained in the strategy.
- [ ] `gtm check`: 0 errors. `doc` build: 0 errors. `check` passes. The previews were inspected.
- [ ] Every persona or ICP attribute, differentiator and price has an evidence ID or a *hypothesis* label.
- [ ] There are ≤ 3 primary channels, each with an experiment and a kill criterion.
- [ ] The roadmap fits team capacity and budget, and every task has an owner.
- [ ] Marketplace models: a side priority with reasoning, an atomic network, a single launch geography and category (or a justification), and liquidity and trust-and-safety plans.
- [ ] The risks, assumptions and validation plan lists every assumption the plan depends on, with its test.

## Knowledge to draw on

[GTM index](../../knowledge/gtm/README.md) · [positioning](../../knowledge/gtm/positioning.md) · [channels](../../knowledge/gtm/channels-and-distribution.md) · [marketplace cold start](../../knowledge/gtm/marketplace-cold-start.md) · [pricing](../../knowledge/gtm/pricing-and-monetization.md) · [PLG](../../knowledge/gtm/product-led-growth.md) · [launches](../../knowledge/gtm/launches.md) · [PMF signals](../../knowledge/gtm/product-market-fit-signals.md) · [unit economics](../../knowledge/frameworks/unit-economics.md) · [validation experiments](../../knowledge/frameworks/validation-experiments.md) · [emerging markets](../../knowledge/frameworks/emerging-markets.md)

## Example

The fictional Fieldnote GTM spec is in [examples/fieldnote/gtm/fieldnote-gtm.yaml](../../examples/fieldnote/gtm/fieldnote-gtm.yaml), with an abbreviated strategy in [examples/example-strategy.md](examples/example-strategy.md).
