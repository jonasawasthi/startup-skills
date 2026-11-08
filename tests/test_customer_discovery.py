"""customer-discovery-validation: notes, provenance, hypotheses, experiments, fit, PMF, reports, CLI, packaging."""
import glob
import json
import os
import re
import shutil
import subprocess
import sys

import pytest
import yaml

from startup_kit import customer_discovery as cd
from startup_kit.evidence import Ledger

SKILL = "customer-discovery-validation"


# ----------------------------------------------------------------------------- fixtures
@pytest.fixture
def fieldnote(example_dir, tmp_path):
    """A private copy of the fictional Fieldnote profile + discovery example (record() writes to the ledger)."""
    dst = tmp_path / "fieldnote"
    shutil.copytree(os.path.join(example_dir, "startup-profile"), dst / "startup-profile")
    shutil.copytree(os.path.join(example_dir, "customer-discovery"), dst / "customer-discovery")
    return dst / "customer-discovery" / "fieldnote-discovery.yaml"


@pytest.fixture
def mini(tmp_path, ledger_file):
    """A minimal workspace: profile with the conftest ledger, empty notes folder; returns a writer."""
    from startup_kit import profile
    prof = tmp_path / "startup-profile"
    profile.init(str(prof), "Acme")
    shutil.copy(ledger_file, prof / "evidence.yaml")
    (tmp_path / "interviews").mkdir()

    def write(spec=None, notes=None, transcripts=None):
        base = {"discovery": {"company": "Acme", "profile": "startup-profile", "notes_dir": "interviews"},
                "business_model": {"type": "b2b-saas"},
                "segments": [{"id": "S1", "name": "Ops managers", "side": "customer", "market": "b2b",
                              "roles": {"user": "Ops analyst", "buyer": "Ops manager", "decision_maker": "CFO"},
                              "jobs": ["close the month"]}]}
        for k, v in (spec or {}).items():
            base[k] = v
        for name, body in (notes or {}).items():
            (tmp_path / "interviews" / name).write_text(body)
        for name, body in (transcripts or {}).items():
            (tmp_path / "interviews" / name).write_text(body)
        p = tmp_path / "discovery.yaml"
        p.write_text(yaml.safe_dump(base, allow_unicode=True))
        return str(p)
    return write


def note(iid="I-01", seg="S1", body="- [problem:x] Took two days\n", extra=""):
    return (f"---\ninterview: {iid}\nsegment: {seg}\ndate: 2026-10-01\nparticipant: P-01\nmethod: call\n"
            f"consent: true\n{extra}---\n\n{body}")


def errs(rep, area=None):
    return [i["message"] for i in rep["issues"] if i["level"] == "error" and (area is None or i["area"] == area)]


def warns(rep, area=None):
    return [i["message"] for i in rep["issues"] if i["level"] == "warning" and (area is None or i["area"] == area)]


H_BASE = {"why_it_matters": "w", "risk": "high", "confidence": "low", "validation_method": "v",
          "success_criteria": "s", "next_action": "n"}


def hyp(**kw):
    h = {"id": "H1", "category": "problem", "segment": "S1", "statement": "Managers lose days to reconciliation",
         "status": "untested", **H_BASE}
    h.update(kw)
    return h


# ----------------------------------------------------------------------------- packaging
def test_skill_discovered_and_registered(root):
    p = os.path.join(root, "skills", SKILL, "SKILL.md")
    fm = yaml.safe_load(open(p).read().split("\n---", 1)[0][4:])
    assert fm["name"] == SKILL and len(fm["description"]) <= 1024 and "Use when" in fm["description"]
    r = subprocess.run([sys.executable, os.path.join(root, "scripts", "validate_skills.py")], capture_output=True,
                       text=True)
    assert r.returncode == 0 and "8 skills, 0 errors" in r.stdout, r.stdout
    plugin = json.load(open(os.path.join(root, ".claude-plugin", "plugin.json")))
    market = json.load(open(os.path.join(root, ".claude-plugin", "marketplace.json")))
    assert "skills" not in plugin and market["plugins"][0]["version"] == plugin["version"]
    for t in ("discovery-spec.yaml", "interview-guide.md", "interview-notes.md", "hypothesis-register.yaml",
              "experiment-plan.yaml", "report-outline.md"):
        assert os.path.exists(os.path.join(root, "skills", SKILL, "assets", "templates", t)), t


