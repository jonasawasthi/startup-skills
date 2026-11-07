"""Abstract drawing surface shared by the PPTX and PDF slide renderers.

Coordinates are inches from the top-left of the slide.  Layout code calls
these primitives; each backend implements them.  Text fitting happens *before*
drawing (``fit_text``) so both backends receive the same font size and the
same overflow verdict.
"""
from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Sequence

from .. import fonts


@dataclass
class TextStyle:
    font: str = "Arial"
    size: float = 14
    color: str = "#14171A"
    bold: bool = False
    italic: bool = False
    align: str = "left"      # left | center | right
    valign: str = "top"      # top | middle | bottom
    leading: float = 1.18
    min_size: Optional[float] = None   # allow shrinking down to this size
    caps: bool = False
    tracking: float = 0      # letter spacing in pt (pptx only; cosmetic)

    def with_(self, **kw) -> "TextStyle":
        d = dict(self.__dict__)
        d.update(kw)
        return TextStyle(**d)


@dataclass
class FitResult:
    size: float
    lines: List[str]
    fits: bool
    height_in: float


def fit_text(text: str, style: TextStyle, w: float, h: float) -> FitResult:
    t = text.upper() if style.caps else text
    size, lines, ok = fonts.fit(t, style.font, style.size, style.min_size or style.size, w, h, style.bold,
                                style.leading)
    return FitResult(size, lines, ok, len(lines) * size * style.leading / 72)


def text_height(text: str, style: TextStyle, w: float) -> float:
    """Height in inches the text needs at style.size within width w."""
    t = text.upper() if style.caps else text
    lines = fonts.wrap(t, style.font, style.size, w * 72, style.bold)
    return len(lines) * style.size * style.leading / 72


def nice_max(v: float) -> float:
    if v <= 0:
        return 1
    exp = math.floor(math.log10(v))
    f = v / 10 ** exp
    for n in (1, 1.2, 1.5, 2, 2.5, 3, 4, 5, 6, 8, 10):
        if f <= n:
            return n * 10 ** exp
    return 10 ** (exp + 1)


def format_value(v: float, fmt: str = "number", prefix: str = "", suffix: str = "") -> str:
    if v is None:
        return ""
    if fmt == "percent":
        s = f"{v * 100:.0f}%" if abs(v) <= 1.5 else f"{v:.0f}%"
    elif fmt in ("currency", "compact", "number"):
        a = abs(v)
        if a >= 1e9:
            s = f"{v / 1e9:.1f}B"
        elif a >= 1e6:
            s = f"{v / 1e6:.1f}M"
        elif a >= 1e4:
            s = f"{v / 1e3:.0f}K"
        elif a >= 1e3 and fmt != "number":
            s = f"{v / 1e3:.1f}K"
        else:
            s = f"{v:,.0f}" if float(v).is_integer() or a >= 100 else f"{v:,.1f}"
    else:
        s = str(v)
    return f"{prefix}{s}{suffix}"


def pptx_number_format(fmt: str, prefix: str = "", suffix: str = "") -> str:
    if fmt == "percent":
        return "0%"
    p = prefix.replace('"', "")
    s = suffix.replace('"', "")
    core = '#,##0'
    return (f'"{p}"' if p else "") + core + (f'"{s}"' if s else "")


@dataclass
class ChartSpec:
    kind: str                         # column | bar | stacked-column | line
    categories: List[str]
    series: List[Dict[str, Any]]      # [{name, values}]
    number_format: str = "number"     # number | currency | percent
    prefix: str = ""
    suffix: str = ""
    colors: List[str] = field(default_factory=list)
    show_values: bool = True
    show_legend: Optional[bool] = None
    highlight: Optional[int] = None   # index of category to emphasise
    axis_title: str = ""


class Canvas:
    """Interface.  Subclasses: PptxCanvas, PdfCanvas."""
    width: float
    height: float

    def new_page(self, background: str = "#FFFFFF"): raise NotImplementedError
    def rect(self, x, y, w, h, fill=None, line=None, line_w=0.75, radius=0.0): raise NotImplementedError
    def ellipse(self, x, y, w, h, fill=None, line=None, line_w=0.75): raise NotImplementedError
    def line(self, x1, y1, x2, y2, color="#000000", width=0.75, dash=False, arrow=False): raise NotImplementedError
    def text(self, x, y, w, h, text: str, style: TextStyle, fit: Optional[FitResult] = None): raise NotImplementedError
    def image(self, path, x, y, w, h, fit="contain"): raise NotImplementedError
    def table(self, x, y, col_widths: Sequence[float], rows: List[List[str]], styles: Dict, row_heights: Sequence[float]): raise NotImplementedError
    def chart(self, x, y, w, h, spec: ChartSpec, theme): raise NotImplementedError
    def notes(self, text: str): pass
    def link(self, x, y, w, h, url): pass
    def save(self, path): raise NotImplementedError


def image_box(img_w: int, img_h: int, x, y, w, h, fit="contain"):
    """Return (x, y, w, h) of an image fitted inside a box, preserving aspect."""
    if not img_w or not img_h:
        return x, y, w, h
    ar = img_w / img_h
    if fit == "contain":
        if w / h > ar:
            nw, nh = h * ar, h
        else:
            nw, nh = w, w / ar
        return x + (w - nw) / 2, y + (h - nh) / 2, nw, nh
    return x, y, w, h


def image_size(path: str):
    try:
        from PIL import Image  # matplotlib depends on Pillow
        with Image.open(path) as im:
            return im.size
    except Exception:
        return (0, 0)
