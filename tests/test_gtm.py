"""gtm-strategy-maker: engine guards, profile/ledger integration, documents, packaging and sources."""
import glob
import json
import os
import re
import shutil
import subprocess
import sys

import pytest
import yaml

from startup_kit import gtm
from startup_kit.evidence import Ledger

SKILL = "gtm-strategy-maker"


# ----------------------------------------------------------------------------- fixtures
@pytest.fixture
def profile_dir(tmp_path, ledger_file):
    """A minimal shared profile: profile.yaml (stage seed) + the conftest ledger."""
    from startup_kit import profile
    d = tmp_path / "startup-profile"
    profile.init(str(d), "Acme")
    txt = (d / "profile.yaml").read_text().replace("stage: idea", "stage: seed")
    (d / "profile.yaml").write_text(txt)
    shutil.copy(ledger_file, d / "evidence.yaml")
    return d


def base_spec(**over):
    spec = {
        "gtm": {"company": "Acme", "profile": "startup-profile"},
        "business_model": {"type": "b2b-saas", "self_serve": False},
        "team": {"people": 1, "hours_per_week": 40, "roles": ["founder"]},
        "budget": {"available": 1000},
        "channels": [],
        "pricing": {"model": "subscription", "value_metric": "per account", "price_points": []},
    }
    spec.update(over)
    return spec


def playbook(**over):
    ch = {"key": "founder-led-sales", "side": "both",
          "scores": {"customer_fit": 5, "economics": 4, "speed": 5, "resources": 4, "scalability": 2},
          "why": "Buyers are reachable directly", "execution": ["call"], "resources": "founder", "cost": "time",
          "leading_indicators": ["meetings"], "success_metrics": ["pilots"], "risks": ["time"],
          "experiment": {"hypothesis": "h", "metric": "m", "threshold": "t", "budget": "0", "duration": "4w",
                         "kill": "k"}}
    ch.update(over)
    return ch


def run(tmp_path, spec):
    p = tmp_path / "gtm.yaml"
    p.write_text(yaml.safe_dump(spec, allow_unicode=True))
    return gtm.analyze(str(p))


def msgs(rep, level=None, area=None):
    return [i["message"] for i in rep["issues"] if (level is None or i["level"] == level)
            and (area is None or i["area"] == area)]


# ----------------------------------------------------------------------------- discovery and packaging
def test_skill_discovered_and_spec_compliant(root):
    path = os.path.join(root, "skills", SKILL, "SKILL.md")
    text = open(path).read()
    fm = yaml.safe_load(text.split("\n---", 1)[0][4:])
    assert fm["name"] == SKILL and len(fm["description"]) <= 1024
    assert "Use when" in fm["description"]
    r = subprocess.run([sys.executable, os.path.join(root, "scripts", "validate_skills.py")], capture_output=True,
                       text=True)
    assert r.returncode == 0, r.stdout
    m = re.search(r"(\d+) skills, 0 errors", r.stdout)
    assert m and int(m.group(1)) >= 7


def test_plugin_registration_autodiscovers_skill(root):
    plugin = json.load(open(os.path.join(root, ".claude-plugin", "plugin.json")))
    market = json.load(open(os.path.join(root, ".claude-plugin", "marketplace.json")))
    # no explicit skills list: Claude Code auto-discovers skills/<name>/SKILL.md from the plugin root
    assert "skills" not in plugin
    assert market["plugins"][0]["source"] == "./"
    assert market["plugins"][0]["version"] == plugin["version"]
    assert SKILL in {os.path.basename(os.path.dirname(p)) for p in glob.glob(os.path.join(root, "skills", "*",
                                                                                           "SKILL.md"))}
    if shutil.which("claude"):
        r = subprocess.run(["claude", "plugin", "validate", root], capture_output=True, text=True, timeout=120)
        assert r.returncode == 0, r.stdout + r.stderr


def test_symlink_install_resolves_toolkit(root, tmp_path):
    target = tmp_path / "skills"
    r = subprocess.run(["bash", os.path.join(root, "scripts", "install.sh"), "--target", str(target), SKILL],
                       capture_output=True, text=True)
    assert r.returncode == 0, r.stderr
    link = target / SKILL
    assert link.is_symlink()
    tk = subprocess.run(["bash", "-c", f'cd "{link}" && cd -P ../.. && pwd'], capture_output=True, text=True)
    assert os.path.exists(os.path.join(tk.stdout.strip(), "bin", "startup-kit"))


