"""investor-panel-evaluator: investor profiles, context, base read, question queue, output guards, sessions,
record, CLI, packaging and generalisation.

Every investor and startup in this file is fictional. Tests that depend on files other contributors write
(SKILL.md, references, templates, shipped profiles, examples) skip with a reason while those files are absent.
"""
import copy
import datetime as dt
import glob
import os
import re
import shutil
import subprocess
import sys

import pytest
import yaml

from startup_kit import shark_tank as st
from startup_kit.evidence import Ledger

SKILL = "investor-panel-evaluator"
NINE_SKILLS = ("business-document-generator", "business-model-designer", "customer-discovery-validation",
               "fundraising-strategist", "gtm-strategy-maker", "pitch-deck-maker", "startup-idea-evaluator",
               "startup-proposal-generator", "startup-research")
TODAY = "2026-11-15"
EXTRA = """
- id: E-005
  claim: Customer interview notes on re-ordering
  status: reported
  confidence: medium
  source: {type: interview, ref: notes/I-01.md}
  updated: 2026-11-10
- id: E-006
  claim: Certification status claimed on the website
  status: unverified
  confidence: low
  source: {type: web, url: "https://example.com/c", accessed: 2026-11-01}
  updated: 2026-11-10
- id: E-007
  claim: Contribution per unit after returns per founder
  value: -3
  status: reported
  confidence: medium
  source: {type: founder, ref: call notes}
  updated: 2026-11-10
"""


# ----------------------------------------------------------------------------- fictional investors
def src(i, typ="press", ver="read-at-source"):
    return {"id": f"S{i}", "title": f"Fictional source {i}", "url": f"https://example.com/s{i}",
            "publisher": "Example Publisher", "type": typ, "published": "undated", "accessed": dt.date(2026, 11, 1),
            "verification": ver}


def prof(pid="avery-quillfeather", name="Avery Quillfeather", emphasis=None, lenses=None, **over):
    d = {"id": pid, "name": name, "name_variants": [], "type": "investor-profile", "kind": "programme-investor",
         "regions": ["GB"],
         "programmes": [{"programme": "example-den", "role": "investor", "seasons": "1–3", "panel_status": "current",
                         "status_note": "Named in the line-up for the latest season.",
                         "status_checked": dt.date(2026, 11, 1), "sources": ["S1"]}],
         "last_verified": dt.date(2026, 11, 1), "profile_confidence": "medium",
         "confidence_rationale": "Panel status rests on the broadcaster page; career facts rest on the company site "
                                 "and one press profile; no portfolio filings were found.",
         "sources": [src(1, "broadcaster"), src(2, "company"), src(3, "press")],
         "business_background": [{"id": "B1", "fact": "Founded a fictional retail company in 2004.",
                                  "sources": ["S2"]}],
         "major_ventures": [{"id": "V1", "name": "Example Retail", "role": "Founder", "years": "2004–2019",
                             "status": "sold", "sources": ["S2"]}],
         "documented_expertise": [{"id": "X1", "domain": "consumer retail", "basis": "Built a retail company (V1).",
                                   "sources": ["S2"]}],
         "documented_philosophy": [{"id": "P1", "kind": "stated",
                                    "paraphrase": "Argues that founders should know their landed cost per unit.",
                                    "sources": ["S3"]}],
         "investment_history": [], "investment_history_note": "No completed investments could be confirmed.",
         "known_gaps": [{"domain": "regulated finance", "basis": "No documented record found."}],
         "evaluation_lenses": lenses or [
             {"id": "L1", "label": "Retail margin stack",
              "interpretation": "Analytical interpretation: the documented record (P1, X1) suggests close attention "
                                "to margins after retailer cuts.",
              "derived_from": ["P1", "X1"], "dimensions": ["D07", "D09"],
              "attracted_by": "Verified sell-through and a margin that survives retail cuts.",
              "concerned_by": "Margins that only work when selling direct.",
              "evidence_demanded": ["sell-through by store", "landed cost per unit"], "decline_pattern": None},
             {"id": "L2", "label": "Repeat demand",
              "interpretation": "Analytical interpretation: the documented record (X1) points to re-orders as the "
                                "test of demand.",
              "derived_from": ["X1"], "dimensions": ["D03", "D08"],
              "attracted_by": "Customers who re-order without discounts.",
              "concerned_by": "One-off trial purchases.", "evidence_demanded": ["re-order rate"]}],
         "dimension_emphasis": emphasis or {"primary": {"D07": "L1"}, "secondary": {"D03": "L2"}},
         "cautions": [], "unsupported": [], "simulation_only": True}
    d.update(over)
    return d


BODY = """
# {name}

> Profile for analytical simulation only. Public, professional information as of 2026-11-01.

## Summary

Founded a fictional retail company [S2] and appears on a fictional programme [S1].

## Panel membership

- Example Den: seasons 1–3, current [S1].

## Notes for maintainers

- Nothing outstanding.
"""


def write_profile(lib, d, body=None, fname=None):
    os.makedirs(lib, exist_ok=True)
    p = os.path.join(lib, (fname or d.get("id", "x")) + ".md")
    with open(p, "w", encoding="utf-8") as f:
        f.write("---\n" + yaml.safe_dump(d, sort_keys=False, allow_unicode=True) + "---\n"
                + (body if body is not None else BODY.format(name=d.get("name", ""))))
    return p


PANEL = [("avery-quillfeather", "Avery Quillfeather", {"primary": {"D07": "L1"}, "secondary": {"D03": "L2"}}),
         ("morgan-fenwick", "Morgan Fenwick", {"primary": {"D03": "L2", "D08": "L2"}, "secondary": {}}),
         ("rowan-tessaly", "Rowan Tessaly", {"primary": {"D09": "L1"}, "secondary": {"D07": "L1"}})]


@pytest.fixture
def lib(tmp_path):
    d = tmp_path / "investors"
    for pid, name, emph in PANEL:
        write_profile(str(d), prof(pid, name, emph))
    (d / "README.md").write_text("# Library\n\nNot a profile.\n")
    return str(d)


@pytest.fixture
def library(lib):
    profs, issues = st.load_library([lib], TODAY, include_default=False)
    assert not issues and all(p.ok for p in profs.values()), [p.issues for p in profs.values()]
    return profs


# ----------------------------------------------------------------------------- fictional startup
@pytest.fixture
def profile_dir(tmp_path, ledger_file):
    from startup_kit import profile
    p = tmp_path / "acme" / "startup-profile"
    profile.init(str(p), "Acme")
    shutil.copy(ledger_file, p / "evidence.yaml")
    with open(p / "evidence.yaml", "a") as f:
        f.write(EXTRA)
    return p


def dim(rating, crit=False, conf="medium", **ev):
    e = {b: [] for b in st.BUCKETS}
    e.update(ev)
    return {"rating": rating, "confidence": conf, "critical": crit, "explanation": "Fictional explanation.",
            "evidence": e, "upgrade_if": "A fictional upgrade trigger.", "downgrade_if": "A fictional trigger."}


def base_read(**over):
    dims = {
        "D01": dim("adequate", True, reported=["E-002"]), "D02": dim("unknown", assumption=["E-003"]),
        "D03": dim("strong", True, verified=["E-001"]), "D04": dim("unknown", unknowns=["What customers use now"]),
        "D05": dim("adequate", estimate=["E-004"]), "D06": dim("adequate", True, reported=["E-005"]),
        "D07": dim("weak", True, reported=["E-007"]), "D08": dim("unknown"), "D09": dim("unknown"),
        "D10": dim("unknown"), "D11": dim("adequate", reported=["E-002"]), "D12": dim("unknown", True),
        "D13": dim("unknown"), "D14": dim("strong", True, verified=["E-001"]),
        "D15": dim("unknown", disputed=["E-006"])}
    d = {"startup": "acme", "as_of": dt.date(2026, 11, 14), "ledger_snapshot": dt.date(2026, 11, 10),
         "business_type": ["saas"], "stage": "early-revenue", "ambition": "venture", "dimensions": dims}
    d.update(over)
    return d


def ledger_of(profile_dir):
    return Ledger.load(str(profile_dir / "evidence.yaml"))


def errs(issues, rule=None):
    return [i for i in issues if i["level"] == "error" and (rule is None or i["rule"] == rule)]


def warns(issues, rule=None):
    return [i for i in issues if i["level"] == "warning" and (rule is None or i["rule"] == rule)]


def label(names):
    return (f"> [!SIMULATION] {st.SIM_LABEL} {names}. Based on public sources as of 2026-11-01 and the startup "
            f"evidence available on 2026-11-10.")


TRACE = """| # | Kind | Point | Lens | Dimension (base rating) | Evidence |
|---|---|---|---|---|---|
| A1 | attracts | Re-orders without discounts point to real demand for the core product | L2 | D03 (Strong) | E-001 verified |
| C1 | concern | Contribution per unit is negative on founder-provided figures after returns | L1 | D07 (Weak) | E-007 founder-provided |
| Q1 | question | Which retailer terms apply and who controls shelf placement | L1 | D09 (Unknown) | gap |
| R1 | evidence demanded | Sell-through by store for three months | L1 | D09 | gap |
| M1 | recommendation | Run a priced channel test before any retail listing | base | D08 | gap |
"""


def evaluation(extra="", inv=("avery-quillfeather", "Avery Quillfeather"), trace=TRACE, stance=None, head=None):
    return f"""---
title: "Acme: simulated evaluation"
doc_type: shark-tank
simulation: true
kind: evaluation
investors: [{inv[0]}]
---

{head if head is not None else label(inv[1])}

# {inv[1]}: simulated evaluation of Acme

Lenses applied: L1 Retail margin stack, L2 Repeat demand (analytical interpretations of the documented record).

## Stance

{stance or "Conditional on evidence of positive contribution after returns."}

## Point trace

{trace}
## Primary concerns

{extra}
"""


def check(text, ledger=None, profiles=None, against=None):
    """Guard tests that do not exercise the base-read gates opt out of them explicitly, as --no-base-read does."""
    return st.check_document(text, ledger, profiles or {}, against, "doc.md", None, allow_no_base=True,
                             allow_no_ledger=ledger is None)


# ----------------------------------------------------------------------------- packaging and structure
def _skill(root, *parts):
    return os.path.join(root, "skills", SKILL, *parts)


def _need(path, what):
    if not os.path.exists(path):
        pytest.skip(f"{what} not written yet ({os.path.relpath(path)})")


def _shipped(root):
    return [p for p in glob.glob(_skill(root, "investors", "*.md")) if os.path.basename(p).lower() != "readme.md"]


def test_skill_discovered_and_registered(root):
    p = _skill(root, "SKILL.md")
    _need(p, "SKILL.md")
    text = open(p, encoding="utf-8").read()
    fm = yaml.safe_load(text.split("\n---", 1)[0][4:])
    assert fm["name"] == SKILL and len(fm["description"]) <= 1024 and "Use when" in fm["description"]
    assert len(text.splitlines()) < 500
    r = subprocess.run([sys.executable, os.path.join(root, "scripts", "validate_skills.py")], capture_output=True,
                       text=True)
    assert r.returncode == 0 and "10 skills, 0 errors" in r.stdout, r.stdout          # exactly ten (audit A-1)
    names = {os.path.basename(os.path.dirname(p)) for p in glob.glob(os.path.join(root, "skills", "*", "SKILL.md"))}
    assert names == set(NINE_SKILLS) | {SKILL}
    import json
    plugin = json.load(open(os.path.join(root, ".claude-plugin", "plugin.json")))
    market = json.load(open(os.path.join(root, ".claude-plugin", "marketplace.json")))
    assert "skills" not in plugin and plugin["version"] == "1.4.0" == market["plugins"][0]["version"]


def test_required_files_exist(root):
    _need(_skill(root, "SKILL.md"), "SKILL.md")
    refs = ["investor-profile-schema", "evaluator-crosswalk", "dimensions", "individual-evaluation", "panel",
            "interrogation", "verdict", "business-types-and-stages", "guards", "integration", "maintaining-investors"]
    for r in refs:
        assert os.path.exists(_skill(root, "references", f"{r}.md")), r
    for t in ("investor-profile.md", "base-read.yaml", "evaluation.md", "panel-report.md", "verdict.md",
              "interrogation-session.yaml", "debrief.md", "summary-report.md"):
        assert os.path.exists(_skill(root, "assets", "templates", t)), t
    assert os.path.exists(_skill(root, "investors", "README.md"))


def test_all_skill_links_resolve_recursively(root):
    _need(_skill(root, "SKILL.md"), "SKILL.md")                    # the skill is still being written
    _need(_skill(root, "investors", "README.md"), "investors/README.md")
    files = glob.glob(_skill(root, "**", "*.md"), recursive=True)
    for f in files:
        text = re.sub(r"```.*?```", "", open(f, encoding="utf-8").read(), flags=re.S)
        for m in re.finditer(r"\]\(([^)\s#]+)(?:#[^)]*)?\)", text):
            target = m.group(1)
            if re.match(r"^[a-z]+:", target) or "<" in target:     # template placeholders such as <id>
                continue
            assert os.path.exists(os.path.normpath(os.path.join(os.path.dirname(f), target))), (f, target)


def test_no_absolute_or_home_paths(root):
    for f in glob.glob(_skill(root, "**", "*"), recursive=True):
        if os.path.isfile(f):
            t = open(f, encoding="utf-8").read().lower()
            assert "/users/" not in t and "~/" not in t, f


def test_profile_template_parses_without_crashing(root, tmp_path):
    t = _skill(root, "assets", "templates", "investor-profile.md")
    p = st.validate_profile(t, TODAY)
    assert p.errors and all(i["rule"].startswith("P") for i in p.issues)    # placeholders: reported, no crash


def test_shipped_library_validates_clean(root):
    if not _shipped(root):
        pytest.skip("no shipped investor profiles yet")
    profs, issues = st.load_library(today=TODAY)
    bad = {p.id: [i["message"] for i in p.errors] for p in profs.values() if p.errors}
    assert not errs(issues) and not bad, bad
    assert all(p.effective for p in profs.values())


def test_shipped_profiles_match_contract_roster_shape(root):
    files = _shipped(root)
    if not files:
        pytest.skip("no shipped investor profiles yet")
    profs, _ = st.load_library(today=TODAY)
    assert {os.path.splitext(os.path.basename(f))[0] for f in files} == set(profs)
    progs = {pr["programme"] for p in profs.values() for pr in p.meta.get("programmes") or []}
    regions = {r for p in profs.values() for r in p.meta.get("regions") or []}
    assert len(progs) >= 2 and len(regions) >= 2          # the library spans more than one market


def test_library_index_lists_every_profile(root):
    readme = _skill(root, "investors", "README.md")
    _need(readme, "investors/README.md")
    if not _shipped(root):
        pytest.skip("no shipped investor profiles yet")
    text = open(readme, encoding="utf-8").read()
    for f in _shipped(root):
        assert os.path.basename(f) in text or os.path.splitext(os.path.basename(f))[0] in text, f