def test_existing_skills_untouched_by_name(root):
    names = sorted(os.path.basename(os.path.dirname(p)) for p in glob.glob(os.path.join(root, "skills", "*",
                                                                                         "SKILL.md")))
    assert names == ["business-document-generator", "customer-discovery-validation", "fundraising-strategist",
                     "gtm-strategy-maker", "pitch-deck-maker", "startup-idea-evaluator", "startup-proposal-generator",
                     "startup-research"]


# ----------------------------------------------------------------------------- segments
def test_segments_buyer_user_and_marketplace_sides(mini):
    spec = mini({"business_model": {"type": "marketplace"},
                 "segments": [{"id": "S1", "name": "Teachers", "side": "supply", "market": "b2c",
                               "roles": {"user": "Teacher"}},
                              {"id": "S2", "name": "Buyers", "side": "supply", "market": "b2b",
                               "roles": {"user": "Analyst", "buyer": "Manager"},
                               "scores": {"pain": 4, "access": 4, "willingness_to_pay": 4, "reachable_size": 9}}]})
    rep = cd.analyze(spec)
    e, w = errs(rep, "segments"), warns(rep, "segments")
    assert any("supply and demand segments separately" in m for m in e)
    assert any("S1: name the buyer" in m for m in w)
    assert any("S2: B2B segment without roles.decision_maker" in m for m in w)
    assert any("S2: scores reachable_size must be 1–5" in m for m in e)


def test_segment_priority_needs_rationale_and_ranks(mini):
    seg = lambda i, sc, why: {"id": i, "name": i, "side": "customer", "roles": {"user": "u", "buyer": "b"},
                              "jobs": ["j"], "scores": dict(zip(("pain", "access", "willingness_to_pay",
                                                                 "reachable_size"), sc)), "why": why}
    rep = cd.analyze(mini({"segments": [seg("A", (2, 2, 2, 2), "r"), seg("B", (5, 4, 3, 4), "r"),
                                        seg("C", (5, 5, 5, 5), "")]}))
    by = {s["id"]: s for s in rep["segments"]}
    assert by["B"]["priority"] == 4.0 and by["B"]["rank"] == 1 and by["A"]["rank"] == 2
    assert any("C: prioritisation scores need a rationale" in m for m in errs(rep))


# ----------------------------------------------------------------------------- interview guides
@pytest.mark.parametrize("q", [
    "Would you use an app that reconciles payments?",
    "Don't you think spreadsheets are painful?",
    "Do you like our product?",
    "How do you handle this today and why did you choose it?",
    "If we built this, how much would you pay?",
    "Wouldn't it be great to save two days a month?",
])
def test_leading_and_hypothetical_questions_flagged(q):
    probs = cd.lint_question(q)
    assert probs and not all(p.startswith("closed") for p in probs), q


@pytest.mark.parametrize("q", [
    "Walk me through the last time you closed the month.",
    "How do you handle this today?",
    "What did that cost you in time or money?",
    "Who decided on the current approach?",
    "Tell me about the last time you paid for something to fix this.",
])
def test_good_questions_pass(q):
    assert cd.lint_question(q) == []


def test_generated_guides_pass_their_own_lint_and_differ_by_segment(fieldnote):
    spec = cd.load_spec(str(fieldnote))
    guides = {s["id"]: cd.interview_guide(spec, s) for s in spec["segments"]}
    for sid, g in guides.items():
        issues, stats = cd.lint_guide(g)
        assert not [i for i in issues if i["level"] in ("error", "warning")], (sid, issues)
        assert stats["questions"] >= 15 and stats["past_behaviour"] / stats["questions"] >= 0.4
        assert "month-end payment reconciliation" in guides["S1"] and "recording milk deliveries" in guides["S2"]
    assert "approved in your organisation" in guides["S1"]          # B2B decision process question
    assert guides["S1"] != guides["S2"]
    assert yaml.safe_load(guides["S1"].split("\n---", 1)[0][4:])["doc_type"] == "interview-guide"


