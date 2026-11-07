# Architecture

Startup Skills is a collection of Claude Code Agent Skills backed by one small, tested Python engine. The skills hold the judgement: what to ask, how to reason and what not to claim. The engine holds the mechanics: scanning codebases, validating evidence, calculating market sizes and rendering documents. Keeping them separate lets each skill stay short and lets every skill share one implementation of the rules that matter most, such as "never present an assumption as a fact".

```
                ┌──────────────────────── skills/ (Agent Skills, SKILL.md) ───────────────────────┐
                │ startup-idea-evaluator  pitch-deck-maker  startup-proposal-generator           │
                │ business-document-generator  startup-research  fundraising-strategist          │
                └───────────────┬──────────────────────────────┬─────────────────────────────────┘
                     reads      │                              │ runs  bin/startup-kit <command>
                                ▼                              ▼
        knowledge/  (attributed summaries,        lib/startup_kit/  (Python engine)
        frameworks, source metadata)               ├─ evidence.py   evidence ledger: schema, conflicts, staleness
                                                   ├─ profile.py    startup-profile init / validate / status
        templates/startup-profile/                 ├─ scan.py       codebase intelligence (read-only, no secrets)
        (shared business model of one startup)     ├─ calc.py       bottom-up market sizing, unit economics
                                                   ├─ theme.py      design tokens, audience themes, brand override
                                                   ├─ render/       Canvas → PPTX + PDF from one layout
                                                   ├─ deck/         deck spec → layouts → PPTX/PDF, claim guard
                                                   ├─ docs/         Markdown+ → DOCX / PDF / MD
                                                   ├─ xlsx.py       driver-based financial model, live formulas
                                                   └─ inspect.py    artifact validation + PNG previews
```

## Design principles

1. **Evidence before narrative.** Every number that reaches a deck, proposal or investor email resolves to an entry in the *evidence ledger* (`evidence.yaml`). Each entry records its source, date, confidence and verification status. The renderers enforce this. A chart without a source fails the build. A claim linked to an assumption is labelled "Assumption" on the slide itself. A numeric claim with no evidence reference produces a warning.
2. **Status is explicit.** Products and features use one vocabulary everywhere: `live`, `built`, `in-development`, `planned`, `proposed`, `unknown`. It shows on roadmap slides, product slides and proposals. Planned work can never render as shipped.
3. **Skills are independent but share state.** Each skill works on its own. When several run for the same startup, they read and write the same `startup-profile/` directory, so the evaluator, deck, proposal and fundraising plan all describe the same company.
4. **Judgement in Markdown, mechanics in code.** SKILL.md files stay under 500 lines and link to `references/` files one level deep, following the Agent Skills specification. Anything deterministic, such as arithmetic, layout, file validation or repository scanning, lives in the engine and has tests.
5. **One layout, two renderers.** Slides are laid out once against an abstract `Canvas`. A PPTX canvas emits editable shapes, native tables and native charts. A PDF canvas draws the same geometry with reportlab. Text is measured with real font metrics, so overflow is caught at build time and does not first show up in PowerPoint.
6. **No silent failure.** Missing inputs become a *missing-information checklist*, contradictions are reported as conflicts, and outdated sources get flagged.
7. **Private data stays private.** Startup analyses go to `outputs/<startup>/`, which is gitignored by default. The scanner reports environment variable *names* only and never reads `.env` files.

## Distribution model

| Mode | How | Shared resources resolved via |
|---|---|---|
| Claude Code plugin (recommended) | `/plugin marketplace add jonasawasthi/startup-skills` then `/plugin install startup-skills@startup-skills` | Whole repo is cached together; skills locate the toolkit root from `${CLAUDE_SKILL_DIR}/../..` |
| Clone + installer | `scripts/install.sh [skill…]` symlinks skills into `~/.claude/skills/` | Physical path resolution (`cd -P`) from the symlinked skill dir |
| Single skill, copied | Copy `skills/<name>` only | Skill degrades gracefully: instructions and `references/` work; engine commands report that the toolkit is missing |

Each SKILL.md resolves the toolkit root with:

```bash
TK="$(cd "${CLAUDE_SKILL_DIR}" 2>/dev/null && cd -P ../.. && pwd)"; "$TK/bin/startup-kit" doctor
```

## Frontmatter policy

Skills use only the portable Agent Skills fields: `name`, `description`, `license`, `compatibility` and `metadata`. Claude Code accepts more fields, but claude.ai uploads and the Skills API reject unknown keys. `scripts/validate_skills.py` enforces these rules:

- `name` is 1–64 characters long, uses only `[a-z0-9-]`, has no leading, trailing or doubled hyphens, and equals the directory name.
- `description` is 1–1024 characters long and says both *what* the skill does and *when* to use it.
- SKILL.md has fewer than 500 lines, and every relative link resolves.

## Data model: the startup profile

```
startup-profile/
  profile.yaml        identity, stage, audience defaults, brand
  evidence.yaml       the evidence ledger (single source of truth for claims)
  company.md problem.md solution.md customers.md market.md competitors.md
  business-model.md products.md traction.md team.md roadmap.md financials.md
  assumptions.md      human-readable view of assumption entries
  sources.md          bibliography (generated from the ledger)
  missing-information.md
```

Narrative files cite ledger IDs inline, for example `Creators keep 90% of revenue [E-014]`. `startup-kit profile validate` checks the following:

- Every cited ID exists.
- No entry with status `assumption` is cited with factual language unless the text marks it.
- Stale sources are flagged.
- Contradictory values for the same `key` are flagged.

### Evidence entry

```yaml
- id: E-014
  claim: Creator revenue share on memberships
  key: pricing.creator_share        # optional, groups entries that should agree
  value: 0.90
  unit: ratio
  status: verified        # verified | reported | estimate | assumption | unverified | contradicted
  confidence: high        # high | medium | low
  source:
    type: codebase        # codebase | document | founder | web | calculation | interview | dataset
    ref: apps/web/lib/fees.ts:12
    url:
    published:            # date the source was published (web/docs)
    accessed: 2026-11-07
  owner: founder          # who stands behind the assumption, if known
  updated: 2026-11-07
  notes:
```

## Testing strategy

- **Unit tests** for the ledger, calculators, scanner, Markdown parser and text fitting.
- **Golden builds** of the bundled example startup (fictional, *Fieldnote*). Each build generates every artifact type and opens it again with an independent reader (python-pptx, python-docx, pypdf, openpyxl plus `formulas`).
- **Guard tests** check that fabrication is blocked: unsourced charts fail, assumption claims get labels, contradictions surface, and missing inputs produce checklists.
- **Spec tests** validate every SKILL.md against the Agent Skills rules.
- **Visual review** renders PDFs to PNG with `pdftoppm`, so slide and page previews can be inspected.