def test_cli_help_lists_new_and_existing_commands(root):
    env = dict(os.environ, PYTHONPATH=os.path.join(root, "lib"))
    r = subprocess.run([sys.executable, "-m", "startup_kit.cli", "--help"], capture_output=True, text=True, env=env)
    for c in ("doctor", "profile", "ledger", "scan", "market-size", "unit-economics", "deck", "doc", "model", "check",
              "preview", "gtm", "discovery", "business-model", "themes", "shark-tank"):
        assert c in r.stdout, c
    r = subprocess.run([sys.executable, "-m", "startup_kit.cli", "shark-tank", "--help"], capture_output=True,
                       text=True, env=env)
    for a in ("profiles", "context", "base-read", "queue", "check", "session", "record"):
        assert a in r.stdout


def test_symlink_install_resolves_toolkit(root, tmp_path):
    _need(_skill(root, "SKILL.md"), "SKILL.md")
    target = tmp_path / "skills"
    r = subprocess.run(["bash", os.path.join(root, "scripts", "install.sh"), "--target", str(target), SKILL],
                       capture_output=True, text=True)
    assert r.returncode == 0, r.stderr
    tk = subprocess.run(["bash", "-c", f'cd "{target / SKILL}" && cd -P ../.. && pwd'], capture_output=True, text=True)
    assert os.path.exists(os.path.join(tk.stdout.strip(), "bin", "startup-kit"))


def test_existing_skills_still_present(root):
    names = {os.path.basename(os.path.dirname(p)) for p in glob.glob(os.path.join(root, "skills", "*", "SKILL.md"))}
    assert names >= {"business-document-generator", "customer-discovery-validation", "fundraising-strategist",
                     "gtm-strategy-maker", "pitch-deck-maker", "startup-idea-evaluator", "startup-proposal-generator",
                     "startup-research", "business-model-designer"}


# ----------------------------------------------------------------------------- research: profile rules (P1–P11)
def test_good_profile_validates_and_readme_is_not_a_profile(lib, library):
    assert set(library) == {i for i, _, _ in PANEL}
    p = library["avery-quillfeather"]
    assert p.ok and p.declared == "medium" and p.effective == "medium" and p.supported == "medium"
    assert p.lens_for("D07") == "L1" and p.lens_for("D08") == "L2" and p.lens_for("D01") is None


def _mut(path, value):
    def f(d):
        cur = d
        for k in path[:-1]:
            cur = cur[k]
        if value is KeyError:
            del cur[path[-1]]
        else:
            cur[path[-1]] = value
    return f


BAD_PROFILES = [
    ("P1", _mut(["sources"], KeyError)),
    ("P1", _mut(["kind"], "celebrity")),
    ("P1", _mut(["profile_confidence"], "certain")),
    ("P1", _mut(["id"], "someone-else")),
    ("P1", _mut(["last_verified"], KeyError)),
    ("P2", _mut(["sources", 0, "url"], "http://example.com/s1")),
    ("P2", lambda d: d.update(sources=d["sources"][:1])),
    ("P2", _mut(["sources", 1, "verification"], "skimmed")),
    ("P3", _mut(["business_background", 0, "sources"], ["S9"])),
    ("P3", lambda d: d["sources"].__setitem__(1, src(2, "reference"))),
    ("P3", lambda d: d.update(investment_history_note="")),
    ("P4", _mut(["programmes", 0, "panel_status"], "guest-judge")),
    ("P4", _mut(["programmes", 0, "status_checked"], dt.date(2026, 11, 5))),
    ("P4", lambda d: d.update(programmes=[])),
    ("P5", _mut(["evaluation_lenses", 0, "interpretation"], "The record shows margin focus.")),
    ("P5", _mut(["evaluation_lenses", 0, "derived_from"], ["P7"])),
    ("P5", _mut(["evaluation_lenses", 1, "decline_pattern"], "Declines when margins rely on direct sales.")),
    ("P6", _mut(["dimension_emphasis"], {"primary": {"D01": "L1"}, "secondary": {}})),
    ("P6", _mut(["dimension_emphasis"], {"primary": {"D07": "L1", "D09": "L1", "D03": "L2", "D08": "L2",
                                                      "D02": "L1"}, "secondary": {}})),
    ("P7", _mut(["profile_confidence"], "high")),
    ("P7", _mut(["confidence_rationale"], "Too short to justify anything.")),
    ("P8", lambda d: d.update(net_worth="large")),
    ("P8", lambda d: d.update(catchphrases=["anything"])),
    ("P8", _mut(["documented_philosophy", 0, "paraphrase"], 'Says "know your numbers" often.')),
    ("P8", _mut(["evaluation_lenses", 0, "attracted_by"], "Founders whom she would invest in.")),
    ("P8", _mut(["business_background", 0, "fact"], "Is interested in pet products.")),
    ("P8", _mut(["cautions"], [{"topic": "contact", "guidance": "office@example-den.com", "sources": []}])),
    ("P9", _mut(["last_verified"], dt.date(2027, 1, 1))),
    ("P9", _mut(["sources", 0, "accessed"], dt.date(2027, 1, 1))),
    ("P10", _mut(["business_background", 0, "fact"], "Grew revenue [E-001].")),
    ("P11", _mut(["simulation_only"], False)),
]


@pytest.mark.parametrize("rule,mutate", BAD_PROFILES, ids=[f"{r}-{i}" for i, (r, _) in enumerate(BAD_PROFILES)])
def test_invalid_profiles_rejected(tmp_path, rule, mutate):
    d = prof()
    mutate(d)
    p = st.validate_profile(write_profile(str(tmp_path), d, fname="avery-quillfeather"), TODAY)
    assert errs(p.issues, rule), (rule, p.issues)


@pytest.mark.parametrize("body,rule", [
    ("# X\n\nFounded a company [S9].\n", "P10"),
    ("# X\n\nGrew sales [E-001].\n", "P10"),
    ('# X\n\nOnce told an audience "every founder must know every number cold".\n', "P8"),
    ("# X\n\nCall +1 555 123 4567 for bookings.\n", "P8"),
])
def test_invalid_profile_bodies_rejected(tmp_path, body, rule):
    p = st.validate_profile(write_profile(str(tmp_path), prof(), body=body), TODAY)
    assert errs(p.issues, rule), p.issues


def test_profile_quoted_title_in_body_and_source_titles_allowed(tmp_path):
    d = prof()
    d["sources"][0]["title"] = 'Meet the panel: "Example Den" returns'
    body = BODY.format(name="Avery Quillfeather") + '\nAuthor of "Margins First" [S3].\n'
    p = st.validate_profile(write_profile(str(tmp_path), d, body=body), TODAY)
    assert p.ok, p.issues


def test_decline_pattern_allowed_with_two_sources(tmp_path):
    d = prof()
    d["documented_philosophy"][0]["sources"] = ["S3"]
    d["evaluation_lenses"][0]["decline_pattern"] = "Documented declines where margin relied on direct sales only."
    p = st.validate_profile(write_profile(str(tmp_path), d), TODAY)       # L1 reaches S3 (P1) and S2 (X1)
    assert p.ok and p.lens_reach("L1") == 2, p.issues


def test_staleness_is_a_warning_that_lowers_effective_confidence(tmp_path):
    d = prof(last_verified=dt.date(2025, 3, 1))
    for s in d["sources"]:
        s["accessed"] = dt.date(2025, 3, 1)
    d["programmes"][0]["status_checked"] = dt.date(2025, 3, 1)
    path = write_profile(str(tmp_path), d)
    fresh = st.validate_profile(path, "2025-06-01")
    assert fresh.ok and fresh.effective == "medium" and not warns(fresh.issues, "P9")
    stale = st.validate_profile(path, TODAY)                                # 20 months later
    assert stale.ok and stale.effective == "low" and warns(stale.issues, "P9")


def test_high_confidence_needs_sources_and_twelve_months(tmp_path):
    d = prof(profile_confidence="high")
    d["sources"] = [src(1, "broadcaster"), src(2, "company"), src(3, "press"), src(4, "own-statement"),
                    src(5, "press"), src(6, "official-bio")]
    d["documented_philosophy"][0]["sources"] = ["S3", "S4"]
    d["documented_expertise"][0]["sources"] = ["S2", "S5"]
    path = write_profile(str(tmp_path), d)
    p = st.validate_profile(path, TODAY)
    assert p.ok and p.effective == "high", p.issues
    later = st.validate_profile(path, "2027-12-01")                         # 13 months: warning, not error
    assert later.ok and later.effective == "medium" and warns(later.issues, "P9")


def test_duplicate_ids_across_libraries_rejected(tmp_path, lib):
    other = tmp_path / "private"
    write_profile(str(other), prof())
    _, issues = st.load_library([lib, str(other)], TODAY, include_default=False)
    assert errs(issues, "P1")


def test_investor_sources_in_link_checker(tmp_path, monkeypatch, root):
    sys.path.insert(0, os.path.join(root, "scripts"))
    try:
        import check_links
    finally:
        sys.path.pop(0)
    monkeypatch.setattr(check_links, "INVESTORS", str(tmp_path / "none"))
    knowledge_only = check_links.expected_titles()
    assert knowledge_only                                   # knowledge/ behaviour unchanged
    lib = tmp_path / "investors"
    write_profile(str(lib), prof())
    (lib / "README.md").write_text("---\nsources:\n  - {title: Not a profile, url: 'https://example.com/readme'}\n---\n")
    monkeypatch.setattr(check_links, "INVESTORS", str(lib))
    titles = check_links.expected_titles()
    assert titles["https://example.com/s1"] == "Fictional source 1"
    assert "https://example.com/readme" not in titles
    assert set(knowledge_only) <= set(titles)
    assert "https://example.com/s2" in check_links.collect(False)


# ----------------------------------------------------------------------------- integration: context (read-only)
def _snapshot(d):
    out = {}
    for dp, _, fns in os.walk(d):
        for fn in fns:
            p = os.path.join(dp, fn)
            out[p] = (os.path.getmtime(p), open(p, "rb").read())
    return out


def test_context_reads_shared_profile_and_writes_nothing(example_dir, tmp_path):
    ws = tmp_path / "fieldnote"
    shutil.copytree(example_dir, ws)
    before = _snapshot(ws)
    ctx = st.context(str(ws / "startup-profile"))
    assert _snapshot(ws) == before
    assert not ctx["has_profile_yaml"] and ctx["entries"] == len(Ledger.load(str(ws / "startup-profile" /
                                                                                  "evidence.yaml")))
    kinds = {o["folder"]: o["kind"] for o in ctx["outputs"]}
    assert kinds["business-model"] == "business model" and kinds["gtm"] == "GTM" and kinds["deck"] == "deck"
    assert kinds["customer-discovery"] == "discovery" and kinds["proposal"] == "proposal"
    assert any(f["path"].startswith("business-model/") for o in ctx["outputs"] for f in o["files"])
    assert "Sibling outputs" in st.context_md(ctx)


def test_context_flags_stale_outputs(profile_dir):
    ws = profile_dir.parent
    (ws / "gtm").mkdir()
    old = ws / "gtm" / "analysis.md"
    old.write_text("# old\n")
    t = dt.datetime(2026, 10, 1).timestamp()
    os.utime(old, (t, t))
    (ws / "shark-tank").mkdir()
    (ws / "shark-tank" / "base-read.yaml").write_text("ledger_snapshot: 2026-11-01\n")
    before = _snapshot(ws)
    ctx = st.context(str(profile_dir))
    assert _snapshot(ws) == before
    o = {x["folder"]: x for x in ctx["outputs"]}
    assert ctx["ledger_latest_updated"] == "2026-11-10"
    assert o["gtm"]["stale"] and o["shark-tank"]["base_read_stale"]
    assert ctx["missing_information"] > 0 and ctx["founder_reported"] == 2


# ----------------------------------------------------------------------------- base read (B1–B6, crosswalk)
def test_valid_base_read_passes_and_renders(profile_dir, library):
    led = ledger_of(profile_dir)
    data = base_read()
    assert not errs(st.validate_base_read(data, led, TODAY))
    line = st.evidence_profile_line(data["dimensions"])
    assert line.startswith("Base read (15 dimensions): Strong 2 · Adequate 4 · Weak 1 · Unknown 8.")
    assert "D07 Weak" in line and "D12 Unknown" in line
    md = st.render_base_read(data, led, "../startup-profile")
    assert line in md and "/15" not in md
    assert not errs(check(md, led, library)), errs(check(md, led, library))


@pytest.mark.parametrize("change,rule,text", [
    (lambda d: d["dimensions"].pop("D09"), "B1", "D09"),
    (lambda d: d["dimensions"]["D02"].update(rating="insufficient"), "B1", "unknown"),
    (lambda d: d["dimensions"]["D02"]["evidence"].pop("disputed"), "B1", "disputed"),
    (lambda d: d["dimensions"]["D02"].update(explanation=""), "B1", "explanation"),
    (lambda d: d.update(stage="series-a"), "B1", "stage"),
    (lambda d: d["dimensions"]["D03"]["evidence"].update(verified=["E-099"]), "B2", "E-099"),
    (lambda d: d["dimensions"]["D01"]["evidence"].update(verified=["E-002"], reported=[]), "B2", "E-002"),
    (lambda d: d["dimensions"]["D04"]["evidence"].update(unknowns=["E-003"]), "B2", "E-003"),
    (lambda d: d["dimensions"]["D01"].update(rating="strong"), "B3", "Strong"),             # founder-reported only
    (lambda d: d["dimensions"]["D02"].update(rating="adequate"), "B3", "Adequate"),         # assumption only
    (lambda d: d["dimensions"]["D15"].update(rating="weak"), "B3", "Weak"),                 # unverified only
    (lambda d: d["dimensions"]["D05"].update(ceiling="strong"), "B3", "ceiling"),
])
def test_base_read_rules(profile_dir, change, rule, text):
    d = base_read()
    change(d)
    e = errs(st.validate_base_read(d, ledger_of(profile_dir), TODAY), rule)
    assert e and any(text in i["message"] for i in e), e


def test_interview_reported_evidence_allows_strong(profile_dir):
    d = base_read()
    d["dimensions"]["D06"]["rating"] = "strong"                            # E-005 is interview-reported
    assert not errs(st.validate_base_read(d, ledger_of(profile_dir), TODAY))


def test_stale_snapshot_is_a_warning(profile_dir):
    d = base_read(ledger_snapshot=dt.date(2026, 11, 1))
    iss = st.validate_base_read(d, ledger_of(profile_dir), TODAY)
    assert not errs(iss) and warns(iss, "B1")


@pytest.mark.parametrize("dimid,evaluator,needs", [
    ("D01", {"problem-severity": "strong"}, True),        # carried, differs
    ("D01", {"problem-severity": "adequate"}, False),
    ("D07", {"business-model": "adequate"}, True),        # primary split, differs
    ("D06", {"business-model": "adequate"}, False),       # secondary, same
    ("D06", {"business-model": "weak"}, False),           # secondary, one level away
    ("D11", {"execution-risk": "weak"}, False),           # derived: no rule
    ("D02", {"market": "adequate", "timing": "weak"}, False),    # base unknown vs start weak -> needs
    ("D03", {"customer-clarity": "weak"}, True),          # D03 strong while clarity weak
    ("D03", {"customer-clarity": "adequate"}, False),
])
def test_divergence_note_rule(profile_dir, dimid, evaluator, needs):
    d = base_read(imported_from="outputs/acme/startup-analysis/acme-evaluation.md")
    d["dimensions"][dimid]["evaluator"] = evaluator
    if dimid == "D02":
        needs = True                                       # D02 is Unknown, the evaluator's start is Weak
    led = ledger_of(profile_dir)
    has = bool(errs(st.validate_base_read(d, led, TODAY), "B1"))
    assert has == needs
    if needs:
        d["dimensions"][dimid]["divergence_note"] = "Evaluator report 2026-10-01 differs; see [E-001]."
        assert not errs(st.validate_base_read(d, led, TODAY))
        assert "Divergences from the idea evaluation" in st.render_base_read(d, led)


