# Changelog

All notable changes follow [Keep a Changelog](https://keepachangelog.com/). The project uses semantic versioning.

## [1.0.0] — 2026-11-07

### Added
- Six Agent Skills: `startup-idea-evaluator`, `pitch-deck-maker`, `startup-proposal-generator`, `business-document-generator`, `startup-research`, `fundraising-strategist`.
- `startup_kit` engine and the `bin/startup-kit` CLI:
  - evidence ledger with status, confidence, staleness and conflict detection, plus a qualifier check for assumptions cited as facts;
  - read-only codebase scanner (units, frameworks, integrations, routes, schemas, roles, docs, brand tokens, unfinished-work markers, git activity; secrets never read);
  - bottom-up TAM/SAM/SOM calculator with weakest-status inheritance, and a unit-economics calculator with sensitivity;
  - deck engine: 21 slide types, one layout model rendered to editable PPTX (native charts and tables) and PDF; evidence and status pills; overflow, unsourced-chart, metric-evidence and YAML-comma guards; paginated sources appendix; short variants; narrative export;
  - document engine: Markdown+ → DOCX/PDF/MD with covers, TOC, Page X of Y, callouts, charts with sources and an automatic evidence appendix; six audience themes; brand overrides;
  - driver-based XLSX financial model with live formulas, cross-checked against a Python mirror;
  - artifact validation (`check`) and PNG contact-sheet previews.
- Knowledge base: attributed summaries of YC, Paul Graham, Sequoia, a16z, NFX, Bessemer, Stripe Atlas and HBR material, plus 11 original frameworks. All 59 URLs were verified by page title.
- Claude Code plugin and marketplace manifests, a symlink installer and a setup script.
- 45 tests, a skill-spec validator and a link checker.
- Fictional *Fieldnote* example (ledger, deck, proposal, model).
