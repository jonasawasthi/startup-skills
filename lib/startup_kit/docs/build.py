"""Build a Markdown+ document into DOCX, PDF and normalised Markdown.

Front matter keys (all optional unless noted):
  title (required), subtitle, company, author, date, version, doc_type, doc_type_label,
  audience / theme, theme_file, brand, paper (a4|letter), confidentiality,
  prepared_for, submitted_to, submitted_by, reference, disclaimer, logo,
  profile (path to startup-profile) or evidence (path to evidence.yaml),
  toc (bool, default true for >= 6 H1/H2 headings), cover (bool, default true),
  references (bool, default true: append cited-evidence table)
"""
from __future__ import annotations

import json
import os
import tempfile
from typing import Dict, List, Optional

from ..evidence import Ledger
from ..theme import get_theme, load_theme_file
from .charts import render_chart, validate_chart
from .markdown import Block, all_citations, headings, inline, parse, plain

DOC_TYPE_THEME = {"investor-proposal": "venture", "proposal": "venture", "partnership-proposal": "corporate",
                  "accelerator-application": "accelerator", "grant-proposal": "institutional",
                  "government-proposal": "institutional", "corporate-proposal": "corporate",
                  "business-plan": "internal", "internal-plan": "internal", "analysis": "venture",
                  "research-report": "venture", "memo": "internal", "fundraising-plan": "venture"}


def _theme(meta: Dict, base: str):
    if meta.get("theme_file"):
        p = meta["theme_file"]
        return load_theme_file(p if os.path.isabs(p) else os.path.join(base, p))
    name = meta.get("theme") or meta.get("audience") or DOC_TYPE_THEME.get(str(meta.get("doc_type", "")), "venture")
    return get_theme(name, meta.get("brand"))


def _ledger(meta: Dict, base: str) -> Optional[Ledger]:
    p = meta.get("evidence") or (os.path.join(meta["profile"], "evidence.yaml") if meta.get("profile") else None)
    if not p:
        return None
    p = p if os.path.isabs(p) else os.path.join(base, p)
    return Ledger.load(p)


def references_blocks(ledger: Ledger, ids: List[str]) -> List[Block]:
    blocks = [Block("heading", level=1, runs=inline("Sources and evidence")),
              Block("para", runs=inline("Every claim marked with an evidence ID in this document is listed below with "
                                        "its verification status. *Verified* claims are backed by a primary source or "
                                        "the codebase; *reported* claims come from the company; *estimates* and "
                                        "*assumptions* are planning inputs that have not been validated."))]
    rows = []
    for eid in ids:
        e = ledger.get(eid)
        if e:
            rows.append([inline(e.id), inline(e.claim), inline(e.status), inline(e.citation())])
    if rows:
        blocks.append(Block("table", header=[inline("ID"), inline("Claim"), inline("Status"), inline("Source")],
                            rows=rows, align=["left"] * 4))
    return blocks


def build(md_path: str, out_dir: Optional[str] = None, formats=("docx", "pdf", "md")) -> Dict:
    with open(md_path) as f:
        src = f.read()
    meta, blocks = parse(src)
    base = os.path.dirname(os.path.abspath(md_path))
    out_dir = out_dir or base
    os.makedirs(out_dir, exist_ok=True)
    stem = meta.get("filename") or os.path.splitext(os.path.basename(md_path))[0]
    theme = _theme(meta, base)
    ledger = _ledger(meta, base)
    issues: List[Dict] = []
    if not meta.get("title"):
        issues.append({"level": "error", "message": "front matter needs a title"})
    # evidence checks on prose
    cited = all_citations(blocks)
    if ledger is not None:
        for i in ledger.check_text(src, os.path.basename(md_path)):
            issues.append({"level": i.level, "message": str(i)})
    elif cited:
        issues.append({"level": "error", "message": f"document cites {len(cited)} evidence IDs but no ledger is "
                                                    "configured (set 'profile' or 'evidence' in front matter)"})
    if meta.get("references", True) and ledger is not None and cited:
        blocks = blocks + references_blocks(ledger, cited)
    toc_entries = headings(blocks, 2)
    want_toc = meta.get("toc", sum(1 for l, _ in toc_entries if l == 1) >= 6)
    want_cover = meta.get("cover", True)
    outputs = {}
    with tempfile.TemporaryDirectory() as tmp:
        # pre-render charts once
        chart_png = {}
        for n, b in enumerate(blocks):
            if b.kind == "chart":
                errs = validate_chart(b.data)
                if errs:
                    chart_png[n] = (None, errs)
                    for e in errs:
                        issues.append({"level": "error", "message": f"chart '{b.data.get('title', n)}': {e}"})
                else:
                    chart_png[n] = (render_chart(b.data, theme, os.path.join(tmp, f"chart{n}.png")), [])
        renderers = []
        if "docx" in formats:
            from .docx_render import DocxRenderer
            renderers.append(("docx", DocxRenderer(meta, theme, ledger, base, tmp)))
        if "pdf" in formats:
            from .pdf_render import PdfRenderer
            renderers.append(("pdf", PdfRenderer(meta, theme, ledger, base, tmp)))
        for fmt, r in renderers:
            if want_cover:
                r.cover()
            if want_toc and not any(b.kind == "toc" for b in blocks):
                r.toc(toc_entries)
            for n, b in enumerate(blocks):
                k = b.kind
                if k == "heading":
                    r.heading(b)
                elif k == "para":
                    r.para(b)
                elif k == "list":
                    r.lst(b)
                elif k == "table":
                    r.table(b)
                elif k == "callout":
                    r.callout(b)
                elif k == "code":
                    r.code(b)
                elif k == "chart":
                    png, errs = chart_png[n]
                    r.chart(b, png, errs)
                elif k == "image":
                    p = b.path if os.path.isabs(b.path) else os.path.join(base, b.path)
                    r.image(p, b.caption)
                elif k == "hr":
                    r.hr()
                elif k == "pagebreak":
                    r.pagebreak()
                elif k == "toc":
                    r.toc(toc_entries)
            outputs[fmt] = os.path.join(out_dir, f"{stem}.{fmt}")
            r.finish(outputs[fmt])
            for msg in sorted(set(r.issues)):
                if not any(msg in i["message"] for i in issues):
                    issues.append({"level": "error" if "not found" in msg else "warning", "message": msg})
    if "md" in formats:
        outputs["md"] = os.path.join(out_dir, f"{stem}.md")
        if os.path.abspath(outputs["md"]) == os.path.abspath(md_path):
            outputs["md"] = os.path.join(out_dir, f"{stem}.final.md")
        with open(outputs["md"], "w") as f:
            body = src
            if meta.get("references", True) and ledger is not None and cited:
                body = body.rstrip() + "\n\n# Sources and evidence\n\n" + ledger.bibliography_md(cited)
            f.write(body)
    report = {"source": os.path.abspath(md_path), "outputs": outputs, "issues": issues, "cited": cited,
              "theme": theme.name, "errors": sum(1 for i in issues if i["level"] == "error"),
              "warnings": sum(1 for i in issues if i["level"] == "warning")}
    with open(os.path.join(out_dir, f"{stem}-build-report.json"), "w") as f:
        json.dump(report, f, indent=2)
    return report