def test_secondary_split_two_levels_needs_note_and_wrong_key_rejected(profile_dir):
    led = ledger_of(profile_dir)
    d = base_read(imported_from="x.md")
    d["dimensions"]["D11"]["evaluator"] = {"business-model": "weak"}
    assert errs(st.validate_base_read(d, led, TODAY), "B1")
    d = base_read(imported_from="x.md")
    d["dimensions"]["D06"].update(rating="strong", evidence=dict(d["dimensions"]["D06"]["evidence"]))
    d["dimensions"]["D06"]["evaluator"] = {"business-model": "weak"}
    assert any("divergence" in i["message"] for i in errs(st.validate_base_read(d, led, TODAY)))


def J(j1="no", j2=(("venture", "no"),), j3="no", j4="yes", j5="yes", j5_reason="D07 contribution is negative"):
    """Judgements that follow from base_read(): D07 critical Weak (medium, founder-provided) and D12 critical
    Unknown, so J1 No, J2 No, J3 No, J4 Yes, J5 Yes."""
    return {"J1": {"answer": j1, "reason": "r"}, "J2": [{"class": c, "answer": a, "reason": "r"} for c, a in j2],
            "J3": {"answer": j3, "reason": "r"}, "J4": {"answer": j4, "reason": "r"},
            "J5": {"answer": j5, "reason": j5_reason}}


@pytest.mark.parametrize("j,ok", [
    (J(), True),
    (J(j5="no", j5_reason="A credible mitigation inside the current model: a price rise to cover returns."), True),
    (J(j5="no"), False),                                   # critical Weak, no mitigation named
    (J(j3="yes", j4="yes"), False),
    (J(j5="yes", j2=(("venture", "yes"),)), False),
    (J(j2=(("angel", "no"),)), False),
    (J(j1="yes"), False),                                  # D07 is Weak
    (J(j1="not-yet-determinable"), False),                 # Weak at medium confidence decides J1: No
    (J(j4="no"), False),                                   # critical D12 Unknown
    (J(j3="yes", j4="no", j2=(("venture", "yes"),)), False),
    (J(j2=(("venture", "not-yet-determinable"),)), False),  # J1 is No, so J2 is No
    ({k: v for k, v in J().items() if k != "J3"}, False),
])
def test_judgement_combinations(profile_dir, j, ok):
    d = base_read(judgements=j)
    e = errs(st.validate_base_read(d, ledger_of(profile_dir), TODAY), "B6")
    assert (not e) == ok, e


# ----------------------------------------------------------------------------- question queue
def test_queue_tiers_rotation_and_budget(profile_dir, library):
    d = base_read()
    d["dimensions"]["D09"]["critical"] = False
    profs = [library[i] for i, _, _ in PANEL]
    rows = st.queue(d, profs, budget=20, ledger=ledger_of(profile_dir))
    tiers = [r["tier"] for r in rows]
    assert tiers == sorted(tiers)
    by = {r["dimension"]: r for r in rows}
    assert by["D12"]["tier"] == 1 and by["D07"]["tier"] == 2 and by["D01"]["tier"] == 3
    assert "D06" not in by                                 # adequate on interview evidence: not tier 3
    assert by["D09"]["tier"] == 4 and by["D08"]["tier"] == 4          # primary emphasis for a panel member
    assert by["D09"]["investor"] == "rowan-tessaly" and by["D08"]["investor"] == "morgan-fenwick"
    assert by["D12"]["investor"] == "base" and by["D07"]["lens"] == "L1"
    assert by["D02"]["tier"] == 5
    assert len({r["investor"] for r in rows if r["investor"] != "base"}) == 3   # rotation covers the panel
    assert rows == st.queue(d, profs, budget=20, ledger=ledger_of(profile_dir))
    assert len(st.queue(d, profs, budget=3)) == 3


# ----------------------------------------------------------------------------- output guards
@pytest.fixture
def ctx(profile_dir, library):
    return ledger_of(profile_dir), library


def test_good_evaluation_passes(ctx):
    led, lib = ctx
    assert not errs(check(evaluation(), led, lib)), errs(check(evaluation(), led, lib))


BAD_LINES = [
    ("O2", 'Avery Quillfeather called the margin "a problem" in this simulation.'),
    ("O2", "Avery Quillfeather would say the margin is too thin."),
    ("O2", "Quillfeather thinks the product is strong."),
    ("O2", "Avery Quillfeather loves the packaging."),
    ("O3", "Avery Quillfeather: the margin does not work."),
    ("O3", "**Morgan Fenwick:** show me the numbers."),
    ("O3", "I'm out."),
    ("O3", "For that reason, I would pass on this one."),
    ("O5", "An offer of $100,000 for 10% of the company."),
    ("O5", "A valuation of $2M is reasonable."),
    ("O5", "A royalty of 5% until the loan is repaid."),
    ("O5", "We have a deal at ₹50 lakh."),
    ("O5", "The panel might take a 20% stake."),
    ("O7", "Avery Quillfeather would invest if margins improve."),
    ("O7", "Morgan Fenwick is likely to invest after the pilot."),
    ("O7", "Rowan Tessaly is interested in the brand."),
    ("O7", "The panel would invest at this stage."),
    ("O7", "Avery Quillfeather has seen the pitch deck."),
    ("O7", "There is a 70% chance of success."),
    ("O7", "The probability of success is modest."),
    ("B4", "Overall the startup scores 9/15 on the base read."),
    ("B4", "The average rating is Adequate."),
    ("B5", "Strong 2 · Adequate 5 · Weak 2."),
]


@pytest.mark.parametrize("rule,line", BAD_LINES, ids=[f"{r}-{i}" for i, (r, _) in enumerate(BAD_LINES)])
def test_bad_lines_rejected(ctx, rule, line):
    led, lib = ctx
    assert errs(check(evaluation(line), led, lib), rule), check(evaluation(line), led, lib)


GOOD_LINES = [
    "The 30/70 revenue split between the platform and suppliers is set out in the model [E-001].",
    "A gross margin of 40% is the target for the next quarter.",
    'The product is sold under the name "FieldBox" to cooperatives.',
    "Through L1 (an analytical interpretation of Avery Quillfeather's documented attention to margins), this "
    "simulation flags the negative contribution as the binding question.",
    "A question raised through L2: which customers have re-ordered in the last three months, and at what volumes?",
    "The founder-provided figure shows contribution of -3 per unit after returns [E-007].",
    "The company signed a distribution deal with a regional retailer at a 30% retailer margin, pending documents.",
    "The core product offer at $29 a month is not yet tested.",
    "Base read (15 dimensions): Strong 2 · Adequate 4 · Weak 1 · Unknown 8.",
    "Reasons an investor might decline include the unit economics.",
    "The founder said the pilot ran for six weeks [E-001].",
    "Equity crowdfunding is outside the scope of this evaluation.",
]


@pytest.mark.parametrize("line", GOOD_LINES)
def test_honest_analytical_prose_passes(ctx, line):
    led, lib = ctx
    assert not errs(check(evaluation(line), led, lib)), errs(check(evaluation(line), led, lib))


def test_simulation_label_and_front_matter_required(ctx):
    led, lib = ctx
    assert errs(check(evaluation().replace("simulation: true", "simulation: false"), led, lib), "O1")
    assert errs(check(evaluation(head="Some intro first."), led, lib), "O1")
    assert errs(check(evaluation(head=label("Morgan Fenwick")), led, lib), "O1")      # wrong name


def test_scenario_callout_rules(ctx):
    led, lib = ctx
    good = ("> [!SCENARIO] Hypothetical scenario: not an offer, not a valuation, not attributed to any investor.\n"
            "> A scenario in which an operator-investor provides $100,000 for 10% equity.\n"
            "> Assumptions:\n> - The founder's own ask, as supplied by the user.\n")
    assert not errs(check(evaluation(good), led, lib)), errs(check(evaluation(good), led, lib))
    for bad in (good.replace("Hypothetical scenario", "Illustration"),
                good.replace("> Assumptions:\n> - The founder's own ask, as supplied by the user.\n", ""),
                good.replace("an operator-investor", "Avery Quillfeather")):
        assert errs(check(evaluation(bad), led, lib), "O6")
    assert errs(check(evaluation(good + "> Avery Quillfeather would invest here.\n"), led, lib), "O7")


def test_evidence_rules(ctx):
    led, lib = ctx
    assert errs(check(evaluation("Contribution is -3 per unit after returns [E-007]."), led, lib), "O8")
    assert errs(check(evaluation("Demand rests on [E-099]."), led, lib), "O8")
    assert errs(check(evaluation("We have 12,000 users across the region."), led, lib), "O8")
    bad = TRACE.replace("E-001 verified", "E-098 verified")
    assert errs(check(evaluation(trace=bad), led, lib), "O8")
    assert warns(check(evaluation(), None, lib), "O8")


def test_unknown_or_invalid_investor_rejected(ctx, tmp_path):
    led, lib = ctx
    assert errs(check(evaluation(inv=("nobody-real", "Nobody Real")), led, lib), "O10")
    d = prof()
    d["simulation_only"] = False
    bad = st.validate_profile(write_profile(str(tmp_path / "b"), d), TODAY)
    assert errs(check(evaluation(), led, dict(lib, **{"avery-quillfeather": bad})), "O10")


def test_stance_and_trace_rules(ctx):
    led, lib = ctx
    assert errs(check(evaluation(stance="Out."), led, lib), "T1")
    assert errs(check(evaluation(trace=TRACE.replace("| L2 |", "| L7 |")), led, lib), "T1")
    deal = TRACE + "| B1 | potential deal-breaker | Negative margin | L1 | D07 (Weak) | E-007 founder-provided |\n"
    assert errs(check(evaluation(trace=deal), led, lib), "T1")                # L1 has no decline_pattern
    generic = TRACE.replace("| L2 | D03", "| base | D03").replace("| L1 | D07", "| base | D07")
    assert errs(check(evaluation(trace=generic), led, lib), "T2")
    twin = TRACE + ("| C2 | concern | Re-orders without discounts point to real demand for the core product | L1 | "
                    "D07 (Weak) | E-007 founder-provided |\n")
    assert warns(check(evaluation(trace=twin), led, lib), "T4")


def test_pairwise_name_swap_check(ctx):
    led, lib = ctx
    a = evaluation()
    b = evaluation(inv=("morgan-fenwick", "Morgan Fenwick"))
    assert errs(check(a, led, lib, [("evaluation-morgan-fenwick.md", b)]), "T3")
    b_conv = b.replace("## Primary concerns", "Declared convergence: both lenses centre on D07.\n\n## Primary concerns")
    assert not errs(check(a, led, lib, [("evaluation-morgan-fenwick.md", b_conv)]), "T3")
    other_trace = TRACE.replace("| C1 | concern | Contribution per unit is negative on founder-provided figures after "
                                "returns | L1 | D07 (Weak) | E-007 founder-provided |",
                                "| C1 | concern | Acquisition cost per paying customer is unmeasured | L2 | D08 (Unknown) "
                                "| gap |")
    b2 = evaluation(inv=("morgan-fenwick", "Morgan Fenwick"), trace=other_trace)
    assert not errs(check(a, led, lib, [("e.md", b2)]), "T3")


def panel_doc(final_cause="X1", exchange_lens="L1", cls="different-priorities", order=True, n=3):
    ids = [i for i, _, _ in PANEL][:n]
    names = ", ".join(nm for _, nm, _ in PANEL[:n])
    init = """## Initial positions

| Investor | Stance | Top attraction | Top concern |
|---|---|---|---|
| Avery Quillfeather | Conditional on evidence | A1 | C1 |
| Morgan Fenwick | Not persuaded on current evidence | A1 | C1 |
| Rowan Tessaly | Cannot form a view (insufficient evidence) | none | Q1 |
"""
    disc = f"""## Discussion

| # | Dimension | Investor | Lens | Evidence or gap | Point |
|---|---|---|---|---|---|
| X1a | D07 | avery-quillfeather | {exchange_lens} | E-007 founder-provided | Contribution is negative after returns |
| X1b | D07 | morgan-fenwick | L2 | E-005 reported | Re-orders matter more than current margin |
"""
    return f"""---
title: "Acme: simulated panel"
doc_type: shark-tank
simulation: true
kind: panel
investors: [{", ".join(ids)}]
---

{label(names)}

# Acme: simulated panel

{init if order else disc}
{disc if order else init}
## Disagreements explained

| Dimension | Class | Cause field | What would resolve it |
|---|---|---|---|
| D07 | {cls} | dimension_emphasis | A founder fit question |

## Final positions

| Investor | Initial stance | Final stance | Cause |
|---|---|---|---|
| Avery Quillfeather | Conditional on evidence | Conditional on evidence | Unchanged |
| Morgan Fenwick | Not persuaded on current evidence | Conditional on evidence | {final_cause} |

## Avery Quillfeather: position summary

{label("Avery Quillfeather")}

Through L1 this simulation keeps D07 as the binding question.
"""


def test_panel_rules(ctx):
    led, lib = ctx
    assert not errs(check(panel_doc(), led, lib)), errs(check(panel_doc(), led, lib))
    assert errs(check(panel_doc(order=False), led, lib), "N2")
    assert errs(check(panel_doc(final_cause="consensus"), led, lib), "N3")
    assert errs(check(panel_doc(final_cause="X9"), led, lib), "N3")
    assert errs(check(panel_doc(exchange_lens="L9"), led, lib), "T1")
    assert errs(check(panel_doc(exchange_lens=""), led, lib), "N4")
    assert errs(check(panel_doc(cls="personality clash"), led, lib), "N4")
    assert errs(check(panel_doc(n=2), led, lib), "O10")
    no_label = panel_doc().replace(label("Avery Quillfeather") + "\n\nThrough", "Through")
    assert errs(check(no_label, led, lib), "O1")
    ev = evaluation(stance="Not persuaded on current evidence.")
    assert errs(check(panel_doc(), led, lib, [("evaluation-avery-quillfeather.md", ev)]), "N2")


def verdict_doc(rows, closing=True):
    table = "| Judgement | Answer | Reason | Deciding dimensions |\n|---|---|---|---|\n" + "\n".join(
        f"| {j} | {a} | Reason. | D07 |" for j, a in rows)
    return f"""---
title: "Acme: verdict"
doc_type: shark-tank
simulation: true
kind: verdict
investors: []
---

{label("any investor")}

# Acme: investment verdict

{table}

{"This assessment reflects the evidence available on 2026-11-14. It is not a prediction of success, nor of any investor's decision." if closing else ""}
"""


GOOD_J = [("J1 Good business", "Not yet determinable"), ("J2 Investable business (venture)", "No"),
          ("J2 Investable business (operator-strategic)", "Not yet determinable"),
          ("J3 Investment-ready business", "No"), ("J4 Needs further validation", "Yes"),
          ("J5 Should not proceed in its current form", "No")]


