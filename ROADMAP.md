# Roadmap

## Near term
- **Screenshot capture** for the pitch deck maker: optional Playwright-based capture of local or public app routes, with consent and redaction of personal data.
- **Deck import**: parse an existing PPTX into a deck spec so founders can rebuild old decks with evidence.
- **More slide types**: cohort retention heatmap, funnel, unit-economics waterfall.
- **Profile sync**: generate `market.md` and `financials.md` sections from calculator and model outputs automatically.
- **Font packaging**: optional embedding of brand fonts (OFL) in PDFs, with a fallback strategy for PPTX.

- **GTM data import**: fill `metrics.inputs` from analytics, payment and ad-platform exports (CSV), keeping their source and date, so the KPI workbook updates itself.
- **GTM slides**: render the channel matrix, launch calendar and roadmap capacity table as deck slide types.

- **Discovery imports**: convert common transcript exports (Zoom, Google Meet, Otter) and survey tools (Typeform, Google Forms CSV) into the notes and survey formats, keeping speaker labels for quote checks.
- **Interview coding assistant checks**: flag observations whose code doesn't match their quote (for example, a `[wtp]` line quoting a compliment).

## Medium term
- Scenario comparison in the financial model (conservative / base / ambitious in one workbook).
- Localised document themes (Devanagari and other scripts) with font checks.
- A data-room generator assembling the profile, ledger, model and documents into a structured folder.
- Evaluation harness: scripted prompts that score skills on fabrication refusal and evidence coverage.

## Not planned
A web application, SaaS backend or database server. This project is a Claude Code skill collection by design.
