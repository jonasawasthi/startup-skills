"""PDF backend for slide layouts (reportlab).  Vector output, embedded fonts."""
from __future__ import annotations

from typing import Dict, List, Sequence

from reportlab.lib.colors import HexColor
from reportlab.pdfgen import canvas as rl_canvas

from .. import fonts
from .base import Canvas, ChartSpec, FitResult, TextStyle, fit_text, format_value, image_box, image_size, nice_max


class PdfCanvas(Canvas):
    def __init__(self, width_in=13.333, height_in=7.5, title="", author="", subject=""):
        self.width, self.height = width_in, height_in
        self._pages = 0
        self._c = None
        self._meta = dict(title=title, author=author, subject=subject)
        self._path = None

    # coordinate helpers
    def _X(self, x):
        return x * 72

    def _Y(self, y):
        return (self.height - y) * 72

    def begin(self, path):
        self._path = path
        self._c = rl_canvas.Canvas(path, pagesize=(self.width * 72, self.height * 72), pageCompression=1)
        self._c.setTitle(self._meta["title"])
        self._c.setAuthor(self._meta["author"])
        self._c.setSubject(self._meta["subject"])
        self._c.setCreator("Startup Skills (startup-kit)")

    def new_page(self, background="#FFFFFF"):
        if self._c is None:
            raise RuntimeError("call begin(path) first")
        if self._pages:
            self._c.showPage()
        self._pages += 1
        self.rect(0, 0, self.width, self.height, fill=background)

    def rect(self, x, y, w, h, fill=None, line=None, line_w=0.75, radius=0.0):
        c = self._c
        c.saveState()
        if fill:
            c.setFillColor(HexColor(fill))
        if line:
            c.setStrokeColor(HexColor(line))
            c.setLineWidth(line_w)
        if radius:
            c.roundRect(self._X(x), self._Y(y + h), w * 72, h * 72, radius * 72, stroke=1 if line else 0,
                        fill=1 if fill else 0)
        else:
            c.rect(self._X(x), self._Y(y + h), w * 72, h * 72, stroke=1 if line else 0, fill=1 if fill else 0)
        c.restoreState()

    def ellipse(self, x, y, w, h, fill=None, line=None, line_w=0.75):
        c = self._c
        c.saveState()
        if fill:
            c.setFillColor(HexColor(fill))
        if line:
            c.setStrokeColor(HexColor(line))
            c.setLineWidth(line_w)
        c.ellipse(self._X(x), self._Y(y + h), self._X(x + w), self._Y(y), stroke=1 if line else 0, fill=1 if fill else 0)
        c.restoreState()

    def line(self, x1, y1, x2, y2, color="#000000", width=0.75, dash=False, arrow=False):
        c = self._c
        c.saveState()
        c.setStrokeColor(HexColor(color))
        c.setLineWidth(width)
        if dash:
            c.setDash(3, 3)
        c.line(self._X(x1), self._Y(y1), self._X(x2), self._Y(y2))
        if arrow:
            import math
            ang = math.atan2(-(y2 - y1), x2 - x1)
            L = 7
            p = c.beginPath()
            tx, ty = self._X(x2), self._Y(y2)
            p.moveTo(tx, ty)
            p.lineTo(tx - L * math.cos(ang - 0.4), ty - L * math.sin(ang - 0.4))
            p.lineTo(tx - L * math.cos(ang + 0.4), ty - L * math.sin(ang + 0.4))
            p.close()
            c.setFillColor(HexColor(color))
            c.drawPath(p, stroke=0, fill=1)
        c.restoreState()

    def text(self, x, y, w, h, text, style: TextStyle, fit: FitResult = None):
        fit = fit or fit_text(text, style, w, h)
        size = fit.size
        lead = size * style.leading
        block = len(fit.lines) * lead
        top = y * 72
        if style.valign == "middle":
            top += (h * 72 - block) / 2
        elif style.valign == "bottom":
            top += h * 72 - block
        c = self._c
        c.saveState()
        c.setFillColor(HexColor(style.color))
        fname = fonts.pdf_font(style.font, style.bold, style.italic)
        c.setFont(fname, size)
        for i, ln in enumerate(fit.lines):
            # baseline: top of line box + half the extra leading + ascent (~0.8 em)
            baseline = top + i * lead + (lead - size) / 2 + size * 0.82
            yy = self.height * 72 - baseline
            if style.align == "center":
                c.drawCentredString(self._X(x + w / 2), yy, ln)
            elif style.align == "right":
                c.drawRightString(self._X(x + w), yy, ln)
            else:
                c.drawString(self._X(x), yy, ln)
        c.restoreState()

    def image(self, path, x, y, w, h, fit="contain"):
        iw, ih = image_size(path)
        bx, by, bw, bh = image_box(iw, ih, x, y, w, h, fit)
        self._c.drawImage(path, self._X(bx), self._Y(by + bh), bw * 72, bh * 72, mask="auto")

    def link(self, x, y, w, h, url):
        self._c.linkURL(url, (self._X(x), self._Y(y + h), self._X(x + w), self._Y(y)), relative=0)

    def table(self, x, y, col_widths: Sequence[float], rows: List[List[str]], styles: Dict, row_heights):
        hs: TextStyle = styles["header"]
        bs: TextStyle = styles["body"]
        first_col: TextStyle = styles.get("first_col", bs)
        rule = styles.get("rule", "#D9DDE1")
        header_fill = styles.get("header_fill")
        zebra = styles.get("zebra")
        pad = styles.get("pad", 0.08)
        cy = y
        for r, row in enumerate(rows):
            rh = row_heights[r]
            cx = x
            if r == 0 and header_fill:
                self.rect(x, cy, sum(col_widths), rh, fill=header_fill)
            elif r > 0 and zebra and r % 2 == 0:
                self.rect(x, cy, sum(col_widths), rh, fill=zebra)
            for ci, cell in enumerate(row):
                st = hs if r == 0 else (first_col if ci == 0 else bs)
                st = st.with_(valign="middle")
                cell_style = styles.get("cell_styles", {}).get((r, ci))
                if cell_style:
                    st = st.with_(**cell_style)
                self.text(cx + pad, cy, col_widths[ci] - 2 * pad, rh, str(cell), st)
                cx += col_widths[ci]
            cy += rh
            self.line(x, cy, x + sum(col_widths), cy, rule, 1.2 if r == 0 else 0.5)

    def chart(self, x, y, w, h, spec: ChartSpec, theme):
        colors = spec.colors or theme.palette(max(len(spec.series), 1))
        n_series = len(spec.series)
        legend = spec.show_legend if spec.show_legend is not None else n_series > 1
        label_style = TextStyle(font=theme.body_font, size=9, color=theme.muted)
        value_style = TextStyle(font=theme.body_font, size=9, color=theme.ink, bold=True)
        top_pad = 0.3 if legend else 0.05
        if legend:
            lx = x
            for i, s in enumerate(spec.series):
                self.rect(lx, y + 0.06, 0.12, 0.12, fill=colors[i % len(colors)])
                tw = fonts.width(s["name"], theme.body_font, 9) / 72
                self.text(lx + 0.18, y, tw + 0.1, 0.25, s["name"], label_style.with_(valign="middle"))
                lx += 0.18 + tw + 0.3
        cats = spec.categories
        if spec.kind == "bar":  # horizontal bars
            vals = spec.series[0]["values"]
            vmax = nice_max(max([v for v in vals if v is not None] or [1]))
            label_w = min(w * 0.38, max(fonts.width(c, theme.body_font, 9) / 72 for c in cats) + 0.15)
            row_h = (h - top_pad) / max(len(cats), 1)
            bar_h = min(row_h * 0.62, 0.42)
            for i, (cname, v) in enumerate(zip(cats, vals)):
                ry = y + top_pad + i * row_h
                self.text(x, ry, label_w - 0.1, row_h, cname, label_style.with_(valign="middle", align="right"))
                bw = (w - label_w - 0.8) * (v or 0) / vmax
                col = colors[0] if spec.highlight in (None, i) else theme.rule
                self.rect(x + label_w, ry + (row_h - bar_h) / 2, max(bw, 0.01), bar_h, fill=col)
                if spec.show_values:
                    self.text(x + label_w + bw + 0.06, ry, 0.9, row_h,
                              format_value(v, spec.number_format, spec.prefix, spec.suffix),
                              value_style.with_(valign="middle"))
            return
        # vertical: column / stacked-column / line
        axis_h = 0.32
        plot_y, plot_h = y + top_pad + 0.2, h - top_pad - 0.2 - axis_h
        if spec.kind == "stacked-column":
            totals = [sum((s["values"][i] or 0) for s in spec.series) for i in range(len(cats))]
            vmax = nice_max(max(totals or [1]))
        else:
            vmax = nice_max(max([v for s in spec.series for v in s["values"] if v is not None] or [1]))
        n = max(len(cats), 1)
        slot = w / n
        base_y = plot_y + plot_h
        self.line(x, base_y, x + w, base_y, theme.rule, 0.75)
        for i, cname in enumerate(cats):
            self.text(x + i * slot, base_y + 0.06, slot, axis_h, str(cname), label_style.with_(align="center"))
        if spec.kind == "line":
            for si, s in enumerate(spec.series):
                pts = [(x + (i + 0.5) * slot, base_y - plot_h * (v or 0) / vmax) for i, v in enumerate(s["values"])]
                col = colors[si % len(colors)]
                for (x1, y1), (x2, y2) in zip(pts, pts[1:]):
                    self.line(x1, y1, x2, y2, col, 2.0)
                for i, (px, py) in enumerate(pts):
                    self.ellipse(px - 0.04, py - 0.04, 0.08, 0.08, fill=col)
                    if spec.show_values and (n <= 8 or i == len(pts) - 1):
                        self.text(px - 0.5, py - 0.3, 1.0, 0.24,
                                  format_value(s["values"][i], spec.number_format, spec.prefix, spec.suffix),
                                  value_style.with_(align="center"))
            return
        group_w = slot * 0.66
        for i in range(len(cats)):
            gx = x + i * slot + (slot - group_w) / 2
            if spec.kind == "stacked-column":
                acc = 0.0
                for si, s in enumerate(spec.series):
                    v = s["values"][i] or 0
                    bh = plot_h * v / vmax
                    self.rect(gx, base_y - plot_h * acc / vmax - bh, group_w, bh, fill=colors[si % len(colors)])
                    acc += v
                if spec.show_values:
                    self.text(gx - 0.3, base_y - plot_h * acc / vmax - 0.26, group_w + 0.6, 0.24,
                              format_value(acc, spec.number_format, spec.prefix, spec.suffix),
                              value_style.with_(align="center"))
            else:
                bw = group_w / n_series
                for si, s in enumerate(spec.series):
                    v = s["values"][i] or 0
                    bh = plot_h * v / vmax
                    col = colors[si % len(colors)]
                    if n_series == 1 and spec.highlight is not None and spec.highlight != i:
                        col = theme.rule
                    self.rect(gx + si * bw, base_y - bh, bw * 0.92, bh, fill=col)
                    if spec.show_values:
                        self.text(gx + si * bw - 0.3, base_y - bh - 0.26, bw + 0.6, 0.24,
                                  format_value(v, spec.number_format, spec.prefix, spec.suffix),
                                  value_style.with_(align="center"))

    def save(self, path=None):
        self._c.showPage()
        self._c.save()
