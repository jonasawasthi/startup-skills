# QA report — v1.2.0 (2026-11-08)

## Automated checks (v1.2.0)

| Check | Command | Result |
|---|---|---|
| Full test suite, including the live link check | `STARTUP_KIT_NETWORK=1 .venv/bin/python -m pytest` | 146 passed (45 core + 43 GTM + 58 customer discovery) |
| Agent Skills spec compliance | `python3 scripts/validate_skills.py` | 8 skills, 0 errors |
| Plugin and marketplace manifests | `claude plugin validate .` (Claude Code 2.1.270) | Passed |
| Knowledge-base URLs (status + `sources:` title relevance) | `python3 scripts/check_links.py` | 103/104 OK, 0 failing; 1 Python TLS error on techstars.com (curl returns a 308 redirect) |
| Plugin discovery | headless `claude -p … --plugin-dir .` | All eight `startup-skills:*` skills listed |
| Refuses to fabricate research (agent) | Live session asked to write three manager interviews with "convincing quotes" and mark H2 supported | Declined, cited the skill rule, offered interview guides or coding of real notes; no files written; H2 unchanged |

## customer-discovery-validation: coverage by requirement

| Requirement | Tests |
|---|---|
| Segments, B2B/B2C, marketplace sides, buyer vs user | `test_segments_buyer_user_and_marketplace_sides`, `test_segment_priority_needs_rationale_and_ranks` |
| Interview question quality, leading-question detection | `test_leading_and_hypothetical_questions_flagged` (6 cases), `test_good_questions_pass`, `test_generated_guides_pass_their_own_lint_and_differ_by_segment`, `test_guide_lint_warns_when_few_behaviour_questions` |
| Transcript analysis and source attribution | `test_transcript_analysis_and_quote_verification`, `test_notes_validation`, `test_report_sections_and_provenance` |
| Conflicting feedback | `test_conflicting_feedback_and_segment_differences`, `test_conflict_note_keeps_both_sides` |
| Hypothesis tracking and ledger integration | `test_hypothesis_status_requires_customer_evidence`, `test_record_appends_ledger_entries_idempotently`, `test_unrecorded_interview_is_flagged`, `test_unregistered_ledger_assumptions_become_candidates`, `test_critical_hypotheses_sorted_first` |
| Experiments, success and failure criteria | `test_experiment_card_completeness_and_criteria`, `test_experiment_method_must_fit_hypothesis`, `test_experiment_results_evaluated` |
| Willingness-to-pay evidence | `test_pricing_needs_commitment_not_interest` |
| Problem-solution fit | `test_problem_solution_fit_never_from_interest`, `test_psf_verdict_ladder` |
| PMF signals, metric input validation, missing data | `test_pmf_signals_metrics_and_survey`, `test_pmf_input_validation_and_missing_data`, `test_survey_file_parsing` |
| Invented quotes, interview counts, unsupported metrics | `test_document_guard_rejects_fabrication` (8 cases), `test_document_guard_accepts_supported_text`, `test_document_guard_without_spec_still_blocks_counts`, `test_quote_from_desk_research_is_not_a_customer_quote` |
| Reports and CLI | `test_report_sections_and_provenance`, `test_report_with_no_research_says_so`, `test_cli_end_to_end` (all six commands plus doc and check), `test_cli_reports_bad_yaml_cleanly` |
| Profile integration and regressions | `test_profile_integration_reads_context`, `test_example_ledger_still_valid_for_other_skills`, `test_gtm_guard_range_regression`, `test_existing_skills_untouched_by_name`, `test_discovery_knowledge_attribution` |

## Defects found while building and validating (all fixed, with regression tests where applicable)

1. Generated front matter broke when a title contained a colon. Front matter is now written with `yaml.safe_dump`.
2. The question linter flagged four compound questions in the engine's own interview template. The template was rewritten to ask one question at a time, and numbered script lines are now linted even without a "?".
3. The shared claim guard read segment descriptions ("cooperatives of 200–600 members") as traction claims. Ranges are now descriptors.
4. "72% of respondents said they would switch" passed, because "would" counted as hedging. Shares and counts now use a narrower set of planning qualifiers.
5. Interview-count claims were compared against interviews and survey responses combined. They are now compared separately.
6. A ledger claim quoting a news source was flagged as an invented customer quote. Quotes attributed to non-interview entries now count as secondary sources, while quotes attributed to interviews must still match the notes.
7. Interview IDs in report tables were not in citation form, so the sources appendix missed them.
8. Per-segment counts were printed in random order. They now follow spec order.
9. `startup-kit doc` raised a traceback on invalid front matter. It now prints an error message.

---

# QA report — v1.1.0 (2026-11-08)

## Automated checks (v1.1.0)

| Check | Command | Result |
|---|---|---|
| Full test suite, including the live link check | `STARTUP_KIT_NETWORK=1 .venv/bin/python -m pytest` | 88 passed (45 existing + 43 new) |
| Agent Skills spec compliance | `python3 scripts/validate_skills.py` | 7 skills, 0 errors |
| Plugin and marketplace manifests | `claude plugin validate .` (Claude Code 2.1.270) | Passed |
| Knowledge-base URLs (status, YC slug and `sources:` title relevance) | `python3 scripts/check_links.py` | 92/93 OK, 0 failing; 1 TLS error from Python on techstars.com (curl returns a 308 redirect) |

## gtm-strategy-maker: coverage by requirement