def test_guide_lint_warns_when_few_behaviour_questions():
    g = "\n".join(f"{i}. What do you think about feature {i}?" for i in range(1, 6))
    issues, stats = cd.lint_guide(g)
    assert any("past behaviour" in i["message"] for i in issues) and stats["past_behaviour"] == 0


# ----------------------------------------------------------------------------- notes, transcripts, provenance
def test_transcript_analysis_and_quote_verification(mini):
    body = ('- [problem:month-end] Closing takes two days\n  > "it takes me two full days"\n'
            '- [problem:month-end] Invented line\n  > "I would pay anything for this"\n'
            '- [interpretation] Probably a strong pain\n')
    spec = mini(notes={"I-01.md": note(body=body, extra="transcript: t1.txt\n")},
                transcripts={"t1.txt": "Interviewer: ...\nP-01: Honestly it takes me two full days every month."})
    rep = cd.analyze(spec)
    obs = rep["interviews"][0]["observations"]
    q = [x for o in obs for x in o["quotes"]]
    assert q[0]["verified"] is True and q[1]["verified"] is False
    assert any("not found in the transcript" in m and "pay anything" in m for m in errs(rep, "notes"))
    assert [o["kind"] for o in obs].count("interpretation") == 1
    theme = next(t for t in rep["themes"] if t["theme"] == "month-end")
    assert theme["positive"] == ["I-01"] and len(theme["items"]) == 2      # interpretation is not counted


def test_notes_validation(mini):
    spec = mini(notes={"a.md": "---\ninterview: I-01\nsegment: S9\nparticipant: Ram Bahadur Thapa\n---\n"
                                "- [vibes:x] something\n  > \"orphan quote\"\n"})
    rep = cd.analyze(spec)
    e, w = errs(rep), warns(rep)
    assert any("needs 'date'" in m for m in e) and any("unknown code 'vibes'" in m for m in e)
    assert any("unknown segment 'S9'" in m for m in e)
    assert any("quotation must follow a coded observation" in m for m in e)
    assert any("looks like a real name" in m for m in w) and any("consent" in m for m in w)


def test_conflicting_feedback_and_segment_differences(mini):
    segs = [{"id": "S1", "name": "Managers", "side": "customer", "roles": {"user": "u", "buyer": "b"}, "jobs": ["j"]},
            {"id": "S2", "name": "Agents", "side": "customer", "roles": {"user": "u", "buyer": "b"}, "jobs": ["j"]}]
    spec = mini({"segments": segs}, notes={
        "1.md": note("I-01", "S1", "- [problem:recon] two days\n"),
        "2.md": note("I-02", "S1", "- [problem:recon -] accountant handles it\n"),
        "3.md": note("I-03", "S2", "- [problem:slips] lost slips\n"),
        "4.md": note("I-04", "S2", "- [problem:slips] wet slips\n")})
    rep = cd.analyze(spec)
    recon = next(t for t in rep["themes"] if t["theme"] == "recon")
    assert recon["contradictory"] and recon["negative"] == ["I-02"]
    assert any(d["theme"] == "slips" and d["shares"] == {"S1": 0.0, "S2": 1.0} for d in rep["differences"])
    md = cd.report_md(rep, os.path.dirname(spec), ["comparison"])
    assert "mentioned in I-01; denied in I-02" in md


def test_record_appends_ledger_entries_idempotently(fieldnote):
    led = fieldnote.parent.parent / "startup-profile" / "evidence.yaml"
    before = Ledger.load(str(led))
    text_before = led.read_text()
    (fieldnote.parent / "interviews" / "I-07-agent.md").write_text(note("I-07", "S2", "- [problem:paper-slips] x\n"))
    added = cd.record(str(fieldnote))
    after = Ledger.load(str(led))
    assert added == ["E-018"] and len(after) == len(before) + 1
    assert led.read_text().startswith(text_before)            # earlier evidence never rewritten
    e = after.get("E-018")
    assert e.source["type"] == "interview" and e.status == "reported"
    assert e.source["ref"] == "../customer-discovery/interviews/I-07-agent.md"
    assert cd.record(str(fieldnote)) == []                    # idempotent
    rep = cd.analyze(str(fieldnote))
    assert next(r for r in rep["interviews"] if r["id"] == "I-07")["ledger_id"] == "E-018"


