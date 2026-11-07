"""Validate generated artifacts by re-opening them with independent readers.

Checks are deliberately about *integrity and honesty*, not taste:
files open, metadata is set, nothing spills off the page, no placeholder
or lorem text ships, formulas are not broken, PDFs have extractable text.
``previews`` renders PDF pages to PNG contact sheets for visual review.
"""
from __future__ import annotations

import glob
import os
import re
import shutil
import subprocess
import tempfile
from typing import Dict, List

PLACEHOLDER = re.compile(r"lorem ipsum|\bTODO\b|\bTBD\b|\[insert|\{\{|\}\}|XXX|\[Amount TBD\]|Screenshot needed", re.I)


def _res(kind, path):
    return {"file": path, "type": kind, "ok": True, "errors": [], "warnings": [], "info": {}}


def check_pptx(path: str) -> Dict:
    from pptx import Presentation
    from pptx.util import Emu
    r = _res("pptx", path)
    try:
        prs = Presentation(path)
    except Exception as e:
        r["ok"] = False
        r["errors"].append(f"cannot open: {e}")
        return r
    sw, sh = prs.slide_width, prs.slide_height
    r["info"]["slides"] = len(prs.slides)
    r["info"]["title"] = prs.core_properties.title
    if not prs.core_properties.title:
        r["warnings"].append("core properties: title not set")
    notes_missing, placeholders, offslide = [], [], []
    tol = Emu(9144 * 4)  # 0.04in tolerance
    for i, slide in enumerate(prs.slides, 1):
        if not (slide.has_notes_slide and slide.notes_slide.notes_text_frame.text.strip()):
            notes_missing.append(i)
        for shp in slide.shapes:
            if shp.left is not None and (shp.left < -tol or shp.top < -tol or shp.left + shp.width > sw + tol
                                         or shp.top + shp.height > sh + tol):
                offslide.append(f"slide {i}: '{shp.name}' extends beyond slide")
            if shp.has_text_frame and PLACEHOLDER.search(shp.text_frame.text):
                placeholders.append(f"slide {i}: '{shp.text_frame.text.strip()[:50]}'")
    if offslide:
        r["errors"] += offslide
    if placeholders:
        r["warnings"].append("placeholder text present (resolve before sending): " + "; ".join(placeholders[:8]))
    if notes_missing:
        r["warnings"].append(f"slides without speaker notes: {notes_missing}")
    r["ok"] = not r["errors"]
    return r


def check_docx(path: str) -> Dict:
    import docx
    r = _res("docx", path)
    try:
        d = docx.Document(path)
    except Exception as e:
        r["ok"] = False
        r["errors"].append(f"cannot open: {e}")
        return r
    heads = [p for p in d.paragraphs if p.style.name.startswith("Heading")]
    text = "\n".join(p.text for p in d.paragraphs)
    r["info"].update(paragraphs=len(d.paragraphs), headings=len(heads), tables=len(d.tables),
                     words=len(text.split()), title=d.core_properties.title,
                     images=len(d.inline_shapes))
    if not d.core_properties.title:
        r["warnings"].append("core properties: title not set")
    m = PLACEHOLDER.findall(text)
    if m:
        r["warnings"].append(f"placeholder text present: {sorted(set(m))[:6]}")
    footer_xml = "".join(s.footer._element.xml for s in d.sections)
    if "PAGE" not in footer_xml:
        r["warnings"].append("no page-number field in footer")
    r["ok"] = not r["errors"]
    return r


def check_pdf(path: str) -> Dict:
    from pypdf import PdfReader
    r = _res("pdf", path)
    try:
        rd = PdfReader(path)
    except Exception as e:
        r["ok"] = False
        r["errors"].append(f"cannot open: {e}")
        return r
    n = len(rd.pages)
    r["info"]["pages"] = n
    meta = rd.metadata or {}
    r["info"]["title"] = meta.get("/Title")
    if not meta.get("/Title"):
        r["warnings"].append("metadata: title not set")
    text = ""
    for p in rd.pages[: min(n, 60)]:
        try:
            text += p.extract_text() or ""
        except Exception:
            pass
    r["info"]["chars"] = len(text)
    if n and len(text) < 50 * min(n, 60) * 0.2:
        r["warnings"].append("little extractable text; is text rasterised?")
    m = PLACEHOLDER.findall(text)
    if m:
        r["warnings"].append(f"placeholder text present: {sorted(set(m))[:6]}")
    fonts = set()
    for p in rd.pages[:5]:
        res = p.get("/Resources") or {}
        f = res.get("/Font") or {}
        for k in f:
            try:
                fonts.add(str(f[k].get_object().get("/BaseFont")))
            except Exception:
                pass
    r["info"]["fonts"] = sorted(fonts)
    r["ok"] = not r["errors"]
    return r


