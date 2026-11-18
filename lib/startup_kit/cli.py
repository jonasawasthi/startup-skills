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
    import yaml
    from .docs.build import build
    try:
        rep = build(a.source, a.out, tuple(a.formats.split(",")))
    except yaml.YAMLError as e:
        print(f"  ERROR   front matter of {a.source} is not valid YAML; quote values that contain ': '\n{e}")
        return 1
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


def cmd_gtm(a):
    from . import gtm
    if a.action == "check":
        from .docs.markdown import split_front_matter
        from .evidence import Ledger
        with open(a.file) as f:
            text = f.read()
        ledger = None
        prof = a.profile
        if not prof:
            meta, _ = split_front_matter(text)
            ev = meta.get("evidence") or (os.path.join(meta["profile"], "evidence.yaml") if meta.get("profile") else None)
            if ev:
                ledger = Ledger.load(ev if os.path.isabs(ev) else os.path.join(os.path.dirname(os.path.abspath(a.file)), ev))
        else:
            ledger = Ledger.load(os.path.join(prof, "evidence.yaml"))
        issues = gtm.check_claims(text, ledger, os.path.basename(a.file))
        for i in issues:
            print(f"  {i['level'].upper():7} {i['message']}")
        errs = sum(1 for i in issues if i["level"] == "error")
        print(f"{errs} errors, {sum(1 for i in issues if i['level'] == 'warning')} warnings"
              + ("" if ledger is not None else " (no ledger: citations not resolved)"))
        return 1 if errs else 0
    try:
        rep = gtm.analyze(a.file)
    except ValueError as e:
        print(f"  ERROR   {e}")
        return 1
    stem = os.path.splitext(os.path.basename(a.file))[0]
    out = a.out or os.path.dirname(os.path.abspath(a.file))
    os.makedirs(out, exist_ok=True)
    if a.action == "kpi":
        info = gtm.kpi_workbook(rep, os.path.join(out, f"{stem}-kpi-dashboard.xlsx"), a.weeks)
        print(f"wrote {info['path']} ({info['kpis']} KPIs, {len(info['inputs'])} weekly inputs, "
              f"{info['formulas']} formulas)")
        return 0
    md_path = os.path.join(out, f"{stem}-analysis.md")
    with open(md_path, "w") as f:
        f.write(gtm.analysis_md(rep))
    js = {k: v for k, v in rep.items() if k != "_spec"}
    for c in js["channels"]:
        c.pop("spec", None)
    if js.get("marketplace"):
        js["marketplace"] = {k: v for k, v in js["marketplace"].items() if k != "spec"}
    js["roadmap"] = [{k: v for k, v in p.items() if k != "spec"} for p in js["roadmap"]]
    with open(os.path.join(out, f"{stem}-analysis.json"), "w") as f:
        json.dump(js, f, indent=2, default=str)
    prim = [c["name"] for c in rep["channels"] if c["decision"] == "primary"]
    computed = sum(1 for m in rep["metrics"] if m["value"] is not None)
    print(f"company: {rep['company']} | stage: {rep['stage']} | model: {', '.join(rep['types'])}")
    print(f"primary channels: {', '.join(prim) or 'none'} | metrics computed: {computed}/{len(rep['metrics'])}"
          f" | errors: {rep['errors']} | warnings: {rep['warnings']}")
    for i in rep["issues"]:
        print(f"  {i['level'].upper():7} {i['area']}: {i['message']}")
    print(f"wrote {md_path} and .json")
    return 1 if rep["errors"] else 0


