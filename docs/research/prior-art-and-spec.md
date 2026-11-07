# Phase 1 research: specification and prior art

Date checked: 2026-11-07.

## Official skill specification

| Source | URL | Key findings used |
|---|---|---|
| Claude Code skills docs | https://code.claude.com/docs/en/skills | Skill locations (personal `~/.claude/skills`, project `.claude/skills`, plugin `<plugin>/skills`); symlinked skill folders are supported; `${CLAUDE_SKILL_DIR}` substitution; SKILL.md < 500 lines; supporting files loaded on demand; for claude.ai uploads / Skills API only `name`, `description`, `license`, `compatibility`, `metadata`, `allowed-tools` are accepted |
| Agent Skills specification | https://agentskills.io/specification | `name` 1–64 chars, `[a-z0-9-]`, no leading/trailing/double hyphen, must equal directory; `description` 1–1024 chars, says what + when; `compatibility` ≤ 500 chars; `metadata` string→string map; `scripts/`, `references/`, `assets/` conventions; file references one level deep |
| Plugin marketplaces | https://code.claude.com/docs/en/plugin-marketplaces | `.claude-plugin/marketplace.json` needs `name`, `owner`, `plugins[]` with `name` + `source`; relative sources must not use `..`; entry name must equal the plugin manifest name; `claude plugin validate <dir>` |

## Prior art reviewed

| Project | License | What it does | Reuse decision |
|---|---|---|---|
| anthropics/skills, document skills (`docx`, `pptx`, `xlsx`, `pdf`). https://github.com/anthropics/skills | The README describes the skills as open source; check each skill folder's LICENSE before reusing | General-purpose Office/PDF manipulation | **Not copied.** Our renderers are purpose-built: one layout model for PPTX + PDF, plus evidence enforcement. Those skills work well beside ours for editing existing files. |
| Pitch-deck skills listed on community registries (e.g. claudskills.com "pitch-deck-creator") | Varies or unclear | Prompt-only slide outlines | **Not reused.** Prompt-only, with no codebase analysis, evidence model or file generation. They confirm the gap this project fills. |
| gsarig/skills, markomitranic/skills | MIT / unspecified | Personal skill collections | Read for structure conventions only. |

**Gap identified:** the existing skills we found generate generic slides from a prompt. None of them (a) inspect the startup's actual codebase, (b) track evidence with verification status, (c) block unsourced statistics at render time, or (d) share one business model across a deck, a proposal and a fundraising plan. Those four capabilities are the core of this project.

## Third-party libraries

| Library | License | Use |
|---|---|---|
| python-pptx | MIT | Editable PPTX with native charts and tables |
| python-docx | MIT | DOCX with styles, fields (TOC, page numbers) and hyperlinks |
| reportlab (open-source edition, < 4.3 for Python 3.9) | BSD | PDF for decks and documents |
| openpyxl | MIT | XLSX financial models with live formulas |
| matplotlib | PSF-style (BSD-compatible) | Chart images for DOCX/PDF documents |
| PyYAML | MIT | Profile and spec files |
| pypdf | BSD | PDF validation |
| formulas (optional, tests) | EUPL-1.2 | Recalculating XLSX formulas during validation. Optional dependency, not vendored. |

## Source verification method

Every knowledge-base URL was fetched on the check date. Many YC Library URLs route by ID prefix and ignore the slug, so a wrong slug can still return HTTP 200 for an unrelated article. We therefore verified **page titles**, not status codes alone. Only title-matched URLs are cited. `scripts/check_links.py` repeats this check.
