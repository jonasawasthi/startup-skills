"""Slide layouts for investor decks.

Each layout is a function ``(ctx, slide_dict) -> None`` that draws on
``ctx.canvas``.  Layouts never invent content: anything missing is drawn as a
clearly marked placeholder and recorded in ``ctx.missing``.

Grid (16:9, 13.333 x 7.5 in): 0.75in side margins, kicker at 0.55in, title
at 0.85in, content band 2.25–6.55in, source line 6.72in, footer 7.0in.
"""
from __future__ import annotations

import os
import re
from typing import Dict, List, Optional

from ..evidence import Ledger, numeric_claims
from ..render.base import ChartSpec, TextStyle, fit_text, text_height
from ..theme import STATUS_LABELS, Theme, mix

W, H = 13.333, 7.5
MX = 0.75
CW = W - 2 * MX
TOP = 2.25
BOTTOM = 6.55

STATUS_SYMBOL = {"yes": "●", "no": "○", "partial": "◐", "planned": "◌", "unknown": "?"}


class Ctx:
    def __init__(self, canvas, theme: Theme, ledger: Ledger, deck: Dict, base_dir: str, record: bool):
        self.canvas = canvas
        self.theme = theme
        self.ledger = ledger
        self.deck = deck
        self.base_dir = base_dir
        self.record = record          # only the first renderer pass records issues
        self.issues: List[Dict] = []
        self.missing: List[str] = []
        self.slide_no = 0
        self.slide_id = ""
        self.badges_on_slide: set = set()
        self.cited: List[str] = []

    # ---------- styles ----------
    def st(self, kind: str, **kw) -> TextStyle:
        t = self.theme
        base = {
            "kicker": TextStyle(font=t.body_font, size=10, color=t.accent, bold=True, caps=True, tracking=1.5),
            "title": TextStyle(font=t.heading_font, size=t.deck_title, color=t.ink, min_size=22, leading=1.12),
            "display": TextStyle(font=t.heading_font, size=t.deck_display, color=t.ink, min_size=28, leading=1.1),
            "h3": TextStyle(font=t.body_font, size=16, color=t.ink, bold=True, min_size=13, leading=1.15),
            "body": TextStyle(font=t.body_font, size=t.deck_body, color=t.muted, min_size=11, leading=1.3),
            "small": TextStyle(font=t.body_font, size=t.deck_small, color=t.muted, min_size=9, leading=1.25),
            "caption": TextStyle(font=t.body_font, size=t.deck_caption, color=t.faint, min_size=7.5, leading=1.2),
            "number": TextStyle(font=t.heading_font, size=44, color=t.accent, min_size=26, leading=1.0),
        }[kind]
        return base.with_(**kw) if kw else base

    # ---------- drawing helpers that record problems ----------
    def text(self, x, y, w, h, text, style: TextStyle, what: str = "text"):
        if text is None or text == "":
            return 0
        text = str(text)
        fit = fit_text(text, style, w, h)
        if not fit.fits and self.record:
            self.issue("error", f"{what} overflows its box even at {fit.size:.1f}pt: '{text[:60]}…' "
                                "(shorten the text)")
        self.canvas.text(x, y, w, h, text, style, fit)
        return fit.height_in

    def issue(self, level, msg):
        if self.record:
            self.issues.append({"level": level, "slide": self.slide_no, "id": self.slide_id, "message": msg})

    def need(self, item: str):
        if self.record and item not in self.missing:
            self.missing.append(item)

    def evidence_badge(self, ids, x, y, align="left") -> Optional[str]:
        """Draw a status pill when evidence is not verified.  Returns label."""
        ids = _ids(ids)
        for i in ids:
            if i not in self.ledger:
                self.issue("error", f"evidence {i} not found in ledger")
            elif i not in self.cited:
                self.cited.append(i)
        label = self.ledger.badge(ids) if ids else None
        if label:
            self.pill(label, x, y, self.theme.warning, align=align)
            self.badges_on_slide.add(label)
        return label

    def pill(self, label, x, y, color, align="left", filled=False):
        st = TextStyle(font=self.theme.body_font, size=8, color=self.theme.paper if filled else color, bold=True,
                       caps=True, tracking=0.5, align="center", valign="middle")
        from .. import fonts
        w = fonts.width(label.upper(), self.theme.body_font, 8, True) / 72 + 0.24
        if align == "right":
            x = x - w
        self.canvas.rect(x, y, w, 0.22, fill=color if filled else None, line=color, line_w=0.75, radius=0.11)
        self.canvas.text(x, y, w, 0.22, label, st)
        return w

    def status_pill(self, status, x, y, align="left"):
        status = (status or "unknown").lower()
        if status not in STATUS_LABELS:
            self.issue("error", f"unknown status '{status}'; use one of {', '.join(STATUS_LABELS)}")
            status = "unknown"
        return self.pill(STATUS_LABELS[status], x, y, self.theme.status_colors[status], align=align,
                         filled=status in ("live",))

    def path(self, p):
        if not p:
            return None
        return p if os.path.isabs(p) else os.path.normpath(os.path.join(self.base_dir, p))


def balanced_width(text: str, style: TextStyle, w: float, h: float) -> float:
    """Narrowest width that keeps the same line count: avoids one-word orphans."""
    base = fit_text(text, style, w, h)
    if len(base.lines) < 2:
        return w
    lo, hi = w * 0.55, w
    for _ in range(14):
        mid = (lo + hi) / 2
        f = fit_text(text, style.with_(min_size=base.size, size=base.size), mid, h)
        if f.fits and len(f.lines) == len(base.lines):
            hi = mid
        else:
            lo = mid
    return hi + 0.05


def _sym(v) -> str:
    """Normalise matrix cells: YAML turns yes/no into booleans."""
    if v is True:
        return "yes"
    if v is False:
        return "no"
    if v is None:
        return "unknown"
    return str(v)