def test_unrecorded_interview_is_flagged(mini):
    rep = cd.analyze(mini(notes={"1.md": note()}))
    assert any("not recorded in the evidence ledger" in m for m in warns(rep, "provenance"))


# ----------------------------------------------------------------------------- hypotheses
def test_hypothesis_status_requires_customer_evidence(mini):
    hs = [hyp(id="H1", status="supported", supporting=["E-003"]),            # assumption only
          hyp(id="H2", status="supported", supporting=["E-001"], contradicting=["E-002"]),
          hyp(id="H3", status="contradicted"),
          hyp(id="H4", status="untested", supporting=["E-001"], contradicting=["E-001"]),
          hyp(id="H5", category="nonsense", status="maybe", risk="huge")]
    rep = cd.analyze(mini({"hypotheses": hs}))
    e = errs(rep, "hypotheses")
    assert any(m.startswith("H1: marked supported, but no verified/reported customer evidence") for m in e)
    assert any(m.startswith("H2: marked supported while contradicting evidence") for m in e)
    assert any(m.startswith("H3: marked contradicted without") for m in e)
    assert any(m.startswith("H4: E-001 cited as both") for m in e)
    assert any(m.startswith("H5: category") for m in e) and any(m.startswith("H5: status") for m in e)
    by = {h["id"]: h for h in rep["hypotheses"]}
    assert by["H1"]["strength"] == "weak" and by["H1"]["critical"] is False   # supported (wrongly) isn't 'unresolved'


def test_conflict_note_keeps_both_sides(mini, tmp_path):
    led = tmp_path / "startup-profile" / "evidence.yaml"
    led.write_text(led.read_text() + "\n- id: E-005\n  claim: interview\n  status: reported\n  confidence: medium\n"
                   "  source: {type: interview, ref: notes}\n")
    h = hyp(status="supported", supporting=["E-005"], contradicting=["E-002"], conflict_note="different segment")
    rep = cd.analyze(mini({"hypotheses": [h]}))
    assert not errs(rep, "hypotheses")
    assert any("despite contradicting evidence (E-002): different segment" in m for m in warns(rep, "hypotheses"))
    assert rep["hypotheses"][0]["contradicting"] == ["E-002"]


def test_pricing_needs_commitment_not_interest(mini, tmp_path):
    led = tmp_path / "startup-profile" / "evidence.yaml"
    led.write_text(led.read_text() + """
- id: E-005
  claim: Survey said they'd pay
  status: reported
  confidence: medium
  source: {type: dataset, ref: survey.csv}
  signal: stated
- id: E-006
  claim: Deposits received
  status: verified
  confidence: high
  source: {type: dataset, ref: stripe export}
  signal: committed
""")
    stated = hyp(id="H1", category="pricing", status="supported", supporting=["E-005"])
    paid = hyp(id="H2", category="pricing", status="supported", supporting=["E-006"])
    rep = cd.analyze(mini({"hypotheses": [stated, paid]}))
    e = errs(rep, "hypotheses")
    assert any(m.startswith("H1: willingness to pay") and "stated interest is not purchase intent" in m for m in e)
    assert not any(m.startswith("H2") for m in e)
    assert {h["id"]: h["strength"] for h in rep["hypotheses"]} == {"H1": "moderate", "H2": "strong"}


def test_unregistered_ledger_assumptions_become_candidates(mini):
    rep = cd.analyze(mini({"hypotheses": [hyp(supporting=["E-003"])]}))
    ids = [u["id"] for u in rep["unregistered"]]
    assert "E-004" in ids and "E-003" not in ids


def test_critical_hypotheses_sorted_first(mini):
    hs = [hyp(id="H1", risk="low"), hyp(id="H2", risk="high")]
    rep = cd.analyze(mini({"hypotheses": hs}))
    assert [h["id"] for h in rep["hypotheses"]] == ["H2", "H1"] and rep["hypotheses"][0]["critical"]
    assert any("H2 is high-risk" in g for g in rep["gaps"])


