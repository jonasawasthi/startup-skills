# Markdown+ dialect

~~~~markdown
---
title: Required
subtitle: Optional
company: Acme
author: Acme founding team
date: November 2026
version: "1.0"
doc_type: investor-proposal     # sets the default theme (see themes.md)
doc_type_label: Investor proposal
audience: venture               # or theme: <name>; overrides doc_type
confidentiality: Confidential
paper: a4                       # or letter
profile: ../startup-profile     # evidence ledger (or evidence: path/to/evidence.yaml)
toc: true                       # default: on when ≥ 6 top-level headings
cover: true
references: true                # append "Sources and evidence" for cited IDs
disclaimer: Optional cover-page note
# institutional extras: organisation, submitted_to, submitted_by, reference
---

# Heading 1
## Heading 2
### Heading 3

Paragraph with **bold**, *italic*, `code`, [link](https://example.com) and a citation [E-001].
Several citations: [E-001, E-004].

- bullet
  - nested bullet
1. numbered

| Column | Value |
|---|---:|
| right-aligned numbers | 1,200 |

> [!KEY] Callout types: NOTE, KEY, TIP, IMPORTANT, WARNING, ASSUMPTION, RISK.
> Plain "> text" renders as a quote.

```chart
title: Monthly revenue
kind: column            # column | bar | stacked-column | line
categories: [Jan, Feb, Mar]
values: [1200, 1800, 2600]        # or series: [{name: A, values: [...]}, ...]
format: currency        # number | currency | percent
prefix: "$"
highlight: 2
source: Stripe export, March 2026
evidence: [E-010]
```

![Figure caption](images/screen.png)

\pagebreak
[[toc]]
~~~~