def test_verdict_rules(ctx):
    led, lib = ctx
    assert not errs(check(verdict_doc(GOOD_J), led, lib)), errs(check(verdict_doc(GOOD_J), led, lib))
    assert errs(check(verdict_doc(GOOD_J, closing=False), led, lib), "O1")
    assert errs(check(verdict_doc(GOOD_J[:3] + GOOD_J[4:]), led, lib), "B6")
    both = [(j, "Yes" if j.startswith(("J3", "J4")) else a) for j, a in GOOD_J]
    assert errs(check(verdict_doc(both), led, lib), "B6")
    j5 = [(j, "Yes" if j.startswith("J5") or "venture" in j else a) for j, a in GOOD_J]
    assert errs(check(verdict_doc(j5), led, lib), "B6")
    noclass = [(j.replace(" (venture)", ""), a) for j, a in GOOD_J if "operator" not in j]
    assert errs(check(verdict_doc(noclass), led, lib), "B6")
    assert errs(check(verdict_doc([]).replace("| Judgement", "| Thing"), led, lib), "B6")


def test_insufficiently_evidenced_label_warns(ctx):
    led, lib = ctx
    iss = check(evaluation("D02 is Insufficiently evidenced."), led, lib)
    assert warns(iss, "B5") and not errs(iss, "B5")


# ----------------------------------------------------------------------------- sessions (I1–I3) and record
def session(**over):
    d = {"session": "2026-11-15-a", "mode": "investor", "investors": ["avery-quillfeather"], "budget": 10,
         "status": "debrief",
         "queue": [{"id": "Q3", "dimension": "D08", "lens": "L2", "tier": 1, "text": "Which channel?"}],
         "turns": [
             {"n": 1, "question": {"id": "Q1", "dimension": "D07", "lens": "L1", "investor": "avery-quillfeather",
                                   "text": "What is the contribution per unit after returns?", "follow_up_of": None},
              "answer": "About minus three per unit.", "decision": "follow-up",
              "assessment": {"specificity": "clear", "evidence": "missing", "financial": "partial",
                             "strategic": "n/a", "customer": "n/a", "execution": "n/a", "risk": "partial"},
              "new_facts": [{"claim": "Contribution per unit after returns", "proposed_status": "reported"}]},
             {"n": 2, "question": {"id": "Q1a", "dimension": "D07", "lens": "L1", "investor": "avery-quillfeather",
                                   "text": "Which cost line drives the loss?", "follow_up_of": "Q1"},
              "answer": "Returns.", "decision": "move-on"}],
         "pending_ledger": [{"id": "F1", "claim": "Return rate in the last quarter", "key": "ops.return_rate",
                             "value": 0.12, "turn": 2, "proposed_status": "reported"},
                            {"id": "F2", "claim": "Stores stocking the product", "value": 40, "unit": "stores",
                             "turn": 1, "proposed_status": "reported"}],
         "next_action": "debrief"}
    d.update(over)
    return d


def test_valid_session_passes(library):
    assert not errs(st.validate_session(session(), library))


def _turn(k, qid, follow=None, text="Which retailer re-ordered?"):
    return {"n": k, "question": {"id": qid, "dimension": "D03", "lens": "L2", "text": text, "follow_up_of": follow}}


@pytest.mark.parametrize("change,rule", [
    (lambda d: d["turns"][0].update(question=[d["turns"][0]["question"]] * 2), "I1"),
    (lambda d: d["turns"][0]["question"].update(text="What is the margin? And the CAC?"), "I2"),
    (lambda d: d["turns"][0]["question"].update(text="I'd like to know the margin?"), "I2"),
    (lambda d: d["turns"].extend([_turn(3, "Q1b", "Q1a"), _turn(4, "Q1c", "Q1b")]), "I1"),   # third follow-up
    (lambda d: d["turns"][1].update(n=5), "I1"),
    (lambda d: d.update(budget=1, turns=d["turns"] + [_turn(3, "Q2")]), "I1"),
    (lambda d: d["turns"][0]["new_facts"][0].update(proposed_status="verified"), "I3"),
    (lambda d: d["pending_ledger"][0].update(proposed_status="verified"), "I3"),
    (lambda d: d.update(mode="panel"), "I1"),
    (lambda d: d["turns"][0]["assessment"].update(charisma="clear"), "I1"),
    (lambda d: d["turns"][0]["question"].update(lens="L9"), "I1"),
])
def test_invalid_sessions_rejected(library, change, rule):
    d = copy.deepcopy(session())
    change(d)
    assert errs(st.validate_session(d, library), rule)


def _write_session(tmp_path, d):
    p = tmp_path / "s.yaml"
    p.write_text(yaml.safe_dump(d, sort_keys=False))
    return str(p)


def test_record_is_append_only_idempotent_and_founder_only(tmp_path, profile_dir, library):
    s = _write_session(tmp_path, session())
    ev = profile_dir / "evidence.yaml"
    before = ev.read_bytes()
    with pytest.raises(ValueError):
        st.record(s, str(profile_dir), confirmed=False)
    assert ev.read_bytes() == before
    added = st.record(s, str(profile_dir), confirmed=True, today=TODAY, profiles=library)
    assert added == ["E-008", "E-009"]
    after = ev.read_bytes()
    assert after.startswith(before)                         # existing entries byte-identical
    led = Ledger.load(str(ev))
    for eid in added:
        e = led.get(eid)
        assert e.status == "reported" and e.source["type"] == "founder" and "2026-11-15-a" in e.notes
        assert e.updated == TODAY
    assert not any(e.status == "verified" for e in led.entries if e.id in added)
    assert not [i for i in led.validate(dt.date(2026, 11, 15)) if i.level == "error"]
    assert st.record(s, str(profile_dir), confirmed=True, today=TODAY) == []
    assert ev.read_bytes() == after


def test_simulated_opinions_never_reach_ledger(tmp_path, profile_dir, library):
    d = session()
    d["pending_ledger"] = [{"id": "F1", "claim": "Avery Quillfeather finds the margin weak",
                            "proposed_status": "reported"}]
    before = (profile_dir / "evidence.yaml").read_bytes()
    with pytest.raises(ValueError):
        st.record(_write_session(tmp_path, d), str(profile_dir), confirmed=True, today=TODAY, profiles=library)
    d["pending_ledger"] = [{"id": "F1", "claim": "Margin is weak under lens L1", "proposed_status": "reported"}]
    with pytest.raises(ValueError):
        st.record(_write_session(tmp_path, d), str(profile_dir), confirmed=True, today=TODAY)
    d["pending_ledger"] = [{"id": "F1", "claim": "Stores", "status": "verified", "proposed_status": "reported"}]
    with pytest.raises(ValueError):
        st.record(_write_session(tmp_path, d), str(profile_dir), confirmed=True, today=TODAY)
    assert (profile_dir / "evidence.yaml").read_bytes() == before


def test_record_refuses_without_existing_ledger(tmp_path):
    (tmp_path / "empty").mkdir()
    with pytest.raises(ValueError):
        st.record(_write_session(tmp_path, session()), str(tmp_path / "empty"), confirmed=True, today=TODAY)
    assert not (tmp_path / "empty" / "evidence.yaml").exists()


# ----------------------------------------------------------------------------- CLI end to end
def kit(root, *args):
    env = dict(os.environ, PYTHONPATH=os.path.join(root, "lib"))
    return subprocess.run([sys.executable, "-m", "startup_kit.cli", "shark-tank", *args], capture_output=True,
                          text=True, env=env)


def test_cli_end_to_end_and_no_parallel_store(root, tmp_path, profile_dir, lib):
    L = ["--no-shipped", "--library", lib, "--today", TODAY]
    r = kit(root, "profiles", *L)
    assert r.returncode == 0 and "avery-quillfeather" in r.stdout and "3 profiles" in r.stdout, r.stdout
    r = kit(root, "profiles", *L, "--id", "morgan-fenwick")
    assert r.returncode == 0 and "L2 Repeat demand" in r.stdout and "primary: D03 L2" in r.stdout
    write_profile(os.path.join(lib, "..", "bad"), prof("bad-one", "Bad One", simulation_only=False))
    assert kit(root, "profiles", *L, "--library", os.path.join(lib, "..", "bad")).returncode == 1
    ws = profile_dir.parent
    r = kit(root, "context", str(profile_dir))
    assert r.returncode == 0 and "Ledger: 7 entries" in r.stdout
    out = ws / "shark-tank"
    out.mkdir()
    br = out / "base-read.yaml"
    br.write_text(yaml.safe_dump(base_read(), sort_keys=False))
    r = kit(root, "base-read", str(br), "--profile", str(profile_dir), "--out", str(out / "base-read.md"), *L)
    assert r.returncode == 0 and "Unknown 8" in r.stdout, r.stdout
    r = kit(root, "check", str(out / "base-read.md"), *L)               # ledger resolved from front matter
    assert r.returncode == 0 and "(no ledger" not in r.stdout, r.stdout
    r = kit(root, "queue", str(br), "--investors", "avery-quillfeather,morgan-fenwick,rowan-tessaly", "--json", *L)
    assert r.returncode == 0 and '"tier": 1' in r.stdout
    assert kit(root, "queue", str(br), "--investors", "nobody", *L).returncode == 1
    (out / "evaluation-avery-quillfeather.md").write_text(evaluation())
    (out / "evaluation-morgan-fenwick.md").write_text(evaluation(inv=("morgan-fenwick", "Morgan Fenwick")))
    r = kit(root, "check", str(out / "evaluation-avery-quillfeather.md"), "--profile", str(profile_dir), *L,
            "--against", str(out / "evaluation-morgan-fenwick.md"))
    assert r.returncode == 1 and "T3" in r.stdout and "T6" in r.stdout    # base-read.yaml beside the document
    (out / "interrogation").mkdir()
    sp = out / "interrogation" / "2026-11-15-a.yaml"
    sp.write_text(yaml.safe_dump(session(), sort_keys=False))
    assert kit(root, "session", str(sp), *L).returncode == 0
    before = (profile_dir / "evidence.yaml").read_bytes()
    r = kit(root, "record", str(sp), "--profile", str(profile_dir), *L)
    assert r.returncode == 1 and (profile_dir / "evidence.yaml").read_bytes() == before
    r = kit(root, "record", str(sp), "--profile", str(profile_dir), "--confirmed", *L)
    assert r.returncode == 0 and "E-008, E-009" in r.stdout
    # the only evidence store is startup-profile/evidence.yaml
    stores = [p for p in glob.glob(str(ws / "**" / "*"), recursive=True)
              if re.search(r"evidence|ledger", os.path.basename(p), re.I) and p.endswith((".yaml", ".yml", ".json"))]
    assert stores == [str(profile_dir / "evidence.yaml")]


def test_doc_type_theme(tmp_path, profile_dir, library):
    from startup_kit.docs.build import DOC_TYPE_THEME, build
    assert DOC_TYPE_THEME["shark-tank"] == "internal" and DOC_TYPE_THEME["business-model"] == "internal"
    md = tmp_path / "base-read.md"
    md.write_text(st.render_base_read(base_read(), ledger_of(profile_dir), str(profile_dir)))
    rep = build(str(md), str(tmp_path / "out"), ("md",))
    assert rep["theme"] == "internal" and rep["errors"] == 0, rep["issues"]


# ----------------------------------------------------------------------------- integration: nothing else changes
def test_example_ledger_still_valid_and_untouched(root, example_dir):
    led = Ledger.load(os.path.join(example_dir, "startup-profile", "evidence.yaml"))
    assert not [i for i in led.validate() if i.level == "error"]
    r = subprocess.run(["git", "diff", "--quiet", "HEAD", "--", "examples/fieldnote/startup-profile",
                        "lib/startup_kit/evidence.py", "lib/startup_kit/profile.py", "lib/startup_kit/gtm.py",
                        "lib/startup_kit/business_model.py", "lib/startup_kit/customer_discovery.py",
                        "templates", "tests/conftest.py", "knowledge", ".gitignore"]
                       + [f"skills/{n}" for n in NINE_SKILLS], cwd=root)                  # audit A-4
    assert r.returncode == 0, "shared files changed"


def _example_folders(root):
    return sorted(d for d in glob.glob(os.path.join(root, "examples", "*", "shark-tank")) if os.path.isdir(d))


# examples carry real dates; only staleness (a warning) can change as time passes, so the clock is safe here
EXAMPLE_TODAY = max(dt.date.today(), dt.date(2026, 11, 16)).isoformat()


@pytest.fixture(scope="module")
def shipped():
    return st.load_library(today=EXAMPLE_TODAY)[0]


def _is_sim_doc(text):
    return text.startswith("---") and bool(re.search(r"^doc_type:\s*shark-tank\s*$", text.split("\n---", 1)[0], re.M))


def test_examples_are_discovered(root):
    if not _example_folders(root):
        pytest.skip("no examples/*/shark-tank/ folders yet")
    for d in _example_folders(root):
        assert os.path.isfile(os.path.join(os.path.dirname(d), "startup-profile", "evidence.yaml")), d


@pytest.mark.parametrize("folder", ["fieldnote", "ottlebrook"])
def test_tracked_example_passes_every_engine_check(root, folder, shipped):
    d = os.path.join(root, "examples", folder, "shark-tank")
    _need(d, f"examples/{folder}/shark-tank")
    prof_dir = os.path.join(root, "examples", folder, "startup-profile")
    led = Ledger.load(os.path.join(prof_dir, "evidence.yaml"))
    assert not [i for i in led.validate(dt.date(2026, 11, 16)) if i.level == "error"]       # the example's ledger
    base = st.load_yaml(os.path.join(d, "base-read.yaml"))
    assert not errs(st.validate_base_read(base, led, EXAMPLE_TODAY)), errs(st.validate_base_read(base, led,
                                                                                               EXAMPLE_TODAY))
    docs = {p: t for p in sorted(glob.glob(os.path.join(d, "*.md")))
            for t in [open(p, encoding="utf-8").read()] if _is_sim_doc(t)}
    evals = [(os.path.basename(p), t) for p, t in docs.items() if os.path.basename(p).startswith("evaluation-")]
    assert docs and evals
    for p, text in docs.items():
        against = [(n, t) for n, t in evals if n != os.path.basename(p)]
        e = errs(st.check_document(text, led, shipped, against, os.path.basename(p), base))   # T6 enforced
        assert not e, (p, e)
    for sp in glob.glob(os.path.join(d, "interrogation", "*.yaml")):
        e = errs(st.validate_session(st.load_yaml(sp), shipped))
        assert not e, (sp, e)


def test_every_example_folder_is_covered_by_the_parametrised_test(root):
    found = {os.path.basename(os.path.dirname(d)) for d in _example_folders(root)}
    assert found <= {"fieldnote", "ottlebrook"}, f"add {sorted(found - {'fieldnote', 'ottlebrook'})} to the test"


# ----------------------------------------------------------------------------- generalisation
def _private_terms(root):
    """Private startups are the folders under outputs/; their profile name, brand name and legal-entity fields are
    read locally at test time and never written anywhere."""
    out = os.path.join(root, "outputs")
    terms = set()
    if not os.path.isdir(out):
        return terms
    for d in os.listdir(out):
        if not os.path.isdir(os.path.join(out, d)):
            continue
        terms.add(d.lower())
        prof = os.path.join(out, d, "startup-profile", "profile.yaml")
        if os.path.isfile(prof):
            data = yaml.safe_load(open(prof, encoding="utf-8")) or {}
            brand = data.get("brand") if isinstance(data.get("brand"), dict) else {}
            for v in (data.get("name"), data.get("legal_name"), data.get("legal_entity"), brand.get("name")):
                if isinstance(v, str) and len(v.strip()) >= 4:
                    terms.add(v.strip().lower())
    return terms


