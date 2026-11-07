"""DOCX renderer for parsed Markdown documents (python-docx)."""
from __future__ import annotations

import os
from typing import Dict, List

import docx
from docx.enum.section import WD_SECTION
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.enum.text import WD_ALIGN_PARAGRAPH, WD_BREAK
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Cm, Pt, RGBColor

from .markdown import Block, Run, plain

PAPER = {"a4": (Cm(21.0), Cm(29.7)), "letter": (Cm(21.59), Cm(27.94))}


def _rgb(h):
    h = h.lstrip("#")
    return RGBColor(int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16))


def _set_cell_fill(cell, hexcolor):
    tcPr = cell._tc.get_or_add_tcPr()
    shd = OxmlElement("w:shd")
    shd.set(qn("w:val"), "clear")
    shd.set(qn("w:color"), "auto")
    shd.set(qn("w:fill"), hexcolor.lstrip("#"))
    tcPr.append(shd)


def _set_cell_borders(cell, **edges):
    """edges: top/bottom/left/right = (size_eighths_pt, hex) or None for nil."""
    tcPr = cell._tc.get_or_add_tcPr()
    b = tcPr.find(qn("w:tcBorders"))
    if b is None:
        b = OxmlElement("w:tcBorders")
        tcPr.append(b)
    for edge in ("top", "left", "bottom", "right"):
        el = OxmlElement(f"w:{edge}")
        spec = edges.get(edge)
        if spec:
            el.set(qn("w:val"), "single")
            el.set(qn("w:sz"), str(spec[0]))
            el.set(qn("w:color"), spec[1].lstrip("#"))
        else:
            el.set(qn("w:val"), "nil")
        b.append(el)


def _field(paragraph, instr: str, placeholder: str = ""):
    r = paragraph.add_run()
    f1 = OxmlElement("w:fldChar")
    f1.set(qn("w:fldCharType"), "begin")
    r._r.append(f1)
    r2 = paragraph.add_run()
    it = OxmlElement("w:instrText")
    it.set(qn("xml:space"), "preserve")
    it.text = instr
    r2._r.append(it)
    r3 = paragraph.add_run()
    f2 = OxmlElement("w:fldChar")
    f2.set(qn("w:fldCharType"), "separate")
    r3._r.append(f2)
    r4 = paragraph.add_run(placeholder)
    r5 = paragraph.add_run()
    f3 = OxmlElement("w:fldChar")
    f3.set(qn("w:fldCharType"), "end")
    r5._r.append(f3)
    return [r, r2, r3, r4, r5]


def _hyperlink(paragraph, url, text, color, font):
    part = paragraph.part
    r_id = part.relate_to(url, "http://schemas.openxmlformats.org/officeDocument/2006/relationships/hyperlink",
                          is_external=True)
    h = OxmlElement("w:hyperlink")
    h.set(qn("r:id"), r_id)
    new_run = OxmlElement("w:r")
    rPr = OxmlElement("w:rPr")
    c = OxmlElement("w:color")
    c.set(qn("w:val"), color.lstrip("#"))
    rPr.append(c)
    u = OxmlElement("w:u")
    u.set(qn("w:val"), "single")
    rPr.append(u)
    new_run.append(rPr)
    t = OxmlElement("w:t")
    t.text = text
    t.set(qn("xml:space"), "preserve")
    new_run.append(t)
    h.append(new_run)
    paragraph._p.append(h)


