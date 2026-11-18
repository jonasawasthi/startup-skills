---
name: business-model-designer
description: Designs, compares, documents and stress-tests startup business models from evidence. It builds a nine-block Business Model Canvas and per-segment Value Proposition Canvases with every item labelled evidence, founder-provided, hypothesis, recommendation or unknown, classifies the model (SaaS, subscription, marketplace, commission, education, services, advertising, licensing, usage-based, B2B, B2C, hybrid and more), stages revenue streams from proposed to repeatable, separates fixed, variable and unknown costs, models marketplace sides, liquidity, take rate and GMV vs platform revenue, treats payment providers and regulation as dependencies to verify, compares alternatives on defined qualitative scales and stress-tests the economics without invented numbers or probabilities. Use when someone wants to design or rethink a business model, fill in a business model or value proposition canvas, choose a revenue model, model a marketplace, map revenue and costs, or find the assumptions that could break the model.
license: MIT
compatibility: The engine, checks and DOCX/PDF/XLSX outputs need Python 3.9+ and the Startup Skills toolkit (bin/startup-kit; run scripts/setup.sh). Payment-provider and regulatory research needs a web search or fetch tool; findings are dependencies to confirm with providers and advisers, never legal advice.
metadata:
  author: Jonas Awasthi
  version: "1.0.0"
  repository: https://github.com/jonasawasthi/startup-skills
  collection: startup-skills
---

# Business Model Designer

Help founders decide **who receives value, who pays, for what, how money flows, what it costs, and what must be true** for the model to work. Then say plainly how much of that is known.

A business model passes through four states, and the skill never confuses them:

1. **Conceptually coherent:** complete and internally consistent.
2. **Supported by customer evidence:** customers confirm the problem and the value.
3. **Economically viable (demonstrated):** paid transactions with positive measured contribution.
4. **Repeatable:** repeat revenue and a measured acquisition cost.

**A well-written canvas is not proof that a business works.** The engine computes the state from the ledger. A spec that claims more (`design.claimed_maturity`) is an error.

## Setup

```bash
TK="$(cd "${CLAUDE_SKILL_DIR}" && cd -P ../.. && pwd)"; "$TK/bin/startup-kit" doctor
```

**Shared state.** Read the startup profile before asking anything:

- `profile.yaml` and `evidence.yaml`;
- `business-model.md`, `customers.md`, `products.md` (statuses: live, built, in-development, planned, proposed) and `financials.md`;
- any GTM spec, and the customer discovery spec (`outputs/<startup>/customer-discovery/`).

Business model files live in `outputs/<startup>/business-model/` (gitignored). There is no separate evidence store. Everything cites the shared ledger, and segments and hypotheses come from the discovery register (`design.discovery`).

## Workflow

1. **Inventory.** Run `startup-kit business-model design <profile-dir> --discovery <discovery-spec> --out <dir>`. It writes:
   - an inventory of what the profile, ledger and discovery register already say (business model text, keyed pricing and cost entries, contradictions, candidate assumptions, the discovery verdicts);
   - a starter spec in which ledger items keep their status and everything else is `unknown`.

   Ask the founder only what is missing and changes the design: who pays today, real prices or quotes, the payment provider and its written terms, and team capacity.
2. **Canvas** ([references/canvas-and-value-proposition.md](references/canvas-and-value-proposition.md)). Fill all nine blocks. Every item gets a `basis`:
   - `evidence` needs verified or reported ledger entries that are not founder statements. On the customer-facing blocks (segments, value propositions, channels, relationships, revenue streams) it needs **customer** evidence: an interview, a dataset, or an observed, committed or paid signal.
   - The founder's account is `founder`.
   - A belief to test is `hypothesis` (link the discovery `H` id).
   - Your advice is `recommendation`, with its rationale.
   - A gap is `unknown`.

   Never write a customer quotation that the ledger does not attribute to an interview.
