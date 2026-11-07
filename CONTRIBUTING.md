# Contributing to Startup Skills

Thank you for helping. The bar for contributions is the same as the bar for the skills: **evidence over enthusiasm**.

## Setup

```bash
scripts/setup.sh                      # Python venv + dependencies + doctor
.venv/bin/python -m pytest            # all tests must pass
python3 scripts/validate_skills.py    # skill spec compliance
```

## Ground rules

1. **No fabricated content.** Examples use the fictional *Fieldnote* company, or clearly marked fictional data. Never commit a real startup's private analysis. `outputs/` is gitignored for that reason.
2. **Attribute sources.** Knowledge-base files need front matter with `urls`, `date_checked`, `type` (attributed-summary or original-analysis) and `verification`. Paraphrase. Keep quotations short and attributed.
3. **Verify URLs by title**, not just HTTP status (`scripts/check_links.py`).
4. **Skills follow the Agent Skills spec**: portable front matter only (`name`, `description`, `license`, `compatibility`, `metadata`), the name equals the directory, SKILL.md has fewer than 500 lines, and references are one level deep.
5. **Mechanics belong in code, judgement in Markdown.** Deterministic logic (arithmetic, layout, validation) goes in `lib/startup_kit` with tests.
6. **Guards are features.** If you add a slide type or document block, add its honesty checks (evidence, status, overflow) and a test for them.

## Pull requests

- Add or adjust tests in the same PR, and include before/after previews (`startup-kit preview`) for visual changes.
- Update `CHANGELOG.md` under *Unreleased*.
- Keep diffs focused. Don't mix refactors with features.

## Adding a skill

1. Create `skills/<name>/SKILL.md` with a description that says *what* the skill does and *when* to use it.
2. Put detailed methodology in `skills/<name>/references/`, and examples in `skills/<name>/examples/`.
3. Reuse the shared profile and ledger. Don't create a parallel data store.
4. Run `scripts/validate_skills.py` and the test suite.
