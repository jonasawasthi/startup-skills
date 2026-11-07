# Startup Skills

**Evidence-based startup intelligence for Claude Code.** Six composable Agent Skills and a tested document engine help founders go from **idea → evaluation → validation → strategy → product analysis → business plan → pitch deck → fundraising**. They never invent the numbers.

[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

---

## Why this exists

Most AI pitch-deck tools produce generic slides full of plausible-sounding statistics. Investors see through that immediately. Startup Skills works the other way round:

- **It reads your actual product.** The pitch deck maker scans your repository (apps, routes, data model, roles, integrations, payment code, git activity) and labels every product as `live`, `built`, `in development`, `planned` or `proposed`, with file-path evidence.
- **Every claim traces to an evidence ledger.** Each figure carries its source, date, confidence and status (`verified`, `reported`, `estimate`, `assumption`, `unverified`, `contradicted`).
- **The renderer enforces honesty in code.** An unsourced chart fails the build. A metric without evidence fails the build. An assumption on a slide gets an "Assumption" label automatically. Planned features cannot render as shipped.
- **The output is professional.** Editable PPTX with native charts, a matching PDF, DOCX/PDF documents with tables of contents and page numbers, and XLSX models with live formulas, all in a consistent, editorial design system tuned to each audience.

## Skills

| Skill | What it does | Outputs |
|---|---|---|
| [`startup-idea-evaluator`](skills/startup-idea-evaluator/SKILL.md) | Investor-grade evaluation: problem, customers, bottom-up market size, competition, unit economics, founder–market fit, risk register, validation experiments with kill criteria. Challenges ideas; never presents scores as probabilities | 14-section report (MD/DOCX/PDF) |
| [`pitch-deck-maker`](skills/pitch-deck-maker/SKILL.md) ⭐ | Codebase-grounded investor decks for idea → growth stage, with a stage- and audience-specific narrative | PPTX + PDF, short variant, speaker notes, narrative, investor Q&A, sources appendix, missing-info checklist |
| [`startup-proposal-generator`](skills/startup-proposal-generator/SKILL.md) | Substantive proposals and business plans (investor, partnership, accelerator, grant, corporate, internal) with up to 28 sections | DOCX + PDF + XLSX model |
| [`business-document-generator`](skills/business-document-generator/SKILL.md) | The rendering engine: Markdown+ → DOCX/PDF/MD, YAML → PPTX, YAML → XLSX, audience themes, validation | All formats |
| [`startup-research`](skills/startup-research/SKILL.md) | Source-disciplined research: primary sources first, dated, triangulated, conflicts surfaced | Research brief + bibliography |
| [`fundraising-strategist`](skills/fundraising-strategist/SKILL.md) | Readiness, raise planning, evidence-based investor fit (never implies interest), outreach, diligence and negotiation prep | Readiness, target list, outreach drafts, data-room index |

The full catalogue is in [docs/skills-catalog.md](docs/skills-catalog.md).

## Installation

**Requirements:** Python 3.9+ and Claude Code. Optional: poppler (`pdftoppm`) for PDF previews.

### Option A: Claude Code plugin (recommended)

```text
/plugin marketplace add jonasawasthi/startup-skills
/plugin install startup-skills@startup-skills
```

Then create the Python environment once (the plugin cache path is shown by `/plugin`):

```bash
<plugin-dir>/scripts/setup.sh
```

Skills appear as `/startup-skills:pitch-deck-maker` and so on, and Claude also invokes them automatically when relevant.

### Option B: clone and symlink

```bash
git clone https://github.com/jonasawasthi/startup-skills.git
cd startup-skills
scripts/setup.sh                        # creates .venv and runs the dependency check
scripts/install.sh                      # all skills → ~/.claude/skills (symlinks)
scripts/install.sh pitch-deck-maker     # or individual skills
scripts/install.sh --project ~/code/my-startup   # into a project's .claude/skills
```

Symlinks keep every skill connected to the shared engine and knowledge base. Remove them with `scripts/install.sh --uninstall`.

### Option C: a single skill folder

Copying one `skills/<name>` folder works for the instructions and references. File generation needs the rest of the toolkit, and the skill tells you when it's missing.

## Usage

Ask naturally, or call a skill directly:

```text
Evaluate this idea: a marketplace where Nepali creators sell memberships to fans abroad.
/startup-skills:pitch-deck-maker Build a seed deck from this repository for angel investors.
/startup-skills:startup-proposal-generator Write a partnership proposal for <company>, using our profile.
/startup-skills:startup-research Size the market for B2B payroll software in Kenya, bottom-up.
/startup-skills:fundraising-strategist Is <investor> a fit for us? Use public information only.
```

### Typical workflow

1. **Evaluate**: `startup-idea-evaluator` creates `outputs/<startup>/startup-profile/` (the shared profile and evidence ledger).
2. **Research**: `startup-research` adds dated, sourced entries to the ledger.
3. **Deck**: `pitch-deck-maker` scans the codebase, writes a deck spec, builds the PPTX/PDF and inspects the previews.
4. **Proposal**: `startup-proposal-generator` writes the business plan and the financial model from the same evidence.
5. **Raise**: `fundraising-strategist` assesses readiness, investor fit and outreach.

All skills read and write the same profile, so the deck, proposal and plan always tell the same story.

### The engine directly

```bash
bin/startup-kit doctor                                   # dependencies and fonts
bin/startup-kit profile init outputs/acme/startup-profile --name Acme
bin/startup-kit scan ~/code/acme --out outputs/acme/evidence
bin/startup-kit market-size market.yaml --profile outputs/acme/startup-profile
bin/startup-kit unit-economics --arpu 60 --gross-margin 0.8 --churn 0.03 --cac 400
bin/startup-kit model model.yaml --profile outputs/acme/startup-profile --out model.xlsx
bin/startup-kit deck deck.yaml --out outputs/acme/investor-pitch [--variant short]
bin/startup-kit doc proposal.md --out outputs/acme/business-proposal
bin/startup-kit check <files…>   &&   bin/startup-kit preview deck.pdf
```

Try the fictional example: `bin/startup-kit deck examples/fieldnote/deck/fieldnote-seed.yaml --out /tmp/fieldnote`.

## Output formats

| Format | Library | Highlights |
|---|---|---|
| PPTX | python-pptx | Editable text, native data-editable charts, native tables, speaker notes, metadata |
| PDF (slides) | reportlab | The same layout as the PPTX (one layout engine, two renderers), embedded fonts, vector charts |
| DOCX | python-docx | Cover, Word TOC field, headers and footers, Page X of Y, tables with repeating headers, callouts, hyperlinks |
| PDF (documents) | reportlab | TOC with page numbers, bookmarks, Page X of Y, figure captions with sources |
| XLSX | openpyxl | Driver-based model, live formulas, inputs/formulas colour convention, assumptions with status and evidence |
| Markdown | — | The source of record, with an auto-generated sources appendix |

Every artifact is re-opened with an independent reader by `startup-kit check`. The test suite recalculates XLSX formulas and compares them against the Python model.

## Repository layout

```
skills/            six Agent Skills (SKILL.md + references/ + examples/)
knowledge/         attributed summaries (YC, Paul Graham, Sequoia, a16z, NFX, BVP, Stripe Atlas, HBR) + original frameworks
lib/startup_kit/   the engine: evidence ledger, scanner, calculators, theme, renderers, validators, CLI
templates/         the startup-profile template
examples/fieldnote fictional end-to-end example (ledger, deck, proposal, model)
docs/              architecture, design system, research notes, skills catalogue
tests/             45 tests: unit, guards (fabrication, contradictions, incomplete data), golden builds, CLI integration
scripts/           setup, install, skill-spec validator, link checker
outputs/           your generated work: gitignored, private by default
```

## Quality assurance

```bash
.venv/bin/python -m pytest          # 45 tests
python3 scripts/validate_skills.py  # Agent Skills spec compliance
python3 scripts/check_links.py      # re-verify knowledge-base URLs (title-matched)
claude plugin validate .            # plugin + marketplace manifests
```

Compatibility was verified on Claude Code 2.1.270 (macOS) by loading the plugin with `--plugin-dir`, confirming all six skills appear as `startup-skills:*`, and invoking a skill whose setup command resolved the toolkit and passed `doctor`.

## Attribution and source policy

The knowledge base contains **original summaries and frameworks** with attribution and links. It does not reproduce essays, articles or books. Each file records its sources, the date checked, and whether it is an attributed summary or original analysis. Summaries of Y Combinator, Paul Graham, Sequoia, a16z and other material reflect their *public* writing and do not describe any firm's private investment process. See [knowledge/README.md](knowledge/README.md).

## Contributing, security, roadmap

[CONTRIBUTING.md](CONTRIBUTING.md) · [SECURITY.md](SECURITY.md) · [CHANGELOG.md](CHANGELOG.md) · [ROADMAP.md](ROADMAP.md)

## License

[MIT](LICENSE) © 2026 Jonas Awasthi. Generated documents belong to their authors. Third-party sources remain the property of their owners.

> Startup Skills produces analysis, not legal, tax or investment advice.