# ----------------------------------------------------------------------------- profile and ledger integration
def test_profile_and_ledger_integration(tmp_path, profile_dir):
    spec = base_spec(metrics={"inputs": {"new_customers": {"value": 5, "evidence": ["E-001"]},
                                         "activated": {"value": 20, "evidence": ["E-002"]}}})
    rep = run(tmp_path, spec)
    assert rep["stage"] == "seed"                         # read from profile.yaml, not re-asked
    assert rep["company"] == "Acme"
    conv = next(m for m in rep["metrics"] if m["key"] == "purchase_conversion")
    assert conv["value"] == pytest.approx(0.25)
    assert conv["status"] == "reported"                  # worst of verified (E-001) and reported (E-002)
    assert any(m.startswith("customers.md") for m in rep["missing_profile"])   # profile gaps surface
    assert rep["ledger_summary"]["verified"] == 1


def test_unknown_evidence_id_is_an_error(tmp_path, profile_dir):
    rep = run(tmp_path, base_spec(channels=[playbook(evidence=["E-999"])]))
    assert any("E-999" in m for m in msgs(rep, "error", "evidence"))


def test_evidence_score_is_computed_not_declared(tmp_path, profile_dir):
    ch = playbook(evidence=["E-001"])
    ch["scores"]["evidence"] = 1
    rep = run(tmp_path, base_spec(channels=[ch, playbook(key="content", evidence=["E-003"])]))
    by = {c["key"]: c for c in rep["channels"]}
    assert by["founder-led-sales"]["evidence_score"] == 5   # verified
    assert by["content"]["evidence_score"] == 2             # assumption
    assert any("computed from the ledger" in m for m in msgs(rep, "warning"))


# ----------------------------------------------------------------------------- missing data and metrics
def test_missing_inputs_are_never_filled(tmp_path, profile_dir):
    rep = run(tmp_path, base_spec(metrics={"inputs": {"arpu": {"value": 50, "status": "assumption"},
                                                      "gross_margin": {"value": None}}}))
    ltv = next(m for m in rep["metrics"] if m["key"] == "ltv_subscription")
    assert ltv["value"] is None and "gross_margin" in ltv["missing"] and "churn" in ltv["missing"]
    md = gtm.analysis_md(rep)
    assert "nothing has been estimated" in md and "arpu × gross_margin ÷ churn" in md


def test_metric_chain_calculations(tmp_path, profile_dir):
    inputs = {"acquisition_spend": {"value": 1200, "status": "reported"},
              "new_customers": {"value": 4, "status": "reported"},
              "revenue": {"value": 600, "status": "reported"}, "active_customers": {"value": 10, "status": "reported"},
              "gross_margin": {"value": 0.8, "status": "estimate"},
              "customers_lost": {"value": 1, "status": "reported"},
              "customers_start": {"value": 20, "status": "reported"},
              "signups": {"value": 0, "status": "reported"}, "activated": {"value": 0, "status": "reported"}}
    rep = run(tmp_path, base_spec(metrics={"inputs": inputs}))
    v = {m["key"]: m for m in rep["metrics"]}
    assert v["cac"]["value"] == pytest.approx(300)
    assert v["arpu"]["value"] == pytest.approx(60)
    assert v["logo_churn"]["value"] == pytest.approx(0.05)
    assert v["ltv_subscription"]["value"] == pytest.approx(60 * 0.8 / 0.05)
    assert v["ltv_cac"]["value"] == pytest.approx(960 / 300)
    assert v["payback_months"]["value"] == pytest.approx(300 / 48)
    assert v["ltv_subscription"]["status"] == "estimate"      # weakest input wins
    assert v["activation_rate"]["value"] is None and "zero" in v["activation_rate"]["display"]


