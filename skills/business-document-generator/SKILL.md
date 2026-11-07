---
name: business-document-generator
description: A reusable document engine that turns structured Markdown into professionally designed DOCX, PDF and Markdown documents, builds PPTX slides from a YAML spec, and produces XLSX financial models with live formulas. Documents include cover pages, tables of contents, headers and footers, page numbers, tables, themed charts, callouts, hyperlinks, evidence citations, an automatic sources appendix and document metadata. Themes are tuned per audience (venture, angel, accelerator, corporate, government/institutional, internal), and every generated file is validated by re-opening it. Use when someone needs a business document such as a memo, report, one-pager, investor update, business plan, data-room index or financial model as Word, PDF, PowerPoint, Excel or Markdown, or when another skill needs to render its output into files.
license: MIT
compatibility: Requires Python 3.9+ with python-docx, python-pptx, openpyxl, reportlab, matplotlib and pypdf via the Startup Skills toolkit (bin/startup-kit; run scripts/setup.sh). Optional poppler (pdftoppm) for previews and the formulas package for spreadsheet recalculation checks.
metadata:
  author: Jonas Awasthi
  version: "1.0.0"
  repository: https://github.com/jonasawasthi/startup-skills
  collection: startup-skills
---

# Business Document Generator

One source document can be rendered into several professional formats, and every output is validated. The other skills in this collection call this engine. You can also use it directly.

## Setup

```bash
TK="$(cd "${CLAUDE_SKILL_DIR}" && cd -P ../.. && pwd)"; "$TK/bin/startup-kit" doctor
```

If `doctor` reports missing packages, run `"$TK/scripts/setup.sh"`, which creates `$TK/.venv`.

## Choose the right path

| Need | Write | Build with |
|---|---|---|
| Report, proposal, memo, plan, one-pager, update | Markdown+ file ([dialect](references/markdown-dialect.md)) | `startup-kit doc file.md --out DIR [--formats docx,pdf,md]` |
| Slides | Deck spec YAML ([pitch-deck-maker spec](../pitch-deck-maker/references/deck-spec.md)) | `startup-kit deck deck.yaml --out DIR` |
| Financial model | Model YAML ([format](references/financial-model.md)) | `startup-kit model model.yaml --profile PROFILE --out FILE.xlsx` |
| Market sizing table | Market YAML ([method](../../knowledge/frameworks/tam-sam-som.md)) | `startup-kit market-size market.yaml --profile PROFILE` |

Start from a template in [assets/templates/](assets/templates/):
- `memo.md`
- `one-pager.md`
- `investor-update.md`
- `report.md`
- `data-room-index.md`
- `financial-model.yaml`

## Workflow

1. **Pick the document type and audience.** The audience sets the theme ([themes](references/themes.md)). Government and grant documents get numbered sections and an institutional cover. Investor documents get the editorial venture theme.
2. **Write the source** with YAML front matter (`title`, `subtitle`, `company`, `date`, `doc_type`, `audience`, `confidentiality`, `profile`). Cite evidence inline as `[E-001]`. Add charts as fenced ```` ```chart ```` YAML blocks, each with a `source` or `evidence`.
3. **Build** with the relevant command. The build report lists errors and warnings: missing evidence IDs, assumptions without qualifying language, charts without sources, missing images.
4. **Validate**: `startup-kit check <files>`. It re-opens each file with an independent reader and checks metadata, page numbering, off-slide shapes, placeholder text and formula errors.
5. **Inspect visually**: `startup-kit preview <file.pdf>`, then read the PNG contact sheets. Fix layout problems in the source and rebuild.
6. **Deliver** with the build report summary, so the user knows about every unresolved warning.

## Format capabilities

| Feature | DOCX | PDF | MD | PPTX | XLSX |
|---|---|---|---|---|---|
| Cover page (editorial / institutional / minimal) | ✓ | ✓ | front matter | cover slide | README sheet |
| Table of contents | Word TOC field, pre-filled | ✓ with page numbers | — | — | — |
| Headers, footers, "Page X of Y" | ✓ | ✓ | — | footer + slide no. | — |
| Tables | ✓ (header row repeats) | ✓ (header repeats) | ✓ | native tables | ✓ |
| Charts | themed image + caption with source | same | chart block | native, data-editable charts | formulas |
| Hyperlinks | ✓ | ✓ | ✓ | — | — |
| Evidence citations → sources appendix | ✓ | ✓ | ✓ | sources slide | Sources sheet |
| Metadata (title, author, subject, keywords) | ✓ | ✓ | front matter | ✓ | ✓ |

## Rules

- **Design follows the audience.** Never use one generic design for every document ([design system](../../docs/design-system.md)).
- **No placeholder text ships.** `check` flags TODO, TBD, lorem, `[insert`, and "Screenshot needed". Resolve each one, or report it.
- **No unsourced charts or numbers.** The engine refuses charts without a source.
- **Assumptions keep their labels.** Citing an `assumption`, `estimate` or `unverified` entry needs qualifying language in the same sentence ("we assume", "estimated", "target"). The build warns otherwise.
- **Fonts**: Office files use universally installed fonts (Georgia, Arial) unless the brand requires otherwise. PDFs embed fonts.
- **Print-friendly**: A4 by default (`paper: letter` for US), with 2.3 cm margins and dark text on white.

## Failure handling

| Problem | Fix |
|---|---|
| `doctor` shows missing modules | Run `scripts/setup.sh`, or install `requirements.txt` into any Python ≥ 3.9 and set `STARTUP_KIT_PYTHON` |
| Build error "cites … but no ledger is configured" | Add `profile:` or `evidence:` to the front matter |
| Chart omitted | Fix the YAML (categories and values lengths, plus `source` or `evidence`) |
| Image not found | Paths are relative to the Markdown file |
| Word shows a pre-filled TOC without page numbers | Expected until fields update. Word prompts on open (`updateFields`); press F9 to refresh |
| No pdftoppm | Previews are unavailable; open the PDF instead and say so |

## Validation checklist

- [ ] Build report: 0 errors.
- [ ] `check`: all files OK; warnings explained.
- [ ] Previews inspected: cover, TOC, a table page, a chart page, the sources appendix.
- [ ] Metadata title and author set; confidentiality footer correct.