def check_xlsx(path: str) -> Dict:
    import openpyxl
    r = _res("xlsx", path)
    try:
        wb = openpyxl.load_workbook(path)
    except Exception as e:
        r["ok"] = False
        r["errors"].append(f"cannot open: {e}")
        return r
    r["info"]["sheets"] = wb.sheetnames
    nform = 0
    bad = []
    for ws in wb.worksheets:
        for row in ws.iter_rows():
            for c in row:
                if isinstance(c.value, str) and c.value.startswith("="):
                    nform += 1
                    if "#REF!" in c.value:
                        bad.append(f"{ws.title}!{c.coordinate}")
    r["info"]["formulas"] = nform
    if bad:
        r["errors"].append(f"broken references: {bad[:10]}")
    # optional full recalculation
    try:
        import formulas  # type: ignore
        xl = formulas.ExcelModel().loads(path).finish()
        sol = xl.calculate()
        errs = [k for k, v in sol.items() if hasattr(v, "value") and any(
            str(x).startswith("#") for x in getattr(v.value, "flat", [v.value]) if isinstance(x, str))]
        if errs:
            r["errors"].append(f"formula errors after recalculation: {errs[:10]}")
        r["info"]["recalculated"] = True
    except ImportError:
        r["info"]["recalculated"] = False
    except Exception as e:  # recalculation engine limits are not file errors
        r["warnings"].append(f"recalculation skipped: {str(e)[:120]}")
    r["ok"] = not r["errors"]
    return r


def check_md(path: str) -> Dict:
    r = _res("md", path)
    with open(path) as f:
        text = f.read()
    r["info"]["words"] = len(text.split())
    m = PLACEHOLDER.findall(text)
    if m:
        r["warnings"].append(f"placeholder text present: {sorted(set(m))[:6]}")
    return r


CHECKERS = {".pptx": check_pptx, ".docx": check_docx, ".pdf": check_pdf, ".xlsx": check_xlsx, ".md": check_md}


def check(path: str) -> Dict:
    ext = os.path.splitext(path)[1].lower()
    if ext not in CHECKERS:
        return {"file": path, "type": ext, "ok": False, "errors": ["unsupported type"], "warnings": [], "info": {}}
    return CHECKERS[ext](path)


def previews(pdf_path: str, out_dir: str, dpi: int = 60, per_sheet: int = 8, cols: int = 2) -> List[str]:
    """Render PDF pages and tile them into contact sheets.  Needs poppler's pdftoppm."""
    if not shutil.which("pdftoppm"):
        raise RuntimeError("pdftoppm not found (install poppler) – cannot render previews")
    from PIL import Image
    os.makedirs(out_dir, exist_ok=True)
    stem = os.path.splitext(os.path.basename(pdf_path))[0]
    with tempfile.TemporaryDirectory() as tmp:
        subprocess.run(["pdftoppm", "-r", str(dpi), "-png", pdf_path, os.path.join(tmp, "p")], check=True)
        pages = sorted(glob.glob(os.path.join(tmp, "p-*.png")))
        ims = [Image.open(p).convert("RGB") for p in pages]
        sheets = []
        for s in range(0, len(ims), per_sheet):
            sub = ims[s:s + per_sheet]
            w = max(i.size[0] for i in sub)
            h = max(i.size[1] for i in sub)
            rows = (len(sub) + cols - 1) // cols
            sheet = Image.new("RGB", (cols * w + (cols + 1) * 10, rows * h + (rows + 1) * 10), (110, 110, 110))
            for i, im in enumerate(sub):
                sheet.paste(im, (10 + (i % cols) * (w + 10), 10 + (i // cols) * (h + 10)))
            p = os.path.join(out_dir, f"{stem}-preview-{s // per_sheet + 1}.png")
            sheet.save(p)
            sheets.append(p)
    return sheets