def cmd_discovery(a):
    from . import customer_discovery as cd
    if a.action == "check":
        from .docs.markdown import split_front_matter
        from .evidence import Ledger
        with open(a.file) as f:
            text = f.read()
        rep, ledger = None, None
        if a.spec:
            rep = cd.analyze(a.spec)
            ledger = Ledger.load(os.path.join(rep["profile_dir"], "evidence.yaml")) if rep["profile_dir"] else None
        if ledger is None:
            meta, _ = split_front_matter(text)
            prof = a.profile or meta.get("profile")
            if prof:
                prof = prof if os.path.isabs(prof) or a.profile else os.path.join(os.path.dirname(os.path.abspath(a.file)), prof)
                ledger = Ledger.load(os.path.join(prof, "evidence.yaml"))
        issues = cd.check_document(text, ledger, rep, os.path.basename(a.file))
        for i in issues:
            print(f"  {i['level'].upper():7} {i['message']}")
        errs = sum(1 for i in issues if i["level"] == "error")
        print(f"{errs} errors, {sum(1 for i in issues if i['level'] == 'warning')} warnings"
              + ("" if rep is not None else " (no --spec: quotations and counts not checked against the research)"))
        return 1 if errs else 0
    try:
        if a.action == "analyze" and a.record:
            added = cd.record(a.file)
            print(f"ledger: recorded {len(added)} new entr{'y' if len(added) == 1 else 'ies'}"
                  + (f" ({', '.join(added)})" if added else ""))
        rep = cd.analyze(a.file)
    except ValueError as e:
        print(f"  ERROR   {e}")
        return 1
    stem = os.path.splitext(os.path.basename(a.file))[0]
    out = a.out or os.path.dirname(os.path.abspath(a.file))
    os.makedirs(out, exist_ok=True)
    written = []
    if a.action == "analyze":
        p = os.path.join(out, f"{stem}-analysis.md")
        with open(p, "w") as f:
            f.write(cd.analysis_md(rep))
        js = {k: v for k, v in rep.items() if k not in ("_spec",)}
        for key in ("segments", "hypotheses", "experiments"):
            js[key] = [{k: v for k, v in r.items() if k != "spec"} for r in js[key]]
        with open(os.path.join(out, f"{stem}-analysis.json"), "w") as f:
            json.dump(js, f, indent=2, default=str)
        written += [p, p.replace(".md", ".json")]
    elif a.action == "interviews":
        segs = rep["_spec"].get("segments", []) or []
        for s in segs:
            if a.segment and str(s.get("id")) != a.segment:
                continue
            g = os.path.join(out, f"interview-guide-{str(s.get('id')).lower()}.md")
            with open(g, "w") as f:
                f.write(cd.interview_guide(rep["_spec"], s))
            n = os.path.join(out, f"interview-notes-template-{str(s.get('id')).lower()}.md")
            with open(n, "w") as f:
                f.write(cd.notes_template(rep["_spec"], s))
            iss, st = cd.lint_guide(open(g).read())
            bad = [i for i in iss if i["level"] == "error"]
            print(f"  {s.get('id')}: {st['questions']} questions, {st['past_behaviour']} about past behaviour, "
                  f"{len(bad)} flagged")
            written += [g, n]
    elif a.action == "hypotheses":
        p = os.path.join(out, f"{stem}-hypotheses.md")
        with open(p, "w") as f:
            f.write("## Hypothesis register\n\n" + "\n".join(cd.hypothesis_table(rep)))
        written.append(p)
        if a.xlsx:
            written.append(cd.hypotheses_workbook(rep, os.path.join(out, f"{stem}-hypotheses.xlsx")))
        if rep["unregistered"]:
            print(f"  {len(rep['unregistered'])} ledger assumptions are not yet covered by a hypothesis")
    elif a.action == "experiment":
        p = os.path.join(out, f"{stem}-experiments.md")
        with open(p, "w") as f:
            f.write("## Experiment plans\n\n" + "\n".join(cd.experiment_cards(rep, a.id)))
        written.append(p)
    elif a.action == "report":
        secs = a.sections.split(",") if a.sections else None
        try:
            md = cd.report_md(rep, out, secs)
        except ValueError as e:
            print(f"  ERROR   {e}")
            return 1
        name = f"{stem}-report.md" if not secs else f"{stem}-{'-'.join(secs)}.md"
        p = os.path.join(out, name)
        with open(p, "w") as f:
            f.write(md)
        written.append(p)
        from .evidence import Ledger
        led = Ledger.load(os.path.join(rep["profile_dir"], "evidence.yaml")) if rep["profile_dir"] else None
        for i in cd.check_document(md, led, rep, name):
            if i["level"] == "error":
                rep["issues"].append({"level": "error", "area": "report", "message": i["message"]})
                rep["errors"] += 1
        print(f"  next: startup-kit doc {p} --out {out}")
    print(f"company: {rep['company']} | interviews: {len(rep['interviews'])} | hypotheses: {len(rep['hypotheses'])} | "
          f"experiments: {len(rep['experiments'])} | errors: {rep['errors']} | warnings: {rep['warnings']}")
    print(f"problem-solution fit: {rep['psf']['verdict']}")
    for i in rep["issues"]:
        print(f"  {i['level'].upper():7} {i['area']}: {i['message']}")
    for w in written:
        print(f"wrote {w}")
    return 1 if rep["errors"] else 0


