# Problem-solution fit and PMF signals

Background: [problem validation](../../../knowledge/customer-discovery/problem-validation.md), [problem-solution fit](../../../knowledge/customer-discovery/problem-solution-fit.md), [PMF measurement](../../../knowledge/customer-discovery/pmf-measurement.md).

## Problem-solution fit

Map hypotheses to the nine dimensions with `dimension:`:

1. existence;
2. frequency;
3. severity;
4. urgency;
5. dissatisfaction;
6. demand for alternatives;
7. solution relevance;
8. behaviour change;
9. purchase commitment.

The engine rates each dimension as supported, contradicted, mixed, untested or "no hypothesis". Hypotheses with errors don't count. Its verdict is one of:

1. Insufficient evidence: existence is not supported.
2. Mixed: problem dimensions are contradicted.
3. Problem exists, but severity and frequency are untested.
4. Problem supported; solution untested.
5. Early problem-solution signals: no behaviour change or purchase commitment yet.
6. Problem-solution fit supported (provisional).

The report lists supported findings, contradicted findings, untested assumptions, missing evidence, critical risks and recommended experiments. Interest never moves the verdict.

## PMF signals

Inputs go under `pmf.inputs`, and are computed by the shared GTM metrics engine:

- activation, purchase conversion, churn and retention cohorts, referral rate, ARPU, CAC and LTV (only when every input exists);
- plus organic acquisition share and repeat usage.

Inputs are validated: a negative count, or a numerator above its denominator, is an error.

**Ellis survey.** Give the counts (not a percentage), the sample type and the evidence. Below about 40 responses, or with a sample that isn't recent active users, the result is directional.

**Vanity inputs** (visitors, sign-ups, waitlist, downloads) are shown as context only.

The verdict is always phrased as early signals. Demonstrated PMF needs sustained retention, repeat use or purchase, organic demand, and working economics over time.
