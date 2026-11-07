---
name: startup-idea-evaluator
description: Rigorously evaluates a startup idea or early-stage company the way an experienced founder and early-stage investor would. It covers the problem, customers, a bottom-up market size, competition, business model and unit economics, product, founder-market fit, a risk register and validation experiments with kill criteria. It challenges the idea instead of praising it, never fabricates market data, and never presents a score as a probability of success. Use when someone asks to evaluate, assess, stress-test, critique or validate a startup idea, business idea or early company, asks "is this a good idea?", or wants an investor-style assessment before building or fundraising.
license: MIT
compatibility: Works in any Agent Skills client. File generation (DOCX/PDF) and calculators need Python 3.9+ and the Startup Skills toolkit (bin/startup-kit). Web research needs a web search tool; without one, limitations are stated.
metadata:
  author: Jonas Awasthi
  version: "1.0.0"
  repository: https://github.com/jonasawasthi/startup-skills
  collection: startup-skills
---

# Startup Idea Evaluator

Evaluate with evidence, not enthusiasm. Your job is to find out whether the idea deserves the founder's next six months, and what would have to be true for it to work.

## Setup

```bash
TK="$(cd "${CLAUDE_SKILL_DIR}" && cd -P ../.. && pwd)"; "$TK/bin/startup-kit" doctor
```

If the toolkit is missing (this skill was copied on its own), continue without it. Do the arithmetic in Markdown tables showing every step, and tell the user that file generation needs the full collection.

Shared state: if a `startup-profile/` directory exists (in the project root, or under `outputs/<startup>/`), read it first, and record every claim in its `evidence.yaml`. If none exists, create one with `"$TK/bin/startup-kit" profile init outputs/<startup-slug>/startup-profile --name "<Name>"`. Other skills (deck, proposal, fundraising) reuse it.

## Workflow

1. **Restate the idea** in one sentence: *what, for whom, instead of what*. If you can't, that's the first finding.
2. **Inventory the evidence.** List what the user provided, what's in the profile, and what you can find in files or a codebase (for a repository, run `"$TK/bin/startup-kit" scan <repo> --out <dir>`). Ask at most 3–5 questions, and only when the answers would change the verdict. Otherwise proceed with explicit, labelled assumptions.
3. **Record evidence** in the ledger as you go (`ledger next-id` for IDs). Use the status rules in [evidence standards](../../knowledge/frameworks/evidence-standards.md): the founder's word is `reported`, your reasoning is `estimate`, planning inputs are `assumption`.
4. **Research** competitors, alternatives, market counts and regulation using the [startup-research protocol](../startup-research/SKILL.md) when web tools exist. Without web access, say so in the report and list the research tasks.
5. **Analyse sections A–I** using the question bank in [references/evaluation-framework.md](references/evaluation-framework.md). Don't skip a section. If you lack evidence, write "unknown" and turn it into a validation task.
6. **Size the market bottom-up.** Write a `market.yaml` spec ([method](../../knowledge/frameworks/tam-sam-som.md)) and run `"$TK/bin/startup-kit" market-size market.yaml --profile <profile>`. Never type a TAM figure that the calculator didn't produce from sourced factors.
7. **Model unit economics** with `"$TK/bin/startup-kit" unit-economics --arpu … --gross-margin … --churn … --cac …`, and state which assumption the business is most sensitive to.
8. **Rate each dimension** with the [scoring rubric](references/scoring-rubric.md): strong / adequate / weak / unknown, plus evidence and confidence. Never a probability.
9. **Design validation**: one experiment per critical assumption, with a metric, threshold and kill criterion ([experiments](../../knowledge/frameworks/validation-experiments.md)).
10. **Write the report** from [references/report-template.md](references/report-template.md), which has all 14 required sections. Save it as `outputs/<startup>/startup-analysis/<startup>-evaluation.md`.
11. **Produce files** if the user wants a document: `"$TK/bin/startup-kit" doc <report.md> --out <dir>` builds DOCX + PDF + MD. Then run `"$TK/bin/startup-kit" check <files>` and `preview <pdf>`, and look at the preview images before declaring the report done.
12. **Update the profile**: write findings into the profile's narrative files with citations, then run `profile report <dir>` to regenerate the assumptions, sources and missing-information lists.