class DocxRenderer:
    def __init__(self, meta: Dict, theme, ledger, base_dir: str, tmp_dir: str):
        self.meta, self.t, self.ledger, self.base, self.tmp = meta, theme, ledger, base_dir, tmp_dir
        self.d = docx.Document()
        self.fig_no = 0
        self.table_no = 0
        self.h_numbers = [0, 0, 0, 0]
        self.issues: List[str] = []
        self._setup()

    # ------------------------------------------------------------ setup
    def _setup(self):
        t, d = self.t, self.d
        sec = d.sections[0]
        w, h = PAPER.get(str(self.meta.get("paper", "a4")).lower(), PAPER["a4"])
        sec.page_width, sec.page_height = w, h
        sec.left_margin = sec.right_margin = Cm(2.3)
        sec.top_margin, sec.bottom_margin = Cm(2.4), Cm(2.2)
        sec.header_distance = sec.footer_distance = Cm(1.1)
        st = d.styles
        normal = st["Normal"]
        normal.font.name = t.body_font
        normal.element.rPr.rFonts.set(qn("w:eastAsia"), t.body_font)
        normal.font.size = Pt(t.doc_body)
        normal.font.color.rgb = _rgb(t.ink)
        pf = normal.paragraph_format
        pf.space_after = Pt(7)
        pf.line_spacing = 1.28
        for lvl, size, col, before, after in ((1, t.doc_h1, t.ink, 20, 8), (2, t.doc_h2, t.accent, 14, 5),
                                              (3, t.doc_h3, t.ink, 10, 3), (4, t.doc_body, t.muted, 8, 2)):
            hs = st[f"Heading {lvl}"]
            hs.font.name = t.heading_font
            rpr = hs.element.get_or_add_rPr()
            rf = rpr.find(qn("w:rFonts"))
            if rf is None:
                rf = OxmlElement("w:rFonts")
                rpr.append(rf)
            for a in ("w:ascii", "w:hAnsi", "w:eastAsia", "w:cs"):
                rf.set(qn(a), t.heading_font)
            for a in ("w:asciiTheme", "w:hAnsiTheme", "w:eastAsiaTheme", "w:cstheme"):
                if rf.get(qn(a)) is not None:
                    del rf.attrib[qn(a)]
            hs.font.size = Pt(size)
            hs.font.bold = lvl != 1 or t.heading_font != "Georgia"
            hs.font.italic = False
            hs.font.color.rgb = _rgb(col)
            hs.paragraph_format.space_before = Pt(before)
            hs.paragraph_format.space_after = Pt(after)
            hs.paragraph_format.keep_with_next = True
            hs.paragraph_format.line_spacing = 1.1
        for name in ("List Bullet", "List Number", "List Bullet 2", "List Number 2"):
            if name in [s.name for s in st]:
                st[name].font.name = t.body_font
                st[name].font.size = Pt(t.doc_body)
                st[name].paragraph_format.space_after = Pt(3)
        cp = d.core_properties
        cp.title = str(self.meta.get("title", ""))
        cp.subject = str(self.meta.get("subtitle", self.meta.get("doc_type", "")))
        cp.author = str(self.meta.get("author", self.meta.get("company", "")))
        cp.keywords = ", ".join(self.meta.get("keywords", [])) if isinstance(self.meta.get("keywords"), list) else str(
            self.meta.get("keywords", ""))
        cp.comments = "Generated by Startup Skills (startup-kit). Claims cite the evidence ledger."
        cp.category = str(self.meta.get("doc_type", ""))
        # ask Word to refresh fields (TOC, page counts) on open
        settings = d.settings.element
        uf = OxmlElement("w:updateFields")
        uf.set(qn("w:val"), "true")
        settings.append(uf)

    def _header_footer(self, sec):
        t = self.t
        sec.different_first_page_header_footer = True
        hp = sec.header.paragraphs[0]
        hp.text = ""
        r = hp.add_run(" · ".join(x for x in [self.meta.get("company", ""), self.meta.get("title", "")] if x))
        r.font.size = Pt(t.doc_small)
        r.font.color.rgb = _rgb(t.faint)
        fp = sec.footer.paragraphs[0]
        fp.text = ""
        tab_stop = sec.page_width - sec.left_margin - sec.right_margin
        fp.paragraph_format.tab_stops.add_tab_stop(tab_stop, alignment=2)  # right
        r = fp.add_run(str(self.meta.get("confidentiality", "Confidential")))
        r.font.size = Pt(t.doc_small)
        r.font.color.rgb = _rgb(t.faint)
        fp.add_run("\t")
        for run_text, instr in (("Page ", None), (None, "PAGE"), (" of ", None), (None, "NUMPAGES")):
            if instr:
                runs = _field(fp, instr, "1")
                for rr in runs:
                    rr.font.size = Pt(t.doc_small)
                    rr.font.color.rgb = _rgb(t.faint)
            else:
                rr = fp.add_run(run_text)
                rr.font.size = Pt(t.doc_small)
                rr.font.color.rgb = _rgb(t.faint)

    # ------------------------------------------------------------ cover
    def cover(self):
        t, d, m = self.t, self.d, self.meta
        style = t.cover_style
        def para(text, size, color, bold=False, font=None, before=0, after=6, align=None, italic=False):
            p = d.add_paragraph()
            p.paragraph_format.space_before = Pt(before)
            p.paragraph_format.space_after = Pt(after)
            p.paragraph_format.line_spacing = 1.1
            if align:
                p.alignment = align
            r = p.add_run(text)
            r.font.size = Pt(size)
            r.font.color.rgb = _rgb(color)
            r.font.bold = bold
            r.font.italic = italic
            r.font.name = font or t.body_font
            return p
        logo = m.get("logo")
        if logo:
            lp = logo if os.path.isabs(logo) else os.path.join(self.base, logo)
            if os.path.exists(lp):
                d.add_picture(lp, height=Cm(1.4))
        if style == "institutional":
            para(str(m.get("organisation", m.get("company", ""))).upper(), 10, t.accent, bold=True, before=0, after=60)
            para(str(m.get("doc_type_label", m.get("doc_type", "Proposal"))).upper(), 10, t.muted, bold=True, after=10)
            para(m.get("title", ""), 26, t.ink, bold=True, font=t.heading_font, after=10)
            if m.get("subtitle"):
                para(m["subtitle"], 13, t.muted, after=40)
            tbl = d.add_table(rows=0, cols=2)
            for k in ("submitted_to", "submitted_by", "date", "version", "reference", "confidentiality"):
                if m.get(k):
                    row = tbl.add_row().cells
                    row[0].text = k.replace("_", " ").title()
                    row[1].text = str(m[k])
                    for c in row:
                        for p in c.paragraphs:
                            for r in p.runs:
                                r.font.size = Pt(9.5)
                        _set_cell_borders(c, bottom=(4, t.rule))
                    row[0].paragraphs[0].runs[0].font.bold = True
                    row[0].paragraphs[0].runs[0].font.color.rgb = _rgb(t.muted)
        else:
            para("", 10, t.ink, before=110 if style == "editorial" else 60)
            # accent rule
            p = d.add_paragraph()
            r = p.add_run("━━━━")
            r.font.color.rgb = _rgb(t.accent)
            r.font.size = Pt(14)
            if m.get("doc_type_label") or m.get("doc_type"):
                para(str(m.get("doc_type_label", m.get("doc_type"))).upper(), 9.5, t.accent, bold=True, after=8)
            para(m.get("title", ""), 30 if style == "editorial" else 26, t.ink, font=t.heading_font, after=10,
                 bold=style != "editorial")
            if m.get("subtitle"):
                para(m["subtitle"], 14, t.muted, after=90)
            meta_lines = [str(m[k]) for k in ("company", "prepared_for", "author", "date", "version") if m.get(k)]
            for line in meta_lines:
                para(line, 10, t.muted, after=2)
            para(str(m.get("confidentiality", "Confidential")), 9, t.faint, before=24)
        if m.get("disclaimer"):
            para(m["disclaimer"], 8.5, t.faint, before=30, italic=True)
        d.add_paragraph().add_run().add_break(WD_BREAK.PAGE)

    # ------------------------------------------------------------ inline
    def runs(self, p, runs: List[Run], size=None, color=None, bold=None):
        t = self.t
        for r in runs:
            if r.link:
                _hyperlink(p, r.link, r.text, t.accent, t.body_font)
                continue
            rr = p.add_run(r.text)
            rr.bold = r.bold if bold is None else (bold or r.bold)
            rr.italic = r.italic
            if size:
                rr.font.size = Pt(size)
            if color:
                rr.font.color.rgb = _rgb(color)
            if r.code:
                rr.font.name = t.mono_font
                rr.font.size = Pt((size or t.doc_body) - 1)
            if r.cite:
                rr.font.superscript = True
                rr.font.size = Pt(7)
                rr.font.color.rgb = _rgb(t.accent)
                for cid in r.cite:
                    if self.ledger is not None and cid not in self.ledger:
                        self.issues.append(f"citation {cid} not found in ledger")

    # ------------------------------------------------------------ blocks
    def heading(self, b: Block):
        lvl = min(b.level, 4)
        text = plain(b.runs)
        if self.t.numbered_headings and lvl <= 3:
            self.h_numbers[lvl - 1] += 1
            for k in range(lvl, 4):
                self.h_numbers[k] = 0 if k >= lvl else self.h_numbers[k]
            num = ".".join(str(n) for n in self.h_numbers[:lvl])
            text = f"{num}  {text}"
        p = self.d.add_paragraph(style=f"Heading {lvl}")
        p.add_run(text)
        if lvl == 1 and self.meta.get("h1_page_break", False):
            p.paragraph_format.page_break_before = True

    def toc(self, entries):
        t = self.t
        p = self.d.add_paragraph(style="Heading 1")
        p.add_run(self.meta.get("toc_title", "Contents"))
        # Real Word TOC field (updated with page numbers by Word); pre-filled with the heading list so that
        # viewers that do not update fields (Pages, previewers) still show meaningful contents.
        first = True
        paras = []
        for lvl, text in entries:
            q = self.d.add_paragraph()
            q.paragraph_format.left_indent = Cm(0.6 * (lvl - 1))
            q.paragraph_format.space_after = Pt(2)
            paras.append((q, text, lvl))
        if not paras:
            return
        q0 = paras[0][0]
        r = q0.add_run()
        fc = OxmlElement("w:fldChar")
        fc.set(qn("w:fldCharType"), "begin")
        r._r.append(fc)
        r = q0.add_run()
        it = OxmlElement("w:instrText")
        it.set(qn("xml:space"), "preserve")
        it.text = 'TOC \\o "1-2" \\h \\z \\u'
        r._r.append(it)
        r = q0.add_run()
        fc = OxmlElement("w:fldChar")
        fc.set(qn("w:fldCharType"), "separate")
        r._r.append(fc)
        for q, text, lvl in paras:
            rr = q.add_run(text)
            rr.font.size = Pt(t.doc_body if lvl == 1 else t.doc_body - 0.5)
            rr.font.bold = lvl == 1
            rr.font.color.rgb = _rgb(t.ink if lvl == 1 else t.muted)
        r = paras[-1][0].add_run()
        fc = OxmlElement("w:fldChar")
        fc.set(qn("w:fldCharType"), "end")
        r._r.append(fc)
        self.d.add_paragraph().add_run().add_break(WD_BREAK.PAGE)

    def para(self, b: Block):
        p = self.d.add_paragraph()
        self.runs(p, b.runs)

    def lst(self, b: Block):
        n = 0
        for depth, runs in b.items:
            style = ("List Number" if b.ordered else "List Bullet") + (" 2" if depth else "")
            p = self.d.add_paragraph(style=style)
            self.runs(p, runs)
            n += 1

    def table(self, b: Block):
        t = self.t
        ncols = max(len(b.header), max((len(r) for r in b.rows), default=0))
        tbl = self.d.add_table(rows=1, cols=ncols)
        tbl.alignment = WD_TABLE_ALIGNMENT.CENTER
        tbl.autofit = True
        hdr = tbl.rows[0].cells
        for i in range(ncols):
            c = hdr[i]
            c.text = ""
            p = c.paragraphs[0]
            p.paragraph_format.space_after = Pt(0)
            self.runs(p, b.header[i] if i < len(b.header) else [], size=t.doc_small + 0.5, color=t.ink, bold=True)
            _set_cell_fill(c, t.tint)
            _set_cell_borders(c, bottom=(10, t.ink))
        # repeat header row on page breaks
        trPr = tbl.rows[0]._tr.get_or_add_trPr()
        th = OxmlElement("w:tblHeader")
        th.set(qn("w:val"), "true")
        trPr.append(th)
        for row in b.rows:
            cells = tbl.add_row().cells
            for i in range(ncols):
                c = cells[i]
                c.text = ""
                p = c.paragraphs[0]
                p.paragraph_format.space_after = Pt(0)
                p.paragraph_format.line_spacing = 1.15
                if i < len(b.align) and b.align[i] == "right":
                    p.alignment = WD_ALIGN_PARAGRAPH.RIGHT
                self.runs(p, row[i] if i < len(row) else [], size=t.doc_small + 0.5)
                _set_cell_borders(c, bottom=(4, t.rule))
        self.d.add_paragraph().paragraph_format.space_after = Pt(2)

    def callout(self, b: Block):
        t = self.t
        colors = {"NOTE": t.accent, "KEY": t.accent, "TIP": t.positive, "WARNING": t.warning,
                  "ASSUMPTION": t.warning, "RISK": t.negative, "QUOTE": t.muted, "IMPORTANT": t.accent_2}
        col = colors.get(b.callout, t.accent)
        tbl = self.d.add_table(rows=1, cols=1)
        c = tbl.rows[0].cells[0]
        _set_cell_fill(c, "#" + "".join(f"{int(min(255, v * 0.08 + 255 * 0.92)):02X}" for v in
                                         [int(col[1:3], 16), int(col[3:5], 16), int(col[5:7], 16)]))
        _set_cell_borders(c, left=(24, col))
        p = c.paragraphs[0]
        p.paragraph_format.space_after = Pt(2)
        if b.callout not in ("QUOTE",):
            r = p.add_run(b.callout.title() + "  ")
            r.bold = True
            r.font.color.rgb = _rgb(col)
            r.font.size = Pt(t.doc_small + 0.5)
        self.runs(p, b.runs, size=t.doc_body - 0.5, color=t.ink)
        if b.callout == "QUOTE":
            for r in p.runs:
                r.italic = True
        self.d.add_paragraph().paragraph_format.space_after = Pt(0)

    def code(self, b: Block):
        tbl = self.d.add_table(rows=1, cols=1)
        c = tbl.rows[0].cells[0]
        _set_cell_fill(c, self.t.tint)
        p = c.paragraphs[0]
        r = p.add_run(b.text)
        r.font.name = self.t.mono_font
        r.font.size = Pt(8.5)
        self.d.add_paragraph()

    def caption(self, text):
        p = self.d.add_paragraph()
        p.paragraph_format.space_after = Pt(10)
        r = p.add_run(text)
        r.font.size = Pt(self.t.doc_small)
        r.font.color.rgb = _rgb(self.t.muted)

    def image(self, path, caption, width_cm=16.0):
        if not os.path.exists(path):
            self.issues.append(f"image not found: {path}")
            p = self.d.add_paragraph()
            r = p.add_run(f"[Missing figure: {caption or os.path.basename(path)}]")
            r.font.color.rgb = _rgb(self.t.negative)
            return
        self.d.add_picture(path, width=Cm(width_cm))
        self.d.paragraphs[-1].alignment = WD_ALIGN_PARAGRAPH.CENTER
        if caption:
            self.fig_no += 1
            self.caption(f"Figure {self.fig_no}. {caption}")

    def chart(self, b: Block, png: str, errors: List[str]):
        if errors:
            self.issues.extend(errors)
            p = self.d.add_paragraph()
            r = p.add_run("[Chart omitted: " + "; ".join(errors) + "]")
            r.font.color.rgb = _rgb(self.t.negative)
            return
        self.d.add_picture(png, width=Cm(16))
        self.d.paragraphs[-1].alignment = WD_ALIGN_PARAGRAPH.CENTER
        self.fig_no += 1
        src = b.data.get("source", "")
        ev = b.data.get("evidence")
        ev_s = ", ".join(ev) if isinstance(ev, list) else (ev or "")
        badge = self.ledger.badge(ev if isinstance(ev, list) else [ev]) if (ev and self.ledger is not None) else None
        cap = f"Figure {self.fig_no}. {b.data.get('title', '')}"
        tail = " · ".join(x for x in [f"Source: {src}" if src else "", f"Evidence: {ev_s}" if ev_s else "",
                                       f"Status: {badge}" if badge else ""] if x)
        self.caption(cap + (f" — {tail}" if tail else ""))

    def hr(self):
        p = self.d.add_paragraph()
        pPr = p._p.get_or_add_pPr()
        bdr = OxmlElement("w:pBdr")
        bt = OxmlElement("w:bottom")
        bt.set(qn("w:val"), "single")
        bt.set(qn("w:sz"), "4")
        bt.set(qn("w:color"), self.t.rule.lstrip("#"))
        bdr.append(bt)
        pPr.append(bdr)

    def pagebreak(self):
        self.d.add_paragraph().add_run().add_break(WD_BREAK.PAGE)

    def finish(self, path):
        self._header_footer(self.d.sections[0])
        self.d.save(path)