BM_SECTION_ACTIONS = {"canvas": ["canvas"], "value-proposition": ["value-proposition"],
                      "compare": ["classification", "alternatives"], "revenue": ["revenue", "financials"],
                      "costs": ["costs"], "marketplace": ["marketplace", "payments"],
                      "assumptions": ["assumptions"], "stress-test": ["stress"]}
BM_AREAS = {"canvas": ("canvas",), "value-proposition": ("value-proposition",),
            "compare": ("alternatives", "classification"), "revenue": ("revenue", "financials", "payments"),
            "costs": ("costs",), "marketplace": ("marketplace", "payments", "dependencies"),
            "assumptions": ("assumptions", "discovery"), "stress-test": ("stress",)}


def _bm_ledger(rep):
    from .evidence import Ledger
    return Ledger.load(os.path.join(rep["profile_dir"], "evidence.yaml")) if rep["profile_dir"] else None


def cmd_business_model(a):
    from . import business_model as bm
    if a.action == "check":
        from .docs.markdown import split_front_matter
        from .evidence import Ledger
        with open(a.file) as f:
            text = f.read()
        rep, ledger = None, None
        if a.spec:
            try:
                rep = bm.analyze(a.spec)
            except ValueError as e:
                print(f"  ERROR   {e}")
                return 1
            ledger = _bm_ledger(rep)
        if ledger is None:
            meta, _ = split_front_matter(text)
            prof = a.profile or meta.get("profile")
            if prof:
                prof = prof if os.path.isabs(prof) or a.profile else os.path.join(os.path.dirname(os.path.abspath(a.file)), prof)
                ledger = Ledger.load(os.path.join(prof, "evidence.yaml"))
        issues = bm.check_document(text, ledger, rep, os.path.basename(a.file))
        for i in issues:
            print(f"  {i['level'].upper():7} {i['message']}")
        errs = sum(1 for i in issues if i["level"] == "error")
        print(f"{errs} errors, {sum(1 for i in issues if i['level'] == 'warning')} warnings"
              + ("" if ledger is not None else " (no ledger: citations not resolved)"))
        return 1 if errs else 0
    if a.action == "design":
        import yaml
        target = a.file
        disc = a.discovery
        if os.path.isfile(target):          # an existing spec: inventory its profile
            try:
                spec = bm.load_spec(target)
            except ValueError as e:
                print(f"  ERROR   {e}")
                return 1
            base = os.path.dirname(os.path.abspath(target))
            _, _, prof = bm.context(spec, base)
            d = spec.get("design", {}) or {}
            if not disc and d.get("discovery"):
                disc = d["discovery"] if os.path.isabs(d["discovery"]) else os.path.join(base, d["discovery"])
            target = prof
            if not target:
                print("  ERROR   the spec names no profile (design.profile)")
                return 1
        if not os.path.isdir(target):
            print(f"  ERROR   profile directory not found: {target}")
            return 1
        try:
            md, starter = bm.inventory(target, disc)
        except ValueError as e:
            print(f"  ERROR   {e}")
            return 1
        out = a.out or os.path.join(os.getcwd(), "business-model")
        os.makedirs(out, exist_ok=True)
        p = os.path.join(out, "business-model-inventory.md")
        with open(p, "w") as f:
            f.write(md)
        print(f"wrote {p}")
        s = os.path.join(out, "business-model.yaml")
        if os.path.exists(s):
            print(f"  kept existing {s} (starter spec not overwritten)")
        else:
            with open(s, "w") as f:
                f.write("# Starter business model spec generated from the profile. Items carry the status of their\n"
                        "# ledger entries; everything else is 'unknown'. Fill in what the founder knows; never invent.\n")
                f.write(yaml.safe_dump(starter, sort_keys=False, allow_unicode=True))
            print(f"wrote {s}")
        return 0
    try:
        if a.action == "assumptions" and a.record:
            added = bm.record(a.file)
            print(f"ledger: recorded {len(added)} new entr{'y' if len(added) == 1 else 'ies'}"
                  + (f" ({', '.join(added)})" if added else ""))
        rep = bm.analyze(a.file, a.model if a.action == "canvas" else None)
    except ValueError as e:
        print(f"  ERROR   {e}")
        return 1
    stem = os.path.splitext(os.path.basename(a.file))[0]
    out = a.out or os.path.dirname(os.path.abspath(a.file))
    os.makedirs(out, exist_ok=True)
    written = []
    if a.action == "report":
        secs = a.sections.split(",") if a.sections else None
        try:
            md = bm.report_md(rep, out, secs, segment=a.segment, only_model=a.model)
        except ValueError as e:
            print(f"  ERROR   {e}")
            return 1
        name = f"{stem}-report.md" if not secs else f"{stem}-{'-'.join(secs)}.md"
        issues = rep["issues"]
    elif a.action in BM_SECTION_ACTIONS:
        if a.segment and a.segment not in {str(s.get("id")) for s in rep["segments"]}:
            print(f"  ERROR   unknown segment '{a.segment}'")
            return 1
        md = bm.report_md(rep, out, BM_SECTION_ACTIONS[a.action], segment=a.segment, only_model=a.model,
                          title={"canvas": "Business Model Canvas", "value-proposition": "Value Proposition Canvas",
                                 "compare": "Business model alternatives", "revenue": "Revenue architecture",
                                 "costs": "Cost structure", "marketplace": "Marketplace model",
                                 "assumptions": "Assumption register", "stress-test": "Business model stress test"
                                 }[a.action])
        name = f"{stem}-{a.action}" + (f"-{a.model.lower()}" if a.model else "") + (
            f"-{a.segment.lower()}" if a.segment else "") + ".md"
        issues = [i for i in rep["issues"] if i["area"] in BM_AREAS[a.action] or i["level"] == "error"]
    else:   # analyze
        md, name, issues = bm.analysis_md(rep), f"{stem}-analysis.md", rep["issues"]
    if a.format == "json":
        js = {k: v for k, v in rep.items() if k != "_spec"}
        for key in ("revenue", "dependencies", "assumptions"):
            js[key] = [{k: v for k, v in r.items() if k != "spec"} for r in js[key]]
        js["alternatives"] = dict(js["alternatives"], alternatives=[
            {k: v for k, v in x.items() if k != "spec"} for x in js["alternatives"]["alternatives"]])
        if js.get("marketplace"):
            js["marketplace"] = {k: v for k, v in js["marketplace"].items() if k != "spec"}
        p = os.path.join(out, os.path.splitext(name)[0] + ".json")
        with open(p, "w") as f:
            json.dump(js, f, indent=2, default=str)
    else:
        p = os.path.join(out, name)
        with open(p, "w") as f:
            f.write(md)
        if a.action != "analyze":
            for i in bm.check_document(md, _bm_ledger(rep), rep, name):
                if i["level"] == "error":
                    issues = issues + [{"level": "error", "area": "report", "message": i["message"]}]
            print(f"  next: startup-kit doc {p} --out {out}")
    written.append(p)
    if a.xlsx:
        written.append(bm.workbook(rep, os.path.join(out, f"{stem}-workbook.xlsx"))["path"])
    errs = sum(1 for i in issues if i["level"] == "error")
    print(f"company: {rep['company']} | model: {', '.join(rep['classification']['labels']) or 'not set'} | "
          f"maturity: {rep['maturity']['level']} | errors: {errs} | "
          f"warnings: {sum(1 for i in issues if i['level'] == 'warning')}")
    for i in issues:
        print(f"  {i['level'].upper():7} {i['area']}: {i['message']}")
    for w in written:
        print(f"wrote {w}")
    return 1 if errs else 0