def parse_amount(v) -> Optional[float]:
    """'$13.2M' -> 13200000.0 ; returns None if not parseable."""
    if isinstance(v, (int, float)):
        return float(v)
    m = re.search(r"([\d.,]+)\s*(k|K|m|M|mn|bn|B|billion|million|thousand|lakh|crore)?", str(v or ""))
    if not m:
        return None
    try:
        num = float(m.group(1).replace(",", ""))
    except ValueError:
        return None
    mult = {"k": 1e3, "thousand": 1e3, "m": 1e6, "mn": 1e6, "million": 1e6, "b": 1e9, "bn": 1e9, "billion": 1e9,
            "lakh": 1e5, "crore": 1e7}.get((m.group(2) or "").lower(), 1)
    return num * mult


def _ids(v) -> List[str]:
    if not v:
        return []
    if isinstance(v, str):
        return [s.strip() for s in v.split(",") if s.strip()]
    return [str(s) for s in v]


# ---------------------------------------------------------------- chrome
def chrome(ctx: Ctx, s: Dict, total: int):
    """Kicker, title, footer and source line shared by content slides."""
    t = ctx.theme
    if s.get("kicker"):
        ctx.text(MX, 0.55, CW, 0.25, s["kicker"], ctx.st("kicker"), "kicker")
    if s.get("title"):
        st = ctx.st("title")
        ctx.text(MX, 0.85, balanced_width(s["title"], st, CW * 0.92, 1.25), 1.25, s["title"], st, "title")
    footer(ctx, total)


def footer(ctx: Ctx, total: int):
    t = ctx.theme
    d = ctx.deck
    left = " · ".join(x for x in [d.get("company", ""), d.get("confidentiality", "Confidential")] if x)
    ctx.text(MX, 7.02, 6, 0.22, left, ctx.st("caption"), "footer")
    ctx.text(W - MX - 1, 7.02, 1, 0.22, f"{ctx.slide_no}", ctx.st("caption", align="right"), "footer")


def source_line(ctx: Ctx, s: Dict, extra_ids=()):
    ids = _ids(s.get("evidence")) + [i for i in extra_ids if i]
    parts = []
    if s.get("source"):
        parts.append(str(s["source"]))
    if ids:
        parts.append("Evidence: " + ", ".join(dict.fromkeys(ids)))
    for i in ids:
        if i in ctx.ledger and i not in ctx.cited:
            ctx.cited.append(i)
        elif i not in ctx.ledger:
            ctx.issue("error", f"evidence {i} not found in ledger")
    if ctx.badges_on_slide:
        parts.append("Labelled figures are not independently verified; see evidence appendix")
    if parts:
        ctx.text(MX, 6.68, CW, 0.28, "  ·  ".join(parts), ctx.st("caption"), "source line")


# ---------------------------------------------------------------- layouts
def cover(ctx: Ctx, s: Dict, total: int):
    t = ctx.theme
    logo = ctx.path(s.get("logo") or t.logo)
    if logo and os.path.exists(logo):
        ctx.canvas.image(logo, MX, 0.7, 1.6, 0.7)
    ctx.canvas.rect(MX, 2.55, 0.9, 0.07, fill=t.accent)
    ctx.text(MX, 2.8, CW * 0.8, 1.3, s.get("title") or ctx.deck.get("company", ""),
             ctx.st("display", size=60, min_size=40), "cover title")
    ctx.text(MX, 4.15, CW * 0.7, 1.0, s.get("subtitle", ""), ctx.st("body", size=22, color=t.muted, min_size=16),
             "cover subtitle")
    ctx.text(MX, 6.55, CW * 0.6, 0.3, s.get("meta", ctx.deck.get("date", "")), ctx.st("small", color=t.faint), "meta")
    ctx.text(W - MX - 4, 6.55, 4, 0.3, ctx.deck.get("confidentiality", "Confidential"),
             ctx.st("small", color=t.faint, align="right"), "meta")


def section(ctx: Ctx, s: Dict, total: int):
    t = ctx.theme
    ctx.text(MX, 2.6, 3, 1.0, s.get("number", ""), ctx.st("number", size=54, color=t.accent), "section number")
    ctx.text(MX, 3.6, CW * 0.8, 1.2, s.get("title", ""), ctx.st("display", size=40), "section title")
    footer(ctx, total)


def statement(ctx: Ctx, s: Dict, total: int):
    t = ctx.theme
    if s.get("kicker"):
        ctx.text(MX, 1.6, CW, 0.3, s["kicker"], ctx.st("kicker"), "kicker")
    h = ctx.text(MX, 2.05, CW * 0.86, 3.3, s.get("text", ""), ctx.st("display", size=s.get("size", 40)), "statement")
    if s.get("support"):
        ctx.text(MX, 2.05 + h + 0.35, CW * 0.7, 1.2, s["support"], ctx.st("body", size=17), "support")
    if s.get("evidence"):
        ctx.evidence_badge(s["evidence"], MX, 1.2)
    footer(ctx, total)
    source_line(ctx, s)


def closing(ctx: Ctx, s: Dict, total: int):
    statement(ctx, {**s, "kicker": s.get("kicker", "")}, total)
    if s.get("contact"):
        ctx.text(MX, 5.7, CW, 0.4, s["contact"], ctx.st("h3", color=ctx.theme.accent), "contact")


