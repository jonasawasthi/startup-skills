"""PDF renderer for parsed Markdown documents (reportlab platypus)."""
from __future__ import annotations

import os
from typing import Dict, List
from xml.sax.saxutils import escape

from reportlab.lib.colors import HexColor
from reportlab.lib.enums import TA_LEFT
from reportlab.lib.pagesizes import A4, LETTER
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import cm
from reportlab.pdfgen import canvas as rl_canvas
from reportlab.platypus import (BaseDocTemplate, Frame, Image, KeepTogether, ListFlowable, ListItem, NextPageTemplate,
                                PageBreak, PageTemplate, Paragraph, Preformatted, Spacer, Table, TableStyle)
from reportlab.platypus.tableofcontents import TableOfContents

from .. import fonts
from .markdown import Block, Run, plain


def _numbered_canvas_factory(meta, theme):
    class NumberedCanvas(rl_canvas.Canvas):
        def __init__(self, *a, **k):
            super().__init__(*a, **k)
            self._saved = []

        def showPage(self):
            self._saved.append(dict(self.__dict__))
            self._startPage()

        def save(self):
            n = len(self._saved)
            for i, state in enumerate(self._saved):
                self.__dict__.update(state)
                if i > 0:  # no chrome on cover
                    self._chrome(i + 1, n)
                super().showPage()
            super().save()

        def _chrome(self, page, total):
            w, h = self._pagesize
            self.saveState()
            self.setFont(fonts.pdf_font(theme.body_font), 7.5)
            self.setFillColor(HexColor(theme.faint))
            left = " · ".join(x for x in [meta.get("company", ""), meta.get("title", "")] if x)
            self.drawString(2.3 * cm, h - 1.4 * cm, left[:110])
            self.drawString(2.3 * cm, 1.2 * cm, str(meta.get("confidentiality", "Confidential")))
            self.drawRightString(w - 2.3 * cm, 1.2 * cm, f"Page {page} of {total}")
            self.setStrokeColor(HexColor(theme.rule))
            self.setLineWidth(0.4)
            self.line(2.3 * cm, h - 1.55 * cm, w - 2.3 * cm, h - 1.55 * cm)
            self.restoreState()
    return NumberedCanvas


class _Doc(BaseDocTemplate):
    def afterFlowable(self, f):
        if isinstance(f, Paragraph) and getattr(f, "_toc_level", None) is not None:
            key = f"h{id(f)}"
            self.canv.bookmarkPage(key)
            self.notify("TOCEntry", (f._toc_level, f.getPlainText(), self.page, key))
            self.canv.addOutlineEntry(f.getPlainText()[:80], key, level=f._toc_level, closed=f._toc_level > 0)