3. **Value Proposition Canvas**, one per segment. Customer jobs, pains and gains, then products, pain relievers and gain creators, each with `addresses: [P1]`. The engine rates fit: *conceptual only* until customer evidence backs the pains.
4. **Classify** the model (`design.types`). Several compatible types form a hybrid. The engine lists what each type structurally requires (a marketplace needs sides, a liquidity assumption and a payout dependency; a subscription needs a retention assumption) and warns about anything missing. Explain in words why each type fits.
5. **Revenue architecture** ([references/revenue-costs-and-financials.md](references/revenue-costs-and-financials.md)). For each stream, record the payer, what they pay for, the mechanism, billing, structure, recognition, dependencies, risks and **stage**. Each stage is gated by evidence:
   - *tested* needs customer evidence;
   - *available* needs verified payment dependencies and a live checkout;
   - *generating* needs paid evidence;
   - *repeatable* needs measured repeat payments.

   Prices without evidence are hypotheses. A proposed stream can never report revenue.
6. **Costs.** Mark each cost fixed, variable or semi-variable, with its type, driver and amount. A number needs evidence or a status, an estimate needs its `basis`, and an unknown cost stays unknown. Totals add up only known values.
7. **Marketplace** ([references/marketplace-models.md](references/marketplace-models.md)):
   - Model supply and demand as separate sides, with their acquisition, value, payments and subsidies.
   - Describe matching, trust and safety, transaction flow, leakage, cold start, network effects, multi-sided pricing, collection, payouts, refunds and disputes.
   - The funnel holds **measured counts only**: registered → active → available → demand → matches → completed → repeat.
   - Registrations are not active participants, and a match is not a completed transaction. Liquidity can be claimed only with measured completed transactions.
   - "Supply brings demand" is an assumption to link and test.
8. **Payments, geography and regulation** ([references/payments-and-regulation.md](references/payments-and-regulation.md)):
   - Register every payment, payout, tax, legal and regulatory item as a dependency with a status, an open question and who must confirm it.
   - The engine rejects any payment provider named in the spec but not registered.
   - *Verified* regulatory items need `confirmed_by` (an adviser, the regulator or the provider).
   - **Never assume Stripe, PayPal or international card acquiring is available**, especially in Nepal.
   - **Never treat in-person cross-border QR (for example, Indian visitors paying Nepali merchants by UPI) as evidence** that a platform can take international online payments or settle sellers' earnings.
   - Report only what the cited source says (for example, "Stripe's country list does not include Nepal"). Do not add legal or regulatory reasons that you have not verified.
   - This is not legal advice. List the questions for qualified people.
9. **Alternatives** ([references/alternatives-and-stress.md](references/alternatives-and-stress.md)):
   - Describe two to four plausible models with all twelve fields.
   - Rate each criterion on its **defined qualitative scale**, with a `why` and evidence. Numeric scores, weights and rankings are rejected.
   - Mark one model `recommended`, and others `viable` or `reject`, each with a reason. A recommendation lists what must be tested before committing.
10. **Assumptions:**
    - Register each assumption with its id, category, why it matters, evidence, contradicting evidence, impact, validation method, status and linked `H` id.
    - Statuses follow the discovery rules:
      - *supported* needs customer evidence;
      - willingness to pay, pricing and revenue need `committed` or `paid` signals;
      - volume, retention, liquidity and margins need measured data;
      - internal items (costs, payments, regulation) need documents, not opinions.
    - An assumption cannot be *supported* while its discovery hypothesis is not.
    - `business-model assumptions <spec> --record` appends untested assumptions to the ledger. This is append-only and idempotent, and never edits existing entries.
11. **Stress test:**
    - The engine computes contribution per transaction, break-even volume, the lowest viable price, the highest payment-fee rate, the highest support cost and the affordable CAC, from recorded inputs only. Missing inputs stay listed.
    - Scenarios are founder-defined changes (`multiply`, `add`, `set`) with a rationale. They are what-ifs, not forecasts, and probabilities are rejected.
    - Thirteen stress cards (willingness to pay, CAC, retention, volume, fees, liquidity, seller churn, support, margins, partners, regulation, international payments, founder capacity) link assumptions, unverified dependencies and mitigations.
12. **Report.** Run `startup-kit business-model report <spec> --out <dir> --xlsx` (or `--sections canvas,revenue,stress`). The section commands are `canvas`, `value-proposition` (`--segment`), `compare` (`--model`), `revenue`, `costs`, `marketplace`, `assumptions` and `stress-test`. Then:
    - `startup-kit business-model check <file.md> --spec <spec>`;
    - `startup-kit doc <file.md> --out <dir>`;
    - `check` and `preview`, and look at the pages.

    Write the narrative fields (`summary`, `decision`, `next_steps`) from the findings, not from optimism.