def test_supplied_metric_reported_as_given(tmp_path, profile_dir):
    rep = run(tmp_path, base_spec(metrics={"inputs": {"churn": {"value": 0.03, "evidence": ["E-003"]}}}))
    churn = next(m for m in rep["metrics"] if m["key"] == "logo_churn")
    assert churn["value"] == 0.03 and churn["status"] == "assumption" and "supplied" in churn["formula"]


# ----------------------------------------------------------------------------- channels and business models
def test_channel_prioritisation_caps_primary(tmp_path, profile_dir):
    chans = [playbook(key=k) for k in ("founder-led-sales", "content", "community", "partnerships", "email")]
    rep = run(tmp_path, base_spec(channels=chans))
    assert sum(c["decision"] == "primary" for c in rep["channels"]) == 3
    assert [c["rank"] for c in rep["channels"]] == [1, 2, 3, 4, 5]
    assert all(c["decision"] != "primary" for c in rep["channels"][3:])


def test_threshold_score_is_not_lost_to_float_error(tmp_path, profile_dir):
    """Regression (private real-world run): 4,4,3,2,3 + evidence 1 sums to 2.9999… in floating point and missed 'primary'."""
    ch = playbook(key="community", scores={"customer_fit": 4, "economics": 4, "speed": 3, "resources": 2,
                                           "scalability": 3})
    rep = run(tmp_path, base_spec(channels=[ch]))
    assert rep["channels"][0]["total"] == 3.0 and rep["channels"][0]["decision"] == "primary"


def test_founder_override_is_respected_and_shown(tmp_path, profile_dir):
    rep = run(tmp_path, base_spec(channels=[playbook(decision="test-later", reason="capacity")]))
    assert rep["channels"][0]["decision"] == "test-later" and rep["channels"][0]["forced"]
    assert "founder override" in gtm.analysis_md(rep)


def test_unjustified_scores_and_incomplete_playbooks_fail(tmp_path, profile_dir):
    no_why = playbook(why="")
    thin = playbook(key="community", execution=None, experiment={"hypothesis": "h"})
    bad = playbook(key="email")
    bad["scores"]["speed"] = 9
    rep = run(tmp_path, base_spec(channels=[no_why, thin, bad]))
    errs = msgs(rep, "error", "channels")
    assert any("rationale" in m for m in errs)
    assert any("needs 'execution'" in m for m in errs)
    assert any("experiment needs" in m and "kill" in m for m in errs)
    assert any("1 to 5" in m for m in errs)
    assert rep["errors"] >= 4


def test_business_model_guards(tmp_path, profile_dir):
    consumer = base_spec(business_model={"type": "consumer-app", "self_serve": False},
                         channels=[playbook(key="outbound", side="demand"), playbook(key="paid-ads"),
                                   playbook(key="product-led")])
    w = msgs(run(tmp_path, consumer), "warning", "model")
    assert any("outbound" in m.lower() and "consumer" in m for m in w)
    assert any("before any retention evidence" in m for m in w)
    assert any("self-serve" in m for m in w)
    # retention evidence lifts the paid-ads guard
    consumer["metrics"] = {"inputs": {"churn": {"value": 0.05, "status": "reported"}}}
    assert not any("retention evidence" in m for m in msgs(run(tmp_path, consumer), "warning", "model"))
    # outbound to the supply side of a marketplace is allowed
    mk = base_spec(business_model={"type": "marketplace"}, channels=[playbook(key="outbound", side="supply")])
    assert not any("outbound" in m.lower() for m in msgs(run(tmp_path, mk), "warning", "model"))


def test_kpi_set_adapts_to_model(tmp_path, profile_dir):
    saas = {m["key"] for m in run(tmp_path, base_spec())["metrics"]}
    market = {m["key"] for m in run(tmp_path, base_spec(business_model={"type": "marketplace"}))["metrics"]}
    assert "liquidity" in market and "supply_utilisation" in market and "liquidity" not in saas
    assert "ltv_subscription" in saas
    assert gtm.recurring(base_spec(pricing={"model": "commission"})) is False


