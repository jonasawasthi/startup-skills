"""Evidence ledger: the single source of truth for every claim.

The ledger is a YAML list of entries (see docs/ARCHITECTURE.md).  This module
loads, validates and queries it, detects contradictions and stale sources, and
renders a bibliography.  Renderers call :func:`Ledger.badge` to decide how a
claim must be labelled when it appears in an artifact.
"""
from __future__ import annotations

import datetime as _dt
import os
import re
from dataclasses import dataclass, field
from typing import Any, Dict, Iterable, List, Optional

import yaml

STATUSES = ("verified", "reported", "estimate", "assumption", "unverified", "contradicted")
CONFIDENCE = ("high", "medium", "low")
SOURCE_TYPES = ("codebase", "document", "founder", "web", "calculation", "interview", "dataset", "analysis")

# How a claim with a given status must be presented.  None = may be stated plainly.
BADGES = {
    "verified": None,
    "reported": "Reported",        # company/founder-reported, not independently verified
    "estimate": "Estimate",
    "assumption": "Assumption",
    "unverified": "Unverified",
    "contradicted": "Disputed",
}

ID_RE = re.compile(r"\bE-\d{3,}\b")
CITE_RE = re.compile(r"\[(E-\d{3,}(?:\s*,\s*E-\d{3,})*)\]")
STALE_DAYS_DEFAULT = 540  # ~18 months; market data older than this is flagged


@dataclass
class Issue:
    level: str   # error | warning | info
    id: Optional[str]
    message: str

    def __str__(self):
        return f"[{self.level.upper()}] {self.id + ': ' if self.id else ''}{self.message}"


@dataclass
class Entry:
    id: str
    claim: str
    status: str
    confidence: str = "low"
    value: Any = None
    unit: Optional[str] = None
    key: Optional[str] = None
    source: Dict[str, Any] = field(default_factory=dict)
    owner: Optional[str] = None
    updated: Optional[str] = None
    notes: Optional[str] = None
    raw: Dict[str, Any] = field(default_factory=dict)

    @property
    def badge(self) -> Optional[str]:
        return BADGES.get(self.status)

    @property
    def is_fact(self) -> bool:
        return self.status == "verified"

    def citation(self) -> str:
        s = self.source or {}
        parts = []
        if s.get("title"):
            parts.append(str(s["title"]))
        if s.get("publisher"):
            parts.append(str(s["publisher"]))
        if s.get("ref") and not s.get("title"):
            parts.append(str(s["ref"]))
        if s.get("published"):
            parts.append(f"published {s['published']}")
        if s.get("url"):
            parts.append(str(s["url"]))
        if s.get("accessed"):
            parts.append(f"accessed {s['accessed']}")
        label = "; ".join(parts) if parts else "(no source recorded)"
        return f"{label} [{s.get('type', 'unknown')}]"


def _to_date(v) -> Optional[_dt.date]:
    if v is None or v == "":
        return None
    if isinstance(v, _dt.datetime):
        return v.date()
    if isinstance(v, _dt.date):
        return v
    s = str(v).strip()
    for fmt in ("%Y-%m-%d", "%Y-%m", "%Y"):
        try:
            return _dt.datetime.strptime(s, fmt).date()
        except ValueError:
            pass
    return None