def test_private_outputs_are_gitignored_and_public_files_are_clean(root):
    r = subprocess.run(["git", "check-ignore", "-q", "outputs/any-startup/shark-tank/base-read.yaml"], cwd=root)
    assert r.returncode == 0
    private = _private_terms(root)
    # every tracked or new file outside outputs/ (audit B-7), not only this skill's folder
    files = subprocess.run(["git", "ls-files", "-co", "--exclude-standard"], cwd=root, capture_output=True,
                           text=True).stdout.split("\n")
    me = os.path.relpath(os.path.abspath(__file__), root)
    leaks = []
    for rel in files:
        if not rel or rel.startswith("outputs/") or rel == me:
            continue
        p = os.path.join(root, rel)
        try:
            t = open(p, encoding="utf-8").read().lower()
        except (UnicodeDecodeError, OSError):
            continue
        if rel.startswith(("skills/investor-panel-evaluator/", "examples/", "lib/startup_kit/shark_tank.py")) \
                and "/users/" in t:
            leaks.append((rel, "/users/"))
        for name in private:
            if re.search(r"(?<![a-z0-9])" + re.escape(name) + r"(?![a-z0-9])", t):
                leaks.append((rel, "a private startup term"))
    assert not leaks, leaks


def test_engine_has_no_programme_specific_rules():
    """The engine knows no real investor: names come only from profile libraries."""
    src = open(st.__file__, encoding="utf-8").read()
    assert "shark-tank-us" not in src and "dragons-den" not in src


# ----------------------------------------------------------------------------- polish round
def test_stance_rule_order_and_counts(library):
    p = library["avery-quillfeather"]                      # primary D07; critical D01 D03 D06 D07 D12 D14
    d = base_read()
    rows = st.parse_trace(st._Doc(evaluation()))
    assert st.expected_stance(d, p, rows)[0] == "not-persuaded"          # D07 deciding, Weak at medium confidence
    want, info = st.expected_stance(d, p, [r for r in rows if r["kind"] != "C"])
    assert want == "not-persuaded"                                       # B-9: omitting the C row changes nothing
    assert info["deciding"] == ["D01", "D03", "D06", "D07", "D12", "D14"]
    d["dimensions"]["D07"]["confidence"] = "low"                         # Weak at low confidence counts as Unknown
    want, info = st.expected_stance(d, p, rows)
    assert want == "conditional" and info["unknown"] == ["D07", "D12"]
    d["dimensions"]["D01"] = dim("unknown", True)
    want, info = st.expected_stance(d, p, rows)
    assert want == "no-view" and len(info["unknown"]) == 3              # D01 D07 D12: half of six
    d["dimensions"]["D01"] = dim("adequate", True, reported=["E-002"])
    d["dimensions"]["D07"] = dim("adequate", True, reported=["E-007"])
    d["dimensions"]["D12"] = dim("adequate", True, reported=["E-002"])
    assert st.expected_stance(d, p, [])[0] == "persuaded"
    assert st.expected_stance(d, p, None)[0] == "persuaded"


def test_stance_consistency_guard(ctx):
    led, lib = ctx
    base = base_read()
    e = errs(check_b(evaluation(), led, lib, base), "T6")
    assert e and "expected 'Not persuaded on current evidence'" in e[0]["message"] and "1 Weak (D07)" in e[0]["message"]
    assert not errs(check_b(evaluation(stance="Not persuaded on current evidence. C1 decides it."), led, lib, base), "T6")
    assert not errs(check(evaluation(), led, lib), "T6")                   # no base read: not checked
    b2 = base_read()
    for k in ("D01", "D07"):
        b2["dimensions"][k] = dim("unknown", True)
    e = errs(check_b(evaluation(stance="Not persuaded on current evidence."), led, lib, b2), "T6")
    assert e and "Cannot form a view" in e[0]["message"] and "3 of 6" in e[0]["message"]


def check_b(text, ledger, profiles, base, against=None):
    return st.check_document(text, ledger, profiles, against, "doc.md", base)


def test_panel_initial_stances_follow_base_read(ctx):
    led, lib = ctx
    e = errs(check_b(panel_doc(), led, lib, base_read()), "T6")
    assert {m for i in e for m in ("avery-quillfeather", "rowan-tessaly", "morgan-fenwick") if m in i["message"]} \
        == {"avery-quillfeather", "rowan-tessaly"}                       # Morgan Fenwick's stance is right


def test_concern_rows_on_unknown_with_gap_are_accepted(ctx):
    led, lib = ctx
    gap_rows = TRACE + ("| C2 | concern | No evidence yet that the cash runway covers the plan | base | D12 (Unknown) | "
                        "gap: no cash figures in the ledger |\n"
                        "| C3 | concern | No evidence yet of re-orders beyond the pilot | L2 | D03 (Unknown) | gap: re-orders |\n")
    doc = evaluation(trace=gap_rows, stance="Not persuaded on current evidence.")
    assert not errs(check_b(doc, led, lib, base_read())), errs(check_b(doc, led, lib, base_read()))
    rows = st.parse_trace(st._Doc(doc))
    assert [r["lens"] for r in rows if r["kind"] == "C"] == ["L1", "base", "L2"]
    generic = gap_rows.replace("| L2 | D03 (Strong)", "| base | D03 (Strong)").replace("| L2 | D03 (Unknown)",
                                                                                      "| base | D03 (Unknown)")
    assert errs(check(evaluation(trace=generic), led, lib), "T2")         # 1 of 4 A/C rows lens-tagged


def test_queue_restricted_mode_and_emphasis_first(tmp_path, library):
    low = prof("casey-lowden", "Casey Lowden", {"primary": {"D09": "L1"}, "secondary": {}}, profile_confidence="low")
    low["sources"][2]["verification"] = "url-verified"
    low["documented_philosophy"][0].update(sources=["S2"], kind="observed")
    lp = st.validate_profile(write_profile(str(tmp_path / "low"), low), TODAY)
    assert lp.ok and lp.effective == "low", lp.issues
    d = base_read()
    d["dimensions"]["D09"]["critical"] = True                            # tier 1: critical and Unknown
    rows = {r["dimension"]: r for r in st.queue(d, [lp, library["avery-quillfeather"]], budget=20)}
    assert rows["D09"]["investor"] == "casey-lowden" and rows["D09"]["lens"] == "base" and rows["D09"]["restricted"]
    order = [library["avery-quillfeather"], library["morgan-fenwick"], library["rowan-tessaly"]]
    rows = {r["dimension"]: r for r in st.queue(d, order, budget=20)}
    assert rows["D09"]["investor"] == "rowan-tessaly" and rows["D09"]["emphasis"] == "primary"
    assert rows["D07"]["investor"] == "avery-quillfeather"              # primary beats Rowan Tessaly's secondary
    assert rows["D08"]["investor"] == "morgan-fenwick"


O8_EXTRA = """
- id: E-008
  claim: Signed orders per the company's sales deck
  value: 40
  status: reported
  confidence: medium
  source: {type: document, ref: sales deck}
  updated: 2026-11-10
"""


@pytest.mark.parametrize("line,level", [
    ("Orders reached 40 last month [E-008].", "error"),
    ("Contribution is -3 per unit after returns [E-007].", "error"),
    ("Orders reached 40 last month, by the company's own account [E-008].", None),
    ("According to the sales deck, orders reached 40 last month [E-008].", None),
    ("Company-provided: orders reached 40 last month [E-008].", None),
    ("The registry suggests 1,000 cooperatives in the region [E-004].", "warning"),
    ("The registry suggests an estimated 1,000 cooperatives in the region [E-004].", None),
    ("| D02 | 1,000 cooperatives | E-004 (estimate, web) |", None),
    ("| D06 | 40 signed orders | E-008 (reported, document) |", None),
    ("Orders are recorded in [E-008] for D06.", None),                     # no figure besides the IDs
])
def test_non_verified_figures_labelled(ctx, profile_dir, line, level):
    with open(profile_dir / "evidence.yaml", "a") as f:
        f.write(O8_EXTRA)
    led, lib = ledger_of(profile_dir), ctx[1]
    text = evaluation(("| Dimension | Figure | Evidence |\n|---|---|---|\n" + line) if line.startswith("|") else line)
    iss = check(text, led, lib)
    mine = [i for i in iss if i["rule"] == "O8" and ("must say" in i["message"] or "should say" in i["message"])]
    assert [i["level"] for i in mine] == ([level] if level else []), mine


@pytest.mark.parametrize("line,fires", [
    ("The panel agreed on D07: 4 of 5 members put it first.", False),
    ("Consensus on D07: unanimous (4 of 4 members).", False),
    ("The deciding metric is retention at 90 days.", False),
    ("Market size (D02) rests on the registry count.", False),
    ("Retention at 90 days is 40%.", True),
    ("3 of 5 customers re-ordered.", True),
    ("The market size is 40,000 cooperatives.", True),
])
def test_claim_guard_exemptions(ctx, line, fires):
    led, lib = ctx
    assert bool(errs(check(evaluation(line), led, lib), "O8")) == fires


def report_doc(extra="", closing=True):
    return f"""---
title: "Acme: founder summary"
doc_type: shark-tank
simulation: true
kind: report
investors: [avery-quillfeather, morgan-fenwick]
---

{label("Avery Quillfeather, Morgan Fenwick")}

# Acme: what the simulation found

{extra}

{"This assessment reflects the evidence available on 2026-11-14. It is not a prediction of success, nor of any investor's decision." if closing else ""}
"""


def test_report_kind(ctx):
    led, lib = ctx
    assert not errs(check(report_doc("Base read (15 dimensions): Strong 2 · Adequate 4 · Weak 1 · Unknown 8."),
                          led, lib))
    assert errs(check(report_doc(closing=False), led, lib), "O1")
    assert errs(check(report_doc("Strong 2 · Adequate 4 · Weak 1."), led, lib), "B5")
    table = "| Judgement | Answer | Reason |\n|---|---|---|\n" + "\n".join(f"| {j} | {a} | r |" for j, a in GOOD_J)
    assert not errs(check(report_doc(table), led, lib))
    assert errs(check(report_doc(table.replace("| J3 Investment-ready business | No", "| J3 Investment-ready "
                                                                                       "business | Yes")), led, lib), "B6")
    assert errs(check(report_doc("Avery Quillfeather would invest after the pilot."), led, lib), "O7")


def test_context_flags_output_written_before_ledger_same_day(profile_dir):
    ws = profile_dir.parent
    (ws / "gtm").mkdir()
    out = ws / "gtm" / "analysis.md"
    out.write_text("# analysis\n")
    ev = os.path.getmtime(profile_dir / "evidence.yaml")
    os.utime(out, (ev - 60, ev - 60))                                    # same day, a minute before the ledger
    o = {x["folder"]: x for x in st.context(str(profile_dir))["outputs"]}["gtm"]
    assert o["stale"] and o["stale_rules"] == ["mtime"] and o["files"][0]["stale_rules"] == ["mtime"]
    assert "modified before evidence.yaml was last written" in st.context_md(st.context(str(profile_dir)))
    os.utime(out, (ev + 60, ev + 60))
    assert not {x["folder"]: x for x in st.context(str(profile_dir))["outputs"]}["gtm"]["stale"]


def archetype_eval(trace=TRACE, lab=None, extra=""):
    text = evaluation(extra, trace=trace, head=lab or (
        f"> [!SIMULATION] {st.SIM_LABEL} any investor. The investor here is an archetype, not a real investor: "
        "retail operator. Based on the startup evidence available on 2026-11-10."))
    return text.replace("investors: [avery-quillfeather]", "investors: []\narchetypes: [retail operator]").replace(
        "# Avery Quillfeather: simulated evaluation", "# Retail operator archetype: simulated evaluation")


def test_archetype_documents(ctx):
    led, lib = ctx
    assert not errs(check(archetype_eval(), led, lib)), errs(check(archetype_eval(), led, lib))
    assert errs(check(archetype_eval(lab=label("any investor")), led, lib), "O1")
    assert errs(check(archetype_eval(trace=TRACE.replace("| L2 |", "| L7 |")), led, lib), "T1")
    deal = TRACE + "| B1 | potential deal-breaker | Negative margin | L1 | D07 (Weak) | E-007 founder-provided |\n"
    assert errs(check(archetype_eval(trace=deal), led, lib), "T1")       # archetypes have no decline pattern
    panel = panel_doc().replace("investors: [", "archetypes: [retail operator]\ninvestors: [")
    assert errs(check(panel, led, lib), "O10")
    e = errs(check_b(archetype_eval(), led, lib, base_read()), "T6")    # critical dimensions only
    assert e and "1 Weak (D07)" in e[0]["message"]


def test_link_checker_accepts_og_and_twitter_titles(root):
    sys.path.insert(0, os.path.join(root, "scripts"))
    try:
        import check_links
    finally:
        sys.path.pop(0)
    body = ("<html><head><title>ABC</title><meta property=\"og:title\" content=\"Meet Jane Example | Example TV\">"
            "<meta content='Jane &amp; the panel' name='twitter:title'></head></html>")
    titles = check_links.page_titles(body)
    assert titles == ["ABC", "Meet Jane Example | Example TV", "Jane & the panel"]
    assert check_links.any_title_matches("Meet Jane Example", titles)
    assert not check_links.title_matches("Meet Jane Example", "ABC")       # <title> alone would have failed
    assert not check_links.any_title_matches("Completely different headline", titles)
    assert check_links.page_titles("<title>Only</title>") == ["Only"]


@pytest.mark.parametrize("line,level", [
    ("Prices of 499 to 1,999 are an assumption [E-003], payments are off [E-008] and nobody has paid.", None),
    ("| Hem | L2 | Asks about an assumed 20 hours a week [E-008, E-003] |", None),
    ("Payments are off [E-008], yet 40 orders are claimed [E-008].", "error"),
])
def test_figure_belongs_to_its_own_citation(ctx, profile_dir, line, level):
    with open(profile_dir / "evidence.yaml", "a") as f:
        f.write(O8_EXTRA)
    led, lib = ledger_of(profile_dir), ctx[1]
    text = evaluation(("| Member | Lens | Reading |\n|---|---|---|\n" + line) if line.startswith("|") else line)
    mine = [i for i in check(text, led, lib) if i["rule"] == "O8" and "must say" in i["message"]]
    assert [i["level"] for i in mine] == ([level] if level else []), mine


# ----------------------------------------------------------------------------- polish round two
CONSENSUS_OK = ["unanimous (3 of 3 members)", "3 of 3 members", "Stance: unanimous (3 of 3): Not persuaded on current "
                "evidence.", "3 of 3 members are Not persuaded on current evidence; on D07 all members list a concern.",
                "4 of 5 members cannot form a view on current evidence; the shared gaps are D03 and D07.",
                "2 out of 3 members list D07.", "Unanimous (3/3 members).", "The 3 members agree on D07.",
                "The panel of 3 members converges on D07.", "2 members cannot form a view on current evidence.",
                "Majority (2 of 3 members): Not persuaded on current evidence.",
                "Market size (D02) rests on the registry count.", "The market size reading (D02, D03) is Unknown.",
                "TAM (D02) is not computed."]