def points(ctx: Ctx, s: Dict, total: int):
    """2–4 columns: numbered insight cards (problem, solution, why-now, use cases)."""
    chrome(ctx, s, total)
    t = ctx.theme
    items = s.get("points") or s.get("items") or []
    if not items:
        ctx.issue("error", "points slide has no points")
        return
    if len(items) > 4:
        ctx.issue("warning", f"{len(items)} points; investors retain 3. Consider cutting.")
        items = items[:4]
    n = len(items)
    gap = 0.4
    cw = (CW - gap * (n - 1)) / n
    ts = ctx.st("h3", size=22 if n <= 3 else 18)
    bs = ctx.st("body", size=17 if n <= 3 else 14.5)
    heights = [0.6 + text_height(it.get("title", ""), ts, cw) + 0.18 + text_height(it.get("body", ""), bs, cw)
               for it in items]
    top = TOP + max(0.0, min(0.9, (BOTTOM - TOP - max(heights)) / 2 - 0.25))
    for i, it in enumerate(items):
        x = MX + i * (cw + gap)
        ctx.canvas.line(x, top, x + cw, top, t.accent if i == s.get("highlight", -1) else t.ink, 1.5)
        ctx.text(x, top + 0.15, 1.0, 0.3, it.get("label", f"{i + 1:02d}"), ctx.st("kicker", color=t.accent), "label")
        if it.get("evidence"):
            ctx.evidence_badge(it["evidence"], x + cw, top + 0.15, align="right")
        hh = ctx.text(x, top + 0.6, cw, 1.2, it.get("title", ""), ts, "point title")
        ctx.text(x, top + 0.6 + hh + 0.18, cw, BOTTOM - (top + 0.78 + hh), it.get("body", ""), bs, "point body")
    source_line(ctx, s, [e for it in items for e in _ids(it.get("evidence"))])


def bullets(ctx: Ctx, s: Dict, total: int):
    """Rows: bold lead + supporting detail, separated by hairlines."""
    chrome(ctx, s, total)
    t = ctx.theme
    items = s.get("items", [])
    if len(items) > 6:
        ctx.issue("warning", f"{len(items)} rows is a wall of text; keep to 5 or fewer")
    n = max(len(items), 1)
    row_h = min((BOTTOM - TOP) / n, 1.1)
    lead_w = CW * 0.36 if any(isinstance(i, dict) and i.get("detail") for i in items) else CW
    for i, it in enumerate(items):
        it = it if isinstance(it, dict) else {"lead": str(it)}
        y = TOP + i * row_h
        ctx.canvas.line(MX, y, MX + CW, y, t.rule, 0.75)
        ctx.text(MX, y + 0.14, lead_w - 0.3, row_h - 0.2, it.get("lead", ""), ctx.st("h3", size=17), "row lead")
        if it.get("detail"):
            ctx.text(MX + lead_w, y + 0.14, CW - lead_w - 1.3, row_h - 0.2, it["detail"], ctx.st("body"), "row detail")
        if it.get("status"):
            ctx.status_pill(it["status"], MX + CW, y + 0.18, align="right")
        elif it.get("evidence"):
            ctx.evidence_badge(it["evidence"], MX + CW, y + 0.18, align="right")
    source_line(ctx, s, [e for it in items if isinstance(it, dict) for e in _ids(it.get("evidence"))])


def split(ctx: Ctx, s: Dict, total: int):
    """Two contrasting columns (today vs. with us, before/after, risks/mitigations)."""
    chrome(ctx, s, total)
    t = ctx.theme
    cols = [s.get("left", {}), s.get("right", {})]
    cw = (CW - 0.6) / 2
    for i, col in enumerate(cols):
        x = MX + i * (cw + 0.6)
        fill = t.tint if i == 0 else mix(t.accent, t.paper, 0.92)
        ctx.canvas.rect(x, TOP, cw, BOTTOM - TOP, fill=fill, radius=0.08)
        ctx.text(x + 0.35, TOP + 0.3, cw - 0.7, 0.3, col.get("heading", ""),
                 ctx.st("kicker", color=t.muted if i == 0 else t.accent), "heading")
        y = TOP + 0.8
        for b in col.get("items", []):
            hgt = text_height(str(b), ctx.st("body", size=16, color=t.ink), cw - 1.0)
            ctx.canvas.ellipse(x + 0.38, y + 0.11, 0.08, 0.08, fill=t.faint if i == 0 else t.accent)
            ctx.text(x + 0.6, y, cw - 1.0, hgt + 0.05, str(b), ctx.st("body", size=16, color=t.ink), "split item")
            y += hgt + 0.25
        if y > BOTTOM:
            ctx.issue("error", "split column content overflows; cut items")
    source_line(ctx, s)


def metrics(ctx: Ctx, s: Dict, total: int):
    """Big-number tiles.  Every number MUST carry evidence."""
    chrome(ctx, s, total)
    t = ctx.theme
    items = s.get("items", [])
    n = max(len(items), 1)
    gap = 0.35
    cw = (CW - gap * (n - 1)) / n
    for i, it in enumerate(items):
        x = MX + i * (cw + gap)
        ids = _ids(it.get("evidence"))
        if not ids:
            ctx.issue("error", f"metric '{it.get('label')}' has no evidence; metrics cannot be shown without a source")
        ctx.canvas.line(x, TOP + 0.2, x + cw, TOP + 0.2, t.ink, 1.5)
        ctx.text(x, TOP + 0.45, cw, 1.1, it.get("value", "—"), ctx.st("number", size=48 if n <= 3 else 40), "metric value")
        ctx.text(x, TOP + 1.65, cw, 0.6, it.get("label", ""), ctx.st("h3", size=16), "metric label")
        ctx.text(x, TOP + 2.25, cw, 1.4, it.get("context", ""), ctx.st("small", size=12), "metric context")
        if ids:
            ctx.evidence_badge(ids, x, TOP + 3.75)
    if s.get("takeaway"):
        ctx.text(MX, 5.85, CW, 0.6, s["takeaway"], ctx.st("body", color=t.ink, size=16), "takeaway")
    source_line(ctx, s, [e for it in items for e in _ids(it.get("evidence"))])


def _chart_spec(ctx: Ctx, c: Dict) -> ChartSpec:
    series = c.get("series")
    if not series and "values" in c:
        series = [{"name": c.get("name", ""), "values": c["values"]}]
    return ChartSpec(kind=c.get("kind", "column"), categories=[str(x) for x in c.get("categories", [])],
                     series=series or [], number_format=c.get("format", "number"), prefix=c.get("prefix", ""),
                     suffix=c.get("suffix", ""), highlight=c.get("highlight"), show_values=c.get("labels", True))


