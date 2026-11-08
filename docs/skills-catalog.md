# Skills catalogue

| Skill | Invoke | Inputs | Requires | Outputs | Composes with |
|---|---|---|---|---|---|
| startup-idea-evaluator | `/startup-skills:startup-idea-evaluator` or "evaluate this idea" | Idea description; optional profile or repo | Toolkit for calculators and files; web search optional | `startup-analysis/<startup>-evaluation.{md,docx,pdf}`, profile updates | research (facts), deck and proposal (via the profile) |
| pitch-deck-maker | `/startup-skills:pitch-deck-maker` or "make a pitch deck" | Repo path and/or documents; stage; audience | Toolkit (python-pptx, reportlab); poppler for previews | `investor-pitch/<deck>.{pptx,pdf}`, `-short`, `-narrative.md`, `investor-qa.md`, `missing-information.md` | evaluator, research, fundraising |
| startup-proposal-generator | `/startup-skills:startup-proposal-generator` | Proposal type, reader, profile | Toolkit (python-docx, reportlab, openpyxl) | `business-proposal/<name>.{docx,pdf,md}`, model XLSX | all |
| business-document-generator | `/startup-skills:business-document-generator` | Markdown+, deck YAML, model YAML | Toolkit | DOCX, PDF, PPTX, XLSX, MD | used by all |
| startup-research | `/startup-skills:startup-research` | Research question | Web search or fetch (states limits if absent) | `research/<brief>.md`, ledger entries, bibliography | evaluator, deck, proposal |
| customer-discovery-validation | `/startup-skills:customer-discovery-validation` or "help me validate this with customers" | Profile and ledger; segments; founder's interview notes, transcripts, survey exports | Toolkit for the engine and files | `customer-discovery/` interview guides, notes templates, `-report.{docx,pdf,md}`, `-hypotheses.{md,xlsx}`, ledger entries (`--record`) | evaluator (assumptions → hypotheses), GTM (ICP, pricing experiments), deck and proposal (evidence), research (desk research stays secondary) |
| gtm-strategy-maker | `/startup-skills:gtm-strategy-maker` or "build our go-to-market plan" | Profile and ledger; business model; founder's GTM hours and budget | Toolkit for the engine and files; web search for competitor research | `gtm/<startup>-gtm-strategy.{docx,pdf,md}`, `-gtm-analysis.md`, `-kpi-dashboard.xlsx`, profile updates | evaluator (ICP, risks), research (competitors), deck and proposal (GTM sections), fundraising (milestones) |
| fundraising-strategist | `/startup-skills:fundraising-strategist` | Profile, model, founder facts, named investors | Web search for investor research | `fundraising/` readiness, raise plan, investor profiles, outreach, data room | deck, proposal, research |

## Shared resources

- `templates/startup-profile/`: the profile every skill shares (`startup-kit profile init`).
- `knowledge/`: methodology and sources (see its README).
- `lib/startup_kit`: the engine (`bin/startup-kit --help`).
