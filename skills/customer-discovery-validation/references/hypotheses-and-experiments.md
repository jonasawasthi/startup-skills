# Hypotheses and experiments

Background: [experimentation](../../../knowledge/customer-discovery/experimentation.md), [willingness to pay](../../../knowledge/customer-discovery/willingness-to-pay.md), [MVP validation](../../../knowledge/customer-discovery/mvp-validation.md).

## Finding hypotheses

Start from what the startup already believes:

- ledger entries with status `assumption`, `estimate` or `unverified` (`discovery hypotheses` lists those not yet covered);
- the evaluation's critical assumptions;
- the GTM spec's channel and pricing hypotheses;
- the product's reason to exist.

Write each one as a falsifiable statement about a specific segment.

## Evidence strength (computed, not declared)

| Strength | Rule |
|---|---|
| none | No supporting evidence |
| weak | Supporting entries are assumptions, estimates, unverified, founder or desk research |
| moderate | At least one verified or reported **customer** entry (interview, dataset, observed or committed signal) |
| strong | Committed or paid evidence, or at least 3 customer entries with no contradictions |

Statuses: `untested → testing → supported | contradicted | inconclusive`. The engine refuses a *supported* status that its evidence can't carry. A hypothesis is **critical** (†) when it is high risk, its evidence is weak or none, and it is unresolved. Design experiments for critical hypotheses first.

## Experiment card (13 fields)

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
13. decision rule (success, failure and inconclusive).

Also record `threshold_basis` (`heuristic`, `benchmark` with a source, or `founder`). Write structured criteria (`{metric, op, value}`) when you can, so the engine evaluates the measured results itself.

| Hypothesis type | Methods that can support it | Methods that can't |
|---|---|---|
| Problem existence, severity, frequency | Interviews (behavioural), complaint logs, observation | Surveys of opinion alone |
| Solution relevance | Prototype tests, concierge, Wizard-of-Oz, usage data | Landing-page clicks alone |
| Willingness to pay / purchase commitment | Pre-orders, deposits, paid pilots, pricing tests with real checkout | Interviews, waitlists, surveys, smoke tests |
| Distribution | Small channel tests with measured conversion | Opinions about channels |
| Retention | Cohorts over a natural usage cycle | Satisfaction surveys alone |

**Pre-register** the criteria before running the experiment. Record results as ledger entries (`dataset`, with `signal` where relevant), and reference them in `results.evidence`.
