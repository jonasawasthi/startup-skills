"""Startup profile: a directory of Markdown + YAML that every skill shares."""
from __future__ import annotations

import glob
import os
import re
import shutil
from typing import Dict, List, Optional

import yaml

from .evidence import Issue, Ledger, cited_ids

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
TEMPLATE_DIR = os.path.join(ROOT, "templates", "startup-profile")
NARRATIVE_FILES = ["company.md", "problem.md", "solution.md", "customers.md", "market.md", "competitors.md",
                   "business-model.md", "products.md", "traction.md", "team.md", "roadmap.md", "financials.md"]
STAGES = ("idea", "pre-seed", "seed", "series-a", "growth")
PRODUCT_STATUSES = ("live", "built", "in-development", "planned", "proposed", "unknown")


def init(target: str, name: str = "", force: bool = False) -> List[str]:
    os.makedirs(target, exist_ok=True)
    created = []
    for src in sorted(glob.glob(os.path.join(TEMPLATE_DIR, "*"))):
        dst = os.path.join(target, os.path.basename(src))
        if os.path.exists(dst) and not force:
            continue
        shutil.copy(src, dst)
        created.append(dst)
    if name:
        p = os.path.join(target, "profile.yaml")
        with open(p) as f:
            txt = f.read()
        txt = re.sub(r'^name: ""', f'name: "{name}"', txt, count=1, flags=re.M)
        with open(p, "w") as f:
            f.write(txt)
    return created


def load_profile(path: str) -> Dict:
    p = os.path.join(path, "profile.yaml") if os.path.isdir(path) else path
    if not os.path.exists(p):
        return {}
    with open(p) as f:
        return yaml.safe_load(f) or {}


def ledger_for(path: str) -> Ledger:
    return Ledger.load(os.path.join(path, "evidence.yaml"))


def _strip_frontmatter(text: str) -> str:
    if text.startswith("---"):
        end = text.find("\n---", 3)
        if end != -1:
            return text[end + 4:]
    return text


def validate(path: str) -> List[Issue]:
    issues: List[Issue] = []
    if not os.path.isdir(path):
        return [Issue("error", None, f"profile directory not found: {path}")]
    prof = load_profile(path)
    if not prof:
        issues.append(Issue("error", None, "profile.yaml missing or empty"))
    else:
        if not prof.get("name"):
            issues.append(Issue("warning", None, "profile.yaml: name is empty"))
        if prof.get("stage") not in STAGES:
            issues.append(Issue("warning", None, f"profile.yaml: stage should be one of {STAGES}"))
    ledger = ledger_for(path)
    issues.extend(ledger.validate())
    for fn in NARRATIVE_FILES:
        fp = os.path.join(path, fn)
        if not os.path.exists(fp):
            issues.append(Issue("info", None, f"{fn} missing"))
            continue
        with open(fp) as f:
            text = _strip_frontmatter(f.read())
        issues.extend(ledger.check_text(text, fn))
        for line in text.splitlines():
            m = re.search(r"\bstatus:\s*([a-z-]+)", line, re.I)
            if m and fn == "products.md" and m.group(1).lower() not in PRODUCT_STATUSES:
                issues.append(Issue("warning", None, f"products.md: unknown status '{m.group(1)}'"))
    return issues


def missing_information(path: str) -> List[str]:
    """Open TODO prompts across the profile: the founder's to-do list."""
    out = []
    prof = load_profile(path)
    for k in ("name", "one_liner", "stage", "industry"):
        if not prof.get(k):
            out.append(f"profile.yaml: {k}")
    for fn in NARRATIVE_FILES:
        fp = os.path.join(path, fn)
        if not os.path.exists(fp):
            out.append(f"{fn}: file missing")
            continue
        with open(fp) as f:
            for line in f:
                if line.strip().startswith("TODO:"):
                    out.append(f"{fn}: {line.strip()[5:].strip()}")
    return out


def report(path: str) -> str:
    """Regenerate assumptions.md, sources.md and missing-information.md; return a status summary."""
    ledger = ledger_for(path)
    with open(os.path.join(path, "assumptions.md"), "w") as f:
        f.write("# Assumptions\n\nGenerated from `evidence.yaml`. Edit the ledger, not this file.\n\n")
        f.write(ledger.assumptions_md())
    with open(os.path.join(path, "sources.md"), "w") as f:
        f.write("# Sources\n\nGenerated from `evidence.yaml`. Edit the ledger, not this file.\n\n")
        f.write(ledger.bibliography_md())
    missing = missing_information(path)
    with open(os.path.join(path, "missing-information.md"), "w") as f:
        f.write("# Missing information\n\nAnswer these to strengthen every document generated from this profile.\n\n")
        f.write("\n".join(f"- [ ] {m}" for m in missing) + ("\n" if missing else "_Nothing outstanding._\n"))
    s = ledger.summary()
    issues = validate(path)
    errs = sum(1 for i in issues if i.level == "error")
    warns = sum(1 for i in issues if i.level == "warning")
    return (f"Ledger: {len(ledger)} entries ({', '.join(f'{k} {v}' for k, v in s.items() if v)})\n"
            f"Validation: {errs} errors, {warns} warnings\nMissing information: {len(missing)} items")
