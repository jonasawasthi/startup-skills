import pytest

from startup_kit.calc import market_size, market_size_md, unit_economics
from startup_kit.evidence import Ledger


def test_market_size_inherits_weakest_status(ledger_file):
    L = Ledger.load(ledger_file)
    spec = {"currency": "USD", "geography": "X",
            "tam": {"factors": [{"label": "customers", "value": 1000, "evidence": "E-001"},
                                {"label": "budget", "value": 600, "evidence": "E-003"}]},
            "sam": {"base": "tam", "factors": [{"label": "reach", "value": 0.5, "status": "estimate"}]}}
    r = market_size(spec, L)
    assert r["layers"]["tam"]["value"] == 600000
    assert r["layers"]["tam"]["status"] == "assumption"
    assert r["layers"]["sam"]["value"] == 300000
    md = market_size_md(r)
    assert "TAM" in md and "assumption" in md


def test_unsourced_factor_is_flagged():
    r = market_size({"tam": {"factors": [{"label": "made-up", "value": 1e9}]}})
    assert r["layers"]["tam"]["status"] == "assumption"
    assert any("neither evidence nor status" in i for i in r["issues"])


def test_sam_larger_than_tam_detected():
    r = market_size({"tam": {"factors": [{"label": "a", "value": 10, "status": "estimate"}]},
                     "sam": {"base": "tam", "factors": [{"label": "b", "value": 2, "status": "estimate"}]}})
    assert any("SAM exceeds TAM" in i for i in r["issues"])


def test_unit_economics():
    r = unit_economics(arpu_month=60, gross_margin=0.8, monthly_churn=0.02, cac=600)
    assert r["ltv"] == pytest.approx(2400)
    assert r["ltv_to_cac"] == pytest.approx(4)
    assert r["payback_months"] == pytest.approx(12.5)


def test_zero_churn_rejected():
    with pytest.raises(ValueError):
        unit_economics(60, 0.8, 0, 100)
