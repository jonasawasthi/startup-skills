# Changelog

All notable changes follow [Keep a Changelog](https://keepachangelog.com/). The project uses semantic versioning.

## [1.4.0] — Unreleased

### Added
- **`investor-panel-evaluator`**, the tenth skill: an analytical simulation of how investors from Shark Tank (United States, India, Nepal, Australia) and Dragons' Den (United Kingdom) would read a startup. It is an orchestration layer over the other skills, not a second evaluator, and it is independent work that is not affiliated with the programmes or the people profiled. It covers:
  - a base read that rates the business once on 15 dimensions with the existing Strong / Adequate / Weak / Unknown scale, an evidence ceiling (Strong needs verified or interview-behavioural evidence; founder-provided figures and estimates allow Adequate at most; assumptions alone mean Unknown), six evidence buckets per rating, and no aggregate score;
  - a documented crosswalk from the ten `startup-idea-evaluator` dimensions, with divergence notes instead of silent overrides;
  - individual investor evaluations in which every point names a lens from the investor's profile and ledger evidence or a named gap, so differences between investors are traceable;
  - four stances (persuaded, conditional, not persuaded, cannot form a view) that follow from the base read, with no offers, valuations or implied interest;
  - a panel of three to seven with initial positions locked before discussion, divergence defined by differences that change a stance, and plain convergence when that is the result;
  - founder interrogation that asks one decisive unknown per turn, holds answers as founder-provided, and writes to the ledger only after the founder agrees;
  - a verdict with five separate judgements: good business, investable (for a named investor class), investment-ready, needs further validation, and should not proceed in its current form;
  - rules for chat replies, role-play requests, requests for offers or scores, hypothetical evidence, and people with no profile.
- An investor profile library, `skills/investor-panel-evaluator/investors/`: 35 profiles of real people, one file each, with public professional facts cited to dated sources, evaluation lenses labelled as analytical interpretation, panel status (current, former, unconfirmed, dormant) with the date checked, and a confidence level (10 high, 23 medium, 2 low) that limits what the simulation may say. Each profile was written by one researcher and checked against its sources by a second, independent pass. The schema accepts investors from outside the programmes and private libraries (`--library`). The index carries a non-affiliation notice and a corrections and removal route.
- `startup_kit.shark_tank` and `startup-kit shark-tank profiles | context | base-read | queue | check | session | record`, with `--library`, `--id`, `--today`, `--profile`, `--base-read`, `--against`, `--investors`, `--budget`, `--json`, `--out`, `--confirmed` and `--chat`. It reuses the ledger and the existing claim guards by import. The skill was named `shark-tank-evaluator` during development and renamed before release to avoid building its name on a programme's trademark; the engine's command, module, doc type and output folder keep the `shark-tank` / `shark_tank` names (see Known limits).
- Guards: profile rules (sources, panel status, lens derivation, confidence minimums, forbidden content, stale status), base-read rules (evidence ceiling, crosswalk divergence, no aggregate), output rules (simulation label, quotations, first person, offers, implied interest, probabilities, uncited figures, labelling of founder- and company-provided figures), traceability rules (lens ownership, stance consistency with the base read, required concern rows, name-swap heuristics), panel rules, judgement gates checked against the base read, and interrogation rules (one question per turn, compound questions, founder-provided facts only). The guards catch structure and common phrasings; a reviewer read of every output is a required step.
- Templates for the base read, evaluation, panel report, verdict, interrogation session, debrief, founder summary report (`summary-report.md`) and investor profile.
- Two fictional examples: `examples/fieldnote/shark-tank/` (subscription software: three investors who differ, a panel, a verdict, and an interrogation session with transcript) and `examples/ottlebrook/` (a physical product sold through a retailer: a panel that agrees on a verified weakness and a verdict not to proceed in the current form).
- `check --chat` for chat replies: the offer, odds, rating-summary and uncited-figure guards, and the voice guards with a first-person list limited to investor-voice phrases ("I'd invest", "you've got a deal"), because the reply itself speaks as the assistant; with the simulation label required only when the reply gives an investor-specific reading (a sentence that names an investor, or refers back to the one investor it names, together with a stance, lens, dimension or point).
- Release hardening of the guards:
  - O5 now covers offer terms phrased through shares or equity with an amount, pre- or post-money, "against" a percentage, an investor's "terms", and pricing the business at a multiple of revenue or profit;
  - I3 now rejects a founder answer described as verified in a debrief (each "verified" must belong to a citation of verified ledger entries) or in a session's fact claims;
  - two false positives are fixed: a score named only to deny it ("there is no overall score") and "validated profiles" (profile verification, not a business claim).
- 562 tests for the new skill, including firing and non-firing cases for every guard and checks over every example folder.

### Changed
- `scripts/check_links.py` also checks the sources of investor profiles, and accepts a page's `og:title` or `twitter:title` as well as its HTML title. The more lenient title match applies to `knowledge/` too. It now percent-encodes non-ASCII URLs, decompresses pages sent gzip-compressed without being asked, and checks a PDF by status only (a PDF has no title to compare).
- The `shark-tank` doc type uses the internal theme.
- `tests/test_business_model.py` accepts additional skills and no longer pins the skill count and version; `tests/test_shark_tank.py` pins exactly ten skills by name and plugin version 1.4.0.
- A ground rule for profiles of real people in `CONTRIBUTING.md`.
- Plugin version 1.4.0.

### Known limits
- The phrase-based guards cannot catch every paraphrase of an offer, a quotation, implied interest or praise. They are tripwires, not proof.
- Panel status and investor facts go stale. The validator warns when a status is more than six months old, and lowers confidence when a profile is more than 18 months old.
- A blind test, written by someone who had not seen the engine, caught 47 of 72 violations as errors and 2 as warnings, with no false positives on 20 honest lines. Replaying the same cases after the release round gives 51 errors, 2 warnings and 19 missed, still with no false positives. The four new catches are cases the new rules were written to cover, so this replay is not a new blind test. Implied interest (3 of 10), unsupported praise (warnings only) and paraphrased reported speech still rely on the reviewer read.
- Before any public release: check company registers and trademark databases that the fictional example names (Fieldnote, Ottlebrook) do not belong to real companies, and review the trademark position of the programme names used in the skill's description and documents. Neither check has been done.
- Open after the final audit (paraphrase gaps and minor false positives, none a release blocker): honest lines flagged by O5 ("retailers value Acme at USD 20", a cited comparables multiple, an employee share pool with an amount); "Acme at 5x revenue" without a price word passes; a founder answer called "verified evidence" or "verified status", or a denial window crossing a colon, passes I3; chat readings that refer back by "she" or "he", or name only a surname, or use "would want" do not require the label; and honest assistant lines ("I'd back that up", "show me the ledger file") are flagged O3 in chat. In chat, uncited figures are errors only on lines with an amount or a percentage (or a traction count), because a reply has no sections to exempt panel counts and planned evidence; so "Runway is 7 months." passes in chat. "I'm out on this one." passes in chat, and some offer wordings with money ("I'd go in with $50k", "put me down for $50k") are caught only as uncited figures (O8), not as offers.
- The engine keeps the `shark-tank` names (a confirmed decision): the `startup-kit shark-tank` command, the `shark_tank` module, `doc_type: shark-tank` and the `outputs/<startup>/shark-tank/` folder. Renaming them would change the document format that every existing output and test relies on, so they stay as internal identifiers; the public skill name is `investor-panel-evaluator`. The skill's description names the programmes so that requests about them reach it; that is not a trademark clearance.
- The live link check passes 353 of 368 URLs (228 of 241 profile sources). Of the profile sources it flags, seven ABC press bios are pages rendered by JavaScript under a generic title, one page serves this checker no title, one request was rate-limited (HTTP 429), and one redirect (HTTP 308) is not followed by Python 3.9; each was confirmed reachable with curl. One article has been retitled by its publisher, and two pages sit behind bot protection and were not verified.

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
