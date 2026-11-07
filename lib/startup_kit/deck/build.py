"""Build a deck spec (YAML) into PPTX + PDF + narrative/notes Markdown + build report."""
from __future__ import annotations

import json
import os
from typing import Dict, List, Optional

import yaml

from ..evidence import Ledger
from ..render.pdf_canvas import PdfCanvas
from ..render.pptx_canvas import PptxCanvas
from ..theme import get_theme, load_theme_file
from .layouts import LAYOUTS, Ctx, H, W, _ids, slide_numeric_warnings

STAGE_SLIDES = {"idea": (6, 10), "pre-seed": (8, 12), "seed": (10, 15), "series-a": (12, 20), "growth": (12, 22)}
WORD_LIMIT = 70


def load_spec(path: str) -> Dict:
    with open(path) as f:
        spec = yaml.safe_load(f) or {}
    if "slides" not in spec:
        raise ValueError("deck spec needs a 'slides' list")
    return spec


def _resolve_ledger(spec: Dict, base: str) -> Ledger:
    d = spec.get("deck", {})
    p = d.get("evidence")
    if not p and d.get("profile"):
        p = os.path.join(d["profile"], "evidence.yaml")
    if not p:
        return Ledger([])
    p = p if os.path.isabs(p) else os.path.join(base, p)
    return Ledger.load(p)


def _resolve_theme(spec: Dict, base: str):
    d = spec.get("deck", {})
    tf = d.get("theme_file")
    if tf:
        theme = load_theme_file(tf if os.path.isabs(tf) else os.path.join(base, tf), d.get("theme", "venture"))
    else:
        theme = get_theme(d.get("theme", d.get("audience", "venture")), d.get("brand"))
    if d.get("brand", {}).get("logo") and not os.path.isabs(d["brand"]["logo"]):
        theme.logo = os.path.join(base, d["brand"]["logo"])
    return theme


def _words(s: Dict) -> int:
    n = 0
    for k, v in s.items():
        if k in ("notes", "type", "id", "evidence", "source", "image", "_ids", "kicker", "short"):
            continue
        if isinstance(v, str):
            n += len(v.split())
        elif isinstance(v, list):
            for it in v:
                if isinstance(it, dict):
                    n += sum(len(str(x).split()) for kk, x in it.items() if kk not in ("evidence", "status", "values"))
                elif isinstance(it, str):
                    n += len(it.split())
    return n


def yaml_lint(slides: List[Dict]) -> List[Dict]:
    """Catch the classic YAML trap: unquoted commas inside {flow: mappings} create keys with no value."""
    issues = []

    def walk(obj, n, path):
        if isinstance(obj, dict):
            for k, v in obj.items():
                if v is None and k not in ("evidence", "notes", "source", "image", "status"):
                    issues.append({"level": "error", "slide": n, "id": "yaml",
                                   "message": f"'{path}{k}' has no value; text containing a comma must be quoted "
                                              "(e.g. detail: \"bank, eSewa, Khalti\")"})
                walk(v, n, f"{path}{k}.")
        elif isinstance(obj, list):
            for i, v in enumerate(obj):
                walk(v, n, f"{path}{i}.")
    for n, s in enumerate(slides, 1):
        walk(s, n, "")
    return issues


def _select(slides: List[Dict], variant: Optional[str]) -> List[Dict]:
    if not variant or variant == "full":
        return [s for s in slides if not s.get("only")]
    return [s for s in slides if variant in (s.get("variants") or []) or s.get("only") == variant
            or (variant == "short" and s.get("short"))]


def render(spec: Dict, base: str, canvas, record: bool, ledger: Ledger, theme, slides: List[Dict]) -> Ctx:
    d = spec.get("deck", {})
    ctx = Ctx(canvas, theme, ledger, d, base, record)
    total = len(slides)
    for i, s in enumerate(slides, 1):
        ctx.slide_no = i
        ctx.slide_id = s.get("id", s.get("type", ""))
        ctx.badges_on_slide = set()
        kind = s.get("type")
        canvas.new_page(theme.paper)
        if kind not in LAYOUTS:
            ctx.issue("error", f"unknown slide type '{kind}'. Available: {', '.join(sorted(LAYOUTS))}")
            continue
        if kind == "sources":
            s = {**s, "_ids": list(ctx.cited)}
        LAYOUTS[kind](ctx, s, total)
        canvas.notes(s.get("notes", ""))
        if record:
            if not s.get("notes") and kind not in ("sources", "section"):
                ctx.issue("warning", "no speaker notes")
            nums = slide_numeric_warnings(s)
            if nums:
                ctx.issue("warning", f"numbers without evidence: {', '.join(sorted(set(nums))[:6])}")
            wc = _words(s)
            if wc > (WORD_LIMIT + 40 if kind == "diagram" else WORD_LIMIT):  # diagrams are labels, not prose
                ctx.issue("warning", f"{wc} words on slide (> {WORD_LIMIT}); move detail to notes or appendix")
    return ctx