def chart(ctx: Ctx, s: Dict, total: int):
    chrome(ctx, s, total)
    t = ctx.theme
    c = s.get("chart", {})
    ids = _ids(c.get("evidence")) + _ids(s.get("evidence"))
    if not (ids or c.get("source") or s.get("source")):
        ctx.issue("error", "chart has no source or evidence; unsourced charts are not allowed")
    spec = _chart_spec(ctx, c)
    if not spec.categories or not spec.series:
        ctx.issue("error", "chart has no data")
        return
    for se in spec.series:
        if len(se.get("values", [])) != len(spec.categories):
            ctx.issue("error", f"series '{se.get('name')}' length != categories length")
            return
    has_side = bool(s.get("takeaway") or s.get("body"))
    cw = CW * 0.62 if has_side else CW
    ctx.canvas.chart(MX, TOP + 0.05, cw, BOTTOM - TOP - 0.15, spec, t)
    if ids:
        ctx.evidence_badge(ids, MX + cw, TOP - 0.3, align="right")
    if has_side:
        x = MX + cw + 0.6
        w = CW - cw - 0.6
        hh = ctx.text(x, TOP + 0.1, w, 1.6, s.get("takeaway", ""), ctx.st("h3", size=20, color=t.ink), "takeaway")
        ctx.text(x, TOP + 0.3 + hh, w, BOTTOM - TOP - 0.4 - hh, s.get("body", ""), ctx.st("body"), "chart body")
    source_line(ctx, {**s, "source": c.get("source") or s.get("source")}, ids)


def market(ctx: Ctx, s: Dict, total: int):
    """TAM/SAM/SOM as nested squares (area ∝ sqrt for legibility) + method notes."""
    chrome(ctx, s, total)
    t = ctx.theme
    layers = s.get("layers", [])
    if not layers:
        ctx.issue("error", "market slide needs layers (TAM/SAM/SOM) – use calc output, never guessed numbers")
        return
    size = BOTTOM - TOP - 0.3
    x0, y0 = MX, TOP
    shades = [mix(t.accent, t.paper, 0.85), mix(t.accent, t.paper, 0.55), t.accent]
    ids_all = []
    amounts = [parse_amount(L.get("amount", L.get("value"))) for L in layers[:3]]
    scaled = all(a for a in amounts) and amounts[0] > 0
    fracs, clamped = [], False
    for i in range(len(layers[:3])):
        if scaled:
            f = (amounts[i] / amounts[0]) ** 0.5   # area proportional to value
            if f < 0.3:
                f, clamped = 0.3, True
        else:
            f = [1.0, 0.68, 0.38][i]
        fracs.append(f)
    if not scaled or clamped:
        ctx.text(x0, BOTTOM - 0.02, size, 0.22, "Areas not to scale" if not scaled else
                 "Area proportional to value; smallest square enlarged for legibility", ctx.st("caption", size=8.5), "scale note")
    for i, L in enumerate(layers[:3]):
        frac = fracs[i]
        side = size * frac
        y = y0 + size - side
        ctx.canvas.rect(x0, y, side, side, fill=shades[i])
        ink = t.ink if i < 2 else t.paper
        ctx.text(x0 + 0.18, y + 0.15, side - 0.3, 0.3, L.get("name", ""), ctx.st("kicker", color=ink), "layer name")
        ctx.text(x0 + 0.18, y + 0.42, side - 0.3, 0.6, L.get("value", ""), ctx.st("number", size=28 if i < 2 else 24,
                                                                                    color=ink, min_size=11), "layer value")
        ids = _ids(L.get("evidence"))
        ids_all += ids
        if not ids and not L.get("status"):
            ctx.issue("error", f"market layer '{L.get('name')}' has no evidence or status")
    # right column: definitions / method
    x = MX + size + 0.6
    w = CW - size - 0.6
    y = TOP
    for L in layers[:3]:
        ids = _ids(L.get("evidence"))
        ctx.text(x, y, w - 1.3, 0.3, f"{L.get('name', '')}  {L.get('value', '')}", ctx.st("h3", size=14), "layer head")
        if ids:
            ctx.evidence_badge(ids, x + w, y, align="right")
        elif L.get("status"):
            ctx.pill(L["status"].title(), x + w, y, t.warning, align="right")
            ctx.badges_on_slide.add(L["status"])
        hh = ctx.text(x, y + 0.32, w, 0.95, L.get("definition", ""), ctx.st("small", size=12), "layer definition")
        y += 0.32 + max(hh, 0.45) + 0.3
    if s.get("method"):
        ctx.text(x, max(y, BOTTOM - 0.9), w, 0.85, s["method"], ctx.st("caption", size=10, color=t.muted), "method")
    source_line(ctx, s, ids_all)


def _symbol(ctx: Ctx, kind: str, cx: float, cy: float, r: float = 0.09):
    t = ctx.theme
    if kind == "yes":
        ctx.canvas.ellipse(cx - r, cy - r, 2 * r, 2 * r, fill=t.accent)
    elif kind == "partial":
        ctx.canvas.ellipse(cx - r, cy - r, 2 * r, 2 * r, line=t.accent, line_w=1.25)
        ctx.canvas.ellipse(cx - r * 0.5, cy - r * 0.5, r, r, fill=t.accent)
    elif kind == "planned":
        ctx.canvas.ellipse(cx - r, cy - r, 2 * r, 2 * r, line=t.muted, line_w=1.0)
    elif kind == "no":
        ctx.canvas.line(cx - r, cy, cx + r, cy, t.faint, 1.5)
    else:
        ctx.canvas.text(cx - 0.3, cy - 0.12, 0.6, 0.24, "?", ctx.st("small", align="center", valign="middle"))


