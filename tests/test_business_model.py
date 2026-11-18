"""business-model-designer: canvas, value propositions, revenue, costs, marketplace, alternatives, assumptions,
stress tests, payments, maturity, reports, CLI, packaging and regressions."""
import glob
import json
import os
import shutil
import subprocess
import sys

import pytest
import yaml

from startup_kit import business_model as bm
from startup_kit import gtm
from startup_kit.evidence import Ledger

SKILL = "business-model-designer"
EXTRA = """
- id: E-010
  claim: Customer interview I-01
  status: reported
  confidence: medium
  source: {type: interview, ref: notes/I-01.md}
- id: E-011
  claim: Paid pilot invoices
  status: verified
  confidence: high
  source: {type: dataset, ref: invoices.csv}
  signal: paid
- id: E-012
  claim: Founder says teachers love it
  status: reported
  confidence: low
  source: {type: founder, ref: call notes}
- id: E-013
  claim: Waitlist sign-ups
  status: reported
  confidence: medium
  source: {type: document, ref: waitlist export}
  signal: stated
- id: E-014
  claim: Market report on tutoring spend
  status: verified
  confidence: medium
  source: {type: web, url: "https://example.com/r", accessed: 2026-11-01}
- id: E-015
  claim: Customer interview I-02 (denies the problem)
  status: reported
  confidence: medium
  source: {type: interview, ref: notes/I-02.md}
- id: E-016
  claim: Signed payment provider contract
  status: verified
  confidence: high
  source: {type: document, ref: contract.pdf}
- id: E-017
  claim: Marketplace transactions export
  status: verified
  confidence: high
  source: {type: dataset, ref: tx.csv}
"""


def U(text="TBD", basis="unknown", **kw):
    return dict(text=text, basis=basis, **kw)


def canvas(**over):
    c = {k: {"items": [U()]} for k in bm.BLOCKS}
    for k, items in over.items():
        c[k] = {"items": items}
    return c


SEGMENTS = [{"id": "S1", "name": "Teachers", "side": "supply", "market": "b2c"},
            {"id": "D1", "name": "Learners", "side": "demand", "market": "b2c"}]


# ----------------------------------------------------------------------------- fixtures
@pytest.fixture
def mini(tmp_path, ledger_file):
    """A minimal workspace: profile with the conftest ledger plus EXTRA entries; returns a spec writer."""
    from startup_kit import profile
    prof = tmp_path / "startup-profile"
    profile.init(str(prof), "Acme")
    shutil.copy(ledger_file, prof / "evidence.yaml")
    with open(prof / "evidence.yaml", "a") as f:
        f.write(EXTRA)

    def write(over=None, name="bm.yaml"):
        spec = {"design": {"company": "Acme", "profile": "startup-profile", "currency": "USD",
                           "types": ["marketplace", "commission", "education", "b2c"]},
                "segments": SEGMENTS, "canvas": canvas()}
        for k, v in (over or {}).items():
            if k == "design":
                spec["design"].update(v)
            else:
                spec[k] = v
        p = tmp_path / name
        p.write_text(yaml.safe_dump(spec, allow_unicode=True, sort_keys=False))
        return str(p)
    write.dir = tmp_path
    return write


@pytest.fixture
def fieldnote(example_dir, tmp_path):
    """Private copy of the fictional Fieldnote profile, discovery and business model examples."""
    dst = tmp_path / "fieldnote"
    for d in ("startup-profile", "customer-discovery", "business-model"):
        shutil.copytree(os.path.join(example_dir, d), dst / d)
    return dst / "business-model" / "fieldnote-business-model.yaml"


def msgs(rep, level, area=None):
    return [i["message"] for i in rep["issues"] if i["level"] == level and (area is None or i["area"] == area)]


def has(rep, level, text, area=None):
    return any(text in m for m in msgs(rep, level, area))


# ----------------------------------------------------------------------------- packaging
def test_skill_discovered_and_registered(root):
    p = os.path.join(root, "skills", SKILL, "SKILL.md")
    text = open(p).read()
    fm = yaml.safe_load(text.split("\n---", 1)[0][4:])
    assert fm["name"] == SKILL and len(fm["description"]) <= 1024 and "Use when" in fm["description"]
    assert len(text.splitlines()) < 500
    r = subprocess.run([sys.executable, os.path.join(root, "scripts", "validate_skills.py")], capture_output=True,
                       text=True)
    assert r.returncode == 0 and " skills, 0 errors" in r.stdout, r.stdout      # exact count and version are pinned in test_shark_tank.py
    plugin = json.load(open(os.path.join(root, ".claude-plugin", "plugin.json")))
    market = json.load(open(os.path.join(root, ".claude-plugin", "marketplace.json")))
    assert plugin["version"] == market["plugins"][0]["version"] and "skills" not in plugin
    for t in ("business-model-spec.yaml", "business-model-canvas.md", "value-proposition-canvas.md",
              "revenue-architecture.md", "cost-structure.md", "marketplace-model.md", "model-comparison.md",
              "assumption-register.yaml", "stress-test.md", "decision-summary.md"):
        assert os.path.exists(os.path.join(root, "skills", SKILL, "assets", "templates", t)), t
    bm.load_spec(os.path.join(root, "skills", SKILL, "assets", "templates", "business-model-spec.yaml"))


def test_all_nine_skills_present(root):
    """The original nine skills must always be present; later skills are added without removing any."""
    names = {os.path.basename(os.path.dirname(p)) for p in glob.glob(os.path.join(root, "skills", "*", "SKILL.md"))}
    assert names >= {"business-document-generator", "customer-discovery-validation", "fundraising-strategist",
                     "gtm-strategy-maker", "pitch-deck-maker", "startup-idea-evaluator", "startup-proposal-generator",
                     "startup-research", "business-model-designer"}


def test_knowledge_base_topics_and_source_verification(root):
    files = sorted(glob.glob(os.path.join(root, "knowledge", "business-model", "*.md")))
    topics = [f for f in files if not f.endswith("README.md")]
    assert len(topics) >= 12
    for f in topics:
        fm = yaml.safe_load(open(f).read().split("\n---", 1)[0][4:])
        assert fm["date_checked"] and fm["sources"], f
        for s in fm["sources"]:
            assert s["title"] and s["url"].startswith("https://"), (f, s)
            assert str(s["verification"]).startswith(("read-at-source", "url-verified")), (f, s)
    hbr = [s for f in topics for s in yaml.safe_load(open(f).read().split("\n---", 1)[0][4:])["sources"]
           if "hbr.org" in s["url"]]
    assert hbr and all(str(s["verification"]).startswith("url-verified") for s in hbr)   # paywalled: never "read"


