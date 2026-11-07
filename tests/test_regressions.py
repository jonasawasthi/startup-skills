"""Regressions found while the first real-world run on a private startup repository."""
import yaml

from startup_kit import fonts
from startup_kit.deck.build import build, yaml_lint


def test_long_token_after_words_is_hard_broken():
    url = "https://kathmandupost.com/art-culture/2026/05/11/a-very-long-url-that-cannot-wrap-on-spaces"
    lines = fonts.wrap("Source: " + url, "Arial", 9, 200)
    assert all(fonts.width(l, "Arial", 9) <= 200.5 for l in lines)


def test_yaml_unquoted_comma_is_caught():
    slides = yaml.safe_load("- {type: products, items: [{name: Pay, detail: bank, eSewa, Khalti}]}")
    issues = yaml_lint(slides)
    assert issues and "must be quoted" in issues[0]["message"]


def test_sources_appendix_paginates(tmp_path):
    ledger = tmp_path / "e.yaml"
    entries = [{"id": f"E-{i:03d}", "claim": "A fairly long claim about the market " * 3, "status": "verified",
                "confidence": "high", "source": {"type": "web", "url": f"https://example.com/{'x' * 80}/{i}",
                                                 "accessed": "2026-11-07"}} for i in range(1, 31)]
    ledger.write_text(yaml.safe_dump(entries))
    slides = [{"type": "statement", "text": "Hello", "notes": "n", "evidence": [e["id"] for e in entries]},
              {"type": "sources"}]
    spec = tmp_path / "d.yaml"
    spec.write_text(yaml.safe_dump({"deck": {"company": "X", "evidence": str(ledger)}, "slides": slides}))
    rep = build(str(spec), str(tmp_path))
    from pptx import Presentation
    assert rep["errors"] == 0
    assert len(Presentation(rep["outputs"]["pptx"]).slides) >= 4   # statement + paginated appendix


def test_headings_never_orphaned():
    from reportlab.platypus import KeepTogether, Paragraph
    from reportlab.lib.styles import getSampleStyleSheet
    from startup_kit.docs.pdf_render import PdfRenderer
    st = getSampleStyleSheet()["Normal"]
    h = Paragraph("H", st)
    h._is_heading = True
    out = PdfRenderer._bind_headings([h, Paragraph("body", st), Paragraph("x", st)])
    assert isinstance(out[0], KeepTogether) and len(out) == 2