def comparison(ctx: Ctx, s: Dict, total: int):
    """Competitive matrix.  Cells: yes / no / partial / planned / unknown / short free text."""
    chrome(ctx, s, total)
    t = ctx.theme
    cols = s.get("columns", [])
    rows = s.get("rows", [])
    if not cols or not rows:
        ctx.issue("error", "comparison needs columns and rows")
        return
    us = s.get("us")
    header = [""] + [str(c) for c in cols]
    body, symbols, cell_styles = [], [], {}
    for ri, r in enumerate(rows, start=1):
        vals = []
        for ci, v in enumerate(r.get("values", [])):
            key = _sym(v).lower()
            if key in STATUS_SYMBOL:
                vals.append("")
                symbols.append((ri, ci + 1, key))
            else:
                vals.append(_sym(v))
        if len(vals) != len(cols):
            ctx.issue("error", f"row '{r.get('name')}' has {len(vals)} values for {len(cols)} columns")
        body.append([r.get("name", "")] + vals)
        if r.get("name") == us:
            cell_styles[(ri, 0)] = {"color": t.accent, "bold": True}
    n = len(header)
    first_w = 2.8
    cw = [first_w] + [(CW - first_w) / (n - 1)] * (n - 1)
    head_h = 0.62
    rh = min(0.62, (BOTTOM - TOP - head_h - 0.4) / max(len(body), 1))
    styles = {"header": ctx.st("small", size=11.5, color=t.ink, bold=True, align="center", min_size=9),
              "body": ctx.st("body", size=13, color=t.ink, align="center"),
              "first_col": ctx.st("body", size=14, color=t.ink, bold=True),
              "rule": t.rule, "cell_styles": cell_styles}
    if us:
        idx = [i for i, r in enumerate(rows, 1) if r.get("name") == us]
        if idx:
            ctx.canvas.rect(MX, TOP + head_h + (idx[0] - 1) * rh, CW, rh, fill=mix(t.accent, t.paper, 0.9))
    ctx.canvas.table(MX, TOP, cw, [header] + body, styles, [head_h] + [rh] * len(body))
    xs = [MX]
    for w_ in cw:
        xs.append(xs[-1] + w_)
    for ri, ci, key in symbols:
        _symbol(ctx, key, (xs[ci] + xs[ci + 1]) / 2, TOP + head_h + (ri - 1) * rh + rh / 2)
    lx = MX
    ly = TOP + head_h + rh * len(body) + 0.3
    for key, label in (("yes", "Yes"), ("partial", "Partial"), ("no", "No"), ("planned", "Planned")):
        _symbol(ctx, key, lx + 0.09, ly + 0.12, 0.07)
        ctx.text(lx + 0.24, ly, 1.0, 0.24, label, ctx.st("caption", size=10, valign="middle"), "legend")
        lx += 1.2
    source_line(ctx, s)


def positioning(ctx: Ctx, s: Dict, total: int):
    """2x2 map.  Points have x,y in [0,1]."""
    chrome(ctx, s, total)
    t = ctx.theme
    size_w, size_h = 6.6, BOTTOM - TOP - 0.2
    x0, y0 = MX + 0.4, TOP
    ctx.canvas.rect(x0, y0, size_w, size_h, fill=t.tint)
    ctx.canvas.line(x0 + size_w / 2, y0, x0 + size_w / 2, y0 + size_h, t.rule, 1)
    ctx.canvas.line(x0, y0 + size_h / 2, x0 + size_w, y0 + size_h / 2, t.rule, 1)
    xa, ya = s.get("x_axis", ["", ""]), s.get("y_axis", ["", ""])
    cap = ctx.st("caption", size=10, color=t.muted)
    ctx.text(x0, y0 + size_h + 0.05, 3, 0.25, f"← {xa[0]}", cap, "axis")
    ctx.text(x0 + size_w - 3, y0 + size_h + 0.05, 3, 0.25, f"{xa[1]} →", cap.with_(align="right"), "axis")
    ctx.text(x0 - 0.4, y0, 0.38, size_h / 2, "", cap, "axis")
    ctx.text(x0 + 0.1, y0 + 0.08, 3, 0.25, f"↑ {ya[1]}", cap, "axis")
    ctx.text(x0 + 0.1, y0 + size_h - 0.33, 3, 0.25, f"↓ {ya[0]}", cap, "axis")
    for p in s.get("points", []):
        px = x0 + float(p.get("x", 0.5)) * size_w
        py = y0 + (1 - float(p.get("y", 0.5))) * size_h
        hl = p.get("highlight")
        r = 0.13 if hl else 0.09
        ctx.canvas.ellipse(px - r, py - r, 2 * r, 2 * r, fill=t.accent if hl else t.muted)
        ctx.text(px + r + 0.06, py - 0.14, 2.2, 0.3, p.get("name", ""),
                 ctx.st("small", size=12 if hl else 11, color=t.ink, bold=bool(hl)), "point label")
    x = x0 + size_w + 0.6
    w = MX + CW - x
    hh = ctx.text(x, TOP + 0.1, w, 1.6, s.get("takeaway", ""), ctx.st("h3", size=20), "takeaway")
    ctx.text(x, TOP + 0.3 + hh, w, BOTTOM - TOP - 0.4 - hh, s.get("body", ""), ctx.st("body"), "body")
    ctx.text(x, BOTTOM - 0.35, w, 0.3, "Placement is the company's qualitative judgement.", ctx.st("caption"), "note")
    source_line(ctx, s)