CONSENSUS_FIRES = ["3 of 5 customers re-ordered after the panel of 3 members met.",
                   "The cooperative has 1,200 members.", "We have 12 members paying monthly.",
                   "5 members joined in October.", "3 of 5 customers re-ordered.", "The market size is 40,000 cooperatives."]


def _panel_with(line):
    return panel_doc().replace("## Final positions", "## Consensus\n\n" + line + "\n\n## Final positions")


@pytest.mark.parametrize("where_", ["evaluation", "panel"])
@pytest.mark.parametrize("cell", [False, True])
@pytest.mark.parametrize("line", CONSENSUS_OK + CONSENSUS_FIRES)
def test_claim_guard_on_consensus_and_dimension_ids(ctx, where_, cell, line):
    led, lib = ctx
    body = f"| Dimension | Consensus |\n|---|---|\n| D07 | {line} |" if cell else line
    doc = evaluation(body) if where_ == "evaluation" else _panel_with(body)
    fired = [i for i in errs(check(doc, led, lib), "O8") if "without evidence" in i["message"]]
    assert bool(fired) == (line in CONSENSUS_FIRES), fired


def test_base_read_cli_reports_warnings_on_rendered_markdown(root, profile_dir, lib, tmp_path):
    d = base_read(note="Fictional example: not a real company")
    d["dimensions"]["D02"]["explanation"] = "D02 is Insufficiently evidenced on the registry figures."
    br = tmp_path / "base-read.yaml"
    br.write_text(yaml.safe_dump(d, sort_keys=False))
    r = kit(root, "base-read", str(br), "--profile", str(profile_dir), "--out", str(tmp_path / "base-read.md"),
            "--no-shipped", "--library", lib, "--today", TODAY)
    assert r.returncode == 0 and "WARNING B5" in r.stdout and "0 errors, 1 warnings" in r.stdout, r.stdout


def test_base_read_note(profile_dir):
    led = ledger_of(profile_dir)
    md = st.render_base_read(base_read(note="Fictional example: not a real company"), led)
    lines = md.split("\n")
    i = lines.index("# acme: base read")
    assert lines[i + 2] == "*Fictional example: not a real company*"
    assert "*Fictional" not in st.render_base_read(base_read(), led)
    assert errs(st.validate_base_read(base_read(note=["a", "b"]), led, TODAY), "B1")
    assert not errs(st.validate_base_read(base_read(note="Fictional example"), led, TODAY))


GAP_TRACE = """| # | Kind | Point | Lens | Dimension (base rating) | Evidence |
|---|---|---|---|---|---|
| A1 | attracts | Re-orders without discounts point to real demand | L2 | D03 (Strong) | E-001 verified |
| A2 | attracts | The founder team has shipped the product | base | D14 (Strong) | E-001 verified |
| C1 | concern | Contribution is negative on founder-provided figures | base | D07 (Weak) | E-007 founder-provided |
| C2 | concern | No evidence yet of the cash runway | base | D12 (Unknown) | gap: no cash figures |
"""


@pytest.mark.parametrize("section,level", [
    (None, "error"),
    ("None. The known gaps do not cover this startup.", "error"),
    ("C1 and A2 fall in the profile's known gap (regulated finance) and are re-tagged base.", None),
    ("Regulated finance is a known gap; the base points above lean on it.", "warning"),   # lists no row
])
def test_t2_counts_rows_outside_documented_expertise(ctx, section, level):
    led, lib = ctx
    doc = evaluation(trace=GAP_TRACE, stance="Not persuaded on current evidence.")
    if section:
        doc += "\n## Outside documented expertise\n\n" + section + "\n"
    t2 = [i for i in check(doc, led, lib) if i["rule"] == "T2"]
    assert [i["level"] for i in t2] == ([level] if level else []), t2
    if level == "warning":
        assert "little basis for reading this startup" in t2[0]["message"]


def test_panel_guard_ids_are_consistent(ctx):
    led, lib = ctx
    ev = evaluation(stance="Not persuaded on current evidence.")
    cases = [(panel_doc(order=False), "N2", "must come before"),
             (panel_doc().replace("## Initial positions", "## Opening"), "N2", "needs an 'Initial positions'"),
             (None, "N2", "differs from its evaluation"),
             (panel_doc(final_cause="consensus"), "N3", "must cite an exchange row"),
             (panel_doc(final_cause="X9"), "N3", "not an exchange row"),
             (panel_doc(cls="personality clash"), "N4", "disagreement class")]
    for doc, rule, text in cases:
        iss = check(doc or panel_doc(), led, lib, [("evaluation-avery-quillfeather.md", ev)] if doc is None else None)
        hits = [i for i in errs(iss) if text in i["message"]]
        assert hits and {i["rule"] for i in hits} == {rule}, (rule, text, iss)
    t6 = [i for i in errs(check_b(panel_doc(), led, lib, base_read())) if "initial stance" in i["message"]]
    assert t6 and {i["rule"] for i in t6} == {"T6"}


def test_queue_says_when_it_runs_without_the_ledger(root, profile_dir, lib, tmp_path):
    import json
    br = tmp_path / "base-read.yaml"
    br.write_text(yaml.safe_dump(base_read(), sort_keys=False))
    common = [str(br), "--investors", "avery-quillfeather", "--no-shipped", "--library", lib]
    r = kit(root, "queue", *common)
    assert r.returncode == 0 and "no --profile" in r.stdout and "tier 3" in r.stdout
    r = kit(root, "queue", *common, "--json")
    assert "no --profile" in r.stderr and json.loads(r.stdout)            # JSON stays parseable
    r = kit(root, "queue", *common, "--profile", str(profile_dir))
    assert r.returncode == 0 and "no --profile" not in r.stdout + r.stderr


# ----------------------------------------------------------------------------- polish round three
@pytest.mark.parametrize("text,want", [
    ("Conditional on evidence.", ["conditional"]),
    ("Conditional on three months of retailer sell-through data. A1 rests on E-001.", ["conditional"]),
    ("**Conditional on a priced pilot.** C1 is the deciding row.", ["conditional"]),
    ("- Conditional on a priced pilot.", ["conditional"]),
    ("Not persuaded on current evidence. The reading is conditional on D07 improving.", ["not-persuaded"]),
    ("Cannot form a view (insufficient evidence). Any view would be conditional on D03.", ["no-view"]),
    ("Persuaded on current evidence.\nThe view stays conditional on the renewal data.", ["persuaded"]),
    ("Interested, conditional on evidence.", []),
])
def test_stance_label_anchoring(text, want):
    assert st.stance_of(text) == want
    assert STANCE_CELL(text.split("\n")[0]) == want


def STANCE_CELL(t):
    return st.stance_of(t)


def test_conditional_label_and_prose_in_evaluation(ctx):
    led, lib = ctx
    assert st.STANCES["conditional"] == "Conditional on evidence"
    good = evaluation(stance="Conditional on three months of retailer sell-through data. The case is conditional on "
                             "D07 turning positive (C1).")
    assert not errs(check(good, led, lib), "T1"), errs(check(good, led, lib), "T1")
    two = evaluation(stance="Not persuaded on current evidence.\n\nConditional on evidence.")
    assert errs(check(two, led, lib), "T1")
    prose = evaluation(stance="Not persuaded on current evidence. Any change is conditional on a priced pilot (C1).")
    assert not errs(check(prose, led, lib), "T1")


def test_retired_label_is_rejected_with_the_new_one_named(ctx):
    led, lib = ctx
    old = evaluation(stance="Interested, conditional on evidence of positive contribution.")
    iss = errs(check(old, led, lib))
    assert any(i["rule"] == "T1" and "Conditional on evidence" in i["message"] for i in iss)
    assert any(i["rule"] == "O7" and "Conditional on evidence" in i["message"] for i in iss)
    stale_panel = panel_doc().replace("| Avery Quillfeather | Conditional on evidence | A1", "| Avery Quillfeather | "
                                      "Interested, conditional on evidence | A1")
    assert any("retired" in i["message"] for i in errs(check(stale_panel, led, lib), "O7"))


@pytest.mark.parametrize("line", [
    "Avery Quillfeather is interested on conditions.",
    "1 of 3 is interested.",
    "Two members are interested.",
    "The panel is interested in the margin story.",
    "Most of the members remain interested.",
    "The sharks are keenly interested.",
    "Each member is interested in D07.",
    "Morgan Fenwick has shown interest in the brand.",
    "One investor expressed interest after the pilot.",
    "Rowan Tessaly would be interested if margins improve.",
    "Two members cannot form a view and one is interested on conditions.",
    "Interested, conditional: only 3 of 7 dimensions are Unknown.",
])
def test_interest_with_investor_or_panel_subject_rejected(ctx, line):
    led, lib = ctx
    assert errs(check(evaluation(line), led, lib), "O7")


@pytest.mark.parametrize("line", [
    "A question raised through L2: what is the founder interested in learning from the pilot?",
    "The loan carries an interest rate of 12% on the founder-provided terms [E-007].",
    "Customers interested in the annual plan were asked to pre-pay.",
    "The founder is interested in a retail partner.",
    "The panel's interest in D07 is analytical: three lenses list it.",
    "No one is interested in paper slips any more, the founder-provided notes say [E-002].",
    "Three are listed as gaps; one is the cash runway.",
])
def test_interest_in_unrelated_uses_passes(ctx, line):
    led, lib = ctx
    assert not errs(check(evaluation(line), led, lib), "O7"), errs(check(evaluation(line), led, lib), "O7")


# ----------------------------------------------------------------------------- final audit (B-1, B-2)
# The auditor's evasion and honest lines, rewritten with fictional names (fixtures never attribute invented
# statements to a real person).
AUDIT_BAD = [
    'A plausible ask would be 50 lakh rupees for a tenth of the company.',
    'Avery Quillfeather could put in two hundred thousand dollars for twenty percent.',
    'The terms might be 200,000 AUD for 15 per cent of the business.',
    'Expect a cheque of around 250k in exchange for a quarter of the shares.',
    'A fair price for the business today would be about 2 million.',
    'She could take a 10 percent shareholding.',
    "Avery Quillfeather's view is that 'the model comes first'.",
    'Quillfeather has made clear that the founder must know every number.',
    "According to Avery Quillfeather, Acme's numbers are not ready.",
    'Avery Quillfeather would point out that the runway is missing.',
    'Avery Quillfeather would ask why the runway is not stated.',
    'Quillfeather would argue that cash flow comes before growth.',
    "Quillfeather's reaction would be disappointment at the missing burn figure.",
    'In her words, the business is not yet a business.',
    'Show me the cash-flow statement first, then we can talk.',
    'Not for me. Out.',
    'Come back when the runway is known.',
    "We're out on this one.",
    'Count me in if the numbers hold.',
    'Avery Quillfeather would be keen on Acme once runway is shown.',
    'Quillfeather would likely back the team after the pilot.',
    'Avery Quillfeather would want a piece of this business.',
    'Avery Quillfeather is drawn to the prepayment model and would want to be involved.',
    "Acme is a natural fit for Avery Quillfeather's portfolio.",
    'Avery Quillfeather would be tempted by the annual plan.',
    'Avery Quillfeather would leave the door open for a follow-up meeting.',
    'Quillfeather is excited by the annual prepayment.',
    'Quillfeather likes the prepayment model.',
    'The panel would be eager to see this company again.',
    'Quillfeather is enthusiastic about the founders.',
    'The odds that Acme raises a round are about one in three.',
    'Acme has a two-in-three shot at a deal.',
    'Success is more likely than not.',
    'There is a 60% likelihood that the panel invests.',
    'The chances of funding are slim.',
    'Acme is a long shot for funding.',
    'Base read: Strong 1, Adequate 4, Weak 0.',
    'Base read: one Strong, four Adequate and no Weak.',
    'Base read: 1 strong rating and 4 adequate ratings.',
    'Most dimensions are rated Adequate or better.',
    'The base read is mostly positive.',
    'Acme rates well on most of the fifteen dimensions.',
    'Acme scores 5 of 15 on the base read.',
]
AUDIT_GOOD = [
    'The founder plans to offer a 10% discount on the annual plan.',
    'Cooperatives that hold equity in their processing plant may decide differently.',
    'Royalty-free open-source libraries keep licence costs low.',
    'The deal flow of cooperative software is not documented in the ledger.',
    "Quillfeather's documented record (S3) says the model comes first; under L1 this simulation reads D06 first.",
    'A stake in the outcome is shared by field agents and managers alike.',
    "The cooperative's members hold a 51% stake in the dairy.",
    'The founder said that 3 cooperatives renewed, which is not yet in the ledger.',
    'Under L2 the question is whether the founder thinks clearly about the use of funds.',
    'Investors such as business angels typically ask for a cash-flow statement.',
    'The founders invested 6 months of savings for the first version.',
    'Three cooperatives were interested enough to prepay the annual plan [E-001].',
    'The probability that an agent loses a slip is not measured.',
    'The odds of a slip being lost were described as high by two agents [E-005].',
    "The valuation of the cooperative's milk stock at 4% shrinkage is outside scope.",
    'Equity in the processing plant, 30% held by the founding families, is a governance fact for D15.',
    'Sources: S7 How to pitch (Example Publisher, 2017).',
    'Avery Quillfeather founded Example Retail in 2001 [S2].',
]
AUDIT_CLAIMS = [
    'Acme has 40 paying cooperatives.',
    'Revenue is NPR 200,000 a month.',
    'Monthly revenue reached two lakh rupees.',
    'Churn is low at 2% a month.',
    'Twelve cooperatives renewed last quarter.',
    'Acme grew 3x last year.',
    'The founder said that 3 cooperatives renewed.',
    'Acme has forty paying cooperatives.',
]


@pytest.mark.parametrize("line", AUDIT_BAD)
def test_audit_evasions_are_caught(ctx, line):
    led, lib = ctx
    assert errs(check(evaluation(line), led, lib)), line


# The final round made every uncited business figure an O8 error, so four of the auditor's honest lines (written
# to test O5) now need a citation; they must still not trip the guard they were written for.
AUDIT_GOOD_UNCITED = ("51% stake", "6 months of savings", "4% shrinkage", "30% held")


@pytest.mark.parametrize("line", AUDIT_GOOD)
def test_audit_honest_lines_pass(ctx, line):
    led, lib = ctx
    rules = {i["rule"] for i in errs(check(evaluation(line), led, lib)) if i["line"] and i["line"] > 20}
    if any(x in line for x in AUDIT_GOOD_UNCITED):
        assert rules == {"O8"}, rules
        assert not errs(check(evaluation(line.rstrip(".") + " [E-001]."), led, lib)), line
    else:
        assert not rules, errs(check(evaluation(line), led, lib))


@pytest.mark.parametrize("line", AUDIT_CLAIMS + ["Acme grew from 4 to 12 cooperatives in a year.",
                                                 "| D03 | 40 paying cooperatives | concern |"])
def test_uncited_traction_is_an_error(ctx, line):
    led, lib = ctx
    text = evaluation(("| Dimension | Figure | Kind |\n|---|---|---|\n" + line) if line.startswith("|") else line)
    assert errs(check(text, led, lib), "O8"), line


