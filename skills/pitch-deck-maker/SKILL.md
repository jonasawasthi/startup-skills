---
name: pitch-deck-maker
description: Builds investor-ready pitch decks as an editable PPTX and a matching PDF, with speaker notes, a slide-by-slide narrative, investor Q&A, a sources appendix and a missing-information checklist. It is grounded in the startup's actual codebase, documents and verified research. It inspects repositories to map products, architecture, data models, user roles, integrations and revenue code, and it labels each product as live, built, in development, planned or proposed. It never invents traction, customers, revenue or market figures, and its renderer blocks unsourced charts and labels unverified claims. It chooses the slide count and narrative by stage (idea, pre-seed, seed, Series A, growth) and by audience. Use when someone asks for a pitch deck, investor deck, investor presentation, fundraising slides, demo-day deck or a short teaser deck, or wants an existing deck rebuilt from their real product.
license: MIT
compatibility: Requires Python 3.9+ with python-pptx and reportlab via the Startup Skills toolkit (bin/startup-kit). PDF previews need poppler (pdftoppm). Codebase analysis needs read access to the startup repository.
metadata:
  author: Jonas Awasthi
  version: "1.0.0"
  repository: https://github.com/jonasawasthi/startup-skills
  collection: startup-skills
---

# Pitch Deck Maker

Build the deck a serious investor would respect: specific to this company, honest about stage, and visually calm. Every claim on every slide traces to evidence.

## Setup

```bash
TK="$(cd "${CLAUDE_SKILL_DIR}" && cd -P ../.. && pwd)"; "$TK/bin/startup-kit" doctor
```

Working directory for outputs: `outputs/<startup>/investor-pitch/` (gitignored). Shared profile: `outputs/<startup>/startup-profile/`, or create it with `profile init`.

## Workflow

### 1. Understand the company from evidence (codebase intelligence)

If a repository is available, follow [references/codebase-intelligence.md](references/codebase-intelligence.md):

1. `"$TK/bin/startup-kit" scan <repo> --out outputs/<startup>/investor-pitch/evidence`, then read `codebase-inventory.md`.
2. Read the READMEs, docs, CLAUDE.md/AGENTS.md, schema files, route trees, payment/pricing code, deployment configs, and recent git history the inventory points to.
3. Build a **product map**. For each product, record its purpose, users and roles, capabilities, dependencies, revenue mechanics and **status** (`live | built | in-development | planned | proposed | unknown`), with file-path evidence. Code proves *built* at most. *Live* needs deployment and usage evidence.
4. Record findings in the ledger (`source.type: codebase`, `source.ref: path:line`).
5. Never read `.env` files or print secrets. The scanner reports variable *names* only.

If there is no repository, use the documents and conversation, and say that product status is founder-reported.

### 2. Fill gaps honestly

List what the deck needs but the evidence lacks: traction numbers, revenue, team bios, the raise amount, customer quotes, screenshots. **Ask the founder.** Whatever stays unknown goes into the missing-information checklist. Never fill it with plausible numbers.

### 3. Choose the narrative

Pick the stage, the audience and an evidence profile (traction-led, thesis-led, technology-led or ecosystem-wedge) using [references/narrative.md](references/narrative.md). Write a **one-line-per-slide outline with action titles** first. Every title should be a sentence the investor could repeat. Check the outline against Seibel's seven questions ([YC pitch](../../knowledge/yc/pitch.md)) and Sequoia's sections ([framework](../../knowledge/sequoia/pitch-framework.md)).

### 4. Write the deck spec

Write `deck.yaml` following [references/deck-spec.md](references/deck-spec.md). It has 21 slide types: cover, statement, points, split, products, screenshot, metrics, chart, market, comparison, positioning, roadmap, diagram, team, ask, table, quote, section, closing and sources. In it:

- attach `evidence: [E-…]` to every number, chart, metric, market layer and quote;
- give every product and roadmap item a `status`;
- write `notes` (speaker notes) for every slide. Notes carry the detail that the slide leaves out;
- mark 5–7 slides `short: true` for the teaser variant;
- apply the startup's brand (`deck.brand`: accent, fonts, logo) when the scan finds brand colours or logos.

### 5. Build, inspect, iterate