# ----------------------------------------------------------------------------- marketplace
def test_marketplace_cold_start_reasoning(tmp_path, profile_dir):
    mk = {"sides": [{"name": "Learners", "role": "demand", "difficulty": 3, "why": "w"},
                    {"name": "Teachers", "role": "supply", "difficulty": 3, "brings_other_side": True,
                     "standalone_value": True, "why": "they bring students"}],
          "launch": {"geographies": ["Country A", "Country B"], "categories": ["Exams"]}}
    rep = run(tmp_path, base_spec(business_model={"type": "creator-platform"}, marketplace=mk,
                                  pricing={"model": "commission", "take_rate": 0.3, "value_metric": "sale"}))
    m = rep["marketplace"]
    assert m["first"]["name"] == "Teachers" and m["first"]["score"] == 6 and not m["tie"]
    assert "+2 brings the other side" in m["first"]["working"]
    w = msgs(rep, "warning", "marketplace")
    assert any("dilutes density" in x for x in w)
    assert any("atomic network" in x for x in w)
    assert any("disintermediation" in x for x in w)
    mk["launch"]["justification"] = "same exam syllabus across the border"
    assert not any("dilutes" in x for x in msgs(run(tmp_path, base_spec(business_model={"type": "marketplace"},
                                                                         marketplace=mk)), "warning"))


def test_marketplace_model_requires_section(tmp_path, profile_dir):
    rep = run(tmp_path, base_spec(business_model={"type": "marketplace"}))
    assert any("needs a 'marketplace' section" in m for m in msgs(rep, "error", "marketplace"))


# ----------------------------------------------------------------------------- pricing
def test_pricing_assumptions_stay_hypotheses(tmp_path, profile_dir):
    pricing = {"model": "commission", "take_rate": 1.5, "value_metric": "sale",
               "price_points": [{"name": "A", "price": 10, "basis": "researched", "evidence": ["E-003"]},
                                {"name": "B", "price": 20, "basis": "hypothesis"},
                                {"name": "C", "price": 30, "basis": "researched", "evidence": ["E-002"]}],
               "competitors": [{"name": "Rival", "price": 9}]}
    rep = run(tmp_path, base_spec(pricing=pricing))
    e = msgs(rep, "error", "pricing")
    assert any("A: marked researched" in m and "assumption" in m for m in e)
    assert not any(m.startswith("C:") for m in e)                       # reported evidence is acceptable
    assert any("Rival" in m and "no evidence" in m for m in e)
    assert any("take_rate 1.5" in m for m in e)
    assert any("'B' has no experiment" in m for m in msgs(rep, "warning", "pricing"))


# ----------------------------------------------------------------------------- roadmap
def test_roadmap_capacity_budget_and_dependencies(tmp_path, profile_dir):
    phases = [{"name": "First 30 days", "days": 30, "objectives": ["o"], "kpis": ["k"], "success_criteria": ["s"],
               "tasks": [{"id": "a", "task": "everything", "owner": "founder", "effort_days": 40, "cost": 900,
                          "deliverable": "d"},
                         {"id": "b", "task": "hire", "owner": "growth lead", "effort_days": 1, "cost": 500,
                          "depends_on": ["zz"], "deliverable": "d"}]}]
    rep = run(tmp_path, base_spec(roadmap={"phases": phases}))
    e = msgs(rep, "error", "roadmap")
    assert any("unrealistic" in m and "41 person-days" in m for m in e)   # 1 person × 40h ≈ 21 days in 30 days
    assert any("exceeds available budget" in m for m in e)
    assert any("unknown task 'zz'" in m for m in e)
    assert any("not in team.roles" in m for m in msgs(rep, "warning", "roadmap"))
    assert any("60, 90, 180, 365" in m for m in msgs(rep, "info", "roadmap"))


def test_cross_product_respects_status(tmp_path, profile_dir):
    spec = base_spec(products=[{"name": "Call", "status": "planned"}, {"name": "Pages", "status": "built"}],
                     roadmap={"phases": [{"name": "First 30 days", "days": 30, "tasks": []},
                                         {"name": "Months 2-6", "days": 150, "tasks": []}]},
                     cross_product=[{"product": "Call", "opportunity": "x", "phase": "First 30 days"},
                                    {"product": "Pages", "opportunity": "y", "phase": "First 30 days"},
                                    {"product": "Call", "opportunity": "z", "phase": "Months 2-6"}])
    rep = run(tmp_path, spec)
    assert sum("Call is planned" in m for m in msgs(rep, "error", "products")) == 1
    assert any("Pages is built, not live" in m for m in msgs(rep, "info", "products"))


