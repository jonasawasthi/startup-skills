# Design system

Startup Skills outputs should read like the work of a serious advisory studio: editorial, calm and specific to the company. The system is implemented in `lib/startup_kit/theme.py` and shared by every renderer, so a deck, proposal and model for the same startup look like one family.

## Principles

1. **Content is the design.** Hierarchy, spacing and real data do the work, not decoration.
2. **One accent colour.** It marks what matters: the key bar, the kicker, the highlighted row.
3. **White space is structure.** Empty space is never filled with ornament.
4. **Honesty is visible.** Status pills (Live, Built, In development, Planned, Proposed) and evidence pills (Reported, Estimate, Assumption, Unverified) are part of the visual language.
5. **No generic AI aesthetics.** No gradients, glows, stock people, isometric clip-art or fake dashboards.

## Colour tokens

| Token | Default (venture) | Use |
|---|---|---|
| `ink` | `#14171A` | Primary text |
| `muted` | `#5B6470` | Body text on slides, secondary text |
| `faint` | `#9AA3AD` | Captions, footers, placeholders |
| `rule` | `#D9DDE1` | Hairlines, de-emphasised bars |
| `paper` | `#FFFFFF` | Background |
| `tint` | `#F3F4F1` | Panels, table headers, cards |
| `accent` | `#1F5C4A` | The single brand accent |
| `accent_2` | `#C8743A` | Rare secondary highlight |
| `positive` / `warning` / `negative` | `#2E7D5B` / `#B7791F` / `#B4423A` | Status and evidence semantics only |

Chart palettes come from the accent: accent → a lighter tint → accent_2 → a darker shade → muted. They are never rainbow. The theme checks WCAG contrast (≥ 4.5:1 for text tokens) and warns if a brand colour fails.

## Typography

| Role | Deck | Document |
|---|---|---|
| Display / titles | Georgia 30–44 pt (Arial for accelerator, corporate, institutional, internal) | H1 20 pt Georgia |
| Section heads | 16–22 pt Arial bold | H2 14 pt accent; H3 11.5 pt bold |
| Body | 15–17 pt Arial (muted) | 10.5 pt Arial, 1.28–1.42 leading |
| Kicker | 10 pt Arial bold caps, tracked, accent | — |
| Captions / sources | 9 pt faint | 8.5 pt muted |

Fonts are chosen so Office files render correctly on Windows and macOS without font installation. PDFs embed TrueType files when available and fall back to metric-compatible core fonts.

## Layout

**Slides (16:9, 13.333 × 7.5 in):** 0.75 in side margins · kicker at 0.55 in · title at 0.85 in (≤ 2 lines, balanced) · content band 2.25–6.55 in · source line 6.7 in · footer 7.0 in (company · confidentiality · slide number).

**Documents (A4 or Letter):** 2.3 cm side margins · header with company and title · footer with confidentiality and "Page X of Y" · cover without chrome.

## Components

| Component | Rules |
|---|---|
| Action title | A sentence stating the slide's claim |
| Points (2–4) | Rule line, number label, title, short body |
| Metric tile | Big number in the accent; label; context with base and period; evidence pill |
| Chart | Values on the marks, no gridlines, one highlighted category, source below |
| Market squares | Area proportional to value (smallest enlarged and noted); definition and status beside each |
| Comparison matrix | Drawn symbols (filled = yes, ring + dot = partial, dash = no, ring = planned); our row tinted |
| Roadmap | Status-coloured nodes and pills; planned items hollow |
| Product cards | Name, status pill, description, users |
| Diagram | Layered rows of nodes, arrows between layers; status pills on non-live nodes |
| Callouts (documents) | Tinted panel with a coloured left rule: Key, Note, Assumption, Risk, Warning |
| Tables | Tinted header, a dark rule under the header, hairlines between rows, a repeating header row |

## Audience themes

| Theme | Accent | Headings | Cover | Character |
|---|---|---|---|---|
| venture | deep green | Georgia | editorial | Confident, editorial |
| angel | warm brown | Georgia | editorial | Personal, warm |
| accelerator | burnt orange | Arial | minimal | Crisp, fast to scan |
| corporate | navy | Arial | institutional | Restrained, partnership-oriented |
| institutional | dark blue | Arial | institutional, numbered sections | Formal, compliance-ready |
| internal | slate | Arial | minimal | Utilitarian |

## Brand adoption

Use the startup's brand when it exists. The codebase scanner reports logo files and colour tokens (CSS variables, Tailwind config). Apply them through `brand:` in a deck spec or document front matter. Keep the system's structure, and swap only the tokens.
