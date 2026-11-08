---
title: Hypothesis-driven and lean experimentation
source: Eric Ries (The Lean Startup); Strategyzer (Testing Business Ideas)
urls:
  - https://theleanstartup.com/principles
  - https://www.strategyzer.com/library/testing-business-ideas-book
sources:
  - {title: "The Lean Startup Methodology", url: "https://theleanstartup.com/principles", author: Eric Ries, verification: read-at-source}
  - {title: "Testing Business Ideas", url: "https://www.strategyzer.com/library/testing-business-ideas-book", author: "David J. Bland, Alexander Osterwalder (Strategyzer)", verification: url-verified}
authors: [Eric Ries, David J. Bland, Alexander Osterwalder]
date_checked: 2026-11-08
type: attributed-summary + original-analysis
verification: read-at-source (Lean Startup principles); url-verified (book page)
related_skills: [customer-discovery-validation, gtm-strategy-maker]
---

# Hypothesis-driven experimentation

See also: [validation experiments framework](../frameworks/validation-experiments.md).

## Attributed (The Lean Startup)

- **Validated learning** is the unit of progress: learning shown by evidence from experiments, not by output.
- **Build–measure–learn.** Turn an idea into something testable, measure how customers respond, and decide to *pivot or persevere*. The faster the loop, the better.
- **Innovation accounting** measures progress with actionable metrics that show cause and effect, not vanity metrics.
- **The MVP** is the smallest thing that starts the learning loop.

*Testing Business Ideas* (Bland and Osterwalder, Strategyzer) is a book-length library of experiment types for testing desirability, feasibility and viability.

## How the skill applies this (original synthesis)

Every experiment card has 13 fields, and the engine rejects cards with any of them missing:

1. hypothesis;
2. objective;
3. target customer;
4. method;
5. resources;
6. duration;
7. cost;
8. execution steps;
9. success criteria;
10. failure criteria;
11. evidence to collect;
12. biases and limitations;
13. decision rule.

Rules:

- **Falsifiable.** The success and failure criteria must differ, and the decision rule must say what happens on each outcome, including an inconclusive one.
- **Thresholds are labelled.** Every threshold states its basis: `heuristic`, a `benchmark` with its source, or the `founder` decision. None is presented as a scientific standard. Small samples give direction, not proof.
- **Match the method to the hypothesis.** Interest-based methods (interviews, surveys, waitlists, landing pages) can test problem and messaging hypotheses. Pricing and willingness-to-pay hypotheses need commitment-based methods (pre-orders, deposits, paid pilots).
- **Pre-register.** Write the criteria before running the experiment. Changing them after seeing results makes the result inconclusive.
- **Record results as ledger evidence** (`source.type: dataset` or `interview`), with the measured numbers. The engine evaluates numeric criteria against the measured results.

| Experiment type | Tests best | Typical bias |
|---|---|---|
| Customer interviews | Problem, job, alternatives | Politeness, recall, interviewer bias |
| Landing page / smoke test | Message resonance, demand signal | Traffic source shapes results; clicks ≠ purchases |
| Waitlist | Interest, reach of a channel | Free to join; weak intent |
| Prototype test | Usability, solution relevance | Lab behaviour ≠ real use |
| Concierge MVP | Value of the outcome, willingness to pay | Founder effort hides real costs |
| Wizard-of-Oz | Solution desirability, without building it | Must disclose where required; scale unknown |
| Paid pilot | Willingness to pay; B2B buying process | Small n; champion effects |
| Pre-order / deposit | Purchase intent with money | Refund expectations; early fans aren't typical |
| Pricing test | Price sensitivity | Segment mix; novelty |
| A/B test | Causal difference between variants | Needs enough traffic; peeking |
| Manual service delivery | Operational feasibility, value | Doesn't scale |
| Retention / repeat-usage test | Habit, ongoing value | Short windows mislead |