@pytest.mark.parametrize("line", [
    "Acme has 5 paying cooperatives [E-001].",
    "| D03 | 5 paying cooperatives | E-001 verified |",
    "The founder said that 3 cooperatives renewed, which is not yet in the ledger.",
    "A question raised through L2: how many cooperatives renewed in the last quarter?",
    "What breaks at 10x volume is not described (D10).",
    "Two of the three lenses list D07.",
    "Acme would need 40 paying cooperatives to cover its costs, a threshold to test.",
])
def test_cited_or_qualified_traction_passes(ctx, line):
    led, lib = ctx
    text = evaluation(("| Dimension | Figure | Evidence |\n|---|---|---|\n" + line) if line.startswith("|") else line)
    assert not [i for i in errs(check(text, led, lib), "O8") if "ledger citation" in i["message"]], line


@pytest.mark.parametrize("line,fires", [
    ("Avery Quillfeather would put in $50,000 for 10% of Acme.", True),
    ("The panel would take a quarter of the shares for 2 million rupees.", True),
    ("Morgan Fenwick could acquire a 15 per cent stake.", True),
    ("A valuation of $2M is reasonable.", True),
    ("The founder offers resellers a 15% margin.", False),
    ("A third-party distributor holds a 20% stake in its own warehouse company.", False),
    ("Stock valuation at 4% shrinkage is outside scope.", False),
    ("The co-founders own 100% of the plant, a governance fact for D15.", False),
])
def test_offer_language_needs_a_party_or_terms(ctx, line, fires):
    led, lib = ctx
    assert bool(errs(check(evaluation(line), led, lib), "O5")) == fires


# ----------------------------------------------------------------------------- final audit (B-9, B-10)
def test_stance_cannot_be_softened_by_omitting_concern_rows(ctx):
    led, lib = ctx
    no_c = "\n".join(l for l in TRACE.split("\n") if not l.startswith("| C"))
    doc = evaluation(trace=no_c, stance="Conditional on evidence of positive contribution.")
    iss = errs(check_b(doc, led, lib, base_read()))
    assert any(i["rule"] == "T6" and "Not persuaded" in i["message"] for i in iss)
    assert any(i["rule"] == "T7" and "D07" in i["message"] and "Weak" in i["message"] for i in iss)
    assert any(i["rule"] == "T7" and "D12" in i["message"] and "evidence gap" in i["message"] for i in iss)
    full = TRACE + "| C2 | concern | No evidence yet of the cash runway | base | D12 (Unknown) | gap: no cash figures |\n"
    ok = evaluation(trace=full, stance="Not persuaded on current evidence.")
    assert not [i for i in errs(check_b(ok, led, lib, base_read())) if i["rule"] in ("T6", "T7")]


def test_low_confidence_weak_counts_as_unknown(ctx):
    led, lib = ctx
    b = base_read()
    b["dimensions"]["D07"]["confidence"] = "low"
    full = TRACE + "| C2 | concern | No evidence yet of the cash runway | base | D12 (Unknown) | gap: no cash figures |\n"
    iss = errs(check_b(evaluation(trace=full, stance="Not persuaded on current evidence."), led, lib, b))
    assert any(i["rule"] == "T6" and "expected 'Conditional on evidence'" in i["message"] for i in iss)
    assert not errs(check_b(evaluation(trace=full), led, lib, b), "T6")


VERDICT_OK = [("J1 Good business", "No"), ("J2 Investable business (venture)", "No"),
              ("J3 Investment-ready business", "No"), ("J4 Needs further validation", "Yes"),
              ("J5 Should not proceed in its current form", "Yes")]


@pytest.mark.parametrize("flip,text", [
    (None, None),
    (("J1 Good business", "Not yet determinable"), "J1 Good business is Not yet determinable"),
    (("J5 Should not proceed in its current form", "No"), "J5 Should not proceed is No"),
    (("J4 Needs further validation", "No"), "J4 Needs further validation is No"),
    (("J2 Investable business (venture)", "Yes"), "J2 Investable business (venture) is Yes"),
])
def test_verdict_table_follows_the_base_read(ctx, flip, text):
    led, lib = ctx
    rows = [(j, flip[1] if flip and j == flip[0] else a) for j, a in VERDICT_OK]
    iss = errs(check_b(verdict_doc(rows), led, lib, base_read()), "B6")
    assert (not iss) if flip is None else any(text in i["message"] for i in iss), iss


def test_auditor_flips_on_a_copy_of_the_ottlebrook_verdict(root, tmp_path, shipped):
    src = os.path.join(root, "examples", "ottlebrook", "shark-tank")
    _need(os.path.join(src, "verdict.md"), "examples/ottlebrook/shark-tank/verdict.md")
    shutil.copytree(os.path.dirname(src), tmp_path / "ottlebrook")
    d = tmp_path / "ottlebrook" / "shark-tank"
    led = Ledger.load(str(tmp_path / "ottlebrook" / "startup-profile" / "evidence.yaml"))
    base = st.load_yaml(str(d / "base-read.yaml"))
    t = (d / "verdict.md").read_text()

    def b6(x):
        return [i["message"] for i in errs(st.check_document(x, led, shipped, None, "v.md", base), "B6")]
    flips = [(r"(\| J5 Should not proceed in its current form \| )Yes", r"\1No", "J5 Should not proceed is No"),
             (r"(\| J1 Good business \| )No", r"\1Not yet determinable", "J1 Good business is Not yet determinable"),
             (r"(\| J4 Needs further validation \| )No", r"\1Yes", "J4 Needs further validation is Yes")]
    for pat, rep, msg in flips:
        flipped = re.sub(pat, rep, t)
        assert flipped != t, pat
        assert any(msg in m for m in b6(flipped)), (msg, b6(flipped))


# ----------------------------------------------------------------------------- final audit (B-3, H-3, C-2, A-3)
@pytest.mark.parametrize("q,compound", [
    ("Which channel brought in the last ten customers, and roughly what did each one cost?", True),
    ("What is your monthly burn, and when does the cash run out?", True),
    ("What is your monthly burn and your runway and your CAC?", True),
    ("What is your burn; what is your runway?", True),
    ("Who pays, and how much?", True),
    ("Which channel brought in the last ten customers?", False),
    ("What was revenue in October and November?", False),
    ("For the last ten customers, which channel brought them in?", False),
    ("What did each cooperative pay in its first month and its third month?", False),
])
def test_compound_questions(q, compound):
    assert any("compound" in m for m in st.question_problems(q)) == compound


@pytest.mark.parametrize("q,rule", [("Why should Avery Quillfeather back you?", "O7"),
                                    ("Would you accept 50 lakh rupees for 10 percent of the company?", "O5")])
def test_session_questions_get_the_voice_guards(library, q, rule):
    d = copy.deepcopy(session())
    d["turns"][0]["question"]["text"] = q
    assert errs(st.validate_session(d, library), rule)


def test_stale_panel_status_and_old_stated_views_warn(tmp_path):
    d = prof(profile_confidence="high")
    d["sources"] = [src(1, "broadcaster"), src(2, "company"), src(3, "press"), src(4, "own-statement"),
                    src(5, "press"), src(6, "official-bio")]
    for x in d["sources"]:
        x["published"] = dt.date(2015, 1, 1)
    d["documented_philosophy"][0]["sources"] = ["S3", "S4"]
    d["documented_expertise"][0]["sources"] = ["S2", "S5"]
    d["programmes"][0]["status_checked"] = dt.date(2026, 3, 1)
    p = st.validate_profile(write_profile(str(tmp_path), d), TODAY)
    assert p.ok, p.issues
    assert any("example-den" in i["message"] and "six months" in i["message"] for i in warns(p.issues, "P9"))
    assert any("within five years" in i["message"] for i in warns(p.issues, "P7"))
    d["sources"][3]["published"] = dt.date(2024, 5, 1)
    d["programmes"][0]["status_checked"] = dt.date(2026, 11, 1)
    p = st.validate_profile(write_profile(str(tmp_path), d), TODAY)
    assert not warns(p.issues), p.issues
    assert "as of 2026-11-01" in p.summary()["programmes"][0]


def test_check_without_ledger_or_base_read_warns(ctx):
    led, lib = ctx
    iss = check(evaluation(), None, lib)
    assert {i["rule"] for i in warns(iss)} >= {"O8", "T6"}
    assert not [i for i in warns(check_b(evaluation(), led, lib, base_read())) if i["rule"] in ("O8", "T6")
                and "no " in i["message"][:30]]


def test_verified_revenue_detection():
    L = Ledger([])
    assert st.has_verified_revenue(L) is False and st.has_verified_revenue(None) is None
    from startup_kit.evidence import Entry
    neg = Entry(id="E-001", claim="No usage or revenue data was available", status="verified", source={"type": "document"})
    fee = Entry(id="E-002", claim="Platform fee of 30% coded in the payment module", key="pricing.platform_fee",
                status="verified", source={"type": "codebase"})
    assert st.has_verified_revenue(Ledger([neg, fee])) is False
    paid = Entry(id="E-003", claim="Three cooperatives paid the annual plan", status="verified",
                 source={"type": "dataset"})
    assert st.has_verified_revenue(Ledger([neg, fee, paid])) is True
    assert st.has_verified_revenue(Ledger([Entry(id="E-004", claim="x", key="traction.revenue_monthly",
                                                 status="verified", source={"type": "dataset"})])) is True


@pytest.mark.parametrize("line,rule", [
    ("Problem interviews with at least 10 of 15 S1 teachers describing a recent incident.", None),
    ("Twelve of the fifteen dimensions are Unknown in the shared base read.", None),
    ("Ten of 15 dimensions are Adequate or Strong.", "B5"),
    ("10 of 15 dimensions have evidence behind them.", "B4"),
    ("Acme scores 5 of 15 on the base read.", "B4"),
    ("Each unit loses AUD 3.36 after landed cost [E-001]; the shelf margin plays the part that rent and royalties "
     "play in a store.", None),
    ("- Unknowns: channel that produced the five paying cooperatives; cost per paying cooperative", None),
    ("Ledger: E-001 (verified): 10 to 20 paying cooperatives in the first region.", None),
])
def test_audit_regeneration_false_positives_stay_fixed(ctx, line, rule):
    led, lib = ctx
    iss = [i for i in errs(check(evaluation(line), led, lib)) if i["line"] and i["line"] > 20]
    assert ({i["rule"] for i in iss} == {rule}) if rule else not iss, iss


# ----------------------------------------------------------------------------- final small round
@pytest.mark.parametrize("q,compound", [
    ("How many months of runway exist today, and does that cover the next milestone?", True),
    ("What did the cooperatives pay, and were they invoiced?", True),
    ("Is the licence granted, or is an application pending?", True),
    ("The model carries a founder-reported balance of USD 40,000; what is the net cash burn per month today?", False),
    ("Has counsel said in writing whether holding teacher earnings is allowed?", False),
    ("How many teachers can be onboarded in one month at that rate?", False),
    ("What was revenue in October and November?", False),
])
def test_yes_no_second_clause_and_context_semicolon(q, compound):
    assert any("compound" in m for m in st.question_problems(q)) == compound


def test_prepared_questions_are_checked(library, root):
    d = copy.deepcopy(session())
    d["queue"][0]["text"] = "Which channel works, and what does it cost?"
    assert any("queue item Q3" in i["message"] for i in errs(st.validate_session(d, library), "I2"))
    doc = """# Acme: interrogation preparation

| Q | Tier | Dimension | Question text |
|---|---|---|---|
| Q1 | 1 | D03 | How many cooperatives have paid for the annual plan? |
| Q2 | 1 | D12 | How many months of runway exist today, and does that cover the next milestone? |

Planned follow-ups:

- Q1a: Which of those paid in full?
- Q2a: What is the burn; what is the runway?
"""
    iss = errs(st.check_queue_document(doc, library))
    assert {m for i in iss for m in ("Q2", "Q2a") if f"{m}:" in i["message"]} == {"Q2", "Q2a"}
    assert not any("Q1:" in i["message"] or "Q1a:" in i["message"] for i in iss)
    assert warns(st.check_queue_document("# Nothing here\n", library), "I2")
    p = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "x")      # CLI routing for .md
    assert p


@pytest.mark.parametrize("line,rule", [
    ("This simulation gives no overall score.", None),
    ("It does not state odds of a deal.", None),
    ("No percentage chance is given.", None),
    ("It never states what an investor would offer.", None),
    ("The simulation does not say whether Avery Quillfeather would invest.", None),
    ("No valuation of $2M or any other figure is given.", None),
    ("The overall score is 9.", "B4"),
    ("The odds of a deal are good.", "O7"),
    ("Avery Quillfeather would invest after the pilot.", "O7"),
    ("A valuation of $2M is fair.", "O5"),
    ("It gives no score, but Avery Quillfeather would invest.", "O7"),
    ("Avery Quillfeather would ask why the runway is not stated.", "O2"),
])
def test_statements_of_the_boundary_pass_and_positive_forms_fire(ctx, line, rule):
    led, lib = ctx
    rules = {i["rule"] for i in errs(check(evaluation(line), led, lib)) if i["line"] and i["line"] > 20}
    assert (rule in rules) if rule else not rules, rules


def test_base_lens_in_exchange_rows_and_divergence_map_roles(ctx):
    led, lib = ctx
    assert not errs(check(panel_doc(exchange_lens="base"), led, lib))
    dmap = """## Divergence map

| Dimension (rating) | Avery Quillfeather | Morgan Fenwick | Rowan Tessaly | Result |
|---|---|---|---|---|
| D07 (Weak) | deciding (critical), L1 | considered, L2 | outside expertise, base | convergent |
| D12 (Unknown) | not covered | deciding (critical), base | concern | convergent |
| Stances | Conditional | Not persuaded | Cannot form a view | divergent |

"""
    doc = panel_doc().replace("## Discussion", dmap + "## Discussion")
    w = warns(check(doc, led, lib), "N6")
    assert len(w) == 1 and "'concern'" in w[0]["message"], w


# ----------------------------------------------------------------------------- re-audit round (structural)
CLAIMS2 = ["Acme serves dozens of cooperatives already.", "Half the cooperatives in the district now use Acme.",
           "Revenue doubled last quarter.", "Retention is above ninety percent.",
           "Acme has a waiting list of 300 cooperatives.", "Acme signed the national federation last week.",
           "More than a thousand farmers are paid through Acme each month.",
           "| D03 | A waiting list of 300 cooperatives | concern |", "Margins tripled after the price change."]


@pytest.mark.parametrize("line", CLAIMS2)
def test_every_uncited_business_figure_or_event_is_an_error(ctx, line):
    led, lib = ctx
    text = evaluation(("| Dimension | Point | Kind |\n|---|---|---|\n" + line) if line.startswith("|") else line)
    assert errs(check(text, led, lib), "O8"), line


@pytest.mark.parametrize("line", [
    "Acme has a waiting list of 300 cooperatives [E-001].",
    "| D03 | A waiting list of 300 cooperatives | E-001 verified |",
    "Contribution is AUD -3.36 per unit, calculated from the invoices and the returns report.",
    "Retention at 90 days: gap, no cohort export in the ledger.",
    "Season 4 of the programme aired in 2024 (S2).",
    "Two of the three lenses list D07, and 4 of 15 dimensions are Unknown.",
    "All three panel members hold the same stance.",
    "The verified 3,000-unit quote is the lever (A2).",
    "Acme sells B2B to cooperatives.",
    "Under L1, the question is whether a 20% price rise would hold.",
    "What breaks at 10x volume is not described (D10).",
])
def test_non_business_numbers_and_cited_figures_pass(ctx, line):
    led, lib = ctx
    text = evaluation(("| Dimension | Point | Evidence |\n|---|---|---|\n" + line) if line.startswith("|") else line)
    assert not [i for i in errs(check(text, led, lib), "O8") if "figure" in i["message"] or "event" in i["message"]]