# ----------------------------------------------------------------------------- canvas
def test_canvas_nine_blocks_and_basis_counts(mini):
    rep = bm.analyze(mini({"canvas": canvas(
        customer_segments=[U("Exam teachers", "evidence", evidence=["E-010"]), U("Learners", "hypothesis")],
        key_resources=[U("Platform code", "evidence", evidence=["E-016"])])}))
    assert list(rep["canvas"]) == list(bm.BLOCKS) and len(rep["canvas"]) == 9
    cs = rep["canvas"]["customer_segments"]
    assert cs["counts"]["evidence"] == 1 and cs["counts"]["hypothesis"] == 1
    assert cs["items"][0]["evidence"] == ["E-010"] and cs["items"][0]["status"] == "reported"
    assert not msgs(rep, "error", "canvas")


def test_canvas_missing_and_unknown_blocks(mini):
    c = canvas()
    del c["key_partnerships"]
    c["mission"] = {"items": [U()]}
    rep = bm.analyze(mini({"canvas": c}))
    assert has(rep, "error", "block 'Key Partnerships' is missing", "canvas")
    assert has(rep, "error", "unknown canvas block 'mission'", "canvas")
    assert rep["maturity"]["level"] == "incomplete"


def test_canvas_evidence_preserved_in_report(mini, tmp_path):
    rep = bm.analyze(mini({"canvas": canvas(value_propositions=[U("Saves a day a month", "evidence",
                                                                   evidence=["E-010"], contradicting=["E-015"])])}))
    md = bm.report_md(rep, str(tmp_path), ["canvas"])
    assert "[E-010]" in md and "contradicted by [E-015]" in md and "Evidence-backed" in md
    assert has(rep, "warning", "contradicting evidence E-015", "canvas")


@pytest.mark.parametrize("item,needle", [
    (U("Teachers want this", "evidence", evidence=["E-003"]), "cites E-003 (assumption)"),
    (U("Teachers want this", "evidence", evidence=["E-012"]), "rests only on founder statements"),
    (U("Teachers want this", "evidence", evidence=["E-014"]), "needs customer evidence"),
    (U("Teachers want this", "evidence"), "cites no ledger entry"),
    ({"text": "Teachers want this"}, "needs basis"),
    (U('One teacher said "this would save me hours every week"', "hypothesis"), "never invent customer quotes"),
])
def test_canvas_assumptions_stay_distinct_from_evidence(mini, item, needle):
    rep = bm.analyze(mini({"canvas": canvas(customer_segments=[item])}))
    assert has(rep, "error", needle, "canvas"), msgs(rep, "error")


def test_internal_block_accepts_document_evidence(mini):
    rep = bm.analyze(mini({"canvas": canvas(key_partnerships=[U("Payment provider", "evidence", evidence=["E-016"])],
                                            key_resources=[U("Market data", "evidence", evidence=["E-014"])])}))
    assert not msgs(rep, "error", "canvas")


# ----------------------------------------------------------------------------- value proposition
def test_value_propositions_per_segment_and_fit_ladder(mini):
    vps = [{"segment": "S1", "customer_profile": {
               "jobs": [U("Sell courses", "hypothesis")],
               "pains": [{"id": "P1", "text": "Chasing payments", "basis": "evidence", "evidence": ["E-010"]},
                         {"id": "P2", "text": "Access control", "basis": "hypothesis"}],
               "gains": [U("Reliable payouts", "hypothesis")]},
            "value_map": {"products": [U("Checkout", "evidence", evidence=["E-016"])],
                          "pain_relievers": [{"text": "QR checkout", "basis": "hypothesis", "addresses": ["P1"]}]}},
           {"segment": "D1", "customer_profile": {"jobs": [U("Pass the exam", "hypothesis")],
                                                  "pains": [U("No structure", "hypothesis")]},
            "value_map": {"products": [U("Courses", "founder")]}}]
    rep = bm.analyze(mini({"value_propositions": vps}))
    v = {x["segment"]: x for x in rep["value_propositions"]}
    assert set(v) == {"S1", "D1"}
    assert v["S1"]["verdict"].startswith("Problem side evidenced") and v["S1"]["unaddressed_pains"] == ["P2"]
    assert v["D1"]["verdict"].startswith("Conceptual fit only")
    assert not msgs(rep, "error", "value-proposition")


def test_value_proposition_flags_unsupported_claims(mini):
    vps = [{"segment": "X9", "pains": [{"id": "P1", "text": "Pain", "basis": "evidence", "evidence": ["E-012"]}],
            "pain_relievers": [{"text": "Fix", "basis": "hypothesis", "addresses": ["P7"]}]},
           {"segment": "X9", "gains": [U("Gain", "hypothesis")]}]
    rep = bm.analyze(mini({"value_propositions": vps}))
    e = msgs(rep, "error", "value-proposition")
    assert any("unknown segment 'X9'" in m for m in e)
    assert any("rests only on founder statements" in m for m in e)
    assert any("unknown pain 'P7'" in m for m in e)
    assert has(rep, "warning", "two canvases for one segment", "value-proposition")


# ----------------------------------------------------------------------------- revenue
def stream(**kw):
    s = {"id": "R1", "name": "Course commission", "payer": "D1", "value": "A course", "mechanism": "commission",
         "billing": "per purchase", "structure": "QR checkout", "recognition": "net", "risks": "WTP",
         "take_rate": {"value": 0.3, "status": "assumption"}, "stage": "proposed", "dependencies": ["D1"]}
    s.update(kw)
    return s


DEP_OK = {"id": "D1", "name": "Card payments via a licensed provider", "type": "payment", "status": "verified",
          "evidence": ["E-016"]}
DEP_OPEN = dict(DEP_OK, status="unverified", evidence=[], question="Which provider?", confirm_with=["payment-provider"])