def roadmap(ctx: Ctx, s: Dict, total: int):
    """Timeline with explicit status per milestone."""
    chrome(ctx, s, total)
    t = ctx.theme
    items = s.get("items", [])
    if not items:
        ctx.issue("error", "roadmap has no items")
        return
    n = len(items)
    y_line = TOP + 1.25
    ctx.canvas.line(MX, y_line, MX + CW, y_line, t.rule, 1.5)
    slot = CW / n
    for i, it in enumerate(items):
        st = (it.get("status") or "unknown").lower()
        col = t.status_colors.get(st, t.negative)
        cx = MX + i * slot
        ctx.canvas.ellipse(cx + 0.02, y_line - 0.09, 0.18, 0.18, fill=col if st in ("live", "built", "in-development") else t.paper,
                           line=col, line_w=1.5)
        ctx.text(cx, y_line - 0.55, slot - 0.2, 0.3, it.get("date", ""), ctx.st("kicker", color=t.muted), "date")
        ctx.status_pill(st, cx, y_line + 0.3)
        hh = ctx.text(cx, y_line + 0.7, slot - 0.25, 0.9, it.get("label", ""), ctx.st("h3", size=15 if n > 4 else 17), "milestone")
        ctx.text(cx, y_line + 0.75 + hh, slot - 0.25, BOTTOM - (y_line + 0.8 + hh), it.get("detail", ""),
                 ctx.st("small", size=12), "milestone detail")
    source_line(ctx, s, [e for it in items for e in _ids(it.get("evidence"))])


def products(ctx: Ctx, s: Dict, total: int):
    """Product / ecosystem cards with mandatory status."""
    chrome(ctx, s, total)
    t = ctx.theme
    items = s.get("items", [])
    n = len(items)
    if n == 0:
        ctx.issue("error", "products slide has no items")
        return
    cols = 3 if n in (3, 5, 6, 9) or n > 4 else min(n, 4)
    if n == 4:
        cols = 2 if s.get("large") else 4
    rows = (n + cols - 1) // cols
    gap = 0.3
    cw = (CW - gap * (cols - 1)) / cols
    ch = (BOTTOM - TOP - gap * (rows - 1)) / rows
    for i, it in enumerate(items):
        r, c = divmod(i, cols)
        x = MX + c * (cw + gap)
        y = TOP + r * (ch + gap)
        if not it.get("status"):
            ctx.issue("error", f"product '{it.get('name')}' has no status")
        ctx.canvas.rect(x, y, cw, ch, fill=t.tint, radius=0.06)
        ctx.text(x + 0.25, y + 0.22, cw - 0.5, 0.45, it.get("name", ""), ctx.st("h3", size=17), "product name")
        ctx.status_pill(it.get("status"), x + 0.25, y + 0.68)
        users = it.get("users")
        body_top = y + 1.05
        hh = ctx.text(x + 0.25, body_top, cw - 0.5, ch - 1.35 - (0.3 if users else 0), it.get("description", ""),
                      ctx.st("small", size=12.5 if rows == 1 else 11.5), "product description")
        if users:
            ctx.text(x + 0.25, y + ch - 0.42, cw - 0.5, 0.3, f"For: {users}", ctx.st("caption", size=9.5, color=t.muted),
                     "product users")
    source_line(ctx, s, [e for it in items for e in _ids(it.get("evidence"))])


def diagram(ctx: Ctx, s: Dict, total: int):
    """Layered architecture / ecosystem diagram: rows of nodes, arrows between layers."""
    chrome(ctx, s, total)
    t = ctx.theme
    layers = s.get("layers", [])
    if not layers:
        ctx.issue("error", "diagram needs layers")
        return
    n = len(layers)
    label_w = 1.9
    gap = 0.38
    lh = (BOTTOM - TOP - gap * (n - 1)) / n
    centers = []
    for li, L in enumerate(layers):
        y = TOP + li * (lh + gap)
        ctx.text(MX, y, label_w - 0.2, lh, L.get("name", ""), ctx.st("kicker", color=t.muted, valign="middle"), "layer")
        nodes = L.get("nodes", [])
        k = max(len(nodes), 1)
        nw = (CW - label_w - 0.2 * (k - 1)) / k
        row = []
        for ni, node in enumerate(nodes):
            node = node if isinstance(node, dict) else {"name": str(node)}
            nx = MX + label_w + ni * (nw + 0.2)
            hl = node.get("highlight")
            st = node.get("status")
            ctx.canvas.rect(nx, y, nw, lh, fill=t.accent if hl else t.paper, line=None if hl else t.rule, radius=0.06)
            ink = t.paper if hl else t.ink
            sub = node.get("detail", "")
            ctx.text(nx + 0.12, y + 0.06, nw - 0.24, (lh - 0.12) * (0.55 if sub else 1), node.get("name", ""),
                     ctx.st("h3", size=13, color=ink, align="center", valign="bottom" if sub else "middle", min_size=9),
                     "node")
            if sub:
                ctx.text(nx + 0.12, y + 0.06 + (lh - 0.12) * 0.57, nw - 0.24, (lh - 0.12) * 0.43, sub,
                         ctx.st("caption", size=9.5, color=mix(ink, t.paper, 0.25) if hl else t.muted, align="center"), "node detail")
            if st and st != "live":
                short = {"built": "Built", "in-development": "In dev", "planned": "Planned", "proposed": "Idea",
                         "unknown": "?"}
                label = STATUS_LABELS.get(st, st) if nw >= 2.2 else short.get(st, st)
                ctx.pill(label, nx + nw - 0.05, y - 0.11, t.status_colors.get(st, t.negative), align="right")
            row.append((nx + nw / 2, y, y + lh))
        centers.append(row)
    for li in range(n - 1):
        a, b = centers[li], centers[li + 1]
        if a and b:
            ctx.canvas.line(MX + label_w + (CW - label_w) / 2, a[0][2] + 0.04, MX + label_w + (CW - label_w) / 2,
                            b[0][1] - 0.04, t.faint, 1.0, arrow=True)
    source_line(ctx, s)


