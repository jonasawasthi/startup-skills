# Ottlebrook: a second, physical-product example

**Fictional example.** Ottlebrook Pty Ltd is an invented Australian company that designs a folding electric heated clothes airer, the DR-2, has it made by a contract manufacturer, and sells it through one national homewares retailer and its own website. The company, retailer, manufacturer, consultant, interview participants and every figure are invented and labelled in [`startup-profile/evidence.yaml`](startup-profile/evidence.yaml). Nothing here asserts that any real business is or is not viable.

The investor profiles used (Janine Allis, Davie Fogarty, Ritu Singh Vaidya) are real people's sourced, dated, public profiles from [`skills/investor-panel-evaluator/investors/`](../../skills/investor-panel-evaluator/investors/). Every shark-tank document is an analytical simulation of how their documented lenses bear on the evidence; none is a statement by them, and nothing says or implies that any of them knows of or would back Ottlebrook.

## Why this example exists

Fieldnote, the repository's main example, is subscription software. This example tests whether the investor-panel-evaluator method holds for a business that shares nothing with it: a manufactured appliance, a different country (Australia, currency AUD, Australian rules), a retailer between the company and its customers, inventory and working capital, certification and warranty returns.

No software, subscription or marketplace concept applies here. There is no take rate, liquidity, churn, logo retention or network effect. The base read uses the hardware and consumer-goods vocabulary from the skill's [business types](../../skills/investor-panel-evaluator/references/business-types-and-stages.md): bill of materials and landed cost, the retailer's margin and deductions, sell-through per store per week, defect and return rates, minimum order quantities, stock bought before the retailer pays, and electrical safety certification. The type is `[hardware, consumer-goods]` and the stage `early-revenue`, which makes nine dimensions critical (D01, D03, D07, D08, D09, D11, D12, D14, D15).

It shows three things the Fieldnote example does not:

1. **A panel that converges on a critical weakness.** Unit economics fail after the retailer's margin on verified evidence: contribution is AUD -3.36 per unit, calculated from invoices, the signed supply agreement and the retailer's returns report (E-009). D07 is critical, so it decides every member's stance, and all three are Not persuaded. The only dimensions the map marks divergent are the documented-gap re-tags (D07 and D08 for Davie Fogarty), which change no stance, so the discussion is a note with no exchange rows. Each evaluation declares the convergence on D07 so the pairwise name-swap check does not mistake it for copying.
2. **Judgements that separate.** Demand is Strong on verified sell-through and a paid re-order, and certification is Strong, yet J1 Good business is No and J5 Should not proceed in its current form is Yes. The verdict names the form that fails (DR-2 to one retailer at the current price and order size) and the changes that would re-open the case. J4 is No because no critical dimension is Unknown: the current form is answered, and it is the changed forms that would need validation.
3. **A known-gap re-tag.** Physical retail and wholesale distribution is a documented gap in Davie Fogarty's profile. His L2 lens (paid acquisition with margin headroom) would otherwise make points about the retailer's margin stack and the retail channel's cost; those two points are re-tagged `base` and listed under "Outside documented expertise", while his L2 point about margin headroom for paid acquisition on the company's own website stays tagged.

It also shows a cross-programme panel: a Shark Tank Nepal profile reads an Australian company, and Australian rules and markets still apply.

## Reading order

| # | File | What it demonstrates |
|---|---|---|
| 1 | [startup-profile/](startup-profile/) | Created with `startup-kit profile init`; a 20-entry fictional ledger (11 verified, 7 reported of which 6 founder-provided and 1 interview, 1 estimate, 1 assumption) and short narrative files that cite it |
| 2 | [shark-tank/base-read.yaml](shark-tank/base-read.yaml) and [base-read.md](shark-tank/base-read.md) | Strong 2, Adequate 4, Weak 5, Unknown 4. Weak ratings rest on verified documents or founder statements against interest (cash, single supplier); D06 and D07 apply the anchor "price below cost" consistently |
| 3 | [shark-tank/evaluation-janine-allis.md](shark-tank/evaluation-janine-allis.md) | The retailer's shelf margin read through store and franchise economics (L2), with the documented basis of that reading stated (a franchise network built before expansion, and stability before franchising) and the analogy marked as the simulation's; the D06 point that merely restates the shared rating is `base` |
| 4 | [shark-tank/evaluation-davie-fogarty.md](shark-tank/evaluation-davie-fogarty.md) | The known-gap re-tag; demand read through L1, and margin headroom for paid acquisition through L2 |
| 5 | [shark-tank/evaluation-ritu-singh-vaidya.md](shark-tank/evaluation-ritu-singh-vaidya.md) | Cash and supplier readiness first (L1, L4); a lens whose documented basis is another country applied to the startup's own market |
| 6 | [shark-tank/panel-2026-11-16.md](shark-tank/panel-2026-11-16.md) | A divergence map of roles and evidence demanded; the outside-expertise note in place of an exchange, and the dropped difference noted under Disagreements explained; unanimous (3 of 3), the same weakness reaching each member by a different route under Competing priorities |
| 7 | [shark-tank/verdict.md](shark-tank/verdict.md) | J1 No, every J2 class No, J3 No, J4 No, J5 Yes with the re-opening changes; experiments that test the changed forms, not the current one |

There is no interrogation in this example; the Fieldnote example shows one.

## Reproduce the checks

From the repository root:

```bash
bin/startup-kit ledger validate examples/ottlebrook/startup-profile/evidence.yaml
bin/startup-kit profile validate examples/ottlebrook/startup-profile
bin/startup-kit shark-tank context examples/ottlebrook/startup-profile
bin/startup-kit shark-tank base-read examples/ottlebrook/shark-tank/base-read.yaml \
  --profile examples/ottlebrook/startup-profile --out examples/ottlebrook/shark-tank/base-read.md

cd examples/ottlebrook/shark-tank
K=../../../bin/startup-kit; P=../startup-profile
$K shark-tank check evaluation-janine-allis.md      --profile $P --against evaluation-davie-fogarty.md --against evaluation-ritu-singh-vaidya.md
$K shark-tank check evaluation-davie-fogarty.md     --profile $P --against evaluation-janine-allis.md --against evaluation-ritu-singh-vaidya.md
$K shark-tank check evaluation-ritu-singh-vaidya.md --profile $P --against evaluation-janine-allis.md --against evaluation-davie-fogarty.md
$K shark-tank check panel-2026-11-16.md --profile $P --against evaluation-janine-allis.md \
  --against evaluation-davie-fogarty.md --against evaluation-ritu-singh-vaidya.md
$K shark-tank check verdict.md --profile $P
```

Each check reports 0 errors and 0 warnings. `check` reads `base-read.yaml` beside each document to confirm that every stance follows from the base read and that every deciding Weak or Unknown dimension has its concern row (guard T6). Simulation labels carry the profile's `last_verified` date and the base read's ledger snapshot (2026-11-10). The test `tests/test_shark_tank.py::test_tracked_example_passes_every_engine_check` runs these checks on this folder as well as on the Fieldnote example.