def test_multiple_revenue_streams_and_stage_ladder(mini):
    streams = [stream(id="R1", price={"value": 10, "status": "assumption"}),
               stream(id="R2", stage="tested", evidence=["E-014"]),
               stream(id="R3", stage="available", evidence=["E-010", "E-016"]),
               stream(id="R4", stage="generating", evidence=["E-010", "E-016"]),
               stream(id="R5", stage="generating", evidence=["E-011", "E-016"]),
               stream(id="R6", stage="repeatable", evidence=["E-011", "E-016"])]
    rep = bm.analyze(mini({"revenue_streams": streams, "dependencies": [DEP_OPEN]}))
    e = msgs(rep, "error", "revenue")
    assert len(rep["revenue"]) == 6
    assert any("R2" in m and "needs customer evidence" in m for m in e)
    assert any("R3" in m and "dependencies D1 are not verified" in m for m in e)
    assert any("R4" in m and "needs paid evidence" in m for m in e)
    assert any("R6" in m and "'repeatable' needs measured repeat" in m for m in e)
    assert not any(m.startswith("R1 ") for m in e)
    r1 = rep["revenue"][0]
    assert r1["price_display"].endswith("(assumption)") and r1["revenue"] is None
    ok = bm.analyze(mini({"revenue_streams": [stream(id="R5", stage="generating", evidence=["E-011", "E-016"])],
                          "dependencies": [DEP_OK]}))
    assert not msgs(ok, "error", "revenue")


def test_proposed_pricing_is_never_revenue(mini):
    rep = bm.analyze(mini({"revenue_streams": [
        stream(id="R1", revenue={"value": 5000, "status": "reported"}),
        stream(id="R2", stage="generating", evidence=["E-011", "E-016"], revenue={"value": 5000, "status": "assumption"}),
        stream(id="R3", take_rate=None), stream(id="R4", take_rate={"value": 1.5, "status": "assumption"})],
        "dependencies": [DEP_OK]}))
    e = msgs(rep, "error", "revenue")
    assert any("R1" in m and "proposed pricing is not actual revenue" in m for m in e)
    assert any("R2" in m and "revenue must be measured" in m for m in e)
    assert any("R3" in m and "needs take_rate" in m for m in e)
    assert any("R4" in m and "must be between 0 and 1" in m for m in e)


def test_financials_never_fabricate_missing_inputs(mini):
    rep = bm.analyze(mini({"financials": {"inputs": {"gmv": {"value": 10000, "status": "reported"}}}}))
    f = {r["key"]: r for r in rep["financials"]}
    assert f["commission_revenue"]["value"] is None and f["commission_revenue"]["missing"] == ["take_rate"]
    assert f["net_revenue"]["value"] is None and set(f["net_revenue"]["missing"]) == {"gross_revenue", "refunds",
                                                                                       "discounts"}
    assert f["aov"]["missing"] == ["orders"]


def test_gmv_and_platform_revenue_are_never_confused(mini):
    inputs = {"gmv": {"value": 10000, "status": "reported"}, "take_rate": {"value": 0.3, "status": "assumption"},
              "seller_fees": {"value": 0, "status": "reported"}, "orders": {"value": 50, "status": "reported"},
              "revenue": {"value": 10000, "status": "reported"}}
    rep = bm.analyze(mini({"financials": {"inputs": inputs}}))
    f = {r["key"]: r for r in rep["financials"]}
    assert f["commission_revenue"]["value"] == pytest.approx(3000)
    assert f["seller_earnings"]["value"] == pytest.approx(7000)
    assert f["aov"]["value"] == pytest.approx(200)
    assert f["commission_revenue"]["status"] == "assumption"         # weakest input wins
    assert has(rep, "error", "revenue equals GMV", "financials")
    gross = bm.analyze(mini({"financials": {"inputs": {"gmv": {"value": 100, "status": "reported"},
                                                       "gross_revenue": {"value": 100, "status": "reported"}}}}))
    assert has(gross, "error", "not declared the principal", "financials")


# ----------------------------------------------------------------------------- costs
def test_costs_fixed_variable_unknown(mini):
    costs = [{"id": "C1", "name": "Hosting", "category": "fixed", "type": "infrastructure",
              "amount": {"value": 100, "unit": "USD per month", "status": "estimate", "basis": "price page"}},
             {"id": "C2", "name": "Office", "category": "fixed", "type": "administrative",
              "amount": {"value": 50, "unit": "USD per month", "evidence": ["E-016"]}},
             {"id": "C3", "name": "Gateway", "category": "variable", "type": "payment-processing", "driver": "payment",
              "amount": {"value": 0.03, "unit": "share of payment", "status": "assumption"}},
             {"id": "C4", "name": "Video", "category": "variable", "type": "delivery", "driver": "sale",
              "amount": {"value": 2, "unit": "USD per transaction", "status": "assumption"}},
             {"id": "C5", "name": "Salaries", "category": "fixed", "type": "personnel"},
             {"id": "C6", "name": "Event", "category": "fixed", "type": "acquisition",
              "amount": {"value": 900, "unit": "USD per event", "status": "assumption"}}]
    rep = bm.analyze(mini({"costs": costs}))
    t = rep["costs"]["totals"]
    assert t["fixed_month"] == pytest.approx(150) and t["fixed_month_items"] == ["C1", "C2"]
    assert t["fixed_month_status"] == "estimate"
    assert t["variable_rate"] == pytest.approx(0.03) and t["variable_per_tx"] == pytest.approx(2)
    assert t["unknown"] == ["C5"] and t["excluded_fixed"] == ["C6"]
    row = {r["id"]: r for r in rep["costs"]["rows"]}
    assert row["C5"]["value"] is None and row["C5"]["status"] == "unknown"
    assert not msgs(rep, "error", "costs")


def test_cost_numbers_need_provenance(mini):
    costs = [{"id": "C1", "name": "Hosting", "category": "fixed", "type": "infrastructure",
              "amount": {"value": 100, "unit": "USD per month"}},
             {"id": "C2", "name": "Support", "category": "variable", "type": "support",
              "amount": {"value": 5, "unit": "USD per transaction", "status": "estimate"}},
             {"id": "C3", "name": "Fees", "category": "variable", "type": "payment-processing", "driver": "x",
              "amount": {"value": 3, "unit": "share of payment", "status": "assumption"}},
             {"id": "C4", "name": "Thing", "category": "sometimes", "amount": {"value": 1, "status": "assumption"}}]
    e = msgs(bm.analyze(mini({"costs": costs})), "error", "costs")
    assert any("C1" in m and "needs evidence or a status" in m for m in e)
    assert any("C2" in m and "needs its source or calculation" in m for m in e)
    assert any("C3" in m and "between 0 and 1" in m for m in e)
    assert any("C4" in m and "category must be" in m for m in e) and any("C4" in m and "needs a unit" in m for m in e)


