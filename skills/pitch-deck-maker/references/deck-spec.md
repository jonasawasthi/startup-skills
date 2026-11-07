# Deck spec reference (`deck.yaml`)

```yaml
deck:
  company: Acme
  title: Seed round            # used in the file title
  stage: seed                  # idea | pre-seed | seed | series-a | growth (slide-count guidance)
  theme: venture               # venture | angel | accelerator | corporate | institutional | internal
  audience: venture-capital
  date: November 2026
  confidentiality: Confidential
  profile: ../startup-profile  # evidence ledger at <profile>/evidence.yaml (or set `evidence:`)
  brand:                       # optional overrides from the startup's brand
    accent: "#0F766E"
    accent_2: "#B45309"
    heading_font: Georgia      # must be installed on viewers' machines (PPTX)
    body_font: Arial
    logo: ../brand/logo.png
  filename: acme-seed          # optional output stem
slides:
  - type: cover
    ...
```

**Common slide fields:** `type`, `kicker` (small label), `title` (an action title, i.e. a full sentence), `notes` (speaker notes), `evidence: [E-…]`, `source` (free-text source line), `short: true` (include in the teaser), `variants: [name]`, `purpose` (shown in the narrative file).

| Type | Fields | Use for |
|---|---|---|
| `cover` | `title`, `subtitle` (what you do, for whom), `meta`, `logo` | Slide 1 |
| `statement` | `kicker`, `text`, `support`, `evidence` | Vision, purpose, insight |
| `closing` | `text`, `contact` | Final vision |
| `section` | `number`, `title` | Appendix divider |
| `points` | `points: [{title, body, label?, evidence?}]` (2–4) | Problem, why now, use cases, insight |
| `bullets` | `items: [{lead, detail?, status?, evidence?}]` (≤ 5) | GTM, model components, risks |
| `split` | `left: {heading, items}`, `right: {heading, items}` | Before/after, today vs with us |
| `products` | `items: [{name, status, description, users?, evidence?}]` | Product map / ecosystem |
| `screenshot` | `image`, `needed` (description if missing), `status`, `callouts: [{title, body}]` | Product demo |
| `metrics` | `items: [{value, label, context, evidence}]` (2–4), `takeaway` | Traction. **Evidence required** |
| `chart` | `chart: {kind: column\|bar\|stacked-column\|line, categories, values \| series: [{name, values}], format: number\|currency\|percent, prefix, suffix, highlight, source, evidence}`, `takeaway`, `body` | Traction curves, pricing, use of funds. **Source required** |
| `market` | `layers: [{name, value, amount?, definition, evidence \| status}]`, `method` | TAM/SAM/SOM from the calculator |
| `comparison` | `columns`, `rows: [{name, values: [yes\|partial\|no\|planned\|text]}]`, `us` | Competitive matrix |
| `positioning` | `x_axis: [low, high]`, `y_axis: [low, high]`, `points: [{name, x, y, highlight}]`, `takeaway`, `body` | 2×2 positioning (qualitative) |
| `roadmap` | `items: [{date, label, status, detail, evidence?}]` (3–6) | Roadmap with statuses |
| `diagram` | `layers: [{name, nodes: [{name, detail?, status?, highlight?}]}]` | Architecture, ecosystem, value flow |
| `team` | `people: [{name, role, bio, photo?, evidence?}]`, `hiring` | Team |
| `ask` | `amount`, `instrument`, `summary`, `use_of_funds: [{name, share, detail?}]`, `milestones` | The raise |
| `table` | `header`, `rows`, `widths?` (fractions), `size?` | Pricing tiers, unit economics |
| `quote` | `text`, `attribution`, `evidence` (**required**) | A customer voice, with consent |
| `sources` | (auto) | Final appendix slide |

## Enforcement (build errors)

Errors: unknown slide type · evidence ID not in the ledger · chart without a source/evidence · metric without evidence · quote without evidence · product or roadmap status missing or unknown · text overflow at minimum size · use-of-funds shares not summing to 100% · comparison row length mismatch · ledger errors.

Warnings: missing notes · numbers in text with no evidence on the slide · more than 70 words · more than 4 points or 6 rows · screenshot missing · ask amount missing · slide count outside the stage range.

## Writing tips

- Titles: one sentence and ideally one line. 2 lines is fine; the builder balances line breaks.
- Bodies: 8–25 words. Put the rest in `notes`.
- Metrics: show the base and the period in `context` ("Weekly active, October 2026").
- Use `highlight` in charts to direct attention to one bar.
