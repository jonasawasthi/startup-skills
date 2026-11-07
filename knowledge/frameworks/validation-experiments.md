---
title: Validation experiments
type: original-analysis
sources: [yc/talking-to-users.md, yc/mvp.md, paul-graham/essay-index.md]
date_checked: 2026-11-07
related_skills: [startup-idea-evaluator]
---

# Validation experiments

Every critical assumption gets an experiment with a **metric, a threshold and a kill criterion**, decided *before* the experiment runs.

| Experiment | Tests | Typical cost | Strong signal | Kill signal (example) |
|---|---|---|---|---|
| Problem interviews (10–15 per segment) | Problem exists, frequency, current spend | Days | ≥ 6/10 describe a recent costly incident and an existing workaround | < 3/10 can recall a specific incident |
| Landing page + targeted traffic | Message resonance, segment | $100s | Email → call conversion; calls booked | CTR/conversion far below the channel benchmark after message iterations |
| Pre-sale / letter of intent | Willingness to pay | Weeks | Paid deposits or signed LOIs with a price | Interest evaporates at price discussion |
| Concierge MVP | Value of the outcome | Weeks | Repeat usage; asks to continue | No repeat usage after delivery |
| Wizard-of-Oz | Workflow fit before automation | Weeks | Task completion and repeat requests | Users revert to the old workflow |
| Prototype usability test (5–8 users) | Usability of the core job | Days | Core task completed unaided | Repeated failure on the core task |
| Pilot with a design partner | Real-environment value, buying process | 1–3 months | Pilot → paid conversion; expansion | No decision-maker engagement |
| Channel test | CAC in a channel | $100s–$1,000s | CAC within the payback target | CAC > 3× target after optimisation |

## Template (one per critical assumption)

```
Assumption (ledger ID):
Why it matters (what fails if it's wrong):
Experiment:
Metric and success threshold:
Kill criterion:
Sample / duration / cost:
Owner and date:
Result → ledger update (status change from assumption to verified, or contradicted):
```
