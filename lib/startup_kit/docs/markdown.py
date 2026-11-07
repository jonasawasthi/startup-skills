"""A small, dependency-free parser for the Markdown dialect used by the document engine.

Supported blocks: YAML front matter, ATX headings, paragraphs, bullet and
numbered lists (two levels), GFM tables, block quotes and callouts
(``> [!NOTE]`` / ``[!WARNING]`` / ``[!ASSUMPTION]`` / ``[!KEY]``), fenced code,
fenced ``chart`` blocks (YAML), images ``![caption](path)``, horizontal rules,
``\\pagebreak`` and ``[[toc]]``.

Inline: **bold**, *italic*, `code`, [links](url), evidence citations [E-001].
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple

import yaml

INLINE_RE = re.compile(
    r"(\*\*(?P<b>.+?)\*\*)|(?<![\w*])\*(?P<i>[^*\n]+?)\*(?![\w*])|(`(?P<c>[^`]+)`)|"
    r"(\[(?P<lt>[^\]]+)\]\((?P<lu>[^)\s]+)\))|(\[(?P<cite>E-\d{3,}(?:\s*,\s*E-\d{3,})*)\])")


@dataclass
class Run:
    text: str
    bold: bool = False
    italic: bool = False
    code: bool = False
    link: Optional[str] = None
    cite: Optional[List[str]] = None


def inline(text: str, bold=False, italic=False) -> List[Run]:
    runs: List[Run] = []
    pos = 0
    for m in INLINE_RE.finditer(text):
        if m.start() > pos:
            runs.append(Run(text[pos:m.start()], bold, italic))
        if m.group("b") is not None:
            runs.extend(inline(m.group("b"), True, italic))
        elif m.group("i") is not None:
            runs.extend(inline(m.group("i"), bold, True))
        elif m.group("c") is not None:
            runs.append(Run(m.group("c"), bold, italic, code=True))
        elif m.group("lt") is not None:
            runs.append(Run(m.group("lt"), bold, italic, link=m.group("lu")))
        elif m.group("cite") is not None:
            ids = [s.strip() for s in m.group("cite").split(",")]
            runs.append(Run("[" + ", ".join(ids) + "]", cite=ids))
        pos = m.end()
    if pos < len(text):
        runs.append(Run(text[pos:], bold, italic))
    return runs


def plain(runs: List[Run]) -> str:
    return "".join(r.text for r in runs)


@dataclass
class Block:
    kind: str                     # heading | para | list | table | callout | code | chart | image | hr | pagebreak | toc
    level: int = 0
    runs: List[Run] = field(default_factory=list)
    items: List[Tuple[int, List[Run]]] = field(default_factory=list)   # (depth, runs) for lists
    ordered: bool = False
    header: List[List[Run]] = field(default_factory=list)
    rows: List[List[List[Run]]] = field(default_factory=list)
    align: List[str] = field(default_factory=list)
    text: str = ""                # code / raw
    lang: str = ""
    data: Dict[str, Any] = field(default_factory=dict)
    caption: str = ""
    path: str = ""
    callout: str = ""


def split_front_matter(src: str) -> Tuple[Dict, str]:
    if src.startswith("---\n"):
        end = src.find("\n---", 4)
        if end != -1:
            meta = yaml.safe_load(src[4:end]) or {}
            rest = src[end + 4:]
            return meta, rest.lstrip("\n")
    return {}, src


def _table_row(line: str) -> List[str]:
    line = line.strip()
    if line.startswith("|"):
        line = line[1:]
    if line.endswith("|"):
        line = line[:-1]
    cells, cur, esc = [], "", False
    for ch in line:
        if ch == "\\" and not esc:
            esc = True
            continue
        if ch == "|" and not esc:
            cells.append(cur.strip())
            cur = ""
        else:
            cur += ch
        esc = False
    cells.append(cur.strip())
    return cells


def parse(src: str) -> Tuple[Dict, List[Block]]:
    meta, body = split_front_matter(src)
    lines = body.splitlines()
    blocks: List[Block] = []
    i = 0
    para: List[str] = []

    def flush():
        nonlocal para
        if para:
            blocks.append(Block("para", runs=inline(" ".join(s.strip() for s in para))))
            para = []

    while i < len(lines):
        line = lines[i]
        s = line.strip()
        if not s:
            flush()
            i += 1
            continue
        if s.startswith("<!--"):
            flush()
            while i < len(lines) and "-->" not in lines[i]:
                i += 1
            i += 1
            continue
        m = re.match(r"^(#{1,4})\s+(.*)$", s)
        if m:
            flush()
            blocks.append(Block("heading", level=len(m.group(1)), runs=inline(m.group(2).strip())))
            i += 1
            continue
        if s in ("\\pagebreak", "<!-- pagebreak -->", "[[pagebreak]]"):
            flush()
            blocks.append(Block("pagebreak"))
            i += 1
            continue
        if s.lower() == "[[toc]]":
            flush()
            blocks.append(Block("toc"))
            i += 1
            continue
        if re.fullmatch(r"(-{3,}|\*{3,}|_{3,})", s):
            flush()
            blocks.append(Block("hr"))
            i += 1
            continue
        if s.startswith("```"):
            flush()
            lang = s[3:].strip()
            j = i + 1
            buf = []
            while j < len(lines) and not lines[j].strip().startswith("```"):
                buf.append(lines[j])
                j += 1
            raw = "\n".join(buf)
            if lang == "chart":
                try:
                    data = yaml.safe_load(raw) or {}
                except yaml.YAMLError as e:
                    data = {"_error": str(e)}
                blocks.append(Block("chart", data=data, text=raw))
            else:
                blocks.append(Block("code", text=raw, lang=lang))
            i = j + 1
            continue
        m = re.match(r"^!\[([^\]]*)\]\(([^)]+)\)$", s)
        if m:
            flush()
            blocks.append(Block("image", caption=m.group(1), path=m.group(2)))
            i += 1
            continue
        if s.startswith("|") and i + 1 < len(lines) and re.match(r"^\|?\s*:?-{2,}", lines[i + 1].strip()):
            flush()
            header = _table_row(s)
            aligns = []
            for c in _table_row(lines[i + 1]):
                c = c.strip()
                aligns.append("center" if c.startswith(":") and c.endswith(":") else "right" if c.endswith(":") else "left")
            rows = []
            j = i + 2
            while j < len(lines) and lines[j].strip().startswith("|"):
                rows.append([inline(c) for c in _table_row(lines[j])])
                j += 1
            blocks.append(Block("table", header=[inline(h) for h in header], rows=rows, align=aligns))
            i = j
            continue
        if s.startswith(">"):
            flush()
            buf = []
            while i < len(lines) and lines[i].strip().startswith(">"):
                buf.append(lines[i].strip()[1:].strip())
                i += 1
            kind = ""
            mm = re.match(r"^\[!(\w+)\]\s*(.*)$", buf[0]) if buf else None
            if mm:
                kind = mm.group(1).upper()
                buf[0] = mm.group(2)
            text = " ".join(b for b in buf if b)
            blocks.append(Block("callout", callout=kind or "QUOTE", runs=inline(text)))
            continue
        m = re.match(r"^(\s*)([-*+]|\d+[.)])\s+(.*)$", line)
        if m:
            flush()
            ordered = m.group(2)[0].isdigit()
            items = []
            while i < len(lines):
                mm = re.match(r"^(\s*)([-*+]|\d+[.)])\s+(.*)$", lines[i])
                if mm:
                    depth = 1 if len(mm.group(1).replace("\t", "    ")) >= 2 else 0
                    if depth == 0 and items and mm.group(2)[0].isdigit() != ordered:
                        break  # a top-level switch between bullets and numbers starts a new list
                    items.append([depth, mm.group(3).strip()])
                    i += 1
                elif lines[i].strip() and lines[i].startswith("  ") and items:
                    items[-1][1] += " " + lines[i].strip()   # continuation line
                    i += 1
                else:
                    break
            blocks.append(Block("list", ordered=ordered, items=[(d, inline(t)) for d, t in items]))
            continue
        para.append(line)
        i += 1
    flush()
    return meta, blocks


def headings(blocks: List[Block], max_level=2) -> List[Tuple[int, str]]:
    return [(b.level, plain(b.runs)) for b in blocks if b.kind == "heading" and b.level <= max_level]


def all_citations(blocks: List[Block]) -> List[str]:
    out = []

    def scan(runs):
        for r in runs:
            if r.cite:
                for c in r.cite:
                    if c not in out:
                        out.append(c)
    for b in blocks:
        scan(b.runs)
        for _, rs in b.items:
            scan(rs)
        for h in b.header:
            scan(h)
        for row in b.rows:
            for c in row:
                scan(c)
        if b.kind == "chart":
            ev = b.data.get("evidence") or []
            for c in (ev if isinstance(ev, list) else [ev]):
                if c not in out:
                    out.append(c)
    return out