# ----------------------------------------------------------------------------- claim guard
@pytest.mark.parametrize("line", [
    "The TAM for exam prep is $2.4B.",
    "We have 5,000 active users across the region.",
    "Revenue reached $12,000 MRR last month.",
    "Our CAC is $14 on Facebook.",
    "Our CAC is USD 40 through Facebook.",          # regression: currency word before the number
    "Revenue was Rs 45,000 in October.",
    "Customers love the product and demand is proven.",
    "We already have product-market fit.",
])
def test_unsupported_claims_fail(line):
    issues = gtm.check_claims(f"# Plan\n\n{line}\n")
    assert any(i["level"] == "error" for i in issues), line


@pytest.mark.parametrize("line", [
    "Target: 100 paid purchases by week 10.",
    "The TAM is USD 1.4M (assumption-based) [E-001].",
    "We have 5 paying customers [E-001].",
    "We do not yet have product-market fit; the survey runs after the second use.",
    "Hypothesis: CAC is below $5 for teacher referrals.",
    "LTV = ARPU × gross margin ÷ churn (formula; inputs missing).",
])
def test_supported_or_framed_claims_pass(line, ledger_file):
    issues = gtm.check_claims(f"# Plan\n\n{line}\n", Ledger.load(ledger_file))
    assert not [i for i in issues if i["level"] == "error"], (line, issues)


def test_claim_guard_ignores_list_markers_and_tasks():
    """Regressions (private real-world run): numbered list markers and imperative plan steps are not traction claims."""
    text = "1. hosts publish and promote paid workshops;\n- List 40 hosts with active channels.\n"
    assert not [i for i in gtm.check_claims(text) if i["level"] == "error"]
    assert [i for i in gtm.check_claims("1. We onboarded 400 members last month.\n") if i["level"] == "error"]


def test_claim_guard_is_sentence_level(ledger_file):
    """Regression (live Claude Code session): an uncited claim appended to a line with citations slipped through."""
    line = ("Pilots use the app weekly [E-001] and 5 pay monthly [E-002]. "
            "Fieldnote has 2,000 paying cooperatives and an LTV:CAC of 5x.\n")
    errs = [i for i in gtm.check_claims(line, Ledger.load(ledger_file)) if i["level"] == "error"]
    assert errs and "2,000 paying cooperatives" in errs[0]["message"]


def test_claim_guard_uses_table_headers():
    text = "| Metric | Target (hypothesis) |\n|---|---|\n| Paid users | 200 users |\n"
    assert not [i for i in gtm.check_claims(text) if i["level"] == "error"]
    text2 = "| Metric | Value |\n|---|---|\n| Paid users | 200 users |\n"
    assert [i for i in gtm.check_claims(text2) if i["level"] == "error"]


# ----------------------------------------------------------------------------- documents and CLI
def test_fieldnote_example_end_to_end(root, example_dir, tmp_path):
    env = dict(os.environ, PYTHONPATH=os.path.join(root, "lib"))
    kit = [sys.executable, "-m", "startup_kit.cli"]
    spec = os.path.join(example_dir, "gtm", "fieldnote-gtm.yaml")
    strat = os.path.join(root, "skills", SKILL, "examples", "example-strategy.md")
    for step in (["gtm", "analyze", spec, "--out", str(tmp_path)], ["gtm", "kpi", spec, "--out", str(tmp_path)],
                 ["gtm", "check", strat], ["doc", strat, "--out", str(tmp_path)],
                 ["check", str(tmp_path / "fieldnote-gtm-kpi-dashboard.xlsx"), str(tmp_path / "example-strategy.pdf"),
                  str(tmp_path / "example-strategy.docx")]):
        r = subprocess.run(kit + step, capture_output=True, text=True, env=env, cwd=root)
        assert r.returncode == 0, (step, r.stdout, r.stderr)
    md = (tmp_path / "fieldnote-gtm-analysis.md").read_text()
    assert "Founder-led sales" in md and "| primary |" in md and "Not computed" in md
    rep = json.loads((tmp_path / "fieldnote-gtm-analysis.json").read_text())
    assert rep["errors"] == 0 and "_spec" not in rep
    build = json.loads((tmp_path / "example-strategy-build-report.json").read_text())
    assert build["theme"] == "internal"            # doc_type gtm-strategy → internal theme