# ----------------------------------------------------------------------------- marketplace
def market(**kw):
    m = {"type": "education",
         "sides": [{"segment": "S1", "role": "supply", "acquisition": "outreach", "value": "sales", "pays": "30%"},
                   {"segment": "D1", "role": "demand", "acquisition": "teachers", "value": "courses", "pays": "price"}],
         "matching": "x", "trust_safety": "x", "transaction_flow": "x", "leakage": "x", "cold_start": {"first_side": "S1"},
         "network_effects": "x", "pricing": "x", "take_rate": {"value": 0.3, "status": "assumption"},
         "payments": {"collection": "QR", "payout": "bank", "refunds": "hold", "disputes": "manual",
                      "fee_bearer": "platform"}}
    m.update(kw)
    return m


def test_marketplace_supply_and_demand_are_separate(mini):
    one = market(sides=[{"segment": "S1", "role": "supply"}, {"segment": "D1", "role": "supply"}])
    rep = bm.analyze(mini({"marketplace": one}))
    assert has(rep, "error", "at least one supply side and one demand side", "marketplace")
    assert has(rep, "error", "side D1: segment is 'demand' but listed as supply", "marketplace")
    three = bm.analyze(mini({"marketplace": market(type="three-sided")}))
    assert has(three, "error", "three-sided marketplace needs three sides", "marketplace")
    none = bm.analyze(mini({}))
    assert has(none, "error", "needs a 'marketplace' section", "marketplace")


def test_registered_users_are_not_active_users(mini):
    rep = bm.analyze(mini({"marketplace": market(funnel={"registered_supply": {"value": 500, "status": "reported"}})}))
    r = {x["key"]: x for x in rep["marketplace"]["ratios"]}
    assert r["supply_activation"]["value"] is None and r["supply_activation"]["missing"] == ["active_supply"]
    st = {s["key"]: s for s in rep["marketplace"]["stages"]}
    assert st["active_supply"]["value"] is None and st["active_supply"]["status"] == "not measured"
    assert has(rep, "info", "registrations are not active participants", "marketplace")
    bad = bm.analyze(mini({"marketplace": market(funnel={"registered_supply": {"value": 5, "status": "reported"},
                                                         "active_supply": {"value": 9, "status": "reported"}})}))
    assert has(bad, "error", "Active supply (9) exceeds registered supply", "marketplace")


def test_matches_are_not_completed_transactions(mini):
    rep = bm.analyze(mini({"marketplace": market(funnel={"matches": {"value": 40, "status": "reported"}})}))
    assert has(rep, "info", "a match is not a completed transaction", "marketplace")
    f = {r["key"]: r for r in rep["financials"]}
    assert "transactions" not in str(f["revenue_per_transaction"]["inputs"]) or \
        f["revenue_per_transaction"]["value"] is None
    bad = bm.analyze(mini({"marketplace": market(funnel={"matches": {"value": 4, "status": "reported"},
                                                         "completed_transactions": {"value": 9, "status": "reported"}})}))
    assert has(bad, "error", "Completed transactions (9) exceeds successful matches", "marketplace")


def test_seller_earnings_and_take_rate(mini):
    measured = {"gmv": {"value": 20000, "evidence": ["E-017"]},
                "platform_revenue": {"value": 5000, "evidence": ["E-017"]},
                "completed_transactions": {"value": 40, "evidence": ["E-017"]}}
    rep = bm.analyze(mini({"marketplace": market(funnel=measured)}))
    m = rep["marketplace"]["money"]
    assert m["realised_take_rate"] == pytest.approx(0.25) and m["seller_earnings"] == pytest.approx(15000)
    assert m["basis"] == "measured platform revenue" and m["status"] == "verified"
    f = {r["key"]: r for r in rep["financials"]}
    assert f["aov"]["value"] == pytest.approx(500)
    design = bm.analyze(mini({"marketplace": market(funnel={"gmv": {"value": 1000, "status": "reported"}})}))
    dm = design["marketplace"]["money"]
    assert dm["platform_revenue"] == pytest.approx(300) and dm["seller_earnings"] == pytest.approx(700)
    assert dm["basis"] == "GMV × design take rate" and dm["status"] == "assumption"
    assert gtm.METRICS["take_rate"][4]({"net_revenue": 30, "gmv": 100}) == pytest.approx(0.3)


def test_liquidity_claims_require_measured_evidence(mini):
    rep = bm.analyze(mini({"marketplace": market(liquidity={"status": "achieved"},
                                                 funnel={"registered_supply": {"value": 900, "status": "reported"}})}))
    assert has(rep, "error", "liquidity claimed 'achieved' without measured completed transactions", "marketplace")
    good = market(liquidity={"status": "achieved", "evidence": ["E-017"]},
                  funnel={"completed_transactions": {"value": 40, "evidence": ["E-017"]},
                          "repeat_transactions": {"value": 12, "evidence": ["E-017"]}})
    assert not msgs(bm.analyze(mini({"marketplace": good})), "error", "marketplace")


def test_supply_does_not_create_demand_by_assumption(mini):
    m = market()
    m["sides"][0]["brings_other_side"] = True
    rep = bm.analyze(mini({"marketplace": m}))
    assert has(rep, "error", "more supply does not create demand by itself", "marketplace")
    m["sides"][0]["assumption"] = "A4"
    assert not has(bm.analyze(mini({"marketplace": m})), "error", "does not create demand", "marketplace")


# ----------------------------------------------------------------------------- alternatives
def alt(aid="M1", **kw):
    a = {"id": aid, "name": f"Model {aid}", "types": ["marketplace", "commission", "b2c"], "fit": "why",
         **{f: "x" for f in bm.ALT_FIELDS}, "validation": ["A1"], "decision": "viable", "decision_reason": "because",
         "ratings": {"customer_fit": {"level": "unknown", "why": "no interviews"},
                     "revenue_clarity": {"level": "favourable", "why": "paid pilots", "evidence": ["E-011"]}}}
    a.update(kw)
    return a


