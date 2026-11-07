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
