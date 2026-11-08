# Customer discovery report: outline

`startup-kit discovery report <spec> --out <dir>` generates every section below from the spec, the notes and the ledger. Only the narrative fields (`summary`, `objectives`, `methodology`, `next_steps`) are written by you, from the findings.

| # | Section | `--sections` key | Source |
|---:|---|---|---|
| 1 | Executive summary | summary | `discovery.summary`, plus a computed evidence-base callout |
| 2 | Research objectives | objectives | `discovery.objectives` |
| 3 | Research methodology | methodology | `discovery.methodology`, plus the counting rules |
| 4 | Customer segment definitions | segments | `segments` (roles, jobs, priority) |
| 5 | Interview participant summary | participants | notes front matter + ledger IDs |
| 6 | Key customer problems | problems | `[problem:…]` themes + verbatim quotes |
| 7 | Jobs to be done | jobs | `[job:…]`, `[outcome:…]` |
| 8 | Existing alternatives | alternatives | `[alternative:…]` |
| 9 | Customer behaviour findings | behavior | `[behavior:…]`, `[trigger:…]`, `[decision:…]` |
| 10 | Pricing and willingness-to-pay evidence | wtp | `[spend:…]`, `[wtp:…]`, `[commitment:…]` + evidence ladder |
| 11 | Objections and unmet needs | objections | `[objection:…]`, `[unmet-need:…]` |
| 12 | Segment comparisons | comparison | theme shares by segment; contradictions; interpretation |
| 13 | Hypothesis assessment | hypotheses | register + computed strength |
| 14 | Problem-solution fit assessment | psf | nine dimensions + verdict |
| 15 | Product-market-fit signals | pmf | measured inputs only; Ellis survey with its counts |
| 16 | Evidence gaps | gaps | uninterviewed segments, critical hypotheses, untested dimensions, unregistered assumptions |
| 17 | Recommended experiments | experiments | experiment cards |
| 18 | Next steps | next | `discovery.next_steps` |

A standalone report is any subset of these, e.g. `--sections problems,wtp,psf`.
