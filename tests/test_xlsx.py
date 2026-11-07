import os

import pytest
import yaml

from startup_kit.evidence import Ledger
from startup_kit.inspect import check
from startup_kit.xlsx import build_workbook, simulate, validate_model


def _model(example_dir):
    with open(os.path.join(example_dir, "financial-model", "model.yaml")) as f:
        return yaml.safe_load(f)


def test_model_validation_flags_missing_funding(example_dir):
    assert any("no amount" in w for w in validate_model(_model(example_dir)))


def test_simulation_basics(example_dir):
    sim = simulate(_model(example_dir))
    assert len(sim["revenue"]) == 36 and sim["revenue"][0] == pytest.approx(180)
    assert sim["cash_out_month"] is not None   # the example is default-dead without the (unset) raise


def test_workbook_formulas_match_simulation(example_dir, tmp_path):
    formulas = pytest.importorskip("formulas")
    from openpyxl.utils import get_column_letter
    m = _model(example_dir)
    path = str(tmp_path / "model.xlsx")
    info = build_workbook(m, path, Ledger.load(os.path.join(example_dir, "startup-profile", "evidence.yaml")))
    assert check(path)["ok"]
    sol = formulas.ExcelModel().loads(path).finish().calculate()

    def cell(sheet, ref):
        for k, v in sol.items():
            if k.upper().endswith(f"{sheet.upper()}'!{ref}"):
                return float(v.value[0][0])
        raise KeyError(ref)
    sim = simulate(m)
    for i in (0, 5, 12, 35):
        col = get_column_letter(i + 2)
        for key in ("revenue", "ebitda", "cash"):
            assert cell("MONTHLY", f"{col}{info['rows'][key]}") == pytest.approx(sim[key][i], rel=1e-9, abs=1e-6)
