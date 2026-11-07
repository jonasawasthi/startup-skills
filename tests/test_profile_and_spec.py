import os
import subprocess
import sys

from startup_kit import profile


def test_profile_init_and_missing_information(tmp_path):
    """Incomplete information becomes a checklist, never invented content."""
    d = str(tmp_path / "p")
    created = profile.init(d, "Acme")
    assert len(created) >= 15
    missing = profile.missing_information(d)
    assert any("one_liner" in m for m in missing)
    assert any(m.startswith("problem.md") for m in missing)
    summary = profile.report(d)
    assert "Missing information" in summary
    assert os.path.exists(os.path.join(d, "missing-information.md"))


def test_example_profile_ledger_valid(example_dir):
    from startup_kit.evidence import Ledger
    errs = [i for i in Ledger.load(os.path.join(example_dir, "startup-profile", "evidence.yaml")).validate()
            if i.level == "error"]
    assert not errs, errs


def test_all_skills_meet_spec(root):
    r = subprocess.run([sys.executable, os.path.join(root, "scripts", "validate_skills.py")], capture_output=True,
                       text=True)
    assert r.returncode == 0, r.stdout


def test_cli_end_to_end(root, example_dir, tmp_path):
    """Cross-skill flow through the CLI: research ledger → market size → model → document → deck → check."""
    env = dict(os.environ, PYTHONPATH=os.path.join(root, "lib"))
    kit = [sys.executable, "-m", "startup_kit.cli"]
    prof = os.path.join(example_dir, "startup-profile")
    market = tmp_path / "market.yaml"
    market.write_text("tam: {factors: [{label: coops, value: 22000, evidence: E-003}, "
                      "{label: budget, value: 600, evidence: E-004}]}\n")
    steps = [
        ["ledger", "validate", os.path.join(prof, "evidence.yaml")],
        ["market-size", str(market), "--profile", prof],
        ["model", os.path.join(example_dir, "financial-model", "model.yaml"), "--profile", prof, "--out",
         str(tmp_path / "m.xlsx")],
        ["doc", os.path.join(example_dir, "proposal", "fieldnote-investor-proposal.md"), "--out", str(tmp_path)],
        ["deck", os.path.join(example_dir, "deck", "fieldnote-seed.yaml"), "--out", str(tmp_path)],
        ["check", str(tmp_path / "m.xlsx"), str(tmp_path / "fieldnote-seed.pptx"),
         str(tmp_path / "fieldnote-investor-proposal.docx")],
    ]
    for s in steps:
        r = subprocess.run(kit + s, capture_output=True, text=True, env=env, cwd=root)
        assert r.returncode == 0, (s, r.stdout, r.stderr)
    out = subprocess.run(kit + ["market-size", str(market), "--profile", prof], capture_output=True, text=True,
                         env=env).stdout
    assert "$13.20M" in out and "assumption" in out   # weakest-status inheritance visible to users