# ----------------------------------------------------------------------------- experiments
def exp(**kw):
    x = {"id": "X1", "name": "n", "hypothesis": "H1", "type": "concierge", "objective": "o", "target_customer": "t",
         "method": "m", "resources": "r", "duration": "2w", "cost": "0", "steps": ["a"], "success": "≥ 3 of 5 pay",
         "failure": "0 of 5 pay", "threshold_basis": "heuristic", "evidence_to_collect": "e", "biases": "b",
         "decision_rule": {"success": "go", "failure": "stop", "inconclusive": "repeat"}}
    x.update(kw)
    return x


def test_experiment_card_completeness_and_criteria(mini):
    xs = [exp(id="X1", objective=None, biases=None),
          exp(id="X2", failure="≥ 3 of 5 pay"),
          exp(id="X3", threshold_basis=None),
          exp(id="X4", threshold_basis="benchmark"),
          exp(id="X5", type="magic", decision_rule="decide later")]
    rep = cd.analyze(mini({"hypotheses": [hyp()], "experiments": xs}))
    e, w = errs(rep, "experiments"), warns(rep, "experiments")
    assert any(m.startswith("X1: missing objective, biases") for m in e)
    assert any(m.startswith("X2: success and failure criteria are identical") for m in e)
    assert any(m.startswith("X3: thresholds need threshold_basis") for m in e)
    assert any(m.startswith("X4: benchmark threshold needs") for m in e)
    assert any(m.startswith("X5: type") for m in e) and any(m.startswith("X5: write decision_rule") for m in w)


def test_experiment_method_must_fit_hypothesis(mini):
    rep = cd.analyze(mini({"hypotheses": [hyp(category="pricing")],
                           "experiments": [exp(type="waitlist"), exp(id="X2", type="interviews",
                                                                     success="12 interviews completed")]}))
    w = warns(rep, "experiments")
    assert any("X1: waitlist measures stated interest" in m for m in w)
    assert any("X2: success measured as interviews completed is activity" in m for m in w)


def test_experiment_results_evaluated(mini, tmp_path):
    led = tmp_path / "startup-profile" / "evidence.yaml"
    led.write_text(led.read_text() + "\n- id: E-005\n  claim: pilot result\n  status: verified\n  confidence: high\n"
                   "  source: {type: dataset, ref: invoices}\n  signal: paid\n")
    s = {"metric": "paid", "op": ">=", "value": 3}
    f = {"metric": "paid", "op": "<=", "value": 0}
    xs = [exp(id="X1", success=s, failure=f, results={"status": "complete", "measured": {"paid": 4},
                                                      "evidence": ["E-005"]}),
          exp(id="X2", success=s, failure=f, results={"status": "complete", "measured": {"paid": 0},
                                                      "evidence": ["E-005"], "outcome": "success"}),
          exp(id="X3", success=s, failure=f, results={"status": "complete", "measured": {"paid": 1}}),
          exp(id="X4", hypothesis="H2", success=s, failure=f, results={"status": "complete", "measured": {"paid": 0},
                                                                       "evidence": ["E-005"]})]
    hs = [hyp(), hyp(id="H2", status="supported", supporting=["E-005"])]
    rep = cd.analyze(mini({"hypotheses": hs, "experiments": xs}))
    out = {x["id"]: x["outcome"] for x in rep["experiments"]}
    assert out == {"X1": "success", "X2": "failure", "X3": "inconclusive", "X4": "failure"}
    e = errs(rep)
    assert any("X2: declared outcome 'success' but the measured results evaluate to 'failure'" in m for m in e)
    assert any("X3: completed experiment needs results.evidence" in m for m in e)
    assert any("H2: marked supported but experiment X4 met its failure criteria" in m for m in e)


# ----------------------------------------------------------------------------- fit and PMF
def test_problem_solution_fit_never_from_interest(fieldnote):
    rep = cd.analyze(str(fieldnote))
    assert rep["errors"] == 0, rep["issues"]
    d = rep["psf"]["dimensions"]
    assert d["existence"]["status"] == "supported" and d["purchase-commitment"]["status"] == "supported"
    assert d["severity"]["status"] == "untested"
    assert rep["psf"]["verdict"].startswith("Problem exists, but severity and frequency are untested")


