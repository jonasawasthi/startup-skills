#!/usr/bin/env python3
"""Validate every skills/*/SKILL.md against the Agent Skills specification.

Rules (https://agentskills.io/specification and Claude Code docs, checked 2026-11-07):
  * file starts with YAML front matter; only portable keys are used
  * name: 1-64 chars, [a-z0-9-], no leading/trailing/double hyphen, equals directory
  * description: 1-1024 chars; says what AND when ("Use when" / "Use this")
  * compatibility <= 500 chars; metadata is a string->string map
  * SKILL.md under 500 lines; every relative Markdown link resolves
"""
import glob
import os
import re
import sys

import yaml

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ALLOWED = {"name", "description", "license", "compatibility", "metadata", "allowed-tools"}
LINK = re.compile(r"\[[^\]]*\]\(([^)#\s]+)(?:#[^)]*)?\)")


def validate(path):
    errs, warns = [], []
    d = os.path.dirname(path)
    text = open(path, encoding="utf-8").read()
    if not text.startswith("---\n"):
        return [f"{path}: must start with YAML front matter"], warns
    end = text.find("\n---", 4)
    fm = yaml.safe_load(text[4:end]) or {}
    extra = set(fm) - ALLOWED
    if extra:
        errs.append(f"non-portable front matter keys: {sorted(extra)}")
    name = str(fm.get("name", ""))
    if not re.fullmatch(r"[a-z0-9]+(-[a-z0-9]+)*", name) or len(name) > 64:
        errs.append(f"invalid name '{name}'")
    if name != os.path.basename(d):
        errs.append(f"name '{name}' != directory '{os.path.basename(d)}'")
    desc = str(fm.get("description", ""))
    if not 1 <= len(desc) <= 1024:
        errs.append(f"description length {len(desc)} not in 1..1024")
    if not re.search(r"\buse (this|when|it)\b", desc, re.I):
        warns.append("description should say when to use the skill ('Use when ...')")
    if "compatibility" in fm and len(str(fm["compatibility"])) > 500:
        errs.append("compatibility > 500 chars")
    md = fm.get("metadata", {})
    if md and (not isinstance(md, dict) or not all(isinstance(k, str) and isinstance(v, str) for k, v in md.items())):
        errs.append("metadata must map strings to strings (quote numbers)")
    lines = text.count("\n") + 1
    if lines >= 500:
        errs.append(f"SKILL.md has {lines} lines (>= 500)")
    for f in [path] + glob.glob(os.path.join(d, "references", "*.md")):
        body = re.sub(r"(?ms)^(```|~~~~).*?^\1", "", open(f, encoding="utf-8").read())  # ignore code fences
        for target in LINK.findall(body):
            if re.match(r"^[a-z]+:", target):
                continue
            if not os.path.exists(os.path.normpath(os.path.join(os.path.dirname(f), target))):
                errs.append(f"broken link in {os.path.relpath(f, d)}: {target}")
    return errs, warns


def main():
    paths = sorted(glob.glob(os.path.join(ROOT, "skills", "*", "SKILL.md")))
    total = 0
    for p in paths:
        errs, warns = validate(p)
        rel = os.path.relpath(p, ROOT)
        print(f"{'FAIL' if errs else 'OK  '} {rel}")
        for e in errs:
            print(f"   error: {e}")
        for w in warns:
            print(f"   warning: {w}")
        total += len(errs)
    print(f"\n{len(paths)} skills, {total} errors")
    return 1 if total or not paths else 0


if __name__ == "__main__":
    sys.exit(main())
