# Example: Fieldnote (fictional)

Fieldnote is the repository's fictional example company: B2B software for dairy cooperatives. Its business model
example lives in [`examples/fieldnote/business-model/`](../../../examples/fieldnote/business-model/fieldnote-business-model.yaml)
and builds on the shared Fieldnote profile and customer discovery example:

- a nine-block canvas mixing evidence-backed items (interviews, a paid prepayment experiment), founder statements,
  hypotheses linked to the discovery register, recommendations and unknowns;
- value proposition canvases for cooperative managers (buyers) and field agents (users), with contradicting
  evidence kept visible;
- three revenue streams: two *generating* (backed by paid evidence) and one *proposed* processor data product;
- costs with estimates, assumptions and explicit unknowns;
- payment, regulatory and partner dependencies with open questions;
- three alternatives on the default qualitative scale: a recommended subscription, a viable hybrid and a rejected
  milk-trade marketplace (with its marketplace design and an empty, unmeasured funnel);
- seven assumptions, linked to discovery hypotheses, and stress scenarios with labelled inputs.

The engine rates it *supported by customer evidence*, not *economically viable*: support costs are assumptions and
renewals are unmeasured. All customers, prices, costs and results are invented for illustration. Try it:

```bash
bin/startup-kit business-model report examples/fieldnote/business-model/fieldnote-business-model.yaml --out /tmp/bm --xlsx
bin/startup-kit business-model check /tmp/bm/fieldnote-business-model-report.md --spec examples/fieldnote/business-model/fieldnote-business-model.yaml
bin/startup-kit doc /tmp/bm/fieldnote-business-model-report.md --out /tmp/bm
```
