import datetime as dt

from startup_kit.evidence import Ledger, cited_ids, numeric_claims


def test_load_and_summary(ledger_file):
    L = Ledger.load(ledger_file)
    assert len(L) == 4
    assert L.summary()["assumption"] == 1
    assert L.next_id() == "E-005"


def test_conflicting_values_are_reported(ledger_file):
    """Contradictory data: two sources disagree on the same key."""
    issues = Ledger.load(ledger_file).conflicts()
    assert len(issues) == 1 and "traction.paying" in issues[0].message


def test_stale_source_flagged(ledger_file):
    issues = Ledger.load(ledger_file).validate(today=dt.date(2026, 11, 7))
    assert any("older than" in i.message and i.id == "E-004" for i in issues)


def test_verified_requires_reference(tmp_path):
    p = tmp_path / "e.yaml"
    p.write_text("- {id: E-001, claim: x, status: verified, confidence: high, source: {type: web}}\n")
    errs = [i for i in Ledger.load(str(p)).validate() if i.level == "error"]
    assert any("requires source.url" in i.message for i in errs)


def test_invalid_status_and_missing_source_type(tmp_path):
    p = tmp_path / "e.yaml"
    p.write_text("- {id: E-1, claim: x, status: true-ish, confidence: high}\n")
    msgs = " ".join(i.message for i in Ledger.load(str(p)).validate())
    assert "id must look like" in msgs and "status" in msgs and "source.type" in msgs


def test_badge_uses_weakest_status(ledger_file):
    L = Ledger.load(ledger_file)
    assert L.badge(["E-001"]) is None
    assert L.badge(["E-001", "E-002"]) == "Reported"
    assert L.badge(["E-001", "E-003"]) == "Assumption"


def test_assumption_cited_as_fact_warns(ledger_file):
    L = Ledger.load(ledger_file)
    bad = L.check_text("Customers spend $600 a year [E-003].", "doc")
    ok = L.check_text("We assume customers spend $600 a year [E-003].", "doc")
    assert any(i.level == "warning" for i in bad)
    assert not ok


def test_unknown_citation_is_error(ledger_file):
    issues = Ledger.load(ledger_file).check_text("Revenue grew [E-099].", "doc")
    assert issues and issues[0].level == "error"


def test_helpers():
    assert cited_ids("a [E-001, E-002] b [E-010]") == ["E-001", "E-002", "E-010"]
    assert numeric_claims("We have 1,200 users and 40% growth")
    assert not numeric_claims("Records live in notebooks")