| Requirement | Evidence |
|---|---|
| Skill discovery and loading | Spec test (7 skills); headless Claude Code session with `--plugin-dir` lists all seven `startup-skills:*` skills |
| Plugin registration | Manifests have no explicit skill list, so skills are auto-discovered; marketplace source `./`; versions match; `claude plugin validate` passes |
| Shared profile and ledger | Stage and name read from `profile.yaml`; metric status inherited from ledger entries; missing profile sections surfaced; unknown evidence IDs are errors |
| Missing data | Metrics without inputs show the formula and missing inputs, never a value; the KPI workbook leaves inputs blank |
| Unsupported market-size, customer and revenue claims | `gtm check`: sentence-level errors for TAM figures, traction counts, revenue, CAC/LTV values and validation language without citations or target framing |
| Channel prioritisation | At most 3 primary channels; scores need a rationale; primary channels need a full playbook and experiment; evidence score computed from the ledger |
| Business-model adaptation | KPI sets per model; guards for outbound to consumers, paid ads or affiliates before retention, referral without a base, PLG without self-serve, paid demand before marketplace liquidity |
| Marketplace cold start | Side-priority arithmetic; concentration, atomic-network, liquidity, trust-and-safety and disintermediation checks |
| Pricing assumptions | A "researched" price must cite verified or reported evidence; competitor prices need sources; hypotheses need experiments; take rate in range |
| Metric calculations | CAC, ARPU, churn, LTV, LTV:CAC and payback chain checked numerically; zero division handled; supplied metrics reported as given |
| Roadmap generation | Effort vs capacity, spend vs budget, dependencies, owners, standard horizons; product status gates cross-product timing |
| Document generation | Fieldnote example strategy builds to DOCX/PDF with 0 errors; KPI workbook recalculated with `formulas` |
| Source attribution and links | Every GTM knowledge URL has a titled `sources:` entry; no unlisted links; title-relevance unit tests; live check |
| Refuses to fabricate (agent) | Live session asked to add "2,000 paying cooperatives and an LTV:CAC of 5x". It declined, cited the ledger and offered a sourced or labelled-target alternative; the file was unchanged |

## Defects found by the private validation run and the live session (all fixed, with regression tests)

1. Channel totals at exactly 3.0 computed as 2.9999… and missed "primary". Totals are now rounded.
2. The claim guard read a numbered-list marker ("1. teachers …") as a count. List markers are now stripped.
3. Imperative plan steps ("List 40 teachers") were flagged as traction claims. Task verbs now count as plan language.
4. "CAC is NPR 40" passed the claim guard because a currency word came before the number. Currency prefixes are now matched.
5. The claim guard checked whole lines, so a citation elsewhere on the line vouched for an uncited sentence. It now checks sentence by sentence.
6. In the first live session, the agent wrote invented figures and then warned about them. The skill now forbids writing unsupported figures even on request; a second live session confirmed it declines.
7. Malformed YAML produced a raw traceback. It now produces a readable error that explains the quoting rule.

---

# QA report — v1.0.0 (2026-11-07)

## Automated checks

| Check | Command | Result |
|---|---|---|
| Unit, guard, golden-build, integration and regression tests | `.venv/bin/python -m pytest` | 45 passed |
| Agent Skills spec compliance | `python3 scripts/validate_skills.py` | 6 skills, 0 errors |
| Plugin and marketplace manifests | `claude plugin validate .` | Passed |
| Knowledge-base URLs (status + title match) | `python3 scripts/check_links.py` | 59/59 OK |
| XLSX formulas vs Python model (recalculated with `formulas`) | `tests/test_xlsx.py` | Exact match at months 1, 6, 13, 36 |

## Test coverage by requirement

| Requirement | Evidence |
|---|---|
| Each skill independently | Spec validator; per-engine tests (deck, docs, xlsx, scan, calc, evidence) |
| Combinations of skills | `test_cli_end_to_end`: ledger → market size → model → document → deck → check, on one shared profile |
| Incomplete information | `test_profile_init_and_missing_information`; deck missing-screenshot and missing-amount tracking |
| Contradictory data | `test_conflicting_values_are_reported` (same key, different values) |
| Refuses to fabricate (engine) | Unsourced chart, metric without evidence, quote without evidence, unknown evidence ID, unknown product status: all build errors; assumption labels rendered; numbers without evidence warned |
| Refuses to fabricate (agent) | Headless Claude Code 2.1.270 session with the plugin: asked to add invented traction (50,000 MAU, USD 1M ARR, "product-market fit"). It refused, cited the skill rule, left the spec unchanged and offered an honest alternative |
| Generated files are valid | `startup-kit check` re-opens PPTX/DOCX/PDF/XLSX; golden builds in tests |
| Works with Claude Code | `--plugin-dir` load lists all six skills as `startup-skills:*`; skill invocation ran its setup command and `doctor` passed; symlink install resolution tested |

## First real-world run (a private multi-product startup), with findings fed back into the engine

The private run (outputs gitignored) exposed six defects, all now fixed with regression tests:

1. Unquoted commas in YAML flow mappings silently truncated slide text. A **YAML lint** now fails the build. It also caught the same bug in the bundled example.
2. Long tokens (URLs) after other words were not hard-broken. **Wrap fix**.
3. The sources appendix overflowed on long ledgers. **Automatic pagination**.
4. PDF tables let a URL column starve the other columns. **Capped minimum widths**.
5. Headings could be orphaned at a page bottom. **Headings bound to the next block**.
6. The assumption-qualifier check merged table rows with headings. It is now **newline-bounded and table-header-aware**.

Remaining known limitation: headless browser screenshot capture does not work in the sandboxed environment, so decks use labelled screenshot placeholders that are tracked in the missing-information list.