def test_alternatives_compared_on_defined_scales(mini, tmp_path):
    rep = bm.analyze(mini({"alternatives": [alt("M1", decision="recommended"), alt("M2"),
                                            alt("M3", decision="reject", types=["saas", "subscription", "b2b"])]}))
    a = rep["alternatives"]
    assert a["recommended"] == "M1" and len(a["alternatives"]) == 3
    assert list(a["criteria"]) == list(bm.DEFAULT_CRITERIA)
    r = a["alternatives"][0]["ratings"]
    assert r["revenue_clarity"]["basis"] == "evidence" and r["customer_fit"]["basis"] == "judgement"
    assert r["capital_needs"]["level"] == "unknown"
    assert not msgs(rep, "error", "alternatives")
    md = bm.report_md(rep, str(tmp_path), ["alternatives"])
    assert "no numerical scores are computed" in md and "favourable" in md


@pytest.mark.parametrize("over,needle", [
    ({"ratings": {"customer_fit": {"level": 4, "why": "x"}}}, "numerical scores are rejected"),
    ({"score": 8.5}, "numerical scores, weights and rankings are not accepted"),
    ({"ratings": {"customer_fit": {"level": "great", "why": "x"}}}, "level 'great' is not on its scale"),
    ({"ratings": {"customer_fit": {"level": "mixed"}}}, "needs 'why'"),
    ({"ratings": {"vibes": {"level": "mixed", "why": "x"}}}, "unknown criterion 'vibes'"),
    ({"types": ["pyramid"]}, "unknown business model type 'pyramid'"),
])
def test_unsupported_rankings_rejected(mini, over, needle):
    rep = bm.analyze(mini({"alternatives": [alt("M1", **over), alt("M2")]}))
    assert any(needle in m for m in msgs(rep, "error")), msgs(rep, "error")


def test_custom_scale_must_be_defined_and_decisions_reasoned(mini):
    rep = bm.analyze(mini({"comparison": {"criteria": [{"key": "fit", "scale": {1: "low", 2: ""}}]},
                           "alternatives": [alt("M1", decision="recommended", validation=[], ratings={}),
                                            alt("M2", decision="recommended", ratings={}),
                                            alt("M3", decision="reject", decision_reason="", ratings={})]}))
    e = msgs(rep, "error", "alternatives")
    assert any("numeric scale level 1" in m for m in e) and any("level '2' has no definition" in m for m in e)
    assert any("more than one recommended model" in m for m in e)
    assert any("M1" in m and "must list what has to be tested" in m for m in e)
    assert any("M3" in m and "needs decision_reason" in m for m in e)


# ----------------------------------------------------------------------------- assumptions
def A(aid="A1", **kw):
    a = {"id": aid, "description": "Learners pay", "category": "wtp", "why": "revenue", "impact": "high",
         "validation": "pre-sales", "status": "untested"}
    a.update(kw)
    return a


def test_record_is_append_only_and_idempotent(mini):
    spec = mini({"assumptions": [A("A1"), A("A2", evidence=["E-010"]), A("A3", category="costs")]})
    led = mini.dir / "startup-profile" / "evidence.yaml"
    before = led.read_text()
    added = bm.record(spec)
    after = led.read_text()
    assert after.startswith(before) and len(added) == 2            # A2 cites evidence: not re-recorded
    L = Ledger.load(str(led))
    e = L.get(added[0])
    assert e.status == "assumption" and e.source["type"] == "analysis" and e.source["ref"].endswith("bm.yaml#A1")
    assert e.key == "business_model.assumption.a1" and e.raw["validate"] == "pre-sales"
    assert bm.record(spec) == [] and led.read_text() == after       # idempotent
    assert not [i for i in L.validate() if i.level == "error"]
    for old in Ledger.load(str(mini.dir / "startup-profile" / "evidence.yaml")).entries[:12]:
        assert old.id in before                                       # nothing rewritten


@pytest.mark.parametrize("a,needle", [
    (A(status="supported", evidence=["E-012"]), "founder opinion, desk research and waitlists are not validation"),
    (A(status="supported", evidence=["E-013"]), "stated interest is not a transaction"),
    (A(status="supported", evidence=["E-010"]), "need committed or paid evidence"),
    (A(category="volume", status="supported", evidence=["E-010"]), "needs measured data"),
    (A(category="costs", status="supported", evidence=["E-012"]), "a founder's opinion is not validation"),
    (A(status="validated", evidence=["E-011"]), "not 'validated'"),
    (A(status="contradicted"), "without contradicting evidence"),
])
def test_assumption_status_discipline(mini, a, needle):
    rep = bm.analyze(mini({"assumptions": [a]}))
    assert any(needle in m for m in msgs(rep, "error", "assumptions")), msgs(rep, "error")


def test_supported_assumptions_with_real_evidence_pass(mini):
    rep = bm.analyze(mini({"assumptions": [A("A1", status="supported", evidence=["E-011"]),
                                           A("A2", category="payments", status="supported", evidence=["E-016"])]}))
    assert not msgs(rep, "error", "assumptions")
    assert {a["id"]: a["strength"] for a in rep["assumptions"]}["A1"] == "strong"


def test_conflicting_evidence_stays_visible(mini, tmp_path):
    a = A(category="acquisition", status="supported", evidence=["E-010", "E-011"], contradicting=["E-015"])
    rep = bm.analyze(mini({"assumptions": [a]}))
    assert has(rep, "error", "contradicting evidence exists (E-015)", "assumptions")
    rep2 = bm.analyze(mini({"assumptions": [dict(a, conflict_note="I-02 is outside the segment")]}))
    assert not msgs(rep2, "error", "assumptions")
    md = bm.report_md(rep2, str(tmp_path), ["assumptions"])
    assert "[E-015]" in md
    warn = bm.analyze(mini({"assumptions": [A(contradicting=["E-015"])]}))
    assert has(warn, "warning", "contradicting evidence E-015 is recorded", "assumptions")