def test_psf_verdict_ladder():
    def H(dim, st):
        return {"id": dim, "dimension": dim, "status": st}
    v = lambda hs: cd.psf_assessment(hs, [])["verdict"]
    assert v([]).startswith("Insufficient evidence")
    assert v([H("existence", "supported"), H("severity", "contradicted")]).startswith("Mixed")
    assert v([H("existence", "supported"), H("severity", "supported")]).startswith("Problem supported; solution")
    assert v([H("existence", "supported"), H("severity", "supported"), H("solution-relevance", "supported")]
             ).startswith("Early problem-solution signals")
    assert "provisional" in v([H("existence", "supported"), H("severity", "supported"),
                               H("solution-relevance", "supported"), H("purchase-commitment", "supported")])
    # a hypothesis whose status the engine rejected does not count
    bad = [{"level": "error", "message": "existence: marked supported, but no …"}]
    assert cd.psf_assessment([H("existence", "supported")], bad)["verdict"].startswith("Insufficient")


def test_pmf_signals_metrics_and_survey(mini, tmp_path):
    led = tmp_path / "startup-profile" / "evidence.yaml"
    led.write_text(led.read_text() + "\n- id: E-005\n  claim: survey\n  status: reported\n  confidence: medium\n"
                   "  source: {type: dataset, ref: s.csv}\n")
    pmf = {"inputs": {"signups": {"value": 50, "status": "reported"}, "activated": {"value": 20, "status": "reported"},
                      "organic_signups": {"value": 30, "status": "reported"}},
           "survey": {"very_disappointed": 9, "somewhat_disappointed": 8, "not_disappointed": 3,
                      "sample": "waitlist", "evidence": ["E-005"]}}
    rep = cd.analyze(mini({"pmf": pmf}))
    m = {x["key"]: x for x in rep["pmf"]["metrics"]}
    assert m["activation_rate"]["value"] == pytest.approx(0.4)
    assert m["organic_share"]["value"] == pytest.approx(0.6)
    assert m["repeat_usage"]["value"] is None and "repeat_users" in m["repeat_usage"]["missing"]
    s = rep["pmf"]["survey"]
    assert s["n"] == 20 and s["share"] == pytest.approx(0.45)
    w = warns(rep, "pmf")
    assert any("20 responses" in x and "directional" in x for x in w) and any("'waitlist'" in x for x in w)
    assert "Early PMF signals only" in rep["pmf"]["verdict"] and "signups" in rep["pmf"]["vanity"]


def test_pmf_input_validation_and_missing_data(mini):
    bad = {"inputs": {"signups": {"value": 10, "status": "reported"}, "activated": {"value": 25, "status": "reported"},
                      "orders": {"value": -1, "status": "reported"}},
           "survey": {"very_disappointed": 9}}
    rep = cd.analyze(mini({"pmf": bad}))
    e = errs(rep, "pmf")
    assert any("'activated' (25) exceeds 'signups' (10)" in x for x in e)
    assert any("'orders' is negative" in x for x in e)
    assert any("a percentage alone cannot be checked" in x for x in e)
    empty = cd.analyze(mini({"pmf": {}}))
    assert empty["pmf"]["verdict"].startswith("No PMF data") and empty["pmf"]["metrics"] == []


def test_survey_file_parsing(fieldnote):
    rep = cd.analyze(str(fieldnote))
    s = rep["pmf"]["survey"]
    assert s["n"] == 12 and s["counts"] == {"very": 7, "somewhat": 4, "not": 1} and s["evidence"] == ["E-016"]


# ----------------------------------------------------------------------------- document guard
@pytest.mark.parametrize("line", [
    'One manager said "we would buy this tomorrow if it existed".',
    "We interviewed 40 cooperative managers.",
    "We spoke to 25 field agents last month.",
    "We spoke to 9 managers.",                         # more interviews than recorded (6), fewer than 6 + 12
    "We surveyed 30 field agents.",
    "72% of respondents said they would switch.",
    "Customers love the reconciliation feature.",
    "We have product-market fit with field agents.",
])
def test_document_guard_rejects_fabrication(fieldnote, line):
    rep = cd.analyze(str(fieldnote))
    issues = cd.check_document(f"# Findings\n\n{line}\n", None, rep)
    assert [i for i in issues if i["level"] == "error"], line