13. **Update the profile carefully.** Put the recommended model into `business-model.md` with citations, labelled as the model *to test*. Never turn a hypothesis into a profile fact, and never edit or delete earlier ledger entries.

## Non-negotiable rules

- **Nothing invented.** Never invent customers, interviews, quotes, prices, conversion rates, volumes, revenue, costs, transactions or probabilities. A missing input is reported as missing.
- **Opinion is not evidence.** A founder's view is `founder`. A waitlist or "I'd pay" is a `stated` signal, never a payment.
- **Money terms stay distinct:** GMV is not platform revenue, revenue is not cash or profit, gross revenue is not net revenue, seller earnings are not platform earnings, and bookings are not recognised revenue. The engine refuses GMV recorded as revenue in a commission model.
- **Contradictions stay visible.** Contradicting evidence appears in every output, and *supported* despite a conflict needs a `conflict_note`.
- **Quote YAML text that contains commas.** In `{flow: mappings}`, an unquoted comma silently cuts the text. The engine reports keys that have no value.
- **Privacy.** Real startups' files stay in `outputs/` (gitignored). Public examples use the fictional Fieldnote company only.

## Failure handling

| Situation | Response |
|---|---|
| No customer research yet | Build the canvas from hypotheses. The maturity verdict says *coherent* at most, and the discovery verdicts are quoted, not upgraded |
| Founder supplies prices or costs without a source | Record them as `founder` or with status `assumption`. Ask for the invoice, quote or price page |
| Founder asks for projections or probabilities | Decline. Offer break-even and headroom arithmetic and labelled what-if scenarios |
| Payment provider availability unknown | Register a dependency with status `unverified`, the question, and `confirm_with: [payment-provider]` |
| Toolkit missing | Write the tables by hand with the same labels, and say the engine checks were not run |

## Validation checklist

- [ ] The profile, ledger and discovery register were read first. The inventory was produced.
- [ ] All nine blocks are present and every item has a basis. `analyze` shows 0 errors.
- [ ] Supply and demand are modelled separately, and the funnel holds measured counts only.
- [ ] Every payment, payout and regulatory dependency has a status, a question and who confirms it.
- [ ] Alternatives use defined scales, and there is one recommendation with its validation list.
- [ ] Stress results come from recorded inputs, and there are no probabilities.
- [ ] `business-model check <report> --spec <spec>` shows 0 errors. `doc` and `check` pass. The previews were inspected.

## Knowledge

[Index](../../knowledge/business-model/README.md) · [canvas](../../knowledge/business-model/business-model-canvas.md) · [value proposition](../../knowledge/business-model/value-proposition-canvas.md) · [patterns](../../knowledge/business-model/patterns-and-archetypes.md) · [marketplaces](../../knowledge/business-model/marketplace-business-models.md) · [platforms and network effects](../../knowledge/business-model/multi-sided-platforms.md) · [revenue](../../knowledge/business-model/revenue-architecture.md) · [costs](../../knowledge/business-model/cost-structure.md) · [liquidity and cold start](../../knowledge/business-model/liquidity-and-cold-start.md) · [pricing](../../knowledge/business-model/pricing-and-willingness-to-pay.md) · [innovation](../../knowledge/business-model/business-model-innovation.md) · [payments](../../knowledge/business-model/payment-infrastructure.md) · [validation](../../knowledge/business-model/validation-and-evidence.md)

## Templates and example

Templates are in [assets/templates/](assets/templates/):

- `business-model-spec.yaml`
- `business-model-canvas.md`
- `value-proposition-canvas.md`
- `revenue-architecture.md`
- `cost-structure.md`
- `marketplace-model.md`
- `model-comparison.md`
- `assumption-register.yaml`
- `stress-test.md`
- `decision-summary.md`

The spec format is in [references/business-model-spec.md](references/business-model-spec.md). A fictional end-to-end example is in [examples/fieldnote/business-model/](../../examples/fieldnote/business-model/fieldnote-business-model.yaml). It has a subscription with paid evidence, a rejected marketplace alternative and stress scenarios, and is described in [examples/README.md](examples/README.md).
