"""startup-kit command line.  Run `startup-kit --help`."""
from __future__ import annotations

import argparse
import json
import os
import shutil
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def _print_issues(issues, as_dicts=False):
    errs = 0
    for i in issues:
        lvl = i["level"] if as_dicts else i.level
        msg = i["message"] if as_dicts else str(i)
        where = ""
        if as_dicts and i.get("slide"):
            where = f"slide {i['slide']} ({i.get('id', '')}): "
        print(f"  {lvl.upper():7} {where}{msg}" if as_dicts else f"  {msg}")
        errs += lvl == "error"
    return errs


def cmd_doctor(a):
    ok = True
    print(f"toolkit root: {ROOT}")
    print(f"python: {sys.executable} ({sys.version.split()[0]})")
    for mod in ("yaml", "pptx", "docx", "openpyxl", "reportlab", "matplotlib", "pypdf", "PIL"):
        try:
            __import__(mod)
            print(f"  ok       {mod}")
        except ImportError:
            ok = False
            print(f"  MISSING  {mod}")
    try:
        __import__("formulas")
        print("  ok       formulas (optional: XLSX recalculation checks)")
    except ImportError:
        print("  optional formulas not installed (XLSX recalculation checks skipped)")
    print(f"  {'ok      ' if shutil.which('pdftoppm') else 'optional'} pdftoppm (PDF previews)")
    from . import fonts
    for fam in ("Arial", "Georgia"):
        r = fonts.register(fam)
        print(f"  font     {fam}: {'embedded TrueType' if not r[0].startswith(('Helvetica', 'Times')) else 'PDF core fallback ' + r[0]}")
    if not ok:
        print(f"\nInstall dependencies: {os.path.join(ROOT, 'scripts', 'setup.sh')}")
    return 0 if ok else 1


def cmd_profile(a):
    from . import profile
    if a.action == "init":
        created = profile.init(a.dir, a.name or "", a.force)
        print(f"initialised {a.dir} ({len(created)} files)")
        return 0
    if a.action == "validate":
        issues = profile.validate(a.dir)
        for i in issues:
            print(f"  {i}")
        errs = sum(1 for i in issues if i.level == "error")
        print(f"{errs} errors, {sum(1 for i in issues if i.level == 'warning')} warnings")
        return 1 if errs else 0
    if a.action == "report":
        print(profile.report(a.dir))
        return 0
    if a.action == "missing":
        for m in profile.missing_information(a.dir):
            print(f"- [ ] {m}")
        return 0


def cmd_ledger(a):
    from .evidence import Ledger
    L = Ledger.load(a.file)
    if a.action == "validate":
        issues = L.validate()
        for i in issues:
            print(f"  {i}")
        print(f"{len(L)} entries; summary: {L.summary()}")
        return 1 if any(i.level == "error" for i in issues) else 0
    if a.action == "next-id":
        print(L.next_id())
    if a.action == "bibliography":
        print(L.bibliography_md())
    if a.action == "assumptions":
        print(L.assumptions_md())
    return 0


def cmd_scan(a):
    from .scan import scan, to_markdown
    r = scan(a.repo)
    out = a.out or "."
    os.makedirs(out, exist_ok=True)
    with open(os.path.join(out, "codebase-inventory.json"), "w") as f:
        json.dump(r, f, indent=2, default=str)
    with open(os.path.join(out, "codebase-inventory.md"), "w") as f:
        f.write(to_markdown(r))
    print(f"units: {len(r['units'])} | schema objects: {sum(len(v) for v in r['schemas'].values())} | "
          f"docs: {len(r['docs'])} | secret-like files skipped: {r['secret_files_skipped']}")
    print(f"wrote {os.path.join(out, 'codebase-inventory.md')} and .json")
    return 0


def cmd_market(a):
    from .calc import load_yaml, market_size, market_size_md
    from .evidence import Ledger
    L = Ledger.load(os.path.join(a.profile, "evidence.yaml")) if a.profile else None
    res = market_size(load_yaml(a.spec), L)
    md = market_size_md(res)
    if a.out:
        with open(a.out, "w") as f:
            f.write(md)
        print(f"wrote {a.out}")
    else:
        print(md)
    return 1 if res["issues"] and any("exceeds" in i for i in res["issues"]) else 0


def cmd_ue(a):
    from .calc import unit_economics_md
    print(unit_economics_md(a.arpu, a.gross_margin, a.churn, a.cac, a.currency))
    return 0


def cmd_deck(a):
    from .deck.build import build
    rep = build(a.spec, a.out, a.variant, tuple(a.formats.split(",")))
    print(f"slides: {rep['slides']} | errors: {rep['errors']} | warnings: {rep['warnings']}")
    _print_issues(rep["issues"], True)
    if rep["missing"]:
        print("missing information:")
        for m in rep["missing"]:
            print(f"  - {m}")
    for k, v in rep["outputs"].items():
        print(f"  {k}: {v}")
    return 1 if rep["errors"] else 0


def cmd_doc(a):
    from .docs.build import build
    rep = build(a.source, a.out, tuple(a.formats.split(",")))
    print(f"theme: {rep['theme']} | cited evidence: {len(rep['cited'])} | errors: {rep['errors']} | warnings: {rep['warnings']}")
    _print_issues(rep["issues"], True)
    for k, v in rep["outputs"].items():
        print(f"  {k}: {v}")
    return 1 if rep["errors"] else 0


