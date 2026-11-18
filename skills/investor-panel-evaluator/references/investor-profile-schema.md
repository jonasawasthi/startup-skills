# Investor profile schema

An investor profile is one Markdown file with YAML front matter in an investor library. The shipped library is [`investors/`](../investors/README.md). A profile holds **sourced facts** about a real person's public business record and a small set of **evaluation lenses**, which are labelled analytical interpretations of that record. The simulation may use nothing else about the person.

Validate a library with `"$TK/bin/startup-kit" shark-tank profiles`. A profile that fails validation is not used.

Start a new profile from the [template](../assets/templates/investor-profile.md). The steps for adding, updating and verifying are in [maintaining investors](maintaining-investors.md).

## File rules

- Path: `<library>/<id>.md`. `id` is a lowercase slug (`[a-z0-9-]`) and equals the file name.
- One person, one file, even if they appeared on several programmes.
- Everything the simulation uses is in the front matter. The body is a short summary for human readers.
- Cite sources as `[S1]` in the body. Never use `[E-…]`: that form is reserved for the startup's evidence ledger.
- Public, professional information only.

## Front matter

```yaml
---
id: example-investor
name: Example Investor
name_variants: []                  # documented alternative spellings, if any
type: investor-profile
kind: programme-investor           # programme-investor | independent-investor
regions: [US]                      # ISO 3166-1 alpha-2 codes of the markets they mainly operate in
programmes:                        # may be empty for an independent-investor
  - programme: shark-tank-us       # lowercase slug; see the programme list below
    role: investor                 # investor | guest
    seasons: "4–18"
    panel_status: current          # current | former | unconfirmed | dormant
    status_note: Named as a permanent panel member for season 18.
    status_checked: 2026-11-14
    sources: [S1]
last_verified: 2026-11-14          # date every source below was last checked
profile_confidence: medium         # high | medium | low
confidence_rationale: >-
  One or two sentences, at least 15 words, saying which claims rest on primary sources,
  which rest on press only, and what could not be confirmed.
sources:
  - id: S1
    title: "Exact page title"      # as the page shows it; the link checker compares it with the live page
    url: "https://…"
    publisher: Name of publisher
    type: broadcaster              # own-statement | official-bio | broadcaster | company | filing | press | reference
    published: 2026-07-07          # date, or "undated"
    accessed: 2026-11-14
    verification: read-at-source   # read-at-source | url-verified
    note:                          # optional
business_background:               # roles and career facts
  - {id: B1, fact: "Founded Example Co in 2003 and ran it until 2019.", sources: [S2]}
major_ventures:
  - {id: V1, name: Example Co, role: Founder and former chief executive, years: "2003–2019", status: sold, sources: [S2]}
documented_expertise:              # a domain plus the documented fact that supports it
  - {id: X1, domain: consumer product retail, basis: "Built and sold a retail product company (V1).", sources: [S2]}
documented_philosophy:             # paraphrase only; stated = their own words or writing, observed = documented behaviour
  - {id: P1, kind: stated, paraphrase: "Argues that founders should know their landed cost per unit.", sources: [S3]}
investment_history:                # may be empty; then investment_history_note is required
  - {id: H1, company: Example Portfolio Co, year: 2021, level: verified-closed, note: , sources: [S4]}
investment_history_note:           # required when the list is empty; optional otherwise
known_gaps:                        # domains with no documented experience
  - {domain: regulated financial services, basis: "No documented operating or investing record found."}
evaluation_lenses:
  - id: L1
    label: Retail margin stack
    interpretation: >-
      Analytical interpretation: the documented record (P1, X1) suggests close attention to whether
      a product keeps its margin after retailer and distributor cuts.
    derived_from: [P1, X1]
    dimensions: [D07, D09]
    attracted_by: Verified sell-through and a margin that survives retail cuts.
    concerned_by: Margins that only work when selling direct, or no retail evidence.
    evidence_demanded: [sell-through by store, retailer margin and terms, landed cost per unit]
    decline_pattern:               # optional; see the rules below
dimension_emphasis:
  primary: {D07: L1}               # at most 4
  secondary: {D09: L1}
cautions:                          # optional notes for maintainers; never used as simulation content
  - {topic: , guidance: , sources: []}
unsupported: []                    # widely repeated claims that could not be verified; kept out of the simulation
simulation_only: true
---
```

## Field rules