def build(spec_path: str, out_dir: Optional[str] = None, variant: Optional[str] = None,
          formats=("pptx", "pdf")) -> Dict:
    spec = load_spec(spec_path)
    base = os.path.dirname(os.path.abspath(spec_path))
    d = spec.get("deck", {})
    out_dir = out_dir or base
    os.makedirs(out_dir, exist_ok=True)
    stem = d.get("filename") or os.path.splitext(os.path.basename(spec_path))[0]
    if variant and variant != "full":
        stem += f"-{variant}"
    ledger = _resolve_ledger(spec, base)
    theme = _resolve_theme(spec, base)
    slides = _select(spec["slides"], variant)
    title = f"{d.get('company', '')} — {d.get('title', 'Investor presentation')}".strip(" —")
    author = d.get("author", d.get("company", ""))
    outputs = {}
    ctx = None
    if "pptx" in formats:
        pc = PptxCanvas(W, H, title=title, author=author, subject=d.get("stage", ""))
        ctx = render(spec, base, pc, True, ledger, theme, slides)
        outputs["pptx"] = os.path.join(out_dir, stem + ".pptx")
        pc.save(outputs["pptx"])
    if "pdf" in formats:
        pdf = PdfCanvas(W, H, title=title, author=author, subject=d.get("stage", ""))
        outputs["pdf"] = os.path.join(out_dir, stem + ".pdf")
        pdf.begin(outputs["pdf"])
        c2 = render(spec, base, pdf, ctx is None, ledger, theme, slides)
        ctx = ctx or c2
        pdf.save()
    ctx.issues.extend(yaml_lint(slides))
    # deck-level checks
    stage = d.get("stage")
    if stage in STAGE_SLIDES and (not variant or variant == "full"):
        lo, hi = STAGE_SLIDES[stage]
        content = [s for s in slides if s.get("type") not in ("sources",)]
        if not lo <= len(content) <= hi:
            ctx.issues.append({"level": "info", "slide": 0, "id": "deck",
                               "message": f"{len(content)} slides; {stage} decks usually run {lo}–{hi}"})
    for w in theme.check():
        ctx.issues.append({"level": "warning", "slide": 0, "id": "theme", "message": w})
    for i in ledger.validate():
        if i.level == "error":
            ctx.issues.append({"level": "error", "slide": 0, "id": "ledger", "message": str(i)})
    outputs["notes"] = os.path.join(out_dir, stem + "-narrative.md")
    with open(outputs["notes"], "w") as f:
        f.write(narrative_md(spec, slides, ledger, ctx))
    report = {"spec": os.path.abspath(spec_path), "variant": variant or "full", "slides": len(slides),
              "outputs": outputs, "issues": ctx.issues, "missing": ctx.missing, "cited": ctx.cited,
              "errors": sum(1 for i in ctx.issues if i["level"] == "error"),
              "warnings": sum(1 for i in ctx.issues if i["level"] == "warning")}
    outputs["report"] = os.path.join(out_dir, stem + "-build-report.json")
    with open(outputs["report"], "w") as f:
        json.dump(report, f, indent=2)
    return report


def narrative_md(spec: Dict, slides: List[Dict], ledger: Ledger, ctx: Ctx) -> str:
    d = spec.get("deck", {})
    L = [f"# {d.get('company', '')}: slide-by-slide narrative and speaker notes", "",
         f"Stage: {d.get('stage', 'n/a')} · Audience: {d.get('audience', d.get('theme', 'venture'))} · "
         f"Slides: {len(slides)}", ""]
    for i, s in enumerate(slides, 1):
        head = s.get("title") or s.get("text") or s.get("kicker") or s.get("type")
        L += [f"## {i}. {s.get('kicker', s.get('type', '')).title()}: {head}", ""]
        if s.get("purpose"):
            L += [f"**Purpose in the story:** {s['purpose']}", ""]
        if s.get("notes"):
            L += ["**Speaker notes:**", "", s["notes"].strip(), ""]
        ids = _ids(s.get("evidence"))
        for k in ("points", "items", "layers", "people"):
            for it in s.get(k, []) or []:
                if isinstance(it, dict):
                    ids += _ids(it.get("evidence"))
        if isinstance(s.get("chart"), dict):
            ids += _ids(s["chart"].get("evidence"))
        if ids:
            L += ["**Evidence:** " + "; ".join(
                f"{e} ({ledger.get(e).status})" if ledger.get(e) else f"{e} (MISSING)" for e in dict.fromkeys(ids)), ""]
        issues = [x for x in ctx.issues if x["slide"] == i]
        if issues:
            L += ["**Build issues:**", ""] + [f"- {x['level']}: {x['message']}" for x in issues] + [""]
    if ctx.missing:
        L += ["## Missing information", ""] + [f"- [ ] {m}" for m in ctx.missing] + [""]
    return "\n".join(L)
