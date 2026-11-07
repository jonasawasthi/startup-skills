# Security policy

## Reporting a vulnerability

Please report security issues privately through GitHub's "Report a vulnerability" (Security → Advisories) on `jonasawasthi/startup-skills`. Don't open public issues for them. We aim to acknowledge reports within 5 working days.

## Security design

- **Read-only codebase analysis.** `startup-kit scan` never writes to the scanned repository. It skips `.env*`, keys, certificates and credential files without opening them (except `.env.example`-style templates, from which only variable *names* are read). It never prints secret values.
- **Private outputs.** Generated analyses go to `outputs/`, which is gitignored. Don't commit real startup data to public forks.
- **No network calls from the engine** except the optional `scripts/check_links.py`. Web research is done by the agent's own tools and recorded with sources.
- **Untrusted inputs.** Deck specs and Markdown are parsed with `yaml.safe_load` and a custom Markdown parser. No code from inputs is executed.
- **Dependencies** are pinned to maintained versions in `requirements.txt`. `formulas` (EUPL-1.2) is an optional development dependency for spreadsheet recalculation and is not vendored.

## Scope notes

Generated documents may contain confidential business information. Treat them like any other confidential file. Investor research must use public, professional information only (see `knowledge/frameworks/investor-fit.md`).
