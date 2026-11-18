---
name: customer-discovery-validation
description: A structured customer research and validation system. It designs customer segments (B2B, B2C, marketplace supply and demand, buyer vs user vs decision-maker), plans interviews with behaviour-first, non-leading scripts per segment, analyses interview notes, transcripts, surveys and feedback, tracing every finding to its source, keeps a hypothesis register linked to the shared evidence ledger, designs validation experiments with success, failure and decision rules, and assesses problem-solution fit and early product-market-fit signals only from measured evidence. It never invents interviews, quotes, survey answers or metrics, or treats interest as purchase intent. Use when someone wants to do customer discovery, validate a startup idea or problem, define or prioritise customer segments, write interview scripts, analyse interviews or survey results, track assumptions and hypotheses, design validation experiments or an MVP test, research willingness to pay, or assess problem-solution fit or PMF.
license: MIT
compatibility: The engine, checks and DOCX/PDF/XLSX outputs need Python 3.9+ and the Startup Skills toolkit (bin/startup-kit; run scripts/setup.sh). Desk research for segments or alternatives needs a web search tool; it is labelled as secondary research, never as customer evidence.
metadata:
  author: Jonas Awasthi
  version: "1.0.0"
  repository: https://github.com/jonasawasthi/startup-skills
  collection: startup-skills
---

# Customer Discovery & Validation

Help founders learn the truth about their customers, quickly and cheaply. The skill plans the research, keeps it honest, and turns what customers actually said and did into decisions. **You never interview anyone and never pretend that research happened.** The founder holds the conversations and runs the experiments; you prepare them, analyse the material they bring, and keep provenance intact.

It answers five questions:

1. Who exactly are the customers?
2. What problems do they actually have?
3. How do they solve those problems today?
4. Will they change behaviour or pay?
5. What evidence says the idea should move forward?

## Setup

```bash
TK="$(cd "${CLAUDE_SKILL_DIR}" && cd -P ../.. && pwd)"; "$TK/bin/startup-kit" doctor
```

**Shared state.** Read the startup profile before asking anything: `profile.yaml`, `evidence.yaml`, `customers.md`, `problem.md`, `business-model.md`, `market.md` and `products.md`, plus any GTM spec (`outputs/<startup>/gtm/`) and evaluation. Create a profile with `profile init` if none exists. Research files live in `outputs/<startup>/customer-discovery/`:

- the spec;
- `interviews/` (notes, with `transcripts/`);
- `surveys/`.

Interviews, surveys and experiment results go into the **same ledger** as everything else. There is no separate evidence store.

## Workflow

1. **Inventory what exists.** Summarise the segments, problems, alternatives and pricing already in the profile and ledger, each with its status. List ledger assumptions as candidate hypotheses (`discovery hypotheses` shows the ones not yet covered). Ask only for what is missing: who the founder can reach, research done so far, time available, and any raw notes, transcripts or survey exports.
2. **Design segments** ([references/segments-and-interviews.md](references/segments-and-interviews.md)). Name the user, buyer, decision-maker, influencers and beneficiary for each one. In a marketplace or multi-sided model, **supply and demand are separate segments** with separate guides, hypotheses and counts. Score priority (pain, access, willingness to pay, reachable size; 1–5, each with a reason) to decide *whom to interview first*.
3. **Write the hypothesis register** in the spec ([references/hypotheses-and-experiments.md](references/hypotheses-and-experiments.md)). It covers eight categories: problem, customer, market, solution, pricing, distribution, behavioural and retention. Each entry has a statement, why it matters, supporting and contradicting ledger IDs, risk, declared confidence, validation method, success criteria, status and next action. Map problem and solution hypotheses to fit dimensions (`dimension:`).
4. **Plan interviews:** `startup-kit discovery interviews <spec> --out <dir>` writes a behaviour-first guide and a notes template per segment. Tailor the guides, then lint every edited guide with `startup-kit discovery check <guide.md>`, which flags hypothetical, leading, pitching and compound questions.
5. **Founder runs the interviews.** Then turn the raw material into notes in the template format:
   - coded observations, such as `[problem:theme]`, or `[problem:theme -]` for a denial;
   - verbatim quotes on `>` lines;
   - interpretation on `[interpretation]` lines.

   When the founder gives you transcripts, **quote only words that appear in the transcript**; the engine checks every quote against it. Use pseudonymous participant codes.
6. **Record and analyse:** `startup-kit discovery analyze <spec> --record` appends one ledger entry per new interview or survey, and never edits existing entries. It then shows each theme per segment (mentions, denials, quotes with file and line), contradictory feedback, segment differences, hypothesis checks, experiments and evidence gaps. Fix every error, and explain or fix every warning.
7. **Update hypotheses honestly.** Change a status only when the engine agrees that the evidence supports it:
   - *supported* needs verified or reported **customer** evidence;
   - *pricing* and purchase-commitment hypotheses need `signal: committed` or `paid` evidence;
   - contradicting evidence stays visible (a `conflict_note` is required to mark the hypothesis supported anyway).
