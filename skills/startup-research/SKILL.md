---
name: startup-research
description: Researches startups, markets, customers, competitors, technologies, pricing, regulation and geographic opportunities with source discipline. It prefers primary sources, records publication and access dates, separates facts from estimates, flags outdated or conflicting evidence, cites claims inline, and writes every finding to an evidence ledger and bibliography that other skills reuse. It covers industry research, competitor intelligence, customer research, market sizing inputs, geographic analysis, business-model and pricing benchmarks, technology landscapes, regulatory research and opportunity discovery. Use when someone asks to research a market, industry, competitor, customer segment, country or region, pricing, regulation or technology for a startup, to find data for market sizing, or to fact-check startup claims.
license: MIT
compatibility: Needs a web search or fetch tool for live research. Without one it works from supplied documents and states the limitation. Ledger validation and reports use the Startup Skills toolkit (bin/startup-kit, Python 3.9+).
metadata:
  author: Jonas Awasthi
  version: "1.0.0"
  repository: https://github.com/jonasawasthi/startup-skills
  collection: startup-skills
---

# Startup Research Intelligence

Research is only useful if someone else can check it. Every finding needs a source, a date and a status.

## Setup

```bash
TK="$(cd "${CLAUDE_SKILL_DIR}" && cd -P ../.. && pwd)"; "$TK/bin/startup-kit" doctor
```

Write findings to the shared ledger (`outputs/<startup>/startup-profile/evidence.yaml`) and reports to `outputs/<startup>/research/`.

## Workflow

1. **Frame the question.** Write it as a decision ("Should we launch in market X first?") plus 3–7 sub-questions. Choose the research type(s) in [references/research-types.md](references/research-types.md).
2. **Check tool availability.** If web search or fetch is unavailable, say so at the top of the report and limit the work to the supplied materials. Never fill gaps from memory as if they were current facts. Memory-based context must be labelled "background knowledge (unverified, as of training data)".
3. **Search systematically** with the query patterns for the research type. Prefer primary sources ([source hierarchy](references/source-evaluation.md)): regulators, statistics offices, company filings and pricing pages, the codebase, official docs.
4. **Read the source**, not the snippet. Confirm the claim exists on the page, then record the publication date and the date accessed.
5. **Record each finding in the ledger** (next ID from `"$TK/bin/startup-kit" ledger next-id <ledger>`):
   ```yaml
   - id: E-031
     claim: <precise claim, with definition, geography, period>
     key: market.<metric>        # shared key lets the ledger detect conflicts
     value: 123000
     unit: <unit>
     status: verified | reported | estimate | unverified
     confidence: high | medium | low
     source: {type: web, title: <page title>, publisher: <org>, url: <url>, published: YYYY-MM, accessed: YYYY-MM-DD}
     notes: <methodology caveats, conflicts>
   ```
6. **Triangulate** important numbers with two or more independent sources. When sources disagree, record both under the same `key`, explain the difference (definitions, years, scope) or mark the weaker one `contradicted`.
7. **Validate**: `"$TK/bin/startup-kit" ledger validate <ledger>`. This flags missing dates, stale sources (> 18 months), conflicts, and "verified" claims without a URL.
8. **Write the report** from [references/report-template.md](references/report-template.md): the answer first, findings with citations near the claims, conflicting evidence, research limitations, implications, and a bibliography (`ledger bibliography <ledger>`). Build DOCX/PDF with `doc` if requested.

## Non-negotiable rules

- **No fabricated statistics.** If you can't find a number, say "not found" and describe how it could be obtained (survey, registry request, proxy method).
- **Cite close to the claim** with the ledger ID. A claim with no ID doesn't go in the report.
- **Facts vs estimates**: a vendor's market report is an *estimate* even when it's published. A company's self-reported user count is *reported*.
- **Date everything.** Flag sources older than 18 months for market data and 6 months for fast-moving areas (AI, pricing, regulation drafts).
- **Respect access.** No paywall circumvention, no scraping where it's prohibited, no personal data about private individuals.
- **Competitors are described fairly**, with current information.

## Failure handling

| Situation | Response |
|---|---|
| No web tools | Report "Research limitations: no live web access" and give a research plan (queries + target sources) instead of facts |
| Only secondary sources found | Record the claims as `unverified`, name the primary source that should be checked, and lower confidence |
| Conflicting figures | Keep both and explain. Recommend the figure to use, with reasoning |
| Paywalled data | Record the title, publisher and date, plus the publicly visible summary only, as `unverified` |
| Very recent events | State the as-of date and that facts may change |

## Validation checklist

- [ ] Every claim in the report has a ledger ID; `ledger validate` shows 0 errors.
- [ ] Publication and access dates are recorded; stale sources are flagged in the report.
- [ ] Conflicts are reported, not hidden.
- [ ] A research limitations section is present.
- [ ] The bibliography is generated from the ledger.
