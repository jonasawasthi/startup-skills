import os

import docx
from pypdf import PdfReader

from startup_kit.docs.build import build
from startup_kit.docs.markdown import parse
from startup_kit.inspect import check


def test_parser_blocks():
    meta, blocks = parse("""---
title: T
---
# H1
Para with **bold** and [link](https://x.y) [E-001].

- a
  - b
1. one

| a | b |
|---|--:|
| 1 | 2 |

> [!RISK] careful

```chart
categories: [a]
values: [1]
source: s
```
\\pagebreak
""")
    kinds = [b.kind for b in blocks]
    assert meta["title"] == "T"
    assert kinds == ["heading", "para", "list", "list", "table", "callout", "chart", "pagebreak"]
    assert blocks[2].items[1][0] == 1  # nested bullet
    assert blocks[4].align == ["left", "right"]
    assert blocks[5].callout == "RISK"


def test_example_proposal_builds(example_dir, tmp_path):
    rep = build(os.path.join(example_dir, "proposal", "fieldnote-investor-proposal.md"), str(tmp_path))
    assert rep["errors"] == 0, rep["issues"]
    for f in rep["outputs"].values():
        r = check(f)
        assert r["ok"], r
    d = docx.Document(rep["outputs"]["docx"])
    heads = [p.text for p in d.paragraphs if p.style.name.startswith("Heading")]
    assert "Sources and evidence" in heads           # auto appendix
    assert d.core_properties.title == "Fieldnote investor proposal"
    assert "PAGE" in d.sections[0].footer._element.xml
    pdf = PdfReader(rep["outputs"]["pdf"])
    text = "".join(p.extract_text() for p in pdf.pages)
    assert "Page 2 of" in text and "Contents" in text


def _doc(tmp_path, body, ledger=None):
    fm = "---\ntitle: X\n" + (f"evidence: {ledger}\n" if ledger else "") + "---\n"
    p = tmp_path / "d.md"
    p.write_text(fm + body)
    return str(p)


def test_citations_without_ledger_are_error(tmp_path):
    rep = build(_doc(tmp_path, "Revenue is high [E-001]."), str(tmp_path / "o"))
    assert rep["errors"] >= 1


def test_chart_without_source_is_error(tmp_path, ledger_file):
    rep = build(_doc(tmp_path, "```chart\ncategories: [a, b]\nvalues: [1, 2]\n```\n", ledger_file), str(tmp_path / "o"))
    assert any("source" in i["message"] for i in rep["issues"] if i["level"] == "error")


def test_assumption_as_fact_warns(tmp_path, ledger_file):
    rep = build(_doc(tmp_path, "Customers spend $600 per year [E-003].", ledger_file), str(tmp_path / "o"))
    assert rep["warnings"] >= 1


def test_institutional_theme_numbers_headings(tmp_path):
    p = tmp_path / "g.md"
    p.write_text("---\ntitle: Grant\ndoc_type: grant-proposal\n---\n# Need\n## Sub\n# Plan\n")
    rep = build(str(p), str(tmp_path / "o"), formats=("docx",))
    heads = [x.text for x in docx.Document(rep["outputs"]["docx"]).paragraphs if x.style.name.startswith("Heading")]
    assert rep["theme"] == "institutional"
    assert "1  Need" in heads and "1.1  Sub" in heads and "2  Plan" in heads