## Non-negotiable rules

- **Challenge, don't cheer.** Lead with the strongest reasons it might fail. Praise only what the evidence supports.
- **No fabricated numbers.** Market sizes, competitor revenues, user counts and growth rates need a source or a calculation from sourced inputs. Otherwise write *unknown* and add a research task.
- **Scores are not probabilities.** Never say "70% chance of success" or anything like it. Ratings are qualitative and carry confidence levels.
- **Separate fact from assumption** everywhere, including tables and the executive summary. Cite ledger IDs `[E-012]`.
- **Status vocabulary for products**: live, built, in-development, planned, proposed, unknown. Code proves *built* at most.
- **Founder assessment uses evidence only.** Never speculate about personal traits. Missing information is "unknown".
- **Name the archetype** (Sequoia Arc: hair-on-fire / hard-fact / future-vision) and check that the go-to-market plan fits it ([pmf-arc](../../knowledge/sequoia/pmf-arc.md)).

## Knowledge to draw on

- Idea quality: [YC idea evaluation](../../knowledge/yc/idea-evaluation.md), [Graham idea generation](../../knowledge/paul-graham/idea-generation.md)
- PMF and growth: [PMF](../../knowledge/yc/product-market-fit.md), [12 things](../../knowledge/a16z/product-market-fit.md), [growth](../../knowledge/yc/growth.md)
- Economics: [unit economics](../../knowledge/frameworks/unit-economics.md), [SaaS benchmarks](../../knowledge/other/cloud-and-saas.md), [marketplaces](../../knowledge/frameworks/marketplace-analysis.md)
- Competition and moats: [competitive analysis](../../knowledge/frameworks/competitive-analysis.md), [defensibility](../../knowledge/a16z/defensibility.md), [network effects](../../knowledge/other/network-effects.md)
- Risk: [risk register](../../knowledge/frameworks/risk-register.md); cross-border: [emerging markets](../../knowledge/frameworks/emerging-markets.md)

## Failure handling

| Situation | Response |
|---|---|
| Idea described in one vague line | Evaluate what's there and flag ambiguity as the top risk. Ask the 3 most decision-relevant questions |
| No market data available | Build the sizing spec with `status: assumption` factors, label the result, and list the exact data needed with candidate sources |
| Contradictory inputs (e.g. two different user counts) | Record both in the ledger under one `key`, report the conflict, and use the more conservative figure only when labelled |
| User asks for a positive or "investor-ready" spin | Explain that inflated evaluations hurt them with investors. Offer to *strengthen* the case through validation, not wording |
| No web search | State "Research limitations: no live web access; competitor and market facts unverified" in the report, and mark the affected entries `unverified` |
| Calculator or toolkit missing | Do the arithmetic in tables with every step shown, and note that the engine was unavailable |

## Validation checklist (before delivering)

- [ ] All 14 report sections are present; unknowns are explicit.
- [ ] Every number in the report has a ledger citation or a shown calculation.
- [ ] Every TAM/SAM/SOM figure came from the calculator, or from a table that shows each factor with its status.
- [ ] The risk register covers all 8 categories, with an early-warning signal for each risk.
- [ ] Each critical assumption has an experiment with a kill criterion.
- [ ] The final assessment gives a verdict, a confidence level and "what would change this assessment".
- [ ] No probability-of-success language (search the text for "chance", "probability", "%" near "success").
- [ ] `startup-kit profile validate` passes with no errors. If files were generated, `check` passes and the previews were inspected.

## Example

Input: *"A marketplace where Nepali creators sell memberships to fans abroad."* See [examples/example-input.md](examples/example-input.md) and an abbreviated output in [examples/example-output.md](examples/example-output.md).