class Ledger:
    def __init__(self, entries: Iterable[Entry] = (), path: Optional[str] = None):
        self.entries: List[Entry] = list(entries)
        self.path = path
        self._by_id = {e.id: e for e in self.entries}

    # ---------- loading ----------
    @classmethod
    def load(cls, path: str) -> "Ledger":
        if not os.path.exists(path):
            return cls([], path)
        with open(path) as f:
            data = yaml.safe_load(f) or []
        if isinstance(data, dict):
            data = data.get("entries", [])
        entries = []
        for raw in data:
            if not isinstance(raw, dict):
                continue
            entries.append(Entry(
                id=str(raw.get("id", "")).strip(),
                claim=str(raw.get("claim", "")).strip(),
                status=str(raw.get("status", "")).strip().lower(),
                confidence=str(raw.get("confidence", "low")).strip().lower(),
                value=raw.get("value"),
                unit=raw.get("unit"),
                key=raw.get("key"),
                source=raw.get("source") or {},
                owner=raw.get("owner"),
                updated=str(raw.get("updated")) if raw.get("updated") else None,
                notes=raw.get("notes"),
                raw=raw,
            ))
        return cls(entries, path)

    def get(self, eid: str) -> Optional[Entry]:
        return self._by_id.get(eid)

    def __contains__(self, eid):
        return eid in self._by_id

    def __len__(self):
        return len(self.entries)

    def next_id(self) -> str:
        nums = [int(e.id.split("-")[1]) for e in self.entries if re.fullmatch(r"E-\d+", e.id)]
        return "E-%03d" % ((max(nums) if nums else 0) + 1)

    # ---------- validation ----------
    def validate(self, today: Optional[_dt.date] = None, stale_days: int = STALE_DAYS_DEFAULT) -> List[Issue]:
        today = today or _dt.date.today()
        issues: List[Issue] = []
        seen = set()
        for e in self.entries:
            if not re.fullmatch(r"E-\d{3,}", e.id or ""):
                issues.append(Issue("error", e.id or None, "id must look like E-001"))
            if e.id in seen:
                issues.append(Issue("error", e.id, "duplicate id"))
            seen.add(e.id)
            if not e.claim:
                issues.append(Issue("error", e.id, "missing claim text"))
            if e.status not in STATUSES:
                issues.append(Issue("error", e.id, f"status '{e.status}' not in {STATUSES}"))
            if e.confidence not in CONFIDENCE:
                issues.append(Issue("error", e.id, f"confidence '{e.confidence}' not in {CONFIDENCE}"))
            st = (e.source or {}).get("type")
            if not st:
                issues.append(Issue("error", e.id, "source.type is required (use 'founder' or 'analysis' if internal)"))
            elif st not in SOURCE_TYPES:
                issues.append(Issue("warning", e.id, f"unusual source.type '{st}'"))
            if e.status == "verified":
                s = e.source or {}
                if not (s.get("url") or s.get("ref")):
                    issues.append(Issue("error", e.id, "status 'verified' requires source.url or source.ref"))
                if st == "founder":
                    issues.append(Issue("warning", e.id,
                                        "founder statements are 'reported', not 'verified', unless backed by a document"))
            if e.status == "verified" and e.confidence == "low":
                issues.append(Issue("warning", e.id, "verified claim with low confidence; reconsider status"))
            if st == "web" and not (e.source or {}).get("accessed"):
                issues.append(Issue("warning", e.id, "web source should record source.accessed date"))
            pub = _to_date((e.source or {}).get("published"))
            if pub and (today - pub).days > stale_days and e.status in ("verified", "reported", "estimate"):
                issues.append(Issue("warning", e.id,
                                    f"source published {pub.isoformat()} is older than {stale_days // 30} months; "
                                    "check for newer data"))
            if e.status == "assumption" and not e.owner:
                issues.append(Issue("info", e.id, "assumption has no owner; record who stands behind it"))
        issues.extend(self.conflicts())
        return issues

    def conflicts(self) -> List[Issue]:
        """Entries sharing a ``key`` whose values disagree."""
        groups: Dict[str, List[Entry]] = {}
        for e in self.entries:
            if e.key and e.value is not None and e.status != "contradicted":
                groups.setdefault(str(e.key), []).append(e)
        out = []
        for key, items in groups.items():
            vals = {}
            for e in items:
                v = e.value
                if isinstance(v, float):
                    v = round(v, 6)
                vals.setdefault(str(v), []).append(e.id)
            if len(vals) > 1:
                desc = "; ".join(f"{v} ({', '.join(ids)})" for v, ids in vals.items())
                out.append(Issue("warning", None,
                                 f"conflicting values for '{key}': {desc}. Resolve or mark one 'contradicted'."))
        return out

    # ---------- citation checks on prose ----------
    def check_text(self, text: str, where: str = "") -> List[Issue]:
        """Validate inline citations like [E-001] in narrative text."""
        issues = []
        for m in CITE_RE.finditer(text):
            for eid in re.split(r"\s*,\s*", m.group(1)):
                e = self.get(eid)
                if not e:
                    issues.append(Issue("error", eid, f"cited in {where} but not in ledger"))
                    continue
                if e.status in ("assumption", "estimate", "unverified", "contradicted"):
                    # require a nearby qualifier in the same sentence
                    start = max(text.rfind(". ", 0, m.start()), text.rfind("\n", 0, m.start())) + 1
                    sentence = text[start:m.end()].lower()
                    qualifiers = ("assum", "estimat", "project", "target", "expect", "hypothes", "unverified",
                                  "if ", "could", "may ", "might", "plan", "forecast", "scenario", "disputed",
                                  "illustrative", "goal", "≈", "about ", "approximately", "roughly", "model",
                                  "reported", "secondary", "unvalidated", "pending")
                    line_start = text.rfind("\n", 0, m.start()) + 1
                    if text[line_start:line_start + 1] == "|":
                        # table row: labelled if the row or the table header carries status language
                        header = _table_header(text, line_start)
                        sentence = sentence + " " + header
                        qualifiers = qualifiers + ("status", "confidence", "assumption", "weakness", "risk")
                    if not any(q in sentence for q in qualifiers):
                        issues.append(Issue("warning", eid,
                                            f"{e.status} cited in {where} without qualifying language: "
                                            f"'{sentence.strip()[:90]}'"))
        return issues

    # ---------- rendering helpers ----------
    def badge(self, ids: Iterable[str]) -> Optional[str]:
        """Strongest label required by a set of evidence IDs (worst status wins)."""
        order = ["contradicted", "unverified", "assumption", "estimate", "reported", "verified"]
        statuses = [self.get(i).status for i in ids if self.get(i)]
        if not statuses:
            return None
        worst = min(statuses, key=lambda s: order.index(s) if s in order else 0)
        return BADGES.get(worst)

    def bibliography_md(self, ids: Optional[Iterable[str]] = None) -> str:
        wanted = list(ids) if ids is not None else [e.id for e in self.entries]
        lines = ["| ID | Claim | Status | Confidence | Source |", "|---|---|---|---|---|"]
        for eid in wanted:
            e = self.get(eid)
            if not e:
                continue
            claim = e.claim.replace("|", "/")
            lines.append(f"| {e.id} | {claim} | {e.status} | {e.confidence} | {e.citation().replace('|', '/')} |")
        return "\n".join(lines) + "\n"

    def assumptions_md(self) -> str:
        rows = [e for e in self.entries if e.status in ("assumption", "estimate")]
        lines = ["| ID | Assumption | Value | Owner | Confidence | How to validate |", "|---|---|---|---|---|---|"]
        for e in rows:
            v = "" if e.value is None else f"{e.value}{(' ' + e.unit) if e.unit else ''}"
            lines.append(f"| {e.id} | {e.claim} | {v} | {e.owner or '—'} | {e.confidence} | "
                         f"{(e.raw.get('validate') or '—')} |")
        return "\n".join(lines) + "\n"

    def summary(self) -> Dict[str, int]:
        out = {s: 0 for s in STATUSES}
        for e in self.entries:
            out[e.status] = out.get(e.status, 0) + 1
        return out


def _table_header(text: str, line_start: int) -> str:
    """Return the header row (lower-case) of the Markdown table containing the line at line_start."""
    lines = text[:line_start].split("\n")[:-1]
    header = ""
    for ln in reversed(lines):
        if not ln.startswith("|"):
            break
        if not set(ln.replace("|", "").strip()) <= set("-: "):
            header = ln
    return header.lower()


def cited_ids(text: str) -> List[str]:
    out = []
    for m in CITE_RE.finditer(text):
        out.extend(re.split(r"\s*,\s*", m.group(1)))
    return out


NUMERIC_CLAIM_RE = re.compile(
    r"(?<![\w-])(?:[$€£₹]|NPR\s?|Rs\.?\s?|USD\s?)?\d[\d,.]*\s?(?:%|x\b|k\b|K\b|m\b|M\b|bn\b|B\b|million|billion|"
    r"thousand|lakh|crore|users|customers|creators|members|downloads|MAU|DAU|GMV|ARR|MRR)", re.I)


def numeric_claims(text: str) -> List[str]:
    """Find number-like claims that should be backed by evidence."""
    return [m.group(0) for m in NUMERIC_CLAIM_RE.finditer(text or "")]
