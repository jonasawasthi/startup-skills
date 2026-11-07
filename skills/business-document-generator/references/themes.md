# Themes

`startup-kit themes` lists them. Each one is a token set (colours, type scale, cover style) shared by DOCX, PDF, PPTX and XLSX.

| Theme | Audience | Headings | Accent | Cover | Notes |
|---|---|---|---|---|---|
| `venture` | VCs, investor proposals, analyses | Georgia | deep green | editorial | default |
| `angel` | Angel investors | Georgia | warm brown | editorial | warmer tone |
| `accelerator` | Accelerator applications | Arial | burnt orange | minimal | crisp |
| `corporate` | Corporate partners | Arial | navy | institutional | restrained |
| `institutional` | Government, grants | Arial | dark blue | institutional | numbered headings, 11 pt body |
| `internal` | Internal plans, memos | Arial | slate | minimal | utilitarian |

## Default theme by `doc_type`

investor-proposal / proposal / analysis / research-report / fundraising-plan → venture · partnership-proposal / corporate-proposal → corporate · accelerator-application → accelerator · grant-proposal / government-proposal → institutional · business-plan / internal-plan / memo → internal.

## Brand overrides

In front matter or a deck spec:

```yaml
brand:
  accent: "#0F766E"
  accent_2: "#B45309"
  heading_font: Georgia
  body_font: Arial
  logo: ../brand/logo.png
```

Or put the same keys in a theme file plus `base: venture`, and reference it with `theme_file:`. The theme checks WCAG contrast of the ink, muted and accent colours against the paper and warns below 4.5:1.
