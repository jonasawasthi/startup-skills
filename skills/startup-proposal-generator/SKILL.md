---
name: startup-proposal-generator
description: Writes comprehensive, professional startup proposals and business plans as DOCX and PDF. These are substantive business documents, not pitch decks turned into paragraphs. It adapts up to 28 sections to the proposal type (general, investor, strategic partnership, accelerator application, government or grant, corporate collaboration, internal business plan) and the audience. It grounds every claim in the shared startup profile and evidence ledger, includes financial assumptions and projections from a live-formula model, and keeps assumptions labelled. Use when someone asks for a startup proposal, business plan, investment proposal, partnership or collaboration proposal, grant or government proposal, accelerator application or a detailed company document for a specific reader.
license: MIT
compatibility: Requires the Startup Skills toolkit (bin/startup-kit; Python 3.9+ with python-docx, reportlab, matplotlib, openpyxl) for DOCX/PDF/XLSX output. Works best after the startup-idea-evaluator or pitch-deck-maker has populated a startup profile.
metadata:
  author: Jonas Awasthi
  version: "1.0.0"
  repository: https://github.com/jonasawasthi/startup-skills
  collection: startup-skills
---

# Startup Proposal Generator

A proposal is an argument written for one reader. It has to stand on its own: someone who has never met the founders should understand the company, believe the evidence, and know exactly what is being asked of them.

## Setup

```bash
TK="$(cd "${CLAUDE_SKILL_DIR}" && cd -P ../.. && pwd)"; "$TK/bin/startup-kit" doctor
```

Outputs go to `outputs/<startup>/business-proposal/`. Read the shared profile at `outputs/<startup>/startup-profile/` (or create it, as described in the idea-evaluator skill).

## Workflow

1. **Identify the reader and the decision.** Who reads it, what they decide, by when, and with what criteria. Choose the proposal type in [references/proposal-types.md](references/proposal-types.md). It sets the sections, length, tone and theme.
2. **Gather evidence.**
   - Read the profile and ledger, plus any evaluation, deck spec or codebase inventory already produced.
   - If a codebase exists and products.md is empty, follow the pitch-deck-maker's [codebase procedure](../pitch-deck-maker/references/codebase-intelligence.md).
   - Run `"$TK/bin/startup-kit" profile missing <profile>` and ask the founder for the gaps that matter for *this* reader.
3. **Build the numbers.**
   - Market: run `market-size` from a sourced spec.
   - Financials: write `model.yaml` (see the [model format](../business-document-generator/references/financial-model.md)) and run `"$TK/bin/startup-kit" model model.yaml --profile <profile> --out <dir>/financial-model.xlsx`. Use the summary JSON for the projection tables and charts.
   - Build conservative, base and ambitious scenarios when the reader evaluates financial risk (investors, grant committees).
4. **Outline**: one line per section, adapted from [references/section-guide.md](references/section-guide.md). Drop sections that don't serve this reader. Never pad.
5. **Write** the proposal in Markdown+, starting from [assets/proposal-template.md](assets/proposal-template.md). Write in full prose paragraphs, with tables where comparison helps. Cite `[E-…]` for every factual claim. Put assumptions in `> [!ASSUMPTION]` callouts or in qualified sentences. Follow [references/writing-style.md](references/writing-style.md).
6. **Build and validate**:
   ```bash
   "$TK/bin/startup-kit" doc proposal.md --out <dir>
   "$TK/bin/startup-kit" check <dir>/*.docx <dir>/*.pdf <dir>/*.xlsx
   "$TK/bin/startup-kit" preview <dir>/<proposal>.pdf
   ```
   Fix every build error. Inspect the previews: cover, TOC, financial tables, charts, appendix.
7. **Deliver** the DOCX, PDF, MD and XLSX, plus a short note listing open assumptions and missing information.

## The 28 sections (adapt them; don't force them)

Cover · executive summary · company overview · vision and mission · problem · market opportunity · target customers · products and services · product architecture · value proposition · business model · revenue strategy · competitive analysis · market positioning · go-to-market · marketing and distribution · operations · technology and infrastructure · roadmap and milestones · team and organisation · financial assumptions · financial projections · funding requirements · use of funds · risk assessment · long-term opportunities · conclusion · references and appendices.

## Non-negotiable rules

- **A proposal is not a deck in paragraphs.** Explain mechanisms (how revenue is generated, how operations scale, why the plan is credible), not slogans.
- **Financial projections are scenarios.** Label them, show the assumptions table, and never present projections as forecasts or commitments.
- **Product status is explicit** (live / built / in development / planned / proposed) in the products, architecture and roadmap sections.
- **Never invent** partners, letters of support, customers, revenue, team members or funding. Grant and government proposals often require these. If they don't exist, list them as *to obtain*.
- **Match the reader's format.** If a funder, accelerator or partner has a template or question list, follow it exactly and map our content to it. Their structure overrides ours.
- **Private by default.** Real startup proposals stay in `outputs/` (gitignored).

## Failure handling

| Situation | Response |
|---|---|
| Thin profile | Write the sections the evidence supports, mark the others "To be completed", and give a prioritised missing-information list |
| Funder template supplied | Mirror its headings and word limits. Put extra material in the appendices |
| No financial data | Build an assumptions-only model, label every figure, and recommend validating the top three drivers |
| Contradictory sources | Report the conflict in the risk section and in the build notes. Don't silently pick one |
| Requested length is far beyond the evidence | Write a shorter, stronger document and explain why |

## Validation checklist

- [ ] Reader, decision and proposal type are stated in the executive summary.
- [ ] Every number is cited, or shown as calculated from cited inputs.
- [ ] The financial assumptions table matches the XLSX Assumptions sheet.
- [ ] The risk section covers market, product, technical, financial, regulatory, operational, distribution and team.
- [ ] Build: 0 errors. `check` OK. Previews inspected.
