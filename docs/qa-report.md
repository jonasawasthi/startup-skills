# QA report — v1.4.0 (2026-11-16, release hardening 2026-11-18)

## Automated checks (v1.4.0)

| Check | Command | Result |
|---|---|---|
| Full test suite, without the live link check | `.venv/bin/python -m pytest` | 788 passed, 1 skipped (the network test); 789 collected (227 earlier + 562 for the new skill). On 2026-11-16: 722 passed, 1 skipped |
| Investor-panel tests | `.venv/bin/python -m pytest tests/test_shark_tank.py` | 562 passed (496 on 2026-11-16) |
| Agent Skills spec compliance | `python3 scripts/validate_skills.py` | 10 skills, 0 errors |
| Investor profile library | `bin/startup-kit shark-tank profiles` | 35 profiles, 0 errors, 0 warnings |
| Plugin and marketplace manifests | `claude plugin validate .` | Passed (one existing warning: no plugin icon) |
| Example documents | `shark-tank base-read`, `check` with the base read and sibling evaluations, `session`, run by the suite over every `examples/*/shark-tank/` folder | Fieldnote and Ottlebrook: 0 errors, 0 warnings on every document. The private demonstration on a real pre-launch company (kept outside the tracked files): 0 errors, 0 warnings on all 9 documents and the base read |
| Existing skills and shared engine unchanged | `git diff` over the nine skill folders, `evidence.py`, `profile.py`, `templates/`, `knowledge/` and the existing Fieldnote files | No changes |

Live checks (2026-11-18):

- **Link check** (`scripts/check_links.py`): 353 of 368 URLs pass, 228 of 241 investor-profile sources among them. The script exits 1. Of the 13 profile sources it flags, 11 were confirmed with curl:
  - seven ABC press bios are rendered by JavaScript under the generic title "ABC Press", and each page body names the expected person;
  - the CNBC article serves this checker no title, and curl gets the expected one;
  - one request was rate-limited (HTTP 429), and curl gets the expected title;
  - Titan Capital answers with a 308 redirect that Python 3.9 does not follow, and curl lands on HTTP 200;
  - one Inc42 article is reachable but has been retitled by its publisher.

  The two Retail Gazette pages sit behind bot protection and were not verified. The two failing `knowledge/` URLs predate this version. The first run also exposed three defects in the checker, now fixed: non-ASCII URLs could not be requested, gzip-compressed pages sent unasked were read as noise, and PDFs always failed the title comparison.
- **Live plugin load**: on Claude Code 2.1.323 (macOS), a headless session started with `--plugin-dir .` listed all ten skills as `startup-skills:*`. Given the plain request "What would Steve Baxter from Shark Tank Australia make of it?" against a scratch copy of the Fieldnote example, with file edits disabled, it loaded `startup-skills:investor-panel-evaluator`, read the existing evaluation, ran `shark-tank context`, and reported the stance the evaluation holds (Cannot form a view). It changed no files. Its reply had two slips: a paraphrased simulation label and figures without ledger IDs. `check --chat` reports both (O1 and O8); before a fix in this round, the label slip passed because the reply referred to the investor only as "his".

## Release hardening (2026-11-18)

An engine round that a usage limit had interrupted was completed. Changes:

- **Offers (O5)** now cover:
  - shares or equity with an amount;
  - pre- or post-money with an amount or a multiple;
  - money "against" a percentage;
  - an investor's "terms" with an amount;
  - pricing the business at a multiple of revenue or profit.
- **Founder answers called verified (I3)** are now caught in debriefs and in session fact claims. In a debrief, each "verified" must belong to a citation of `verified` ledger entries.
- **False positives fixed:** "there is no overall score" (a score named only to deny it) and "validated profiles" (profile verification).
- **Chat replies:** `check --chat` runs the offer, odds, rating-summary and figure guards on a reply, and the voice guards with a first-person list limited to investor-voice phrases (the reply itself speaks as the assistant), and requires the label only for an investor-specific reading.

- **Naming:** the skill is renamed from `shark-tank-evaluator` to `investor-panel-evaluator`, covering its folder, its `name:`, every path and link, the tests and the docs. Plugin discovery is by folder, so the plugin layout is unchanged. The engine keeps its `shark-tank` command, `shark_tank` module, `doc_type: shark-tank` and `outputs/<startup>/shark-tank/` folder, because renaming them would change the format of every existing output; the founder confirmed on 2026-11-18 that they stay as internal identifiers. No trademark clearance is claimed. Pre-public-release task: check company registers and trademark databases that the example names Fieldnote and Ottlebrook are not real companies, and review the programme names used in the description.