def test_assumption_cannot_outrun_discovery_register(fieldnote):
    spec = yaml.safe_load(open(fieldnote))
    spec["assumptions"].append({"id": "A9", "description": "Federations refer", "category": "partnerships",
                                "why": "x", "impact": "high", "validation": "X3", "status": "supported",
                                "evidence": ["E-017"], "hypothesis": "H5"})
    spec["assumptions"].append({"id": "A10", "description": "x", "category": "wtp", "why": "x", "impact": "low",
                                "validation": "x", "status": "untested", "hypothesis": "H99"})
    open(fieldnote, "w").write(yaml.safe_dump(spec, allow_unicode=True))
    rep = bm.analyze(str(fieldnote))
    e = msgs(rep, "error", "assumptions")
    assert any("discovery register says H5 is 'untested'" in m for m in e)
    assert any("H99 is not in the discovery register" in m for m in e)


# ----------------------------------------------------------------------------- stress tests
STRESS = {"inputs": {"price": {"value": 1000, "status": "assumption"}, "take_rate": {"value": 0.3, "status": "assumption"},
                     "payment_fee_rate": {"value": 0.03, "status": "assumption"}, "fee_bearer": "platform",
                     "delivery_cost": {"value": 15, "status": "estimate"}, "support_cost": {"value": 5, "status": "assumption"},
                     "fixed_costs_month": {"value": 5000, "status": "estimate"},
                     "transactions_per_month": {"value": 10, "status": "assumption"}},
          "scenarios": [{"name": "downside", "changes": {"transactions_per_month": {"multiply": 0.5},
                                                         "payment_fee_rate": {"add": 0.01}}, "rationale": "x"}]}


def test_stress_downside_and_thresholds(mini):
    rep = bm.analyze(mini({"stress": STRESS}))
    m = {x["key"]: x for x in rep["stress"]["metrics"]}
    assert m["contribution_per_tx"]["value"] == pytest.approx(300 - 30 - 15 - 5)          # 250
    assert m["break_even_tx_month"]["value"] == pytest.approx(5000 / 250)
    assert m["min_viable_price"]["value"] == pytest.approx(20 / 0.27)
    assert m["max_fee_rate"]["value"] == pytest.approx(0.3 - 0.02)
    assert m["seller_earnings_per_tx"]["value"] == pytest.approx(700)
    assert m["operating_result_month"]["value"] == pytest.approx(2500 - 5000)
    sc = rep["stress"]["scenarios"][0]["results"]
    assert sc["contribution_per_tx"] == pytest.approx(300 - 40 - 20)
    assert sc["operating_result_month"] == pytest.approx(5 * 240 - 5000)
    assert len(rep["stress"]["cards"]) == 13 and not msgs(rep, "error", "stress")


def test_stress_missing_inputs_stay_explicit(mini):
    st = {"inputs": {"price": {"value": 1000, "status": "assumption"}, "take_rate": {"value": 0.3, "status": "assumption"}}}
    rep = bm.analyze(mini({"stress": st}))
    m = {x["key"]: x for x in rep["stress"]["metrics"]}
    assert m["contribution_per_tx"]["value"] is None
    assert set(m["contribution_per_tx"]["missing"]) == {"payment_fee_rate", "delivery_cost", "support_cost"}
    assert m["platform_revenue_per_tx"]["value"] == pytest.approx(300)
    card = next(c for c in rep["stress"]["cards"] if c["key"] == "volume")
    assert not card["quantified"] and "fixed_costs_month" in card["missing"]


def test_stress_rejects_probabilities_and_unfounded_changes(mini):
    st = dict(STRESS, scenarios=[{"name": "bad", "probability": 0.2, "changes": {"cac": {"set": 5}}},
                                 {"name": "odd", "changes": {"price": 2}, "rationale": "x"}])
    rep = bm.analyze(mini({"stress": st}))
    e = msgs(rep, "error", "stress")
    assert any("probabilities are not supported" in m for m in e)
    assert any("changes 'cac', which has no base value" in m for m in e)
    assert any("needs a rationale" in m for m in e)
    assert any("must be {multiply|add|set: number}" in m for m in e)


# ----------------------------------------------------------------------------- payments and regulation
def test_payment_provider_availability_is_never_assumed(mini):
    rep = bm.analyze(mini({"design": {"geography": ["Nepal"]},
                           "revenue_streams": [stream(structure="Learners pay by Stripe checkout")]}))
    assert has(rep, "error", "'stripe' is named in the spec but its availability is not registered", "payments")
    dep = {"id": "D1", "name": "Stripe for a foreign entity", "type": "payment", "status": "unverified",
           "question": "Is it available?", "confirm_with": ["payment-provider", "legal"]}
    ok = bm.analyze(mini({"design": {"geography": ["Nepal"]}, "dependencies": [dep],
                          "revenue_streams": [stream(structure="Learners pay by Stripe checkout")]}))
    assert not msgs(ok, "error", "payments")


def test_qr_visitor_payments_are_not_international_checkout(mini):
    bad = {"id": "D1", "name": "International online payments", "type": "payment", "status": "unverified",
           "question": "Since Indian tourists can pay by UPI QR, learners abroad can use our online checkout",
           "confirm_with": ["bank"]}
    rep = bm.analyze(mini({"dependencies": [bad]}))
    assert has(rep, "error", "not international online checkout", "payments")
    good = dict(bad, question="UPI QR for Indian visitors paying merchants in person does not show that online "
                              "checkout works for learners abroad")
    assert not msgs(bm.analyze(mini({"dependencies": [good]})), "error", "payments")


def test_regulatory_uncertainty_is_explicit(mini):
    deps = [{"id": "D1", "name": "VAT treatment", "type": "tax", "status": "verified", "evidence": ["E-016"]},
            {"id": "D2", "name": "Payout licence", "type": "regulatory", "status": "verified"},
            {"id": "D3", "name": "Consumer rules", "type": "legal", "status": "unverified"}]
    rep = bm.analyze(mini({"dependencies": deps}))
    e = msgs(rep, "error", "dependencies")
    assert any("D1" in m and "qualified adviser" in m for m in e)
    assert any("D2" in m and "without verified or reported evidence" in m for m in e)
    w = msgs(rep, "warning", "dependencies")
    assert any("D3" in m and "open question" in m for m in w) and any("D3" in m and "confirm_with" in m for m in w)
    assert any(g.startswith("D3 Consumer rules is unverified") for g in rep["gaps"])