def cmd_model(a):
    import yaml
    from .evidence import Ledger
    from .xlsx import build_workbook, simulate, validate_model
    with open(a.spec) as f:
        m = yaml.safe_load(f)
    for w in validate_model(m):
        print(f"  WARNING {w}")
    L = Ledger.load(os.path.join(a.profile, "evidence.yaml")) if a.profile else None
    out = a.out or os.path.splitext(a.spec)[0] + ".xlsx"
    os.makedirs(os.path.dirname(os.path.abspath(out)), exist_ok=True)
    info = build_workbook(m, out, L)
    sim = simulate(m)
    summary = os.path.splitext(out)[0] + "-summary.json"
    with open(summary, "w") as f:
        json.dump({"annual": sim["annual"], "cash_out_month": sim["cash_out_month"],
                   "monthly_revenue": sim["revenue"], "monthly_cash": sim["cash"]}, f, indent=2)
    cur = m.get("model", {}).get("currency", "")
    for y in sim["annual"]:
        print(f"  Year {y['year']}: revenue {y['revenue']:,.0f} {cur} | EBITDA {y['ebitda']:,.0f} | ending cash {y['ending_cash']:,.0f}")
    print(f"  first month with negative cash: {sim['cash_out_month'] or 'none in horizon'}")
    if info["missing_evidence"]:
        print(f"  ERROR evidence IDs not in ledger: {info['missing_evidence']}")
    print(f"wrote {out} and {summary}")
    return 1 if info["missing_evidence"] else 0


def cmd_check(a):
    from .inspect import check
    bad = 0
    for p in a.files:
        r = check(p)
        status = "OK " if r["ok"] else "FAIL"
        print(f"{status} {p}  {json.dumps(r['info'], default=str)}")
        for e in r["errors"]:
            print(f"   ERROR   {e}")
        for w in r["warnings"]:
            print(f"   WARNING {w}")
        bad += not r["ok"]
    return 1 if bad else 0


def cmd_preview(a):
    from .inspect import previews
    for p in previews(a.pdf, a.out or os.path.dirname(os.path.abspath(a.pdf)), a.dpi, a.per_sheet, a.cols):
        print(p)
    return 0


def cmd_themes(a):
    from .theme import AUDIENCE_TO_THEME, available_themes, get_theme
    for t in available_themes():
        th = get_theme(t)
        aud = sorted(k for k, v in AUDIENCE_TO_THEME.items() if v == t)
        print(f"{t:14} accent {th.accent}  headings {th.heading_font:8} cover {th.cover_style:13} aliases: {', '.join(aud)}")
    return 0


def main(argv=None):
    p = argparse.ArgumentParser(prog="startup-kit", description="Startup Skills engine: evidence, scanning, "
                                                                 "calculators and document generation.")
    sub = p.add_subparsers(dest="cmd", required=True)
    sub.add_parser("doctor", help="check dependencies").set_defaults(fn=cmd_doctor)
    sp = sub.add_parser("profile", help="startup profile: init | validate | report | missing")
    sp.add_argument("action", choices=["init", "validate", "report", "missing"])
    sp.add_argument("dir")
    sp.add_argument("--name")
    sp.add_argument("--force", action="store_true")
    sp.set_defaults(fn=cmd_profile)
    sp = sub.add_parser("ledger", help="evidence ledger: validate | next-id | bibliography | assumptions")
    sp.add_argument("action", choices=["validate", "next-id", "bibliography", "assumptions"])
    sp.add_argument("file")
    sp.set_defaults(fn=cmd_ledger)
    sp = sub.add_parser("scan", help="read-only codebase inventory")
    sp.add_argument("repo")
    sp.add_argument("--out")
    sp.set_defaults(fn=cmd_scan)
    sp = sub.add_parser("market-size", help="bottom-up TAM/SAM/SOM from a YAML spec")
    sp.add_argument("spec")
    sp.add_argument("--profile")
    sp.add_argument("--out")
    sp.set_defaults(fn=cmd_market)
    sp = sub.add_parser("unit-economics", help="LTV, CAC payback and sensitivity")
    sp.add_argument("--arpu", type=float, required=True, help="revenue per customer per month")
    sp.add_argument("--gross-margin", type=float, required=True, help="0..1")
    sp.add_argument("--churn", type=float, required=True, help="monthly churn 0..1")
    sp.add_argument("--cac", type=float, required=True)
    sp.add_argument("--currency", default="USD")
    sp.set_defaults(fn=cmd_ue)
    sp = sub.add_parser("deck", help="build a deck spec into PPTX + PDF + narrative")
    sp.add_argument("spec")
    sp.add_argument("--out")
    sp.add_argument("--variant", help="e.g. short")
    sp.add_argument("--formats", default="pptx,pdf")
    sp.set_defaults(fn=cmd_deck)
    sp = sub.add_parser("doc", help="build a Markdown+ document into DOCX / PDF / MD")
    sp.add_argument("source")
    sp.add_argument("--out")
    sp.add_argument("--formats", default="docx,pdf,md")
    sp.set_defaults(fn=cmd_doc)
    sp = sub.add_parser("model", help="build a financial model YAML into XLSX")
    sp.add_argument("spec")
    sp.add_argument("--profile")
    sp.add_argument("--out")
    sp.set_defaults(fn=cmd_model)
    sp = sub.add_parser("check", help="validate generated files")
    sp.add_argument("files", nargs="+")
    sp.set_defaults(fn=cmd_check)
    sp = sub.add_parser("preview", help="render PDF pages to PNG contact sheets")
    sp.add_argument("pdf")
    sp.add_argument("--out")
    sp.add_argument("--dpi", type=int, default=60)
    sp.add_argument("--per-sheet", type=int, default=8)
    sp.add_argument("--cols", type=int, default=2)
    sp.set_defaults(fn=cmd_preview)
    sub.add_parser("themes", help="list design themes").set_defaults(fn=cmd_themes)
    a = p.parse_args(argv)
    return a.fn(a) or 0


if __name__ == "__main__":
    sys.exit(main())