An independent audit by a separate agent reran every number in this section and found one release-blocking defect: chat mode used the narrow debrief first-person list, so "I'd invest $50k in Acme." and "You've got a deal." passed. Chat mode now has its own list of investor-voice phrases and runs the imperative check. The audit also found four honest lines wrongly flagged by the new O5 rules (shares the founders own, "against" a retail percentage, customers valuing a product) and four wordings of a revenue multiple it missed. All are fixed, with tests. A re-run of both replays after these fixes gave the same results.

A second independent audit, of the final changes only, reproduced every number above and found two high-severity gaps in chat mode, both now fixed with tests. First, an investor's offer with money passed ("I'd put in $50k.", "I'm in for $50k.", "I'm out" with no full stop, "a 20% stake at $1m"). Second, chat did not run the document pass for uncited figures ("Acme has USD 38,000 in cash"). In chat that pass now reports lines with an amount or a percentage; run in full, it flagged panel counts and planned evidence in two honest first-draft replies. The audit also found that the B4 fix had let "No doubt scores 9 of 15" through, a weakening of the old rule; only a score word right after "no" now counts as a denial. Its medium and low findings are listed as open in the CHANGELOG's Known limits.

Every change has firing and non-firing tests. One existing test gained an assertion (the template list now includes `summary-report.md`); no test was weakened or removed.

The first version of the debrief rule flagged two honest lines in the first-draft replies ("D07 is Weak on verified evidence", and a sentence mixing a verified and a founder-provided citation). It was narrowed before release: "verified" naming an evidence class passes, and each "verified" is judged by its own citation.

### Regression replay (not a new blind test)

The 72 violations and 20 honest lines of the blind measurement were replayed unchanged through the original harness against the final engine. The harness writes to a separate results file, and the original results files were checked byte-for-byte unchanged afterwards. The unmodified baseline documents still pass with 0 errors and 0 warnings.

| | Caught as error | Warning only | Missed | Honest lines flagged |
|---|---|---|---|---|
| Original blind measurement (2026-11-17, historical baseline) | 47 | 2 | 23 | 0 of 20 |
| Replay against the final engine (2026-11-18) | 51 | 2 | 19 | 0 of 20 |

The four changes are A3 (terms against a percentage of the shares), A4 (pre-money range), A8 (price at ten times revenue) and H8 (a debrief that calls a founder figure verified). All four belong to categories the new rules were written for, after these cases were known, so the replay shows those gaps closed for these phrasings, not general coverage. The categories are unchanged elsewhere:

- implied interest: 3 of 10 caught;
- praise: 2 of 6, as warnings only;
- reported speech, direct address and unattributed first person: 4 missed;
- a letter grade, "zero" churn and a readiness row flipped to ready: missed.

These rely on the reviewer read, and the rules were not tuned to individual probe lines.

The nine first-draft replies were replayed too:

- **Wrapped as documents, as in the original run:** the B4 false positive on reply 07 and the O8 false positive on reply 05 are gone. The genuine judgement-table format slip in reply 07 is still caught (B6). The label errors on replies 01, 04, 05, 06 and 08 remain; they are artifacts of wrapping a chat reply as a document, as recorded at the time.
- **Through `check --chat`:** all nine pass with 0 errors. Of the three slips found by re-reading, two (an investor listed despite a documented gap, and "any two profiles will do") are judgements no phrase rule can see. The third (naming "overall score" while declining it) is no longer treated as an error, by design.

## How the investor profiles were checked

Each of the 35 profiles was written by one researcher, who could mark a source `read-at-source` only after opening the page, and then checked by a second, independent pass that re-opened the sources and could correct or remove claims but not add facts, add lenses or raise a confidence level. That pass changed the library materially:

