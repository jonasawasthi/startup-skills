import os
import sys

import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "lib"))
os.environ.setdefault("MPLCONFIGDIR", os.path.join(os.environ.get("TMPDIR", "/tmp"), "startup-kit-mpl"))

EXAMPLE = os.path.join(ROOT, "examples", "fieldnote")


@pytest.fixture
def root():
    return ROOT


@pytest.fixture
def example_dir():
    return EXAMPLE


@pytest.fixture
def ledger_file(tmp_path):
    """A small ledger covering every status, used by guard tests."""
    p = tmp_path / "evidence.yaml"
    p.write_text("""
- id: E-001
  claim: Paying customers
  key: traction.paying
  value: 5
  status: verified
  confidence: high
  source: {type: dataset, ref: billing export, accessed: 2026-11-01}
- id: E-002
  claim: Paying customers per founder
  key: traction.paying
  value: 7
  status: reported
  confidence: medium
  source: {type: founder, ref: call notes}
- id: E-003
  claim: Annual budget per customer
  value: 600
  status: assumption
  confidence: low
  source: {type: analysis, ref: estimate}
- id: E-004
  claim: Old market report figure
  value: 1000
  status: estimate
  confidence: medium
  source: {type: web, url: https://example.com/r, published: 2019-01, accessed: 2026-11-01}
""")
    return str(p)
