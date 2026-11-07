# Skills catalogue

| Skill | Invoke | Inputs | Requires | Outputs | Composes with |
|---|---|---|---|---|---|
| startup-idea-evaluator | `/startup-skills:startup-idea-evaluator` or "evaluate this idea" | Idea description; optional profile or repo | Toolkit for calculators and files; web search optional | `startup-analysis/<startup>-evaluation.{md,docx,pdf}`, profile updates | research (facts), deck and proposal (via the profile) |
| pitch-deck-maker | `/startup-skills:pitch-deck-maker` or "make a pitch deck" | Repo path and/or documents; stage; audience | Toolkit (python-pptx, reportlab); poppler for previews | `investor-pitch/<deck>.{pptx,pdf}`, `-short`, `-narrative.md`, `investor-qa.md`, `missing-information.md` | evaluator, research, fundraising |
| startup-proposal-generator | `/startup-skills:startup-proposal-generator` | Proposal type, reader, profile | Toolkit (python-docx, reportlab, openpyxl) | `business-proposal/<name>.{docx,pdf,md}`, model XLSX | all |
| business-document-generator | `/startup-skills:business-document-generator` | Markdown+, deck YAML, model YAML | Toolkit | DOCX, PDF, PPTX, XLSX, MD | used by all |
| startup-research | `/startup-skills:startup-research` | Research question | Web search or fetch (states limits if absent) | `research/<brief>.md`, ledger entries, bibliography | evaluator, deck, proposal |
| fundraising-strategist | `/startup-skills:fundraising-strategist` | Profile, model, founder facts, named investors | Web search for investor research | `fundraising/` readiness, raise plan, investor profiles, outreach, data room | deck, proposal, research |

## Shared resources

- `templates/startup-profile/`: the profile every skill shares (`startup-kit profile init`).
- `knowledge/`: methodology and sources (see its README).
- `lib/startup_kit`: the engine (`bin/startup-kit --help`).