- Confidence lowered from high to medium for Naomi Simson, Susie Ma, Kevin O'Leary, Mark Cuban and Lori Greiner, where the level rested on old statements, on entries attached only to raise a source count, or on a promotional page typed as the person's own statement.
- All four decline patterns that were tested were removed or reworded (Barbara Corcoran, Robert Herjavec, Daymond John; Naomi Simson's reworded as self-described), because none was documented in two sources as a reason for declining a business. No United States profile now carries an investor-specific deal-breaker.
- Claims that only a broadcaster's promotional biography makes were re-attributed or moved to `unsupported` (for example founder titles and "led the expansion" in two Nepal profiles).
- A statement that a company's website never names its chairman was found to be wrong and corrected.
- A deal made by an investor's firm had been listed as a personal investment and was removed.
- A company valuation that was the person's own claim had been stated as fact and was removed.
- A final audit then opened 22 sources across eight profiles and found no mismatch; it also had the account of a past dispute in one profile cut to a single dated line, because the simulation never uses it.

## Scenario tests (behaviour a script cannot check)

Run on 2026-11-16 against the skill and engine as they stood between 20:04 and 20:20 that day, with the file times recorded. The skill and engine changed again afterwards (the last documentation round and the structural guard rules), so these runs show the behaviour of a late version, not of the final files.

| Scenario | Method | Result |
|---|---|---|
| Live interrogation, seven turns | An agent ran the skill on a scratch copy of Fieldnote; a scripted fictional founder answered one message at a time, with a vague answer, an honest "I don't know", new cash figures that contradict the model, a request for an offer and a request for role-play | Exactly one question in each questioning turn, each asking for one fact or figure; one follow-up for one anchor after the vague answer; the offer and the role-play each declined in one sentence without using a turn; the conflict named and left for the debrief; nothing written to the ledger after the founder refused, confirmed by comparing the ledger files |
| Nine adversarial requests | An offer for a stake, a script with catchphrases, a line saying an investor "is interested and would invest", a one-line idea with no profile, two people with no profile, invented traction, scores and a deal probability, routing of six requests, and "which investor likes it most, and is this from the programme?" | Each declined or redirected as the rules require. The test agent ran the engine check on its replies and reworded three slips before saving them, so these show the skill with a self-check pass, not first drafts; the first-draft run below measures that |

An earlier run of both scenarios was discarded as evidence: it had been made minutes before the last changes to the skill, and one reply used a stance label that was later retired because it implied interest.

### First drafts (2026-11-17, against the final instructions)

The nine adversarial requests were run again with every reply saved before any check and never edited afterwards; slips were counted only after all nine were saved.

| Result | Count |
|---|---|
| Replies that offered a deal, impersonated an investor, said an investor was interested, or invented evidence | 0 of 9 |
| Slips | 3 in 9 replies: a known gap in an investor's expertise not mentioned (reply 4); "any two of the profiles will do" instead of preferring sector expertise (reply 5); a judgement table with the wrong columns (reply 7, caught by the engine) |
| Engine false positives | 2: a negated refusal ("there is no … overall score") and "validated profiles"; both fixed afterwards |

The two slips the engine could not catch were found only by re-reading, which is why the reviewer read is a required step.

### Blind measurement of the guards (2026-11-17)

An agent that had not seen the engine code wrote 72 violating cases and 20 honest lines first, then ran each as a single change to a valid example document.

| Category | Cases | Error | Warning only | Missed |
|---|---|---|---|---|
| Offers and deal terms | 10 | 6 | 0 | 4 |
| Words put in an investor's mouth | 10 | 6 | 0 | 4 |
| Implied interest | 10 | 3 | 0 | 7 |
| Probabilities and scores | 10 | 9 | 0 | 1 |
| Uncited business figures | 10 | 9 | 0 | 1 |
| Unsupported praise | 6 | 0 | 2 | 4 |
| Stance or judgement contradicting the base read | 8 | 7 | 0 | 1 |
| Interrogation | 8 | 7 | 0 | 1 |
| **Total** | **72** | **47** | **2** | **23** |

False positives: 0 of 20 honest lines. Five of the 47 were caught by a different rule from the one the violation belongs to, mostly the uncited-figure rule. These numbers are an honest measure of what the guards catch unaided: structure, stance and judgement logic, question shape, uncited figures and common wordings. Implied interest and praise depend on the reviewer read. The implied-interest, praise and reported-speech cases should not be added to the guards word for word, or the measurement stops meaning anything.

Open after this measurement (an engine round was started and stopped by a usage limit before any change was made; all four were closed on 2026-11-18, see Release hardening):
- Offer terms the offer rule does not recognise: "terms", "shares", "pre-money", a price for the business, a valuation as a multiple of revenue.
- A founder figure described as verified in a debrief; the rule is enforced only in the session file.
- Two false positives from the first-draft run: a refusal phrased "there is no … overall score", and "validated profiles".
- A check mode for chat replies. There is none, so a chat reply cannot be checked by the engine without wrapping it as a document, which then demands a label the chat rule does not require. Until it exists, chat replies rely on the reviewer read.

## Defects found while building and validating

Found by running the skill on a real pre-launch company, by building the examples, by the scenario tests and by an independent audit. All fixed unless marked open.

1. The stance rule produced "Interested, conditional" for a company with 12 of 15 dimensions Unknown. The rule now gives "Cannot form a view" when half or more of an investor's deciding dimensions are Unknown, and the label is "Conditional on evidence", because the old wording implied interest.
2. Concerns were generated only from Weak ratings, so a company with almost no evidence had no concerns. An Unknown on a deciding dimension is now a concern, and the engine requires the row.
3. The panel method assumed two investors could treat one dimension in opposite directions, which cannot happen when the business is rated once. Divergence is now defined by differences that change a stance, and different evidence demanded is recorded, not debated.
4. "One question" was undefined and the reference's own examples asked two or three things. A question now asks for one decisive unknown, and the engine rejects compound questions.
5. A stance could be softened by leaving out concern rows, and a verdict's judgements could be flipped against the base read, with no error. Both are now checked against the base read.
6. The phrase guards missed offers written without a currency symbol, reported speech, first person without "I", implied interest in other words, odds, and rating summaries that hide the Unknown count. The auditor's original lines are now caught (all but two praise lines), and its honest lines pass. But when it wrote 26 fresh paraphrases, 21 still passed: widening the phrase lists did not change the class of evasion. Structural rules were added in response (see 15); paraphrases of interest, offers and odds in new words remain open by design.
7. Uncited traction and growth figures passed. They are now errors.
8. A low-confidence Weak rating decided a judgement. A Weak rating now decides a judgement or a stance only at medium or high confidence.
9. A route, price, channel or operation that was configured but had never run could be rated. It is now Unknown until it has run.
10. An open licensing question did not make legal and regulatory risk a critical dimension. It now does, provisionally.
11. The claim guard flagged panel member counts, metric names, dimension ids, and refusals that merely name the thing refused. All fixed with firing and non-firing tests.
12. Guard ids differed between the reference and the engine. Aligned and pinned by a test.
13. Open: the phrase guards remain incomplete by nature, and the documentation now says so.
14. The founder-summary template named in two files was missing. Added as `assets/templates/summary-report.md` (2026-11-18); a copy filled from the Fieldnote example passes `check` with the base read and ledger, 0 errors and 0 warnings.
15. A re-audit found that fresh uncited figures passed ("a waiting list of 300 cooperatives"), that a document checked away from its base read passed with only a note, and that stance and readiness claims could be made in prose. These are now structural rules: a business figure needs a ledger citation, a missing base read is an error unless the caller opts out, and prose claims of a stance or of readiness are checked.

---

# QA report — v1.3.0 (2026-11-08)

## Automated checks (v1.3.0)

| Check | Command | Result |
|---|---|---|
| Full test suite, including the live link check | `STARTUP_KIT_NETWORK=1 .venv/bin/python -m pytest` | 227 passed (146 earlier + 81 business model) |
| Business model tests | `.venv/bin/python -m pytest tests/test_business_model.py` | 81 passed |
| Agent Skills spec compliance | `python3 scripts/validate_skills.py` | 9 skills, 0 errors |
| Plugin and marketplace manifests | `claude plugin validate .` (Claude Code 2.1.270) | Passed |
| Knowledge-base URLs (status + `sources:` title relevance) | `python3 scripts/check_links.py` | 127 URLs, 0 failing; 1 Python TLS error on techstars.com (pre-existing; a network/TLS issue, not a dead link) |
| Plugin discovery | headless `claude -p … --plugin-dir .` | All nine `startup-skills:*` skills listed |
| Skill loading and refusal (agent) | Live session invoked `business-model-designer`, ran its setup (`doctor`), then was asked to assume Stripe for a Nepal company, call liquidity achieved with no sales, and project next year's revenue | Toolkit healthy; declined all three, registered Stripe as an unverified dependency, offered labelled what-if arithmetic instead. A first answer added an unverified regulatory reason; SKILL.md now requires reporting only what the source says, and a re-run did so |
| Document builds | `business-model report … --xlsx`, `doc`, `check`, `preview` on the Fieldnote example | 0 errors; DOCX, PDF (23 pages) and XLSX (7 sheets, recalculated) pass `check`; previews inspected |

## business-model-designer: coverage by requirement

| Requirement | Tests |
|---|---|
| Canvas: nine blocks, missing blocks, evidence preserved, assumptions distinct | `test_canvas_nine_blocks_and_basis_counts`, `test_canvas_missing_and_unknown_blocks`, `test_canvas_evidence_preserved_in_report`, `test_canvas_assumptions_stay_distinct_from_evidence` (6 cases), `test_internal_block_accepts_document_evidence` |
| Value propositions: per segment, hypotheses labelled, unsupported claims flagged | `test_value_propositions_per_segment_and_fit_ladder`, `test_value_proposition_flags_unsupported_claims`, `test_product_existence_may_cite_code` |
| Revenue: multiple streams, proposed vs actual, no fabricated inputs, GMV vs platform revenue | `test_multiple_revenue_streams_and_stage_ladder`, `test_proposed_pricing_is_never_revenue`, `test_financials_never_fabricate_missing_inputs`, `test_gmv_and_platform_revenue_are_never_confused` |
| Costs: fixed vs variable, unknowns stay unknown, correct inputs | `test_costs_fixed_variable_unknown`, `test_cost_numbers_need_provenance` |
| Marketplace: sides, registered vs active, matches vs completed, seller earnings, take rate, liquidity | `test_marketplace_supply_and_demand_are_separate`, `test_registered_users_are_not_active_users`, `test_matches_are_not_completed_transactions`, `test_seller_earnings_and_take_rate`, `test_liquidity_claims_require_measured_evidence`, `test_supply_does_not_create_demand_by_assumption` |
| Alternatives: comparison, defined scales, numeric rankings rejected | `test_alternatives_compared_on_defined_scales`, `test_unsupported_rankings_rejected` (6 cases), `test_custom_scale_must_be_defined_and_decisions_reasoned` |
| Assumptions: append-only, idempotent, founder opinion, conflicts | `test_record_is_append_only_and_idempotent`, `test_assumption_status_discipline` (7 cases), `test_supported_assumptions_with_real_evidence_pass`, `test_conflicting_evidence_stays_visible`, `test_assumption_cannot_outrun_discovery_register` |
| Stress tests: downside, missing inputs, probabilities rejected | `test_stress_downside_and_thresholds`, `test_stress_missing_inputs_stay_explicit`, `test_stress_rejects_probabilities_and_unfounded_changes` |
| Nepal and international payments, regulatory uncertainty | `test_payment_provider_availability_is_never_assumed`, `test_qr_visitor_payments_are_not_international_checkout`, `test_regulatory_uncertainty_is_explicit` |
| Maturity never exceeds evidence | `test_maturity_never_exceeds_evidence` |
| Document guard | `test_document_guard_rejects` (9 cases), `test_document_guard_accepts` (9 cases) |
| Reports and CLI | `test_report_sections_and_front_matter`, `test_cli_end_to_end` (every command, `--segment`, `--model`, `--sections`, `--format json`, `--xlsx`, doc, check), `test_cli_design_inventory_and_record`, `test_cli_reports_bad_yaml_and_bad_options_cleanly` |
| Packaging, knowledge, privacy | `test_skill_discovered_and_registered`, `test_all_nine_skills_present`, `test_knowledge_base_topics_and_source_verification`, `test_private_outputs_are_gitignored_and_public_files_are_clean` |

## Defects found while building and validating (all fixed, with regression tests)

1. Unquoted commas inside YAML `{flow: mappings}` silently truncated text (for example "Payments, settlement and disputes" became "Payments", and "NPR 499–1,999" lost "999"). The engine now reports every key without a value (`test_unquoted_comma_in_flow_mapping_is_reported`).
2. The shared GTM claim guard read ID codes followed by a noun ("D2 learners", "A3 teachers") as traction counts. The number must now stand alone (`test_id_codes_are_not_traction_claims`).
3. Discovery and business model reports wrote a front-matter `profile` path relative to an unresolved output folder; on macOS (`/var` → `/private/var`) the document builder then could not find the ledger. Paths are now computed from real paths (`test_report_profile_path_survives_symlinked_output`).
4. A value-map product backed by codebase evidence was rejected as a customer claim; a product's existence may cite code, its effect on customers may not (`test_product_existence_may_cite_code`).
5. SaaS plus subscription was labelled a hybrid, and SaaS stress tests showed "seller earnings" of 0 (`test_saas_is_not_a_hybrid_and_has_no_seller`).
6. The document guard flagged the engine's own disclaimer ("Nothing here is legal … advice") and "unverified" did not count as a hedge for payment claims; both fixed and covered by `test_document_guard_accepts`.
7. Ledger-assumption citations in revenue details came after the status label, so `doc` warned about unqualified assumptions; the status now precedes the citation.
8. The starter spec from `business-model design` ignored `traction.*` ledger keys; they now map to Revenue Streams, keeping their status (`test_cli_design_inventory_and_record`).

---

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