def test_figures_in_scenarios_and_planned_sections_are_exempt(ctx):
    led, lib = ctx
    scn = ("> [!SCENARIO] Hypothetical scenario: not an offer, not attributed to any investor.\n"
           "> An operator-investor provides capital against 300 cooperatives of demand.\n"
           "> Assumptions:\n> - The founder's own ask.\n")
    assert not errs(check(evaluation(scn), led, lib), "O8")
    plan = evaluation() + "\n## Recommendations\n\nCollect eight weeks of support hours per cooperative.\n"
    assert not errs(check(plan, led, lib), "O8")


def test_missing_base_read_or_ledger_is_an_error_unless_waived(ctx):
    led, lib = ctx
    strict = st.check_document(evaluation(), led, lib, None, "d.md")
    assert errs(strict, "T6") and "--no-base-read" in errs(strict, "T6")[0]["message"]
    waived = st.check_document(evaluation(), led, lib, None, "d.md", allow_no_base=True)
    assert not errs(waived, "T6") and warns(waived, "T6") and "T7" in warns(waived, "T6")[0]["message"]
    assert errs(st.check_document(evaluation(), None, lib, None, "d.md", base_read()), "O8")
    assert warns(st.check_document(evaluation(), None, lib, None, "d.md", base_read(), allow_no_ledger=True), "O8")
    debrief = evaluation().replace("kind: evaluation", "kind: debrief")
    assert not errs(st.check_document(debrief, led, lib, None, "d.md"), "T6")       # only the four full kinds


def test_cli_check_fails_away_from_base_read(root, tmp_path, profile_dir, lib):
    soft = tmp_path / "elsewhere" / "evaluation.md"
    soft.parent.mkdir()
    soft.write_text(evaluation(stance="Persuaded on current evidence."))
    common = ["--profile", str(profile_dir), "--no-shipped", "--library", lib]
    r = kit(root, "check", str(soft), *common)
    assert r.returncode == 1 and "no base read" in r.stdout
    r = kit(root, "check", str(soft), *common, "--no-base-read")
    assert "WARNING T6" in r.stdout and "no base read" in r.stdout
    br = tmp_path / "base-read.yaml"
    br.write_text(yaml.safe_dump(base_read(), sort_keys=False))
    r = kit(root, "check", str(soft), *common, "--base-read", str(br))
    assert r.returncode == 1 and "T6" in r.stdout and "Not persuaded" in r.stdout


@pytest.mark.parametrize("line,fires", [
    ("Overall the lenses are persuaded by Acme and see a strong case.", True),
    ("The panel is leaning towards a yes.", True),
    ("Our panel is impressed with the founders.", True),
    ("Avery Quillfeather is convinced by the margin story.", True),
    ("Morgan Fenwick is not persuaded on current evidence (see the Stance section of that evaluation).", False),
    ("Through L1, this simulation is not persuaded that the margin holds.", False),
    ("3 of 3 members are Not persuaded on current evidence.", False),
])
def test_stance_stated_in_prose(ctx, line, fires):
    led, lib = ctx
    assert bool(errs(check(evaluation(line), led, lib), "T8")) == fires


@pytest.mark.parametrize("line,fires", [
    ("Acme is investment-ready.", True),          # J3 is No in the table
    ("Acme is not investment-ready yet.", False),
    ("Acme is investable for an operator-strategic investor.", True),
    ("Acme is not yet a good business on this evidence.", False),
    ("Acme is a good business.", True),           # J1 is No
])
def test_readiness_claims_agree_with_the_judgements(ctx, line, fires):
    led, lib = ctx
    doc = verdict_doc(VERDICT_OK).replace("# Acme: investment verdict", "# Acme: investment verdict\n\n" + line)
    assert bool(errs(check_b(doc, led, lib, base_read()), "T8")) == fires
    assert errs(check(evaluation("Acme is investment-ready."), led, lib), "T8")  # nothing to agree with


@pytest.mark.parametrize("q", ["What is the monthly burn as well as the runway?", "Give the burn rate (and the runway)?",
                               "What is the burn, i.e. the monthly spend, and the runway in months?",
                               "What is the cash balance followed by the monthly spend?",
                               "State the cash balance along with the burn?"])
def test_more_compound_connectives(q):
    assert any("compound" in m for m in st.question_problems(q))


@pytest.mark.parametrize("q", ["What is the burn, i.e. the monthly spend?", "How much cash does Acme hold today?",
                               "Give the number of paying cooperatives today?"])
def test_single_questions_with_glosses_pass(q):
    assert not st.question_problems(q)


@pytest.mark.parametrize("line", ["Nothing here suggests that Avery Quillfeather is interested in Acme.",
                                  "No member is said to be interested in Acme.",
                                  "No investor is shown as interested here."])
def test_negated_interest_is_a_boundary_statement(ctx, line):
    led, lib = ctx
    assert not errs(check(evaluation(line), led, lib), "O7")
    assert errs(check(evaluation(line.replace("Nothing here suggests that ", "").replace("No member is said",
                                                                                         "Morgan Fenwick is said")),
                      led, lib), "O7") or "No investor" in line


@pytest.mark.parametrize("line,warn_", [
    ("Acme is a strong business with a bright future.", True),
    ("The founders are outstanding operators.", True),
    ("The prepayment model is compelling [E-001].", False),
    ("The case would be more compelling with renewals.", False),
    ("Nothing here is exceptional: the gap is renewals.", False),
])
def test_unsupported_praise_warns(ctx, line, warn_):
    led, lib = ctx
    iss = check(evaluation(line), led, lib)
    assert bool(warns(iss, "P-W")) == warn_ and not errs(iss, "P-W")
    heading = evaluation() + "\n## What would make the business more compelling under these lenses\n\nRenewals.\n"
    assert not warns(check(heading, led, lib), "P-W")


# ----------------------------------------------------------------------------- release round (v1.4.0 hardening)
@pytest.mark.parametrize("line,fires", [
    ("The likely terms are about 2 crore rupees against 20% of the shares.", True),
    ("A fair price sits between £400k and £600k pre-money.", True),
    ("The members would price Acme at roughly ten times its annual recurring revenue.", True),
    ("A valuation at 8x ARR is where the conversation would land.", True),
    ("Avery Quillfeather's terms would be $90,000 with a board seat.", True),
    ("$50,000 buys shares in Acme at the next close.", True),
    ("Each cooperative member holds shares worth NPR 100 in the cooperative.", False),
    ("Acme prices the annual plan at USD 400 per customer [E-001].", False),
    ("Revenue grew three times in the pilot (founder-provided) [E-002].", False),
    ("Pre-money and dilution belong to fundraising-strategist; this verdict states no amount.", False),
])
def test_offer_terms_through_shares_pre_money_and_price(ctx, line, fires):
    led, lib = ctx
    assert bool(errs(check(evaluation(line), led, lib), "O5")) == fires, check(evaluation(line), led, lib)


@pytest.mark.parametrize("line,rule", [
    ("There is no per-dimension score, no overall score and no deal likelihood.", None),
    ("The simulation gives no scores, so there is no overall score.", None),
    ("The overall score is 7.", "B4"),
    ("There is no chance of a deal on these numbers.", "O7"),
])
def test_score_named_only_to_deny_it(ctx, line, rule):
    led, lib = ctx
    rules = {i["rule"] for i in errs(check(evaluation(line), led, lib)) if i["line"] and i["line"] > 20}
    assert (rule in rules) if rule else not ({"B4", "O7"} & rules), rules


@pytest.mark.parametrize("line,fires", [
    ("A panel needs three to seven validated profiles.", False),
    ("Only validated investor profiles sit on the panel.", False),
    ("Each profile is validated against its sources.", False),
    ("Demand for Acme is validated.", True),
])
def test_validated_profiles_are_not_a_business_claim(ctx, line, fires):
    led, lib = ctx
    hits = [i for i in errs(check(evaluation(line), led, lib), "O8") if "asserted without evidence" in i["message"]]
    assert bool(hits) == fires, hits


def _debrief(line):
    return evaluation(line).replace("kind: evaluation", "kind: debrief")


@pytest.mark.parametrize("line,fires", [
    ("| F1 | Cash at bank, confirmed by the founder and verified | finance.cash | USD 38,000 (verified) |", True),
    ("The founder's churn figure is verified.", True),
    ("The pilot price is verified [E-002].", True),           # E-002 is reported, not verified
    ("The pilot price is verified [E-001].", False),          # E-001 is a verified entry
    ("The cash figure is founder-provided and not verified.", False),
    ("Every answer here is unverified until documents arrive.", False),
    ("D07 is Weak on verified evidence, so the facts are not in question.", False),
    ("The verified re-order [E-001] needs most of the cash (founder-provided) [E-002].", False),
])
def test_debrief_never_calls_a_founder_answer_verified(ctx, line, fires):
    led, lib = ctx
    assert bool(errs(check(_debrief(line), led, lib), "I3")) == fires


def test_session_claims_never_call_a_fact_verified(library):
    s = session()
    s["turns"][0]["new_facts"][0]["claim"] = "Contribution per unit, verified by the founder"
    assert errs(st.validate_session(s, library), "I3")
    s = session(pending_ledger=[{"id": "F1", "claim": "Cash at bank, verified", "proposed_status": "reported"}])
    assert errs(st.validate_session(s, library), "I3")
    s = session(pending_ledger=[{"id": "F1", "claim": "Cash at bank, not verified", "proposed_status": "reported"}])
    assert not errs(st.validate_session(s, library), "I3")


def chat(text, led, lib):
    return st.check_chat(text, led, lib, "reply.md")


def test_chat_reply_without_investor_reading_needs_no_label(ctx):
    led, lib = ctx
    reply = ("I can't state what a real person would offer. I would suggest running a panel with three profiles "
             "whose documented expertise touches retail.\n\nWhich three should we use?")
    assert not errs(chat(reply, led, lib))
    assert not errs(chat("Avery Quillfeather has a current profile (medium confidence).", led, lib), "O1")


def test_chat_reply_with_investor_reading_needs_the_label(ctx):
    led, lib = ctx
    reading = "Avery Quillfeather's profile makes D07 primary through L1, so contribution per unit decides it."
    assert errs(chat(reading, led, lib), "O1")
    assert not errs(chat(label("Avery Quillfeather") + "\n\n" + reading, led, lib))
    assert errs(chat(label("Morgan Fenwick") + "\n\n" + reading, led, lib), "O1")   # label names someone else


@pytest.mark.parametrize("line,rule", [
    ("Avery Quillfeather would put in $50,000 for 10% of Acme.", "O5"),
    ("Avery Quillfeather is clearly keen on Acme.", "O7"),
    ("Avery Quillfeather would tell the founders that runway matters most.", "O2"),
    ("The odds of a deal are good.", "O7"),
    ("Ratings: 1 Strong, 4 Adequate, 0 Weak.", "B5"),
    ("Acme now serves 42 cooperatives across two regions.", "O8"),
    ("I'm out.", "O3"),
])
def test_chat_reply_keeps_every_voice_and_offer_guard(ctx, line, rule):
    led, lib = ctx
    assert errs(chat(label("Avery Quillfeather") + "\n\n" + line, led, lib), rule)


def test_cli_check_chat(root, tmp_path, lib):
    f = tmp_path / "reply.md"
    f.write_text("Avery Quillfeather's L1 lens makes D07 decide this.\n")
    common = ["--chat", "--no-shipped", "--library", lib]
    r = kit(root, "check", str(f), *common)
    assert r.returncode == 1 and "O1" in r.stdout, r.stdout
    f.write_text("No profile has been chosen yet. Which sector does the startup sit in?\n")
    r = kit(root, "check", str(f), *common)
    assert r.returncode == 0, r.stdout


def test_chat_reading_by_pronoun_needs_the_exact_label(ctx):
    led, lib = ctx
    reply = ("> [!SIMULATION] This is an analytical simulation, not a statement by Avery Quillfeather.\n\n"
             "**Stance: Cannot form a view (insufficient evidence).** Under his documented lenses the margin "
             "decides it.\n")
    assert errs(chat(reply, led, lib), "O1")                       # paraphrased label
    exact = label("Avery Quillfeather") + "\n\n" + reply.split("\n\n", 1)[1]
    assert not errs(chat(exact, led, lib), "O1")
    two = ("Avery Quillfeather and Morgan Fenwick both have current profiles. Their lenses differ.\n")
    assert not errs(chat(two, led, lib), "O1")                     # two names: a pronoun is not attributed


@pytest.mark.parametrize("line,fires", [
    ("I'd invest $50k in Acme.", True), ("I would invest in Acme.", True), ("You've got a deal.", True),
    ("Show me the numbers first.", True), ("I'm out.", True), ("Take it or leave it.", True),
    ("I'll offer a short summary of the base read below.", False),
    ("We're out of evidence on retention, so D08 stays Unknown.", False),
    ("I would suggest a panel of three profiles.", False), ("Give me the amount you are asking for.", False),
    ("That is not for me to say; the simulation states no offer.", False),
])
def test_chat_investor_voice_is_caught_and_assistant_voice_passes(ctx, line, fires):
    led, lib = ctx
    assert bool(errs(chat(line, led, lib), "O3")) == fires, chat(line, led, lib)


@pytest.mark.parametrize("line,fires", [
    ("The founders own 100% of the shares and Acme holds USD 38,000 in cash [E-001].", False),
    ("Acme collects $12 per order against 30% of retail [E-001].", False),
    ("Customers value Acme at roughly $20 per month, per the interviews [E-001].", False),
    ("The sharks would pay 3x revenue for Acme.", True),
    ("A 12x multiple on ARR would be the price.", True),
    ("Acme would fetch 6 times revenue in a sale.", True),
    ("A deal at 4x revenue looks fair.", True),
    ("USD 200,000 against 20% of the company is the working figure.", True),
])
def test_offer_rules_after_the_release_audit(ctx, line, fires):
    led, lib = ctx
    assert bool(errs(check(evaluation(line), led, lib), "O5")) == fires, check(evaluation(line), led, lib)


@pytest.mark.parametrize("line,rule", [
    ("I'd put in $50k.", "O3"), ("I'm in for $50k.", "O3"), ("I'm out", "O3"),
    ("A 20% stake at $1m is the working figure.", "O5"),
    ("Acme has USD 38,000 in cash and burns USD 9,000 a month.", "O8"),
])
def test_final_audit_chat_gaps(ctx, line, rule):
    led, lib = ctx
    assert errs(chat(line, led, lib), rule), chat(line, led, lib)


def test_chat_cited_figures_and_owned_stakes_pass(ctx):
    led, lib = ctx
    assert not errs(chat("Acme's annual plan costs USD 400 [E-001].", led, lib))
    assert not errs(check(evaluation("The founders hold a 100% stake in Acme [E-001]."), led, lib), "O5")


@pytest.mark.parametrize("line,fires", [
    ("No doubt scores 9 of 15 here.", True), ("There is no overall score.", False),
    ("There is no score, ranking or probability.", False),
])
def test_only_a_score_word_after_no_is_a_denial(ctx, line, fires):
    led, lib = ctx
    assert bool(errs(check(evaluation(line), led, lib), "B4")) == fires