| Field | Rule |
|---|---|
| `kind` | `programme-investor` needs at least one `programmes` entry. `independent-investor` is for investors from outside these television programmes; `programmes` may be empty |
| `programmes[].panel_status` | `current`: named in the line-up for the latest or announced season. `former`: a documented exit. `unconfirmed`: on the latest aired season, and the next line-up has not been announced. `dormant`: the programme has no announced future season. Each entry cites a source and has a `status_checked` date no later than `last_verified` |
| `sources` | At least 2. Every source has a unique `S#` id, a title, an `https` URL, a publisher, a type, an access date and a verification value |
| `sources[].type` | `own-statement`: the person's own book, article, site, interview or talk. `official-bio`: a biography published by their company or the broadcaster. `broadcaster`: other programme or broadcaster material. `company`: a company's own site or announcement. `filing`: a regulatory or court record. `press`: established news or business press. `reference`: encyclopaedias and aggregators, used only to support another source |
| `sources[].verification` | `read-at-source`: the page was opened and the claim was read there. `url-verified`: the URL resolves and the title matches, but the content was not read (for example behind a paywall) |
| Fact entries (`B`, `V`, `X`, `P`, `H`) | Each cites at least one source that is `read-at-source` and is not of type `reference` |
| `documented_philosophy` | Paraphrase only. No quotation marks. `stated` needs an `own-statement` source or a press interview |
| `investment_history[].level` | `televised`: agreed on air, completion not confirmed. `reported-closed`: the investor, the company or press says it completed. `verified-closed`: confirmed by a filing, the company's announcement or the investor's portfolio page. `off-programme`: an investment made outside the programme, with the same sourcing standard. A televised deal is never described as an investment |
| `evaluation_lenses` | 1 to 6. `interpretation` starts with "Analytical interpretation:". `derived_from` lists existing `P` or `X` ids. `dimensions` are from D01–D15. A lens describes what the record suggests the person examines, never how they behave on television |
| `decline_pattern` | Optional text describing a documented reason for declining. Allowed only when the lens reaches at least 2 distinct sources through `derived_from`. It is the only basis for an investor-specific potential deal-breaker |
| `dimension_emphasis` | Each dimension maps to a lens that lists it. At most 4 `primary`. Unlisted dimensions are standard |
| `profile_confidence` | Must not exceed what the sources support (next section) |
| `simulation_only` | Always `true` |

**Never in a profile:** net worth, quotations, catchphrases, descriptions of temperament or personality, family or personal-life details, private contact details, on-air deal terms presented as habits, or any statement about a named startup. Wording such as "would invest in" or "is interested in" is rejected by the validator.

## Confidence

| Level | Minimum the sources must meet | Effect on the simulation |
|---|---|---|
| **high** | 6 or more `read-at-source` sources, at least 2 of them primary (`own-statement`, `official-bio`, `broadcaster`, `company`, `filing`) and at least 1 `own-statement`. Every lens reaches 2 or more sources. Verified within 12 months | Full evaluation. Potential deal-breakers allowed where a `decline_pattern` exists |
| **medium** | 3 or more `read-at-source` sources, at least 1 primary. Every lens reaches 1 or more sources. Verified within 18 months | Full evaluation. Lens points are worded "on the documented record". No potential deal-breaker from a lens that reaches only one source |
| **low** | 2 or more `read-at-source` sources, with identity and panel status sourced | Restricted mode: no investor-specific deal-breakers, at most one lens point each under attractions and concerns, and a low-confidence notice in the header. Cannot be the only investor on one side of a panel disagreement |

A `high` level should not rest only on old statements: if none of the `stated` philosophy entries cites a source published within five years, the validator warns, and the level is normally held at `medium`.

Panel status goes stale faster than the rest of a profile. The validator warns when a `status_checked` date is more than six months old, and outputs show a status with its date ("current as of 2026-11-15").

When one page mixes a publisher's own text with an interview, give the source the type of the claim it supports and say so in its `note`.

A profile below the `low` minimum is not shipped. A profile whose `last_verified` date is more than 18 months old is treated as one level lower until it is re-verified; the validator warns about it.

## Programme slugs

| Slug | Programme |
|---|---|
| `shark-tank-us` | Shark Tank (ABC, United States) |
| `shark-tank-india` | Shark Tank India (Sony) |
| `shark-tank-nepal` | Shark Tank Nepal (Himalaya TV) |
| `dragons-den-uk` | Dragons' Den (BBC, United Kingdom) |
| `shark-tank-australia` | Shark Tank Australia (Network 10) |

Any other lowercase slug is valid, so further programmes need no code change.

## Body

```markdown
# <Name>

> Profile for analytical simulation only. Public, professional information as of <last_verified>.

## Summary
Three to six sentences on the business record, each claim cited [S1].

## Panel membership
One line per programme: seasons and status, cited.

## Notes for maintainers
What could not be confirmed, and what to re-check first next time.
```

## Validation rules

`startup-kit shark-tank profiles` checks every rule above and reports errors (the profile is not used) and warnings (the profile is used with reduced confidence or should be re-verified). It also accepts `--library DIR` more than once, so a private library can sit beside the shipped one.
