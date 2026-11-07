"""Font registration and text measurement shared by all renderers.

Measurement uses reportlab metrics.  When the system has the real TrueType
file (Arial, Georgia) we register and embed it so PDF output matches what
PowerPoint/Word will draw; otherwise we fall back to PDF core fonts whose
metrics are very close (Helvetica ~ Arial, Times ~ Georgia is narrower, so we
add a safety factor when Georgia is unavailable).
"""
from __future__ import annotations

import os
from typing import Dict, List, Tuple

from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

_SEARCH_DIRS = [
    "/System/Library/Fonts/Supplemental", "/System/Library/Fonts", "/Library/Fonts",
    os.path.expanduser("~/Library/Fonts"), "/usr/share/fonts/truetype/msttcorefonts",
    "/usr/share/fonts/truetype", "/usr/share/fonts", "C:/Windows/Fonts",
]

_FILES = {
    "Arial": {"regular": ["Arial.ttf", "arial.ttf"], "bold": ["Arial Bold.ttf", "arialbd.ttf"],
              "italic": ["Arial Italic.ttf", "ariali.ttf"], "bolditalic": ["Arial Bold Italic.ttf", "arialbi.ttf"]},
    "Georgia": {"regular": ["Georgia.ttf", "georgia.ttf"], "bold": ["Georgia Bold.ttf", "georgiab.ttf"],
                "italic": ["Georgia Italic.ttf", "georgiai.ttf"], "bolditalic": ["Georgia Bold Italic.ttf", "georgiaz.ttf"]},
    "Courier New": {"regular": ["Courier New.ttf", "cour.ttf"], "bold": ["Courier New Bold.ttf", "courbd.ttf"],
                    "italic": ["Courier New Italic.ttf", "couri.ttf"], "bolditalic": ["Courier New Bold Italic.ttf", "courbi.ttf"]},
}

_FALLBACK = {
    "Arial": ("Helvetica", "Helvetica-Bold", "Helvetica-Oblique", "Helvetica-BoldOblique", 1.0),
    "Georgia": ("Times-Roman", "Times-Bold", "Times-Italic", "Times-BoldItalic", 1.12),
    "Courier New": ("Courier", "Courier-Bold", "Courier-Oblique", "Courier-BoldOblique", 1.0),
}

_registered: Dict[str, Tuple[str, str, str, str, float]] = {}


def _find(names: List[str]):
    for d in _SEARCH_DIRS:
        for n in names:
            p = os.path.join(d, n)
            if os.path.exists(p):
                return p
    return None


def register(family: str) -> Tuple[str, str, str, str, float]:
    """Return reportlab font names (regular, bold, italic, bolditalic, width_factor)."""
    if family in _registered:
        return _registered[family]
    files = _FILES.get(family)
    result = None
    if files and os.environ.get("STARTUP_KIT_CORE_FONTS") != "1":
        paths = {k: _find(v) for k, v in files.items()}
        if paths["regular"]:
            names = []
            for style in ("regular", "bold", "italic", "bolditalic"):
                p = paths[style] or paths["regular"]
                fname = f"{family.replace(' ', '')}-{style}"
                try:
                    pdfmetrics.registerFont(TTFont(fname, p))
                except Exception:
                    fname = None
                names.append(fname)
            if all(names):
                pdfmetrics.registerFontFamily(names[0], normal=names[0], bold=names[1], italic=names[2],
                                              boldItalic=names[3])
                result = (names[0], names[1], names[2], names[3], 1.0)
    if result is None:
        result = _FALLBACK.get(family, _FALLBACK["Arial"])
    _registered[family] = result
    return result


def pdf_font(family: str, bold: bool = False, italic: bool = False) -> str:
    r, b, i, bi, _ = register(family)
    if bold and italic:
        return bi
    if bold:
        return b
    if italic:
        return i
    return r


def width(text: str, family: str, size: float, bold: bool = False) -> float:
    """Width in points."""
    *_, factor = register(family)
    return pdfmetrics.stringWidth(text, pdf_font(family, bold), size) * factor


def wrap(text: str, family: str, size: float, max_width_pt: float, bold: bool = False) -> List[str]:
    """Greedy word wrap respecting explicit newlines."""
    lines: List[str] = []
    for para in str(text).split("\n"):
        words = para.split(" ")
        cur = ""
        for w in words:
            trial = (cur + " " + w).strip() if cur else w
            if width(trial, family, size, bold) <= max_width_pt or not cur:
                cur = trial
            else:
                lines.append(cur)
                cur = w
            # hard-break an over-long token (URLs, paths) wherever it lands
            while width(cur, family, size, bold) > max_width_pt and len(cur) > 1:
                cut = len(cur)
                while cut > 1 and width(cur[:cut], family, size, bold) > max_width_pt:
                    cut -= 1
                lines.append(cur[:cut])
                cur = cur[cut:]
        lines.append(cur)
    return lines


def fit(text: str, family: str, max_size: float, min_size: float, box_w_in: float, box_h_in: float,
        bold: bool = False, leading: float = 1.18):
    """Largest size in [min,max] at which text fits the box.

    Returns (size, lines, fits).  ``fits`` False means even min_size overflows;
    renderers draw anyway and the validator reports an overflow error.
    """
    size = max_size
    while True:
        lines = wrap(text, family, size, box_w_in * 72, bold)
        height = len(lines) * size * leading
        if height <= box_h_in * 72 + 0.5:
            return size, lines, True
        if size <= min_size:
            return size, lines, False
        size = max(min_size, round(size - 0.5, 2))
