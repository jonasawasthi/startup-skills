# Changelog

All notable changes follow [Keep a Changelog](https://keepachangelog.com/). The project uses semantic versioning.

## [1.3.0] — Unreleased

### Added
- **`business-model-designer`**, the ninth skill: evidence-based business model design. It covers:
  - a nine-block Business Model Canvas where every item has a basis (evidence, founder-provided, hypothesis, recommendation, unknown), with customer evidence required on customer-facing blocks;
  - per-segment Value Proposition Canvases with a computed fit ladder;
  - model classification (SaaS, subscription, freemium, marketplace, transaction, commission, digital products, education, services, consulting, advertising, licensing, usage-based, e-commerce, direct sales, B2B, B2C, B2B2C, hybrid) and the structural requirements of each type;
  - revenue streams on an evidence-gated ladder (proposed, tested, available, generating, repeatable);
  - cost structure with fixed, variable, semi-variable and unknown costs kept apart;
  - marketplace modelling: separate sides, a measured funnel from registrations to repeat transactions, liquidity claims gated on data, GMV vs platform revenue vs seller earnings, payouts, refunds and leakage;
  - payment, payout, tax, legal and regulatory dependencies with open questions and who must confirm them;
  - alternatives compared on defined qualitative scales (numeric scores, weights and rankings rejected);
  - an assumption register on the shared ledger and discovery register;
  - stress tests with break-even and headroom arithmetic, founder-defined scenarios and thirteen stress cards (no probabilities);
  - a maturity verdict (coherent, customer evidence, economic viability, repeatable) that a spec cannot overclaim.
- `startup_kit.business_model` and `startup-kit business-model design | analyze | canvas | value-proposition | compare | revenue | costs | marketplace | assumptions | stress-test | report | check`, with `--record`, `--model`, `--segment`, `--format md|json`, `--sections`, `--xlsx`, `--spec`. It reuses the ledger, the profile, the discovery engine (evidence strength, hypothesis statuses), the GTM metrics and claim guard, the document builder and the workbook conventions.
- Document guard for business model documents: GMV presented as revenue, registrations as active users, unsupported liquidity or viability claims, payment provider availability asserted for Nepal, in-person cross-border QR used as evidence of online checkout, legal certainty, probabilities, and stated interest presented as payment.
- `knowledge/business-model/`: 12 files plus an index (Strategyzer, Steve Blank, Eric Ries, HBR, Christensen Institute, NFX, a16z, Bill Gurley, Lenny Rachitsky, Stripe, Nepal Rastra Bank, Fonepay), each source marked read-at-source or url-verified.
- Ten templates: spec, canvas, value proposition canvas, revenue architecture, cost structure, marketplace model, model comparison, assumption register, stress test and decision summary.
- Fictional Fieldnote business model example (recommended subscription, viable hybrid, rejected marketplace).
- 81 tests for the new skill.

### Changed
- The shared claim guard no longer reads ID codes followed by a noun ("D2 learners", "A3 teachers") as traction counts.
- Discovery and business model reports compute the front-matter `profile` path from resolved real paths, so documents built in a symlinked folder (such as macOS `/var` → `/private/var`) find their ledger.
- The `business-model` doc type uses the internal theme.
- Discovery tests accept additional skills in the collection.
- Plugin version 1.3.0.

## [1.2.0] — Unreleased

### Added
- **`customer-discovery-validation`**, the eighth skill: a structured customer research and validation system. It covers:
  - segment design (buyer, user, decision-maker and influencers; marketplace supply and demand kept apart);
  - behaviour-first interview guides per segment;
  - analysis of interview notes, transcripts, surveys and feedback, with full provenance;
  - a hypothesis register on the shared ledger;
  - 13-field experiment cards;
  - problem-solution fit and early PMF signals;
  - an 18-section discovery report, consolidated or standalone.
- `startup_kit.customer_discovery` and `startup-kit discovery analyze | interviews | hypotheses | experiment | report | check`:
  - coded notes, with every quotation checked against the transcript;
  - themes with mentions and denials per segment, contradictory feedback and segment differences;
  - `--record` appends interview and survey entries to the existing ledger (idempotent, never rewrites);
  - evidence strength computed from source type, status and the optional `signal` ladder (stated, observed, committed, paid). *Supported* needs customer evidence, and pricing needs committed or paid evidence;
  - experiment validation and evaluation of measured results;
  - fit verdicts that never move on interest alone;
  - PMF signals through the shared GTM metrics engine, with input validation;
  - a question linter (hypothetical, leading, pitching and compound questions);
  - a document guard against invented quotations, inflated interview or response counts and uncited survey shares.
- `knowledge/customer-discovery/`: 10 files plus an index covering 12 topics (Steve Blank, Rob Fitzpatrick, Eric Ries, Strategyzer, the Christensen Institute, HBR, the YC Library, First Round Review, Sean Ellis, Rahul Vohra, Monetizing Innovation).
- Templates: discovery spec, interview guide, interview notes, hypothesis register, experiment plan and report outline.
- Fictional Fieldnote example: 6 coded interviews, 2 transcripts, a survey, 7 hypotheses and 3 experiments, with ledger entries E-010 to E-017.
- 58 tests for the new skill.

### Changed
- The shared claim guard (`gtm check`) treats number ranges ("cooperatives of 200–600 members") as segment descriptions, not traction claims.
- `startup-kit doc` reports invalid front-matter YAML as an error message instead of a traceback.
- Document engine: the `customer-discovery-report` and `interview-guide` doc types use the internal theme.
- Plugin version 1.2.0.

## [1.1.0] — Unreleased

### Added
- **`gtm-strategy-maker`**, the seventh skill: an evidence-backed go-to-market strategy covering segmentation, ICPs and personas, positioning and messaging, competitive GTM intelligence, a prioritised channel matrix with execution playbooks and validation experiments, launch plans, marketplace cold start, pricing and monetisation, AARRR growth metrics, a KPI dashboard and 30/60/90-day to 12-month roadmaps. It adapts to nine business models and to the startup's stage.
- `startup_kit.gtm` engine and `startup-kit gtm analyze | kpi | check`:
  - channel scoring where the evidence criterion is computed from the ledger, with a cap on primary channels and a required playbook and experiment for each;
  - business-model guards;
  - metrics computed only from measured inputs, with formulas and missing inputs shown otherwise;
  - pricing and marketplace checks;
  - roadmap capacity and budget checks;
  - product-status gating of cross-product plans;
  - a sentence-level claim guard for market-size, traction and validation claims;
  - a KPI tracker workbook with live formulas and no pre-filled values.
- `knowledge/gtm/`: 11 attributed and original files (April Dunford, Geoffrey Moore, Sean Ellis and First Round Review, Reforge, Brian Balfour, NFX, Andrew Chen, HubSpot, OpenView via archived copies, YC, a16z, Steve Blank, Rob Fitzpatrick, HBR).
- Fictional Fieldnote GTM spec and example strategy.
- 43 tests for the new skill, including regressions found in a private real-world run and a live Claude Code session.

### Changed
- `scripts/check_links.py` checks that page titles are relevant: a knowledge file's `sources:` titles must match the live page title, which catches URLs that now redirect to an unrelated page.
- Document engine: the `gtm-strategy`, `gtm-plan` and `market-segmentation` doc types use the internal theme.
- Plugin version 1.1.0. Existing installs keep working: no files were moved and the other six skills are unchanged.

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