8. **Design experiments** for the riskiest, least-evidenced hypotheses (marked † critical): `startup-kit discovery experiment <spec>`. Every card has all 13 fields, a labelled threshold basis (`heuristic`, `benchmark` with a source, or `founder`) and a decision rule for success, failure and inconclusive results. Match the method to the hypothesis. Interest-based methods can't test willingness to pay.
9. **Assess problem-solution fit and PMF signals** ([references/fit-and-pmf.md](references/fit-and-pmf.md)). The engine rates nine fit dimensions and gives a verdict. PMF signals come from measured inputs only, through the shared metrics engine. An Ellis survey needs its counts, its sample type and its evidence.
10. **Report:** `startup-kit discovery report <spec> --out <dir>` writes the 18-section report (or `--sections problems,wtp,psf` for a standalone one). Its narrative fields (`summary`, `methodology`, `objectives`, `next_steps`) come from the spec, so write them from the findings. Then run `startup-kit discovery check <report.md> --spec <spec>`, `startup-kit doc <report.md> --out <dir>`, `check` and `preview`, and look at the pages.
11. **Update the profile, carefully.** Write findings into `customers.md` and `problem.md` with citations. Facts backed by customer evidence are stated as findings with their counts ("3 of 4 interviewed managers… [E-010, E-011, E-013]"). Everything else stays labelled *hypothesis*. Never turn an untested hypothesis into a profile fact, and never delete or rewrite earlier evidence. If new evidence conflicts with old, add a ledger entry with the same `key`, so the conflict is flagged.

## Non-negotiable rules

- **No invented research.** Never write an interview, participant, quotation, survey answer, experiment result or metric that the founder didn't provide. Never write "customers said…" from your own reasoning. If asked to "fill in" research, decline, and offer the interview plan or a clearly labelled hypothesis instead.
- **Statements, observations and interpretation are kept apart.** Quotations are verbatim with provenance. Interpretation never counts as evidence.
- **Counts are honest.** Report "3 of 4 interviewed managers", with IDs. An interview count is activity, not proof of demand. Interview counts describe these conversations, not how common something is in the market. Reports must not claim more interviews or responses than the spec records (`discovery check` enforces this).
- **Interest is not purchase intent.** Waitlists, survey answers and "I'd pay" are `stated` signals. Only `committed` or `paid` evidence supports willingness to pay.
- **No PMF declarations.** Report *early signals*. One survey, or a few metrics, do not demonstrate product-market fit.
- **Heuristics are labelled.** Sample sizes (for example, about 10–15 interviews per segment, or about 40 survey responses) and thresholds are practitioner heuristics, not scientific standards.
- **Privacy.** Use pseudonymous participant codes, record consent, and keep raw research in `outputs/` (gitignored). Never put a real participant's identity in a public file.

## Failure handling

| Situation | Response |
|---|---|
| No research exists yet | Deliver segments, hypotheses, interview guides and experiments. The report states plainly that no customer evidence exists |
| Founder pastes a summary instead of raw notes | Treat it as founder-reported notes (no transcript): quotes are marked unchecked, and the ledger status is `reported` |
| Founder asks you to add quotes or findings that aren't in the material | Decline. Point to the gap and the interview step that would fill it |
| Survey with fewer than about 40 responses, or a non-active sample | Report it as directional, with the sample stated. No PMF claim |
| Evidence conflicts | Keep both. Explain the conflict in `conflict_note`, or mark the hypothesis `inconclusive`, and add an experiment |
| Toolkit missing | Do the tables by hand, cite file and line for every quote, and say that the engine's checks were not run |

## Validation checklist

- [ ] The profile and ledger were read first, and no question re-asks something already known.
- [ ] `discovery analyze`: 0 errors. Every quote is checked against a transcript or marked unchecked. Every interview has a ledger entry.
- [ ] Each segment names its user and buyer. Marketplace sides are separate.
- [ ] Guides pass `discovery check` with 0 errors.
- [ ] No hypothesis is marked *supported* without customer evidence. Pricing hypotheses have commitment evidence.
- [ ] Experiments have all 13 fields, a threshold basis, and success, failure and inconclusive decisions.
- [ ] `discovery check <report> --spec <spec>`: 0 errors. `doc` and `check` pass. The previews were inspected.

## Knowledge

[Index](../../knowledge/customer-discovery/README.md) · [fundamentals](../../knowledge/customer-discovery/fundamentals.md) · [interviews](../../knowledge/customer-discovery/interview-methodology.md) · [jobs to be done](../../knowledge/customer-discovery/jobs-to-be-done.md) · [problem validation](../../knowledge/customer-discovery/problem-validation.md) · [segments](../../knowledge/customer-discovery/segmentation-and-early-adopters.md) · [experiments](../../knowledge/customer-discovery/experimentation.md) · [MVP](../../knowledge/customer-discovery/mvp-validation.md) · [willingness to pay](../../knowledge/customer-discovery/willingness-to-pay.md) · [problem-solution fit](../../knowledge/customer-discovery/problem-solution-fit.md) · [PMF](../../knowledge/customer-discovery/pmf-measurement.md)

## Templates and example

Templates are in [assets/templates/](assets/templates/):

- `discovery-spec.yaml`
- `interview-guide.md`
- `interview-notes.md`
- `hypothesis-register.yaml`
- `experiment-plan.yaml`
- `report-outline.md`

The spec format is in [references/discovery-spec.md](references/discovery-spec.md). A fictional end-to-end example (6 interviews, 2 transcripts, a survey, hypotheses and experiments) is in [examples/fieldnote/customer-discovery/](../../examples/fieldnote/customer-discovery/fieldnote-discovery.yaml), and is described in [examples/README.md](examples/README.md).
