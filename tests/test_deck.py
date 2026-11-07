import os

import pytest
import yaml
from pptx import Presentation
from pypdf import PdfReader

from startup_kit.deck.build import build
from startup_kit.inspect import check


def _spec(tmp_path, ledger_file, slides, **deck):
    d = {"company": "TestCo", "title": "Seed", "stage": "seed", "evidence": ledger_file, **deck}
    p = tmp_path / "deck.yaml"
    p.write_text(yaml.safe_dump({"deck": d, "slides": slides}, sort_keys=False))
    return str(p)


def _errors(rep):
    return [i["message"] for i in rep["issues"] if i["level"] == "error"]


def test_example_deck_builds_clean(example_dir, tmp_path):
    rep = build(os.path.join(example_dir, "deck", "fieldnote-seed.yaml"), str(tmp_path))
    assert rep["errors"] == 0, _errors(rep)
    prs = Presentation(rep["outputs"]["pptx"])
    assert len(prs.slides) == rep["slides"] == len(PdfReader(rep["outputs"]["pdf"]).pages)
    assert check(rep["outputs"]["pptx"])["ok"] and check(rep["outputs"]["pdf"])["ok"]
    # missing information is surfaced, never invented
    assert any("screenshot" in m for m in rep["missing"])
    assert any("fundraising amount" in m for m in rep["missing"])
    assert os.path.exists(rep["outputs"]["notes"])


def test_short_variant(example_dir, tmp_path):
    rep = build(os.path.join(example_dir, "deck", "fieldnote-seed.yaml"), str(tmp_path), variant="short")
    assert rep["slides"] == 4
    assert rep["outputs"]["pptx"].endswith("-short.pptx")


def test_unsourced_chart_is_blocked(tmp_path, ledger_file):
    rep = build(_spec(tmp_path, ledger_file, [{"type": "chart", "title": "Growth",
                                              "chart": {"categories": ["a", "b"], "values": [1, 2]}}]), str(tmp_path))
    assert any("no source or evidence" in e for e in _errors(rep))


def test_metric_without_evidence_is_blocked(tmp_path, ledger_file):
    rep = build(_spec(tmp_path, ledger_file, [{"type": "metrics", "title": "Traction",
                                              "items": [{"value": "10K", "label": "Users"}]}]), str(tmp_path))
    assert any("no evidence" in e for e in _errors(rep))


def test_unknown_evidence_id_is_blocked(tmp_path, ledger_file):
    rep = build(_spec(tmp_path, ledger_file, [{"type": "metrics", "title": "T",
                                              "items": [{"value": "5", "label": "x", "evidence": ["E-999"]}]}]),
                str(tmp_path))
    assert any("E-999 not found" in e for e in _errors(rep))


def test_product_status_required(tmp_path, ledger_file):
    rep = build(_spec(tmp_path, ledger_file, [{"type": "products", "title": "P",
                                              "items": [{"name": "App", "description": "x"},
                                                        {"name": "Bot", "status": "launched-soon"}]}]), str(tmp_path))
    errs = " ".join(_errors(rep))
    assert "has no status" in errs and "unknown status" in errs


def test_quote_requires_evidence(tmp_path, ledger_file):
    rep = build(_spec(tmp_path, ledger_file, [{"type": "quote", "text": "Love it", "attribution": "A user"}]),
                str(tmp_path))
    assert any("require evidence" in e for e in _errors(rep))


def test_assumption_label_rendered(tmp_path, ledger_file):
    rep = build(_spec(tmp_path, ledger_file, [{"type": "metrics", "title": "Budget", "notes": "n",
                                              "items": [{"value": "$600", "label": "Budget", "evidence": ["E-003"]}]}]),
                str(tmp_path))
    assert rep["errors"] == 0
    text = " ".join(sh.text_frame.text for s in Presentation(rep["outputs"]["pptx"]).slides
                    for sh in s.shapes if sh.has_text_frame)
    assert "ASSUMPTION" in text.upper()


def test_overflow_is_an_error(tmp_path, ledger_file):
    long = " ".join(["unbelievably"] * 160)
    rep = build(_spec(tmp_path, ledger_file, [{"type": "statement", "text": long}]), str(tmp_path))
    assert any("overflows" in e for e in _errors(rep))


def test_use_of_funds_must_sum(tmp_path, ledger_file):
    rep = build(_spec(tmp_path, ledger_file, [{"type": "ask", "title": "Ask", "amount": "$1M",
                                              "use_of_funds": [{"name": "a", "share": 50}, {"name": "b", "share": 20}]}]),
                str(tmp_path))
    assert any("sum to" in e for e in _errors(rep))


def test_numbers_without_evidence_warn(tmp_path, ledger_file):
    rep = build(_spec(tmp_path, ledger_file, [{"type": "statement", "text": "We have 50,000 users and 30% growth",
                                              "notes": "n"}]), str(tmp_path))
    assert any("numbers without evidence" in i["message"] for i in rep["issues"])


def test_all_layouts_render(tmp_path, ledger_file):
    slides = [
        {"type": "cover", "title": "T", "subtitle": "s"},
        {"type": "section", "number": "01", "title": "Appendix"},
        {"type": "bullets", "title": "B", "items": [{"lead": "a", "detail": "b", "status": "planned"}]},
        {"type": "positioning", "title": "P", "x_axis": ["lo", "hi"], "y_axis": ["lo", "hi"],
         "points": [{"name": "Us", "x": 0.8, "y": 0.8, "highlight": True}], "takeaway": "t"},
        {"type": "diagram", "title": "D", "layers": [{"name": "Apps", "nodes": ["A", {"name": "B", "status": "planned"}]},
                                                     {"name": "Core", "nodes": [{"name": "C", "highlight": True}]}]},
        {"type": "team", "title": "Team", "people": [{"name": "Ada L", "role": "CEO", "bio": "b"}]},
        {"type": "table", "title": "Tb", "header": ["a", "b"], "rows": [["1", "2"]]},
        {"type": "chart", "title": "C", "chart": {"kind": "line", "categories": ["a", "b", "c"],
                                                  "series": [{"name": "x", "values": [1, 2, 3]},
                                                             {"name": "y", "values": [2, 2, 1]}], "evidence": ["E-001"]}},
        {"type": "chart", "title": "C2", "chart": {"kind": "bar", "categories": ["a", "b"], "values": [3, 1],
                                                   "source": "s"}},
        {"type": "chart", "title": "C3", "chart": {"kind": "stacked-column", "categories": ["a", "b"],
                                                   "series": [{"name": "x", "values": [1, 2]}, {"name": "y", "values": [1, 1]}],
                                                   "source": "s"}},
        {"type": "sources"},
    ]
    rep = build(_spec(tmp_path, ledger_file, slides), str(tmp_path))
    assert rep["errors"] == 0, _errors(rep)
    assert check(rep["outputs"]["pptx"])["ok"]
