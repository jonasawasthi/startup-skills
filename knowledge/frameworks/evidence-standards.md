---
title: Evidence standards
type: original-analysis
date_checked: 2026-11-07
related_skills: [all]
---

# Evidence standards

## Status vocabulary (ledger `status`)

| Status | Meaning | How it may appear in documents |
|---|---|---|
| `verified` | Backed by a primary source, the codebase, accounts, or a reproducible calculation | Plain statement with citation |
| `reported` | Stated by the company or founder, not independently checked | "Company-reported" label |
| `estimate` | Derived by reasoning from partial data | "Estimate" label, method shown |
| `assumption` | A planning input not yet validated | "Assumption" label, owner named |
| `unverified` | From a secondary or uncertain source | "Unverified" label, or omitted |
| `contradicted` | Conflicts with stronger evidence | Not used as support. Shown as "disputed" if discussed |

## Product status vocabulary

`live` (deployed and used; needs deployment evidence) · `built` (implemented but not launched) · `in-development` (partially implemented) · `planned` (on the roadmap, not started) · `proposed` (an idea under consideration) · `unknown` (no evidence either way).

Code in a repository proves **built** at most. **Live** also needs evidence of deployment and use: a live URL check, a store listing, analytics or founder confirmation (recorded as *reported*).

## Source hierarchy (prefer higher)

1. Primary data: accounts, databases, analytics exports, contracts, the codebase
2. Official statistics, regulators, company filings
3. Company primary publications (pricing pages, docs, press releases), noting the company's interest
4. Reputable research and journalism, with the date and methodology noted
5. Secondary aggregators (cite only with a primary corroboration, or mark *unverified*)

## Dates

Record `published` (when the source was published) and `accessed` (when we read it). Market data older than about 18 months is flagged for refresh.

## Conflicts

When two sources disagree, record both, give them the same `key`, and either explain the difference (different definitions, years or geographies) or mark the weaker one `contradicted`.