def screenshot(ctx: Ctx, s: Dict, total: int):
    chrome(ctx, s, total)
    t = ctx.theme
    img = ctx.path(s.get("image"))
    iw = CW * 0.62
    box = (MX, TOP - 0.05, iw, BOTTOM - TOP)
    if img and os.path.exists(img):
        ctx.canvas.rect(*box, fill=t.tint, radius=0.06)
        ctx.canvas.image(img, box[0] + 0.15, box[1] + 0.15, box[2] - 0.3, box[3] - 0.3)
    else:
        ctx.canvas.rect(*box, fill=t.tint, line=t.faint, line_w=1, radius=0.06)
        need = s.get("needed") or s.get("image") or "product screenshot"
        ctx.text(box[0] + 0.5, box[1], box[2] - 1.0, box[3], f"Screenshot needed\n{need}",
                 ctx.st("h3", size=16, color=t.faint, align="center", valign="middle"), "placeholder")
        ctx.need(f"Slide {ctx.slide_no}: screenshot – {need}")
        ctx.issue("warning", f"screenshot missing ({need}); placeholder drawn")
    x = MX + iw + 0.5
    w = CW - iw - 0.5
    y = TOP
    if s.get("status"):
        ctx.status_pill(s["status"], x, y)
        y += 0.45
    for c in s.get("callouts", []):
        c = c if isinstance(c, dict) else {"title": str(c)}
        ctx.canvas.line(x, y, x + w, y, t.rule, 0.75)
        hh = ctx.text(x, y + 0.12, w, 0.7, c.get("title", ""), ctx.st("h3", size=15), "callout")
        h2 = ctx.text(x, y + 0.16 + hh, w, 1.0, c.get("body", ""), ctx.st("small", size=12), "callout body")
        y += 0.35 + hh + h2
    source_line(ctx, s)


def team(ctx: Ctx, s: Dict, total: int):
    chrome(ctx, s, total)
    t = ctx.theme
    people = s.get("people", [])
    n = max(len(people), 1)
    cols = min(n, 4)
    rows = (n + cols - 1) // cols
    gap = 0.4
    cw = (CW - gap * (cols - 1)) / cols
    ch = (BOTTOM - TOP - 0.3 * (rows - 1)) / rows
    for i, p in enumerate(people):
        r, c = divmod(i, cols)
        x = MX + c * (cw + gap)
        y = TOP + r * (ch + 0.3)
        photo = ctx.path(p.get("photo"))
        d = min(1.2, ch * 0.4)
        if photo and os.path.exists(photo):
            ctx.canvas.image(photo, x, y, d, d)
        else:
            ctx.canvas.ellipse(x, y, d, d, fill=mix(t.accent, t.paper, 0.85))
            initials = "".join(w[0] for w in p.get("name", "?").split()[:2]).upper()
            ctx.text(x, y, d, d, initials, ctx.st("h3", size=20, color=t.accent, align="center", valign="middle"), "initials")
        ctx.text(x, y + d + 0.15, cw, 0.4, p.get("name", ""), ctx.st("h3", size=17), "name")
        ctx.text(x, y + d + 0.52, cw, 0.3, p.get("role", ""), ctx.st("kicker", color=t.accent, size=9.5), "role")
        ctx.text(x, y + d + 0.9, cw, ch - d - 0.95, p.get("bio", ""), ctx.st("small", size=12), "bio")
        if p.get("evidence"):
            ctx.evidence_badge(p["evidence"], x + cw, y, align="right")
    if s.get("hiring"):
        ctx.text(MX, BOTTOM - 0.3, CW, 0.3, s["hiring"], ctx.st("small", color=t.ink), "hiring")
    source_line(ctx, s)


def ask(ctx: Ctx, s: Dict, total: int):
    """The raise: amount, instrument, use of funds, milestones it buys."""
    chrome(ctx, s, total)
    t = ctx.theme
    amount = s.get("amount")
    if not amount or re.search(r"TBD|\[|\?", str(amount)):
        ctx.need(f"Slide {ctx.slide_no}: fundraising amount (founder decision)")
        ctx.issue("warning", "ask slide has no amount; placeholder drawn")
        amount = "[Amount TBD]"
    lw = CW * 0.38
    ctx.text(MX, TOP, lw, 1.2, amount, ctx.st("number", size=60, min_size=36), "amount")
    ih = ctx.text(MX, TOP + 1.25, lw - 0.3, 0.9, s.get("instrument", ""), ctx.st("h3", size=18), "instrument")
    sy = TOP + 1.25 + max(ih, 0.3) + 0.2
    ctx.text(MX, sy, lw - 0.3, BOTTOM - sy, s.get("summary", ""), ctx.st("body"), "summary")
    x = MX + lw + 0.5
    w = CW - lw - 0.5
    uof = s.get("use_of_funds", [])
    if uof:
        ctx.text(x, TOP, w, 0.3, "Use of funds", ctx.st("kicker"), "uof heading")
        total_pct = sum(float(u.get("share", 0)) for u in uof)
        if abs(total_pct - 1.0) > 0.011 and abs(total_pct - 100) > 1.1:
            ctx.issue("error", f"use of funds shares sum to {total_pct}, not 100%")
        y = TOP + 0.45
        for u in uof:
            share = float(u.get("share", 0))
            share = share / 100 if share > 1 else share
            ctx.text(x, y, 2.6, 0.32, u.get("name", ""), ctx.st("small", size=12.5, color=t.ink, bold=True), "uof name")
            ctx.canvas.rect(x + 2.7, y + 0.06, (w - 3.5) * share, 0.2, fill=t.accent)
            ctx.text(x + 2.75 + (w - 3.5) * share, y, 0.75, 0.32, f"{share:.0%}", ctx.st("small", size=12, color=t.ink), "uof pct")
            if u.get("detail"):
                ctx.text(x, y + 0.3, w, 0.3, u["detail"], ctx.st("caption", size=10, color=t.muted), "uof detail")
                y += 0.25
            y += 0.5
        y += 0.15
    else:
        y = TOP
    ms = s.get("milestones", [])
    if ms:
        ctx.text(x, y, w, 0.3, s.get("milestones_heading", "What this round achieves"), ctx.st("kicker"), "ms heading")
        y += 0.4
        for m in ms:
            hh = ctx.text(x + 0.25, y, w - 0.25, 0.6, str(m), ctx.st("small", size=12.5, color=t.ink), "milestone")
            ctx.canvas.ellipse(x, y + 0.08, 0.09, 0.09, fill=t.accent)
            y += hh + 0.12
        if y > BOTTOM + 0.05:
            ctx.issue("error", "ask slide right column overflows; shorten use-of-funds or milestones")
    source_line(ctx, s)