@pytest.mark.parametrize("line", [
    'One manager said "Last month it took me two full days" [E-010].',
    "We interviewed 6 people: 4 managers and 2 field agents.",
    "12 survey responses came from active field agents [E-016].",
    "3 of 4 interviewed managers described a multi-day reconciliation [E-010, E-011, E-013].",
    "Target: interview 12 more managers before the next decision.",
])
def test_document_guard_accepts_supported_text(fieldnote, line):
    rep = cd.analyze(str(fieldnote))
    led = Ledger.load(str(fieldnote.parent.parent / "startup-profile" / "evidence.yaml"))
    issues = cd.check_document(f"# Findings\n\n{line}\n", led, rep)
    assert not [i for i in issues if i["level"] == "error"], (line, issues)


def test_quote_from_desk_research_is_not_a_customer_quote(fieldnote):
    """Regression (private run): a ledger claim quoting a news source was flagged as an invented customer quote."""
    rep = cd.analyze(str(fieldnote))
    led = Ledger.load(str(fieldnote.parent.parent / "startup-profile" / "evidence.yaml"))
    ok = '- E-003 (estimate): registry summary says "about twenty-two thousand cooperatives"\n'
    assert not [i for i in cd.check_document(ok, led, rep) if i["kind"] == "quote"]
    fake = '- Manager said "we would sign up today" [E-010]\n'          # attributed to an interview, not in notes
    assert [i for i in cd.check_document(fake, led, rep) if i["kind"] == "quote" and i["level"] == "error"]


def test_document_guard_without_spec_still_blocks_counts():
    issues = cd.check_document("# X\n\nWe interviewed 30 teachers and they loved it.\n")
    assert [i for i in issues if i["level"] == "error" and i["kind"] == "count"]


# ----------------------------------------------------------------------------- reports and CLI
def test_report_sections_and_provenance(fieldnote, tmp_path):
    rep = cd.analyze(str(fieldnote))
    md = cd.report_md(rep, str(tmp_path))
    heads = re.findall(r"^# (.+)$", md, re.M)
    assert len(heads) == 18 and heads[0] == "Executive summary" and heads[-1] == "Next steps"
    assert '"Last month it took me two full days" (I-01, notes line' in md and "checked against the transcript" in md
    assert "from the notes; no transcript to check" not in md or "I-0" in md
    assert "1 of 4" in md and "No interviews yet with segment S3" in md
    fm = yaml.safe_load(md.split("\n---", 1)[0][4:])
    assert fm["doc_type"] == "customer-discovery-report" and os.path.isdir(os.path.join(str(tmp_path), fm["profile"]))
    assert not [i for i in cd.check_document(md, None, rep) if i["level"] == "error"]
    sub = cd.report_md(rep, str(tmp_path), ["problems", "wtp"])
    assert re.findall(r"^# (.+)$", sub, re.M) == ["Key customer problems", "Pricing and willingness-to-pay evidence"]
    with pytest.raises(ValueError):
        cd.report_md(rep, str(tmp_path), ["bogus"])


def test_report_with_no_research_says_so(mini, tmp_path):
    rep = cd.analyze(mini())
    md = cd.report_md(rep, str(tmp_path))
    assert "No interviews have been conducted or recorded yet" in md
    assert "No PMF data" in md