# ----------------------------------------------------------------------------- maturity
def test_maturity_never_exceeds_evidence(mini, fieldnote):
    rep = bm.analyze(mini({"design": {"claimed_maturity": "economic-viability"}}))
    assert rep["maturity"]["level"] == "coherent"
    assert has(rep, "error", "claimed maturity 'economic-viability' exceeds what the evidence shows", "maturity")
    fn = bm.analyze(str(fieldnote))
    assert fn["maturity"]["level"] == "customer-evidence" and fn["errors"] == 0
    assert fn["maturity"]["discovery_psf"]


# ----------------------------------------------------------------------------- document guard
@pytest.mark.parametrize("line", [
    "Our GMV of NPR 2 million is our revenue this year.",
    "We have 500 registered teachers, so supply is active.",
    "The marketplace has achieved liquidity.",
    "This is a proven business model.",
    "Learners will pay through Stripe, which we will integrate next month.",
    "Indian tourists already pay by QR, so international learners can use our online checkout.",
    "The platform is fully compliant and no licence is required.",
    "There is a 70% chance the launch succeeds.",
    "The waitlist proves willingness to pay.",
])
def test_document_guard_rejects(line):
    issues = bm.check_document(f"# Model\n\nThis is about Nepal.\n\n{line}\n")
    assert any(i["level"] == "error" for i in issues), line


@pytest.mark.parametrize("line", [
    "GMV is not revenue: platform revenue is only the 30% commission.",
    "Registered teachers are not active supply until they publish.",
    "Liquidity is not yet measured.",
    "Whether Stripe is available to a Nepal company must be verified with the provider.",
    "UPI QR for Indian visitors paying in person is not online checkout.",
    "Whether a licence is required is a question for a lawyer.",
    "The canvas does not prove the business works.",
    "A waitlist is not willingness to pay.",
    "D2 learners and A2 teachers are segments, not counts.",
])
def test_document_guard_accepts(line):
    issues = bm.check_document(f"# Model\n\nThis is about Nepal.\n\n{line}\n")
    assert not [i for i in issues if i["level"] == "error"], (line, issues)


# ----------------------------------------------------------------------------- reports and CLI
def test_report_sections_and_front_matter(fieldnote, tmp_path):
    rep = bm.analyze(str(fieldnote))
    md = bm.report_md(rep, str(tmp_path))
    meta = yaml.safe_load(md.split("\n---", 1)[0][4:])
    assert meta["doc_type"] == "business-model" and "Fictional" in meta["disclaimer"]
    for h in ("# Business Model Canvas", "# Value Proposition Canvas", "# Revenue architecture", "# Cost structure",
              "# Marketplace model", "# Business model alternatives", "# Assumption register", "# Stress tests",
              "# Founder decision summary", "# Payments, geography and regulation"):
        assert h in md, h
    part = bm.report_md(rep, str(tmp_path), ["canvas", "stress"])
    assert "# Business Model Canvas" in part and "# Revenue architecture" not in part
    with pytest.raises(ValueError, match="unknown section"):
        bm.report_md(rep, str(tmp_path), ["nonsense"])
    assert not [i for i in bm.check_document(md, Ledger.load(os.path.join(rep["profile_dir"], "evidence.yaml")),
                                             rep) if i["level"] == "error"]


def test_report_profile_path_survives_symlinked_output(fieldnote, tmp_path):
    real = tmp_path / "real-out"
    real.mkdir()
    link = tmp_path / "link-out"
    os.symlink(real, link)
    rep = bm.analyze(str(fieldnote))
    md = bm.report_md(rep, str(link))
    prof = yaml.safe_load(md.split("\n---", 1)[0][4:])["profile"]
    assert os.path.exists(os.path.join(str(link), prof, "evidence.yaml"))


def test_cli_end_to_end(root, fieldnote, tmp_path):
    env = dict(os.environ, PYTHONPATH=os.path.join(root, "lib"))
    kit = [sys.executable, "-m", "startup_kit.cli", "business-model"]
    out = tmp_path / "out"
    spec = str(fieldnote)
    for act in ("analyze", "canvas", "value-proposition", "compare", "revenue", "costs", "marketplace",
                "assumptions", "stress-test"):
        r = subprocess.run(kit + [act, spec, "--out", str(out)], capture_output=True, text=True, env=env)
        assert r.returncode == 0, (act, r.stdout, r.stderr)
    for extra in (["value-proposition", spec, "--segment", "S2"], ["compare", spec, "--model", "M3"],
                  ["report", spec, "--xlsx"], ["report", spec, "--sections", "canvas,stress"],
                  ["revenue", spec, "--format", "json"]):
        r = subprocess.run(kit + extra + ["--out", str(out)], capture_output=True, text=True, env=env)
        assert r.returncode == 0, (extra, r.stdout, r.stderr)
    assert (out / "fieldnote-business-model-value-proposition-s2.md").exists()
    js = json.loads((out / "fieldnote-business-model-revenue.json").read_text())
    assert "_spec" not in js and js["maturity"]["level"] == "customer-evidence"
    rpt = out / "fieldnote-business-model-report.md"
    r = subprocess.run(kit + ["check", str(rpt), "--spec", spec], capture_output=True, text=True, env=env)
    assert r.returncode == 0 and "0 errors" in r.stdout, r.stdout
    base = [sys.executable, "-m", "startup_kit.cli"]
    r = subprocess.run(base + ["doc", str(rpt), "--out", str(out)], capture_output=True, text=True, env=env)
    assert r.returncode == 0 and "errors: 0" in r.stdout, r.stdout
    r = subprocess.run(base + ["check", str(out / "fieldnote-business-model-report.pdf"),
                               str(out / "fieldnote-business-model-report.docx"),
                               str(out / "fieldnote-business-model-workbook.xlsx")], capture_output=True, text=True,
                       env=env)
    assert r.returncode == 0, r.stdout
    assert json.loads((out / "fieldnote-business-model-report-build-report.json").read_text())["theme"] == "internal"
    bad = tmp_path / "bad.md"
    bad.write_text("# Plan\n\nOur GMV is our revenue.\n")
    r = subprocess.run(kit + ["check", str(bad), "--spec", spec], capture_output=True, text=True, env=env)
    assert r.returncode == 1 and "GMV presented as revenue" in r.stdout