```bash
"$TK/bin/startup-kit" deck deck.yaml --out <dir>                  # full deck: PPTX + PDF + narrative + report
"$TK/bin/startup-kit" deck deck.yaml --out <dir> --variant short  # teaser
"$TK/bin/startup-kit" preview <dir>/<deck>.pdf                   # PNG contact sheets
"$TK/bin/startup-kit" check <dir>/<deck>.pptx <dir>/<deck>.pdf
```

- Fix **every error** (text overflow, unsourced chart, missing evidence, unknown status). Don't suppress errors.
- **Look at every preview image** (Read the PNGs). Check hierarchy, crowding, orphans, balance, and whether each slide makes exactly one point. Revise the spec and rebuild until it reads like a professional VC deck.
- Resolve warnings, or explain them in the final report (for example, a screenshot placeholder kept because no screenshot exists).

### 6. Write the companion documents

In `outputs/<startup>/investor-pitch/`:
- `<deck>-narrative.md` (generated): the slide-by-slide story plus notes.
- `investor-qa.md`: 15–30 likely questions with honest suggested answers ([question bank](references/investor-qa.md)). Answers to questions about weaknesses acknowledge them.
- `missing-information.md`: the build report's missing items plus your own gaps, grouped by owner.
- The sources appendix is the deck's last slide (`type: sources`, auto-filled from cited evidence).

## Non-negotiable rules

1. **Never invent** customers, users, revenue, growth, partnerships, funding, valuations, testimonials, logos or market sizes.
2. **Never present planned features as existing.** Status pills are mandatory on product and roadmap slides.
3. **"Product-market fit" only with level-3+ evidence** ([PMF ladder](../../knowledge/yc/product-market-fit.md)). Otherwise say "early usage" or "pilots".
4. **No decorative charts.** A chart needs real data and a source. Cumulative charts are never presented as growth.
5. **Market sizes come from the calculator** (`market-size`) with shown factors, or are labelled with their status.
6. **Labels travel with claims.** The renderer adds "Reported", "Estimate" or "Assumption" pills automatically. Never remove them by changing a claim's evidence status without new evidence.
7. **The ask is the founder's decision.** If the amount is unknown, the slide shows a placeholder and it goes on the missing list.
8. **Private information stays private.** Decks for a real startup go only to the gitignored `outputs/` directory.

## Design standards

Follow [references/design.md](references/design.md) and the repository's [design system](../../docs/design-system.md): one idea per slide, action titles, minimal text (≤ 70 words, enforced as a warning), one accent colour, real screenshots, generous white space, no gradients, no clip-art and no generic AI imagery. Choose the theme by audience (`venture`, `angel`, `accelerator`, `corporate`, `institutional`, `internal`) and override it with brand tokens.

## Failure handling

| Situation | Response |
|---|---|
| No repo access | Ask for the path. Meanwhile, build from documents and mark product status `reported` |
| Repo too large or unusual stack | The scanner caps file counts. Read manifests and docs directly, and note any limits on coverage |
| No traction | Use a progress or milestones slide (what's built, pilots, LOIs with evidence). Never pad it with vanity metrics |
| No screenshots | The renderer draws labelled placeholders and logs them as missing. Offer to capture screens if the app can be run locally |
| Conflicting numbers in sources | Surface the conflict to the founder. Use one figure only after it's resolved, and record the resolution in the ledger |
| Founder insists on an unsupported claim | Explain the credibility risk. Include it only as a labelled assumption or a goal, never as fact |
| Build errors you can't resolve | Report them plainly with the build report. Don't deliver a deck that fails `check` |

## Validation checklist

- [ ] `deck` build: **0 errors**; every remaining warning is explained.
- [ ] Every slide preview was inspected; there are no overflows, orphans or crowding.
- [ ] Every number traces to the ledger; every product and roadmap item has a status.
- [ ] Notes exist for every content slide. The narrative, Q&A and missing-information files are written.
- [ ] The short variant is built when useful (fundraising outreach, accelerators).
- [ ] `check` passes for the PPTX and PDF.

## Example

The fictional *Fieldnote* seed deck: [spec](../../examples/fieldnote/deck/fieldnote-seed.yaml) and [evidence ledger](../../examples/fieldnote/startup-profile/evidence.yaml). Build it with `"$TK/bin/startup-kit" deck examples/fieldnote/deck/fieldnote-seed.yaml --out /tmp/fieldnote`.