def test_cli_end_to_end(root, fieldnote, tmp_path):
    env = dict(os.environ, PYTHONPATH=os.path.join(root, "lib"))
    kit = [sys.executable, "-m", "startup_kit.cli"]
    out = tmp_path / "out"
    spec = str(fieldnote)
    steps = [["discovery", "analyze", spec, "--record", "--out", str(out)],
             ["discovery", "interviews", spec, "--out", str(out)],
             ["discovery", "hypotheses", spec, "--out", str(out), "--xlsx"],
             ["discovery", "experiment", spec, "--out", str(out), "--id", "X1"],
             ["discovery", "report", spec, "--out", str(out)],
             ["discovery", "check", str(out / "fieldnote-discovery-report.md"), "--spec", spec],
             ["discovery", "check", str(out / "interview-guide-s1.md")],
             ["doc", str(out / "fieldnote-discovery-report.md"), "--out", str(out)],
             ["check", str(out / "fieldnote-discovery-report.pdf"), str(out / "fieldnote-discovery-report.docx"),
              str(out / "fieldnote-discovery-hypotheses.xlsx")]]
    for s in steps:
        r = subprocess.run(kit + s, capture_output=True, text=True, env=env, cwd=root)
        assert r.returncode == 0, (s, r.stdout, r.stderr)
    assert "recorded 0 new entries" in subprocess.run(kit + steps[0], capture_output=True, text=True, env=env).stdout
    js = json.loads((out / "fieldnote-discovery-analysis.json").read_text())
    assert js["errors"] == 0 and "_spec" not in js
    assert json.loads((out / "fieldnote-discovery-report-build-report.json").read_text())["theme"] == "internal"
    bad = tmp_path / "bad.md"
    bad.write_text("# R\n\nWe interviewed 50 managers.\n")
    r = subprocess.run(kit + ["discovery", "check", str(bad), "--spec", spec], capture_output=True, text=True, env=env)
    assert r.returncode == 1 and "claims 50 interviews but the research spec records 6" in r.stdout


def test_cli_reports_bad_yaml_cleanly(root, tmp_path):
    p = tmp_path / "s.yaml"
    p.write_text("discovery: {company: [unclosed\n")
    env = dict(os.environ, PYTHONPATH=os.path.join(root, "lib"))
    r = subprocess.run([sys.executable, "-m", "startup_kit.cli", "discovery", "analyze", str(p)], capture_output=True,
                       text=True, env=env)
    assert r.returncode == 1 and "not valid YAML" in r.stdout and "Traceback" not in r.stderr


# ----------------------------------------------------------------------------- profile integration and regressions
def test_profile_integration_reads_context(fieldnote):
    rep = cd.analyze(str(fieldnote))
    assert rep["company"] == "Fieldnote (fictional example)" and rep["stage"] == "seed"
    assert rep["profile_dir"].endswith("startup-profile")
    assert {i["ledger_id"] for i in rep["interviews"]} == {f"E-0{n}" for n in range(10, 16)}
    assert any(u["id"] == "E-004" for u in rep["unregistered"])


def test_example_ledger_still_valid_for_other_skills(example_dir):
    errs_ = [i for i in Ledger.load(os.path.join(example_dir, "startup-profile", "evidence.yaml")).validate()
             if i.level == "error"]
    assert not errs_


def test_gtm_guard_range_regression():
    """Shared claim guard (GTM): a range describes a segment; it is not a traction claim."""
    from startup_kit import gtm
    assert not [i for i in gtm.check_claims("Cooperatives of roughly 200–600 members.\n") if i["level"] == "error"]
    assert [i for i in gtm.check_claims("We have 600 members.\n") if i["level"] == "error"]


def test_discovery_knowledge_attribution(root):
    files = [p for p in glob.glob(os.path.join(root, "knowledge", "customer-discovery", "*.md"))
             if not p.endswith("README.md")]
    assert len(files) >= 10
    for p in files:
        t = open(p, encoding="utf-8").read()
        fm = yaml.safe_load(t.split("\n---", 1)[0][3:])
        for k in ("title", "type", "date_checked", "verification"):
            assert fm.get(k), (p, k)
        if fm["type"] == "original-analysis":
            continue
        titled = {s["url"]: s for s in fm.get("sources") or []}
        for u in fm["urls"]:
            assert u in titled and titled[u]["title"] and titled[u]["verification"], (p, u)
        for u in re.findall(r"https?://[^\s)>\]\"']+", t.split("\n---", 1)[1]):
            assert u.rstrip(".,;") in fm["urls"], (p, u)
    idx = open(os.path.join(root, "knowledge", "customer-discovery", "README.md")).read()
    assert all(f"| {n} |" in idx for n in range(1, 13))
    assert "customer-discovery/README.md" in open(os.path.join(root, "knowledge", "README.md")).read()