def test_kpi_workbook_has_no_invented_values(example_dir, tmp_path):
    import openpyxl
    rep = gtm.analyze(os.path.join(example_dir, "gtm", "fieldnote-gtm.yaml"))
    info = gtm.kpi_workbook(rep, str(tmp_path / "k.xlsx"), weeks=4)
    ws = openpyxl.load_workbook(str(tmp_path / "k.xlsx"))["Weekly"]
    n_inputs = len(info["inputs"])
    for row in ws.iter_rows(min_row=2, max_row=5):
        assert all(c.value is None for c in row[1:1 + n_inputs])          # inputs left blank
        assert all(str(c.value).startswith("=IF(") for c in row[1 + n_inputs:])
    defs = openpyxl.load_workbook(str(tmp_path / "k.xlsx"))["KPIs"]
    values = {r[1].value: r[4].value for r in defs.iter_rows(min_row=2)}
    assert values["Blended CAC"] == "not measured"


def test_gtm_check_cli_fails_on_fabrication(root, tmp_path):
    p = tmp_path / "s.md"
    p.write_text("---\ntitle: X\n---\n\n# Summary\n\nWe have 12,000 learners and strong traction.\n")
    env = dict(os.environ, PYTHONPATH=os.path.join(root, "lib"))
    r = subprocess.run([sys.executable, "-m", "startup_kit.cli", "gtm", "check", str(p)], capture_output=True,
                       text=True, env=env)
    assert r.returncode == 1 and "without evidence" in r.stdout


# ----------------------------------------------------------------------------- knowledge base
def _fm(path):
    t = open(path, encoding="utf-8").read()
    return yaml.safe_load(t.split("\n---", 1)[0][3:]), t


def test_gtm_knowledge_attribution(root):
    files = [p for p in glob.glob(os.path.join(root, "knowledge", "gtm", "*.md")) if not p.endswith("README.md")]
    assert len(files) >= 10
    for p in files:
        fm, text = _fm(p)
        for key in ("title", "type", "date_checked", "verification"):
            assert fm.get(key), (p, key)
        if fm["type"] == "original-analysis":
            continue
        urls = fm.get("urls") or []
        titled = {s["url"]: s for s in fm.get("sources") or []}
        assert urls, p
        for u in urls:
            assert u in titled, (p, u)                                     # every URL has a title to verify
            assert titled[u].get("title") and titled[u].get("verification"), (p, u)
        for u in re.findall(r"https?://[^\s)>\]\"']+", text.split("\n---", 1)[1]):
            assert u.rstrip(".,;") in urls, (p, u)                         # no unlisted links in the body
    index = open(os.path.join(root, "knowledge", "README.md")).read()
    assert "gtm/README.md" in index


def test_link_checker_title_relevance(root):
    sys.path.insert(0, os.path.join(root, "scripts"))
    import check_links
    assert check_links.title_matches("Growth Loops are the New Funnels", "Growth Loops are the New Funnels | Reforge Blog")
    assert check_links.title_matches("Know Your Customers' “Jobs to Be Done”", "Know Your Customers’ “Jobs to Be Done”")
    assert not check_links.title_matches("How Product-Led Growth Went From Idea to the Biggest Trend In Software",
                                         "OpenView Venture Partners")     # redirect-to-homepage is caught
    titles = check_links.expected_titles()
    assert sum(1 for u in titles if "/library/" in u) >= 5


@pytest.mark.skipif(os.environ.get("STARTUP_KIT_NETWORK") != "1", reason="network check; set STARTUP_KIT_NETWORK=1")
def test_gtm_links_live(root):
    r = subprocess.run([sys.executable, os.path.join(root, "scripts", "check_links.py")], capture_output=True,
                       text=True, timeout=600)
    assert r.returncode == 0, r.stdout[-3000:]
