# Example: Fieldnote (fictional)

Fieldnote is the repository's fictional example company: B2B software for dairy cooperatives. Its customer discovery
example lives in [`examples/fieldnote/customer-discovery/`](../../../examples/fieldnote/customer-discovery/fieldnote-discovery.yaml):

- three segments: cooperative managers (buyer and decision-maker split), field agents (users) and dairy processors (not yet interviewed);
- six coded interviews, two with transcripts, so their quotations are checked;
- one manager *denies* the core problem, so the analysis shows contradictory feedback and a conflict note;
- a 12-response survey of active users, which is reported as directional;
- seven hypotheses, from supported (with interview or paid evidence) to critical and untested;
- three experiments, one complete with a measured outcome;
- ledger entries E-010 to E-017 in the shared Fieldnote profile.

All participants, quotations and results are invented for illustration. Try it:

```bash
bin/startup-kit discovery analyze examples/fieldnote/customer-discovery/fieldnote-discovery.yaml --out /tmp/cd
bin/startup-kit discovery report examples/fieldnote/customer-discovery/fieldnote-discovery.yaml --out /tmp/cd
bin/startup-kit doc /tmp/cd/fieldnote-discovery-report.md --out /tmp/cd
```