def test_cli_design_inventory_and_record(root, fieldnote, tmp_path):
    env = dict(os.environ, PYTHONPATH=os.path.join(root, "lib"))
    kit = [sys.executable, "-m", "startup_kit.cli", "business-model"]
    prof = fieldnote.parent.parent / "startup-profile"
    disc = fieldnote.parent.parent / "customer-discovery" / "fieldnote-discovery.yaml"
    out = tmp_path / "design"
    r = subprocess.run(kit + ["design", str(prof), "--discovery", str(disc), "--out", str(out)], capture_output=True,
                       text=True, env=env)
    assert r.returncode == 0, r.stdout + r.stderr
    inv = (out / "business-model-inventory.md").read_text()
    assert "E-009" in inv and "Problem-solution fit" in inv and "Questions for the founder" in inv
    starter = bm.load_spec(str(out / "business-model.yaml"))
    assert set(starter["canvas"]) == set(bm.BLOCKS)
    items = [i for b in starter["canvas"].values() for i in b]
    churn = next(i for i in items if i.get("evidence") == ["E-009"])
    assert churn["basis"] == "hypothesis"                     # an assumption entry never becomes evidence
    assert "kept existing" in subprocess.run(kit + ["design", str(prof), "--out", str(out)], capture_output=True,
                                             text=True, env=env).stdout
    led = prof / "evidence.yaml"
    before = led.read_text()
    r = subprocess.run(kit + ["assumptions", str(fieldnote), "--record", "--out", str(tmp_path / "o")],
                       capture_output=True, text=True, env=env)
    assert r.returncode == 0 and "recorded 4 new entries" in r.stdout, r.stdout
    assert led.read_text().startswith(before)
    r = subprocess.run(kit + ["assumptions", str(fieldnote), "--record", "--out", str(tmp_path / "o")],
                       capture_output=True, text=True, env=env)
    assert "recorded 0 new entries" in r.stdout


def test_cli_reports_bad_yaml_and_bad_options_cleanly(root, tmp_path, fieldnote):
    env = dict(os.environ, PYTHONPATH=os.path.join(root, "lib"))
    kit = [sys.executable, "-m", "startup_kit.cli", "business-model"]
    p = tmp_path / "s.yaml"
    p.write_text("design: {company: [unclosed\n")
    r = subprocess.run(kit + ["analyze", str(p)], capture_output=True, text=True, env=env)
    assert r.returncode == 1 and "not valid YAML" in r.stdout and "Traceback" not in r.stderr
    p.write_text("canvas: {}\n")
    r = subprocess.run(kit + ["analyze", str(p)], capture_output=True, text=True, env=env)
    assert r.returncode == 1 and "'design' section" in r.stdout
    for extra in (["canvas", str(fieldnote), "--model", "M9"], ["value-proposition", str(fieldnote), "--segment", "Z"],
                  ["report", str(fieldnote), "--sections", "bogus"]):
        r = subprocess.run(kit + extra + ["--out", str(tmp_path / "x")], capture_output=True, text=True, env=env)
        assert r.returncode == 1 and "ERROR" in r.stdout and "Traceback" not in r.stderr, extra


# ----------------------------------------------------------------------------- regressions
def test_unquoted_comma_in_flow_mapping_is_reported(mini, tmp_path):
    """Regression: `{why: Payments, settlement and disputes}` silently truncated the text."""
    p = tmp_path / "t.yaml"
    p.write_text(open(mini()).read() + "alternatives:\n  - {id: M1, name: X, fit: Payments, settlement and disputes}\n"
                 "  - {id: M2, name: Y, fit: NPR 499–1,999}\n")
    rep = bm.analyze(str(p))
    e = msgs(rep, "error", "spec")
    assert any("settlement and disputes" in m for m in e) and any("999" in m for m in e)


def test_id_codes_are_not_traction_claims():
    """Regression: 'D2 learners' or 'A3 teachers' read as counts by the shared GTM guard."""
    issues = gtm.check_claims("# P\n\nSegments D2 learners and A3 Teachers are hypotheses only here.\n")
    assert not [i for i in issues if i["kind"] == "traction"]
    issues = gtm.check_claims("# P\n\nWe have 300 learners.\n")
    assert [i for i in issues if i["kind"] == "traction"]


def test_product_existence_may_cite_code(mini):
    """Regression: a value-map product backed by codebase evidence was rejected as a customer claim."""
    vps = [{"segment": "S1", "pains": [U("p", "hypothesis")],
            "products": [U("Offline app", "evidence", evidence=["E-016"])],
            "pain_relievers": [{"text": "Works offline", "basis": "evidence", "evidence": ["E-016"], "addresses": ["P1"]}]}]
    e = msgs(bm.analyze(mini({"value_propositions": vps})), "error", "value-proposition")
    assert len(e) == 1 and "R1" in e[0] and "customer-facing" in e[0]


def test_saas_is_not_a_hybrid_and_has_no_seller(mini):
    """Regression: SaaS + subscription was labelled hybrid; SaaS stress showed seller earnings of 0."""
    cls, _ = bm.classify(["saas", "subscription", "b2b"])
    assert not cls["hybrid"] and bm.classify(["saas", "commission", "b2b"])[0]["hybrid"]
    st = {"inputs": {"price": {"value": 40, "status": "reported"}, "take_rate": {"value": 1, "status": "reported"}}}
    m = {x["key"]: x for x in bm.analyze(mini({"stress": st}))["stress"]["metrics"]}
    assert m["seller_earnings_per_tx"]["value"] is None and m["platform_revenue_per_tx"]["value"] == 40


def test_private_outputs_are_gitignored_and_public_files_are_clean(root):
    r = subprocess.run(["git", "check-ignore", "-q", "outputs/any-startup/business-model/x.md"], cwd=root)
    assert r.returncode == 0
    # private startups are whatever folders exist locally under outputs/ (never named in public files)
    private = [d.lower() for d in os.listdir(os.path.join(root, "outputs"))
               if os.path.isdir(os.path.join(root, "outputs", d))]
    public = (glob.glob(os.path.join(root, "skills", SKILL, "**", "*"), recursive=True)
              + glob.glob(os.path.join(root, "knowledge", "business-model", "*.md"))
              + glob.glob(os.path.join(root, "examples", "fieldnote", "business-model", "*"))
              + [os.path.join(root, "lib", "startup_kit", "business_model.py")])
    for p in public:
        if os.path.isfile(p):
            t = open(p, encoding="utf-8").read().lower()
            assert "/users/" not in t, p
            for name in private:
                assert name not in t, (p, name)