def _st_print(issues):
    for i in issues:
        print(f"  {i['level'].upper():7} {i['rule']}: {i['message']}")
    errs = sum(1 for i in issues if i["level"] == "error")
    print(f"{errs} errors, {sum(1 for i in issues if i['level'] == 'warning')} warnings")
    return errs


def cmd_shark_tank(a):
    from . import shark_tank as st
    from .evidence import Ledger

    def library():
        profs, issues = st.load_library(a.library, a.today, include_default=not a.no_shipped)
        return profs, issues

    def need(what):
        if not a.target:
            print(f"  ERROR   shark-tank {a.action} needs {what}")
            return False
        return True

    try:
        if a.action == "profiles":
            profs, lib_issues = library()
            if a.id:
                p = profs.get(a.id)
                if not p:
                    print(f"  ERROR   no profile '{a.id}' in the libraries")
                    return 1
                if a.json:
                    print(json.dumps({**p.summary(), "lenses": p.lenses, "emphasis": p.emphasis,
                                      "issues": p.issues}, indent=2, default=str))
                    return 1 if p.errors else 0
                s = p.summary()
                print(f"{p.name} ({p.id}) · confidence declared {s['declared']}, effective {s['effective']}")
                for lid, ln in p.lenses.items():
                    print(f"  {lid} {ln.get('label')}: dimensions {', '.join(str(d) for d in ln.get('dimensions') or [])}"
                          f"{' · decline pattern' if ln.get('decline_pattern') else ''}")
                for tier in ("primary", "secondary"):
                    print(f"  {tier}: " + (", ".join(f"{d} {l}" for d, l in p.emphasis[tier].items()) or "none"))
                return 1 if _st_print(p.issues) else 0
            rows = [p.summary() for p in profs.values()]
            issues = lib_issues + [i for p in profs.values() for i in p.issues]
            if a.json:
                print(json.dumps({"profiles": rows, "issues": issues}, indent=2, default=str))
                return 1 if any(i["level"] == "error" for i in issues) else 0
            print(f"{'id':22} {'name':24} {'regions':8} {'declared':8} {'effective':9} src lenses  programmes (status, as of)")
            for r in rows:
                print(f"{r['id']:22} {r['name'][:24]:24} {','.join(r['regions']):8} {r['declared']:8} "
                      f"{str(r['effective']):9} {r['sources']:3} {r['lenses']:<6} {'; '.join(r['programmes'])}")
            print(f"{len(rows)} profiles")
            return 1 if _st_print(issues) else 0
        if a.action == "context":
            if not need("a profile directory"):
                return 1
            ctx = st.context(a.target)
            print(json.dumps(ctx, indent=2, default=str) if a.json else st.context_md(ctx))
            return 0
        if a.action == "base-read":
            if not need("a base-read YAML file") or not a.profile:
                print("  ERROR   base-read needs FILE and --profile PROFILE_DIR")
                return 1
            data = st.load_yaml(a.target)
            ledger = Ledger.load(os.path.join(a.profile, "evidence.yaml"))
            issues = st.validate_base_read(data, ledger, a.today)
            if isinstance(data, dict) and isinstance(data.get("dimensions"), dict):
                print(st.evidence_profile_line(data["dimensions"]))
            if a.out and not any(i["level"] == "error" for i in issues):
                rel = os.path.relpath(os.path.abspath(a.profile), os.path.dirname(os.path.abspath(a.out)))
                md = st.render_base_read(data, ledger, rel)
                os.makedirs(os.path.dirname(os.path.abspath(a.out)), exist_ok=True)
                with open(a.out, "w", encoding="utf-8") as f:
                    f.write(md)
                profs, _ = library()
                # every guard result on the rendered Markdown, warnings included, as `check` would report them
                issues += st.check_document(md, ledger, profs, where=os.path.basename(a.out), base=data)
                print(f"wrote {a.out}")
            elif a.out:
                print("  not written: fix the errors first")
            return 1 if _st_print(issues) else 0
        if a.action == "queue":
            if not need("a base-read YAML file"):
                return 1
            profs, _ = library()
            ids = [i.strip() for i in (a.investors or "").split(",") if i.strip()]
            chosen, bad = [], []
            for i in ids:
                p = profs.get(i)
                if not p or not p.ok:
                    bad.append(i)
                else:
                    chosen.append(p)
            if bad:
                print(f"  ERROR   unknown or invalid investor profiles: {', '.join(bad)}")
                return 1
            if a.budget < 1:
                print("  ERROR   --budget must be at least 1")
                return 1
            ledger = Ledger.load(os.path.join(a.profile, "evidence.yaml")) if a.profile else None
            rows = st.queue(st.load_yaml(a.target) or {}, chosen, a.budget, ledger)
            if ledger is None:
                note = ("NOTE    no --profile: the ledger was not read, so tier 3 rests on the base read's buckets "
                        "alone (a critical Adequate with no verified entry). Pass --profile PROFILE_DIR so that "
                        "interview-reported evidence keeps a dimension out of tier 3.")
                print(note, file=sys.stderr if a.json else sys.stdout)
            if a.json:
                print(json.dumps(rows, indent=2))
                return 0
            print("tier  dim  rating    investor              lens  decisive question")
            for r in rows:
                print(f"{r['tier']:<5} {r['dimension']}  {r['rating']:9} {r['investor'][:21]:21} {r['lens']:5} "
                      f"{r['decisive_question']}")
            return 0
        if a.action == "check":
            if not need("a Markdown document"):
                return 1
            from .docs.markdown import split_front_matter
            with open(a.target, encoding="utf-8") as f:
                text = f.read()
            ledger = None
            if a.profile:
                ledger = Ledger.load(os.path.join(a.profile, "evidence.yaml"))
            else:
                try:
                    meta, _ = split_front_matter(text)
                except Exception:
                    meta = {}
                ev = meta.get("evidence") or (os.path.join(meta["profile"], "evidence.yaml")
                                              if meta.get("profile") else None)
                if ev:
                    ledger = Ledger.load(ev if os.path.isabs(ev) else
                                         os.path.join(os.path.dirname(os.path.abspath(a.target)), ev))
            profs, _ = library()
            if a.chat:          # a chat reply: voice, offer and figure guards; the label only for a reading
                return 1 if _st_print(st.check_chat(text, ledger, profs, os.path.basename(a.target))) else 0
            against = [(os.path.basename(p), open(p, encoding="utf-8").read()) for p in (a.against or [])]
            br = a.base_read or os.path.join(os.path.dirname(os.path.abspath(a.target)), "base-read.yaml")
            base = st.load_yaml(br) if os.path.isfile(br) else None
            if a.base_read and base is None:
                print(f"  ERROR   base read not found: {a.base_read}")
                return 1
            issues = st.check_document(text, ledger, profs, against, os.path.basename(a.target),
                                       base if isinstance(base, dict) else None,
                                       allow_no_base=a.no_base_read, allow_no_ledger=a.no_ledger)
            return 1 if _st_print(issues) else 0
        if a.action == "session":
            if not need("a session YAML file"):
                return 1
            profs, _ = library()
            if a.target.lower().endswith((".md", ".markdown")):      # a saved queue document with question wording
                with open(a.target, encoding="utf-8") as f:
                    return 1 if _st_print(st.check_queue_document(f.read(), profs, os.path.basename(a.target))) else 0
            return 1 if _st_print(st.validate_session(st.load_yaml(a.target), profs)) else 0
        if a.action == "record":
            if not need("a session YAML file") or not a.profile:
                print("  ERROR   record needs SESSION.yaml and --profile PROFILE_DIR")
                return 1
            profs, _ = library()
            added = st.record(a.target, a.profile, a.confirmed, a.today, profs)
            print(f"ledger: recorded {len(added)} new founder-provided entr{'y' if len(added) == 1 else 'ies'}"
                  + (f" ({', '.join(added)})" if added else " (nothing new)"))
            return 0
    except (ValueError, OSError) as e:
        print(f"  ERROR   {e}")
        return 1
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
    sp = sub.add_parser("gtm", help="go-to-market: analyze spec | kpi workbook | check strategy claims")
    sp.add_argument("action", choices=["analyze", "kpi", "check"])
    sp.add_argument("file", help="GTM spec YAML (analyze, kpi) or strategy Markdown (check)")
    sp.add_argument("--out")
    sp.add_argument("--profile", help="check: profile directory whose ledger resolves citations")
    sp.add_argument("--weeks", type=int, default=26, help="kpi: weeks in the tracker")
    sp.set_defaults(fn=cmd_gtm)
    sp = sub.add_parser("discovery", help="customer discovery: analyze | interviews | hypotheses | experiment | "
                                          "report | check")
    sp.add_argument("action", choices=["analyze", "interviews", "hypotheses", "experiment", "report", "check"])
    sp.add_argument("file", help="discovery spec YAML (check: a Markdown document or interview guide)")
    sp.add_argument("--out")
    sp.add_argument("--record", action="store_true", help="analyze: append ledger entries for unrecorded "
                                                          "interviews and surveys (never edits existing entries)")
    sp.add_argument("--segment", help="interviews: one segment id")
    sp.add_argument("--xlsx", action="store_true", help="hypotheses: also write an XLSX register")
    sp.add_argument("--id", help="experiment: one experiment id")
    sp.add_argument("--sections", help="report: comma-separated subset, e.g. problems,wtp,psf")
    sp.add_argument("--spec", help="check: discovery spec whose notes verify quotations and counts")
    sp.add_argument("--profile", help="check: profile directory whose ledger resolves citations")
    sp.set_defaults(fn=cmd_discovery)
    sp = sub.add_parser("business-model", help="business model: design | analyze | canvas | value-proposition | "
                                               "compare | revenue | costs | marketplace | assumptions | "
                                               "stress-test | report | check")
    sp.add_argument("action", choices=["design", "analyze", "canvas", "value-proposition", "compare", "revenue",
                                       "costs", "marketplace", "assumptions", "stress-test", "report", "check"])
    sp.add_argument("file", help="business model spec YAML (design: a profile directory or spec; check: a Markdown "
                                 "document)")
    sp.add_argument("--out")
    sp.add_argument("--record", action="store_true", help="assumptions: append untested assumptions to the ledger "
                                                          "(append-only, idempotent)")
    sp.add_argument("--model", help="canvas: an alternative's own canvas; compare/report: one alternative")
    sp.add_argument("--segment", help="value-proposition/report: one segment id")
    sp.add_argument("--format", choices=["md", "json"], default="md")
    sp.add_argument("--sections", help="report: comma-separated subset, e.g. canvas,revenue,stress")
    sp.add_argument("--xlsx", action="store_true", help="also write the business model workbook")
    sp.add_argument("--discovery", help="design: customer discovery spec to read segments and hypotheses from")
    sp.add_argument("--spec", help="check: business model spec that supplies geography and the ledger")
    sp.add_argument("--profile", help="check: profile directory whose ledger resolves citations")
    sp.set_defaults(fn=cmd_business_model)
    sp = sub.add_parser("shark-tank", help="investor simulation: profiles | context | base-read | queue | check | "
                                           "session | record")
    sp.add_argument("action", choices=["profiles", "context", "base-read", "queue", "check", "session", "record"])
    sp.add_argument("target", nargs="?", help="context: profile directory; base-read/queue: base-read YAML; "
                                              "check: Markdown document; session: session YAML or a queue document "
                                              "(.md); record: session YAML")
    sp.add_argument("--library", action="append", default=[], help="extra investor library directory (repeatable)")
    sp.add_argument("--no-shipped", action="store_true", help="do not load the shipped investor library")
    sp.add_argument("--today", help="date that drives staleness rules (YYYY-MM-DD; default: today)")
    sp.add_argument("--json", action="store_true")
    sp.add_argument("--id", help="profiles: show one profile's lenses and emphasis")
    sp.add_argument("--profile", help="startup profile directory whose evidence.yaml is used")
    sp.add_argument("--out", help="base-read: write the rendered Markdown here")
    sp.add_argument("--investors", help="queue: comma-separated profile ids")
    sp.add_argument("--budget", type=int, default=10, help="queue: number of questions (default 10)")
    sp.add_argument("--against", action="append", default=[], help="check: other evaluation or panel documents "
                                                                    "for pairwise checks (repeatable)")
    sp.add_argument("--confirmed", action="store_true", help="record: the founder agreed to record the facts")
    sp.add_argument("--base-read", help="check: base-read YAML for the stance rule (default: base-read.yaml beside "
                                        "the document)")
    sp.add_argument("--no-base-read", action="store_true", help="check: accept a weaker check without a base read "
                                                                "(a counted warning instead of an error)")
    sp.add_argument("--no-ledger", action="store_true", help="check: accept a weaker check without a ledger (a "
                                                             "counted warning instead of an error)")
    sp.add_argument("--chat", action="store_true", help="check: the file is a chat reply, not a document (the "
                                                        "label is required only for an investor-specific reading)")
    sp.set_defaults(fn=cmd_shark_tank)
    sub.add_parser("themes", help="list design themes").set_defaults(fn=cmd_themes)
    a = p.parse_args(argv)
    return a.fn(a) or 0


if __name__ == "__main__":
    sys.exit(main())