class PdfRenderer:
    def __init__(self, meta: Dict, theme, ledger, base_dir: str, tmp_dir: str):
        self.meta, self.t, self.ledger, self.base, self.tmp = meta, theme, ledger, base_dir, tmp_dir
        self.story: List = []
        self.issues: List[str] = []
        self.fig_no = 0
        self.h_numbers = [0, 0, 0, 0]
        t = theme
        for fam in {t.body_font, t.heading_font, t.mono_font}:
            fonts.register(fam)
        body = fonts.pdf_font(t.body_font)
        self.S = {
            "body": ParagraphStyle("body", fontName=body, fontSize=t.doc_body, leading=t.doc_body * 1.42,
                                   textColor=HexColor(t.ink), spaceAfter=6.5, alignment=TA_LEFT),
            "h1": ParagraphStyle("h1", fontName=fonts.pdf_font(t.heading_font, bold=t.heading_font != "Georgia"),
                                 fontSize=t.doc_h1, leading=t.doc_h1 * 1.18, textColor=HexColor(t.ink), spaceBefore=16,
                                 spaceAfter=8, keepWithNext=1),
            "h2": ParagraphStyle("h2", fontName=fonts.pdf_font(t.heading_font, bold=True), fontSize=t.doc_h2,
                                 leading=t.doc_h2 * 1.2, textColor=HexColor(t.accent), spaceBefore=12, spaceAfter=5,
                                 keepWithNext=1),
            "h3": ParagraphStyle("h3", fontName=fonts.pdf_font(t.body_font, bold=True), fontSize=t.doc_h3,
                                 leading=t.doc_h3 * 1.25, textColor=HexColor(t.ink), spaceBefore=9, spaceAfter=3,
                                 keepWithNext=1),
            "h4": ParagraphStyle("h4", fontName=fonts.pdf_font(t.body_font, bold=True), fontSize=t.doc_body,
                                 leading=t.doc_body * 1.3, textColor=HexColor(t.muted), spaceBefore=6, spaceAfter=2,
                                 keepWithNext=1),
            "cell": ParagraphStyle("cell", fontName=body, fontSize=t.doc_small + 0.5, leading=(t.doc_small + 0.5) * 1.3,
                                   textColor=HexColor(t.ink)),
            "cellh": ParagraphStyle("cellh", fontName=fonts.pdf_font(t.body_font, bold=True), fontSize=t.doc_small + 0.5,
                                    leading=(t.doc_small + 0.5) * 1.3, textColor=HexColor(t.ink)),
            "caption": ParagraphStyle("caption", fontName=body, fontSize=t.doc_small, leading=t.doc_small * 1.35,
                                      textColor=HexColor(t.muted), spaceBefore=3, spaceAfter=10),
            "code": ParagraphStyle("code", fontName=fonts.pdf_font(t.mono_font), fontSize=8, leading=10.5,
                                   textColor=HexColor(t.ink)),
        }

    # ------------------------------------------------------------ inline
    def markup(self, runs: List[Run]) -> str:
        t = self.t
        out = []
        for r in runs:
            s = escape(r.text)
            if r.code:
                s = f'<font face="{fonts.pdf_font(t.mono_font)}">{s}</font>'
            if r.bold:
                s = f"<b>{s}</b>"
            if r.italic:
                s = f"<i>{s}</i>"
            if r.link:
                s = f'<a href="{escape(r.link)}" color="{t.accent}"><u>{s}</u></a>'
            if r.cite:
                for cid in r.cite:
                    if self.ledger is not None and cid not in self.ledger:
                        self.issues.append(f"citation {cid} not found in ledger")
                s = f'<super><font size="6.5" color="{t.accent}">{s}</font></super>'
            out.append(s)
        return "".join(out)

    # ------------------------------------------------------------ cover
    def cover(self):
        t, m = self.t, self.meta
        st = lambda name, **kw: ParagraphStyle(name, **{**dict(fontName=fonts.pdf_font(t.body_font), fontSize=10,
                                                                 leading=13, textColor=HexColor(t.muted)), **kw})
        items = []
        logo = m.get("logo")
        if logo:
            lp = logo if os.path.isabs(logo) else os.path.join(self.base, logo)
            if os.path.exists(lp):
                img = Image(lp)
                ratio = img.imageWidth / img.imageHeight
                img.drawHeight, img.drawWidth = 1.4 * cm, 1.4 * cm * ratio
                img.hAlign = "LEFT"
                items.append(img)
        if t.cover_style == "institutional":
            items += [Spacer(1, 1.2 * cm),
                      Paragraph(escape(str(m.get("organisation", m.get("company", ""))).upper()),
                                st("o", textColor=HexColor(t.accent), fontName=fonts.pdf_font(t.body_font, True))),
                      Spacer(1, 3.2 * cm),
                      Paragraph(escape(str(m.get("doc_type_label", m.get("doc_type", "Proposal"))).upper()),
                                st("dt", fontName=fonts.pdf_font(t.body_font, True))),
                      Spacer(1, 0.3 * cm),
                      Paragraph(escape(str(m.get("title", ""))), st("t", fontName=fonts.pdf_font(t.heading_font, True),
                                                                    fontSize=26, leading=31, textColor=HexColor(t.ink))),
                      Spacer(1, 0.3 * cm)]
            if m.get("subtitle"):
                items.append(Paragraph(escape(str(m["subtitle"])), st("s", fontSize=13, leading=17)))
            items.append(Spacer(1, 1.6 * cm))
            rows = [[k.replace("_", " ").title(), str(m[k])] for k in
                    ("submitted_to", "submitted_by", "date", "version", "reference", "confidentiality") if m.get(k)]
            if rows:
                tb = Table([[Paragraph(f"<b>{escape(a)}</b>", self.S["cell"]), Paragraph(escape(b), self.S["cell"])]
                            for a, b in rows], colWidths=[4.5 * cm, 10.5 * cm], hAlign="LEFT")
                tb.setStyle(TableStyle([("LINEBELOW", (0, 0), (-1, -1), 0.4, HexColor(t.rule)),
                                        ("TOPPADDING", (0, 0), (-1, -1), 5), ("BOTTOMPADDING", (0, 0), (-1, -1), 5)]))
                items.append(tb)
        else:
            items += [Spacer(1, 6.5 * cm if t.cover_style == "editorial" else 4 * cm)]
            bar = Table([[""]], colWidths=[2.2 * cm], rowHeights=[0.13 * cm], hAlign="LEFT")
            bar.setStyle(TableStyle([("BACKGROUND", (0, 0), (-1, -1), HexColor(t.accent))]))
            items += [bar, Spacer(1, 0.5 * cm)]
            if m.get("doc_type_label") or m.get("doc_type"):
                items.append(Paragraph(escape(str(m.get("doc_type_label", m.get("doc_type"))).upper()),
                                       st("dt", textColor=HexColor(t.accent), fontName=fonts.pdf_font(t.body_font, True),
                                          fontSize=9)))
                items.append(Spacer(1, 0.25 * cm))
            items.append(Paragraph(escape(str(m.get("title", ""))),
                                   st("t", fontName=fonts.pdf_font(t.heading_font, t.cover_style != "editorial"),
                                      fontSize=32, leading=37, textColor=HexColor(t.ink))))
            if m.get("subtitle"):
                items += [Spacer(1, 0.35 * cm), Paragraph(escape(str(m["subtitle"])), st("s", fontSize=14, leading=19))]
            items.append(Spacer(1, 3.2 * cm))
            for k in ("company", "prepared_for", "author", "date", "version"):
                if m.get(k):
                    items.append(Paragraph(escape(str(m[k])), st("m")))
            items += [Spacer(1, 0.6 * cm), Paragraph(escape(str(m.get("confidentiality", "Confidential"))),
                                                    st("c", fontSize=8.5, textColor=HexColor(t.faint)))]
        if m.get("disclaimer"):
            items += [Spacer(1, 1.0 * cm), Paragraph(f"<i>{escape(str(m['disclaimer']))}</i>",
                                                    st("d", fontSize=8, leading=11, textColor=HexColor(t.faint)))]
        self.story += items + [NextPageTemplate("body"), PageBreak()]

    # ------------------------------------------------------------ blocks
    def heading(self, b: Block):
        lvl = min(b.level, 4)
        text = plain(b.runs)
        if self.t.numbered_headings and lvl <= 3:
            self.h_numbers[lvl - 1] += 1
            for k in range(lvl, 4):
                self.h_numbers[k] = 0
            text = ".".join(str(n) for n in self.h_numbers[:lvl]) + "  " + text
        p = Paragraph(escape(text), self.S[f"h{lvl}"])
        p._is_heading = True
        if lvl <= 2:
            p._toc_level = lvl - 1
        self.story.append(p)

    def toc(self, entries):
        t = self.t
        toc = TableOfContents()
        toc.levelStyles = [
            ParagraphStyle("toc1", fontName=fonts.pdf_font(t.body_font, True), fontSize=10, leading=15,
                           textColor=HexColor(t.ink)),
            ParagraphStyle("toc2", fontName=fonts.pdf_font(t.body_font), fontSize=9.5, leading=13.5, leftIndent=14,
                           textColor=HexColor(t.muted)),
        ]
        toc.dotsMinLevel = 0
        self.story += [Paragraph(escape(self.meta.get("toc_title", "Contents")), self.S["h1"]), toc, PageBreak()]

    def para(self, b: Block):
        self.story.append(Paragraph(self.markup(b.runs), self.S["body"]))

    def lst(self, b: Block):
        items = []
        sub = []
        def flush_sub():
            nonlocal sub
            if sub and items:
                items[-1] = ListItem([items[-1]._flowables[0] if hasattr(items[-1], "_flowables") else items[-1],
                                      ListFlowable(sub, bulletType="bullet", start="–", leftIndent=12, bulletFontSize=8)])
            sub = []
        for depth, runs in b.items:
            p = Paragraph(self.markup(runs), ParagraphStyle("li", parent=self.S["body"], spaceAfter=2.5))
            if depth:
                sub.append(ListItem(p, leftIndent=12))
            else:
                flush_sub()
                items.append(ListItem(p, leftIndent=14))
        flush_sub()
        lf = ListFlowable(items, bulletType="1" if b.ordered else "bullet", start=None if b.ordered else "•",
                          leftIndent=14, bulletFontSize=8 if not b.ordered else self.t.doc_body - 1,
                          bulletColor=HexColor(self.t.accent), bulletFontName=fonts.pdf_font(self.t.body_font))
        self.story += [lf, Spacer(1, 4)]

    def table(self, b: Block):
        t = self.t
        ncols = max(len(b.header), max((len(r) for r in b.rows), default=0))
        data = [[Paragraph(self.markup(b.header[i]) if i < len(b.header) else "", self.S["cellh"]) for i in range(ncols)]]
        for row in b.rows:
            data.append([Paragraph(self.markup(row[i]) if i < len(row) else "",
                                   ParagraphStyle("c", parent=self.S["cell"],
                                                  alignment=2 if i < len(b.align) and b.align[i] == "right" else 0))
                         for i in range(ncols)])
        widths = self._col_widths(b, ncols)
        tb = Table(data, colWidths=widths, repeatRows=1, hAlign="LEFT")
        tb.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), HexColor(t.tint)),
            ("LINEBELOW", (0, 0), (-1, 0), 0.9, HexColor(t.ink)),
            ("LINEBELOW", (0, 1), (-1, -1), 0.35, HexColor(t.rule)),
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("TOPPADDING", (0, 0), (-1, -1), 4), ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
            ("LEFTPADDING", (0, 0), (-1, -1), 5), ("RIGHTPADDING", (0, 0), (-1, -1), 5)]))
        self.story += [tb, Spacer(1, 9)]

    def _col_widths(self, b: Block, ncols: int) -> List[float]:
        """Each column gets at least its longest word (measured); the rest is shared by text length."""
        avail = self._frame_w
        size = self.t.doc_small + 0.5
        pad = 15  # 10pt cell padding + slack for rounding
        mins, lens = [], []
        for i in range(ncols):
            cells = ([plain(b.header[i])] if i < len(b.header) else []) + [plain(r[i]) for r in b.rows if i < len(r)]
            words = [w for c in cells for w in c.split()] or [""]
            bold_head = fonts.width(cells[0], self.t.body_font, size, True) + pad if cells and len(cells[0]) < 14 else 0
            longest = max(fonts.width(w, self.t.body_font, size) for w in words) + pad
            # long unbreakable tokens (URLs) may wrap; never let one column starve the others
            mins.append(max(min(longest, avail * 0.3), bold_head, 28))
            lens.append(min(max((len(c) for c in cells), default=4), 80))
        if sum(mins) >= avail:
            return [avail * m / sum(mins) for m in mins]
        extra = avail - sum(mins)
        flex = [max(l - m / (size * 0.5), 0) for l, m in zip(lens, mins)]
        tot = sum(flex) or 1
        return [m + extra * f / tot for m, f in zip(mins, flex)]

    def callout(self, b: Block):
        t = self.t
        colors = {"NOTE": t.accent, "KEY": t.accent, "TIP": t.positive, "WARNING": t.warning,
                  "ASSUMPTION": t.warning, "RISK": t.negative, "QUOTE": t.muted, "IMPORTANT": t.accent_2}
        col = colors.get(b.callout, t.accent)
        from ..theme import mix
        label = "" if b.callout == "QUOTE" else f'<font color="{col}"><b>{b.callout.title()}</b></font>&nbsp;&nbsp;'
        body = self.markup(b.runs)
        if b.callout == "QUOTE":
            body = f"<i>{body}</i>"
        p = Paragraph(label + body, ParagraphStyle("co", parent=self.S["body"], fontSize=self.t.doc_body - 0.5,
                                                   spaceAfter=0))
        tb = Table([[p]], colWidths=[self._frame_w])
        tb.setStyle(TableStyle([("BACKGROUND", (0, 0), (-1, -1), HexColor(mix(col, "#FFFFFF", 0.92))),
                                ("LINEBEFORE", (0, 0), (0, -1), 3, HexColor(col)),
                                ("LEFTPADDING", (0, 0), (-1, -1), 10), ("RIGHTPADDING", (0, 0), (-1, -1), 10),
                                ("TOPPADDING", (0, 0), (-1, -1), 7), ("BOTTOMPADDING", (0, 0), (-1, -1), 7)]))
        self.story += [tb, Spacer(1, 9)]

    def code(self, b: Block):
        tb = Table([[Preformatted(b.text, self.S["code"])]], colWidths=[self._frame_w])
        tb.setStyle(TableStyle([("BACKGROUND", (0, 0), (-1, -1), HexColor(self.t.tint)),
                                ("LEFTPADDING", (0, 0), (-1, -1), 8), ("TOPPADDING", (0, 0), (-1, -1), 6),
                                ("BOTTOMPADDING", (0, 0), (-1, -1), 6)]))
        self.story += [tb, Spacer(1, 8)]

    def _img(self, path, max_w):
        img = Image(path)
        ratio = img.imageHeight / img.imageWidth
        w = min(max_w, self._frame_w)
        img.drawWidth, img.drawHeight = w, w * ratio
        return img

    def image(self, path, caption, width_cm=16.0):
        if not os.path.exists(path):
            self.issues.append(f"image not found: {path}")
            self.story.append(Paragraph(f'<font color="{self.t.negative}">[Missing figure: {escape(caption or path)}]</font>',
                                        self.S["body"]))
            return
        parts = [self._img(path, width_cm * cm)]
        if caption:
            self.fig_no += 1
            parts.append(Paragraph(f"Figure {self.fig_no}. {escape(caption)}", self.S["caption"]))
        self.story.append(KeepTogether(parts))

    def chart(self, b: Block, png: str, errors: List[str]):
        if errors:
            self.issues.extend(errors)
            self.story.append(Paragraph(f'<font color="{self.t.negative}">[Chart omitted: {escape("; ".join(errors))}]</font>',
                                        self.S["body"]))
            return
        self.fig_no += 1
        src = b.data.get("source", "")
        ev = b.data.get("evidence")
        ev_s = ", ".join(ev) if isinstance(ev, list) else (ev or "")
        badge = self.ledger.badge(ev if isinstance(ev, list) else [ev]) if (ev and self.ledger is not None) else None
        tail = " · ".join(x for x in [f"Source: {src}" if src else "", f"Evidence: {ev_s}" if ev_s else "",
                                       f"Status: {badge}" if badge else ""] if x)
        cap = f"Figure {self.fig_no}. {escape(str(b.data.get('title', '')))}" + (f" — {escape(tail)}" if tail else "")
        self.story.append(KeepTogether([self._img(png, 16 * cm), Paragraph(cap, self.S["caption"])]))

    def hr(self):
        tb = Table([[""]], colWidths=[self._frame_w], rowHeights=[2])
        tb.setStyle(TableStyle([("LINEBELOW", (0, 0), (-1, -1), 0.5, HexColor(self.t.rule))]))
        self.story += [tb, Spacer(1, 6)]

    def pagebreak(self):
        self.story.append(PageBreak())

    @property
    def _frame_w(self):
        size = A4 if str(self.meta.get("paper", "a4")).lower() == "a4" else LETTER
        return size[0] - 4.6 * cm

    def finish(self, path):
        size = A4 if str(self.meta.get("paper", "a4")).lower() == "a4" else LETTER
        doc = _Doc(path, pagesize=size, leftMargin=2.3 * cm, rightMargin=2.3 * cm, topMargin=2.3 * cm,
                   bottomMargin=2.1 * cm, title=str(self.meta.get("title", "")),
                   author=str(self.meta.get("author", self.meta.get("company", ""))),
                   subject=str(self.meta.get("subtitle", self.meta.get("doc_type", ""))),
                   creator="Startup Skills (startup-kit)",
                   keywords=", ".join(self.meta.get("keywords", [])) if isinstance(self.meta.get("keywords"), list) else "")
        frame = Frame(doc.leftMargin, doc.bottomMargin, doc.width, doc.height, id="f")
        doc.addPageTemplates([PageTemplate("cover", [frame]), PageTemplate("body", [frame])])
        doc.multiBuild(self._bind_headings(self.story), canvasmaker=_numbered_canvas_factory(self.meta, self.t))

    @staticmethod
    def _bind_headings(story):
        """Keep each run of headings together with the first flowable that follows (no orphaned headings)."""
        out, i = [], 0
        while i < len(story):
            group = []
            while i < len(story) and getattr(story[i], "_is_heading", False):
                group.append(story[i])
                i += 1
            if group:
                if i < len(story) and not isinstance(story[i], PageBreak):
                    group.append(story[i])
                    i += 1
                out.append(KeepTogether(group))
            else:
                out.append(story[i])
                i += 1
        return out