def table(ctx: Ctx, s: Dict, total: int):
    chrome(ctx, s, total)
    t = ctx.theme
    rows = s.get("rows", [])
    header = s.get("header", [])
    allrows = ([header] if header else []) + rows
    if not allrows:
        ctx.issue("error", "table has no rows")
        return
    n = max(len(r) for r in allrows)
    widths = s.get("widths")
    cw = [CW * w for w in widths] if widths else [CW / n] * n
    body_st = ctx.st("body", size=s.get("size", 12.5), color=t.ink)
    rh = []
    for r in allrows:
        h = max(text_height(str(c), body_st, cw[i] - 0.16) for i, c in enumerate(r)) + 0.16
        rh.append(max(0.42, h))
    if sum(rh) > BOTTOM - TOP + 0.1:
        ctx.issue("error", "table too tall for the slide; split it or move it to the appendix")
    styles = {"header": ctx.st("small", size=11, color=t.ink, bold=True), "body": body_st,
              "first_col": body_st.with_(bold=True), "rule": t.rule}
    ctx.canvas.table(MX, TOP, cw, allrows, styles, rh)
    source_line(ctx, s)


def quote(ctx: Ctx, s: Dict, total: int):
    t = ctx.theme
    if not _ids(s.get("evidence")):
        ctx.issue("error", "quotes/testimonials require evidence (who said it, when, consent)")
    if s.get("kicker"):
        ctx.text(MX, 1.6, CW, 0.3, s["kicker"], ctx.st("kicker"), "kicker")
    ctx.text(MX, 1.9, 1, 1, "“", ctx.st("display", size=96, color=t.accent), "quote mark")
    h = ctx.text(MX + 0.9, 2.3, CW * 0.8, 2.8, s.get("text", ""), ctx.st("display", size=30, min_size=20, leading=1.25),
                 "quote")
    ctx.text(MX + 0.9, 2.3 + h + 0.3, CW * 0.8, 0.4, f"— {s.get('attribution', '')}", ctx.st("h3", size=14, color=t.muted),
             "attribution")
    ctx.evidence_badge(s.get("evidence"), MX + CW, 1.6, align="right")
    footer(ctx, total)
    source_line(ctx, s)


def sources(ctx: Ctx, s: Dict, total: int):
    """Evidence appendix: auto-filled with every ID cited earlier in the deck."""
    chrome(ctx, {**s, "kicker": s.get("kicker", "Appendix"), "title": s.get("title", "Sources and evidence")}, total)
    t = ctx.theme
    ids = s.get("_ids", [])
    rows = []
    for eid in ids:
        e = ctx.ledger.get(eid)
        if e:
            rows.append([e.id, e.claim, e.status, e.citation()])
    if not rows:
        ctx.text(MX, TOP, CW, 0.5, "No evidence cited in this deck.", ctx.st("body"), "empty")
        return
    cw = [0.8, CW * 0.36, 1.1, CW - 0.8 - CW * 0.36 - 1.1]
    st = ctx.st("caption", size=9, color=t.ink)
    heights = [max(0.3, max(text_height(str(c), st, cw[i] - 0.16) for i, c in enumerate(r)) + 0.08) for r in rows]
    styles = {"header": ctx.st("caption", size=9, color=t.ink, bold=True), "body": st, "first_col": st.with_(bold=True),
              "rule": t.rule}
    pages, cur, used = [], [], 0.0
    avail = BOTTOM - TOP + 0.1 - 0.32
    for r, h in zip(rows, heights):
        if cur and used + h > avail:
            pages.append(cur)
            cur, used = [], 0.0
        cur.append((r, h))
        used += h
    pages.append(cur)
    for pi, page in enumerate(pages):
        if pi:
            ctx.canvas.new_page(t.paper)
            ctx.slide_no += 1
            chrome(ctx, {"kicker": "Appendix", "title": f"Sources and evidence (continued)"}, total)
        ctx.canvas.table(MX, TOP - 0.2, cw, [["ID", "Claim", "Status", "Source"]] + [r for r, _ in page], styles,
                         [0.32] + [h for _, h in page])


LAYOUTS = {
    "cover": cover, "section": section, "statement": statement, "closing": closing, "points": points,
    "bullets": bullets, "split": split, "metrics": metrics, "chart": chart, "market": market,
    "comparison": comparison, "positioning": positioning, "roadmap": roadmap, "products": products,
    "diagram": diagram, "screenshot": screenshot, "team": team, "ask": ask, "table": table, "quote": quote,
    "sources": sources,
}

TEXT_FIELDS = ("title", "text", "subtitle", "support", "takeaway", "body", "summary")


def slide_numeric_warnings(s: Dict) -> List[str]:
    """Numbers in free text with no evidence anywhere on the slide."""
    has_ev = bool(s.get("evidence")) or any(
        isinstance(v, list) and any(isinstance(i, dict) and i.get("evidence") for i in v) for v in s.values()) or bool(
        isinstance(s.get("chart"), dict) and (s["chart"].get("evidence") or s["chart"].get("source")))
    if has_ev or s.get("type") in ("cover", "sources", "ask", "roadmap", "section"):
        return []
    found = []
    for f in TEXT_FIELDS:
        found += numeric_claims(str(s.get(f, "")))
    for k in ("points", "items"):
        for it in s.get(k, []) or []:
            if isinstance(it, dict):
                for f in ("title", "body", "lead", "detail", "description"):
                    found += numeric_claims(str(it.get(f, "")))
    return found
