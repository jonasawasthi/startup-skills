"""Customer discovery and validation engine: the deterministic half of customer-discovery-validation.

The skill (and the founder) do the research judgement. This module keeps the
research honest and traceable:

* parses structured interview notes, keeps every observation and quotation tied
  to its file and line, and verifies quotations against the raw transcript;
* aggregates coded observations into themes per segment, including denials, so
  contradictory feedback and segment differences stay visible;
* evaluates the hypothesis register against the shared evidence ledger
  (strength from source type and the optional ``signal`` ladder) and rejects
  "supported" claims that rest on belief, interest or contradicted evidence;
* validates 13-field experiment cards and evaluates numeric criteria against
  measured results;
* rates problem-solution fit dimensions and early PMF signals using the shared
  GTM metrics engine, computing nothing without measured inputs;
* generates interview guides and lints questions for leading, hypothetical,
  pitching and compound wording;
* assembles a Markdown+ discovery report for ``startup-kit doc``;
* guards discovery documents against invented quotations, interview counts and
  unsupported metrics.

There is no separate evidence store: interviews, surveys and experiment
results are ordinary ledger entries (``source.type: interview`` or ``dataset``).
Spec format: skills/customer-discovery-validation/references/discovery-spec.md
"""
from __future__ import annotations

import csv
import datetime as _dt
import os
import re
from collections import OrderedDict
from typing import Any, Dict, List, Optional, Tuple

import yaml

from . import gtm
from .evidence import CITE_RE, Ledger

# ----------------------------------------------------------------------------- vocabularies
CODES = OrderedDict([
    ("problem", "Problems and pains"),
    ("job", "Jobs to be done"),
    ("alternative", "Existing alternatives"),
    ("behavior", "Behaviour"),
    ("trigger", "Triggers"),
    ("spend", "Current spending"),
    ("wtp", "Willingness to pay"),
    ("commitment", "Commitments"),
    ("objection", "Objections"),
    ("unmet-need", "Unmet needs"),
    ("outcome", "Desired outcomes"),
    ("decision", "Purchase decision process"),
])
INTERPRETATION = "interpretation"
SIDES = ("supply", "demand", "customer", "other")
MARKETS = ("b2b", "b2c", "b2b2c", "b2g")
HYPOTHESIS_CATEGORIES = ("problem", "customer", "market", "solution", "pricing", "distribution", "behavioral",
                         "retention")
HYPOTHESIS_STATUSES = ("untested", "testing", "supported", "contradicted", "inconclusive")
LEVELS = ("high", "medium", "low")
SIGNALS = ("stated", "observed", "committed", "paid")
PSF_DIMENSIONS = OrderedDict([
    ("existence", "Problem exists"),
    ("frequency", "Problem frequency"),
    ("severity", "Problem severity"),
    ("urgency", "Customer urgency"),
    ("dissatisfaction", "Dissatisfaction with existing solutions"),
    ("demand-for-alternatives", "Demand for alternatives"),
    ("solution-relevance", "Solution relevance"),
    ("behaviour-change", "Evidence of behaviour change"),
    ("purchase-commitment", "Evidence of purchase commitment"),
])
EXPERIMENT_TYPES = ("interviews", "landing-page", "waitlist", "prototype", "concierge", "wizard-of-oz", "paid-pilot",
                    "pre-order", "pricing", "ab-test", "smoke-test", "manual-service", "retention", "survey")
INTEREST_ONLY = ("interviews", "landing-page", "waitlist", "smoke-test", "survey")
EXPERIMENT_FIELDS = OrderedDict([
    ("hypothesis", "Hypothesis"), ("objective", "Objective"), ("target_customer", "Target customer"),
    ("method", "Method"), ("resources", "Required resources"), ("duration", "Estimated duration"),
    ("cost", "Estimated cost"), ("steps", "Execution steps"), ("success", "Success criteria"),
    ("failure", "Failure criteria"), ("evidence_to_collect", "Evidence to collect"),
    ("biases", "Potential biases and limitations"), ("decision_rule", "Decision rule"),
])
STRONG_SOURCES = ("interview", "dataset")
OPS = {">=": lambda a, b: a >= b, ">": lambda a, b: a > b, "<=": lambda a, b: a <= b, "<": lambda a, b: a < b,
       "==": lambda a, b: a == b}
PMF_EXTRA = {  # discovery-specific ratios (inputs follow the same {value, evidence|status} convention)
    "organic_share": ("Organic acquisition share", "organic_signups ÷ signups", ("organic_signups", "signups")),
    "repeat_usage": ("Repeat usage", "repeat_users ÷ active_users", ("repeat_users", "active_users")),
}
VANITY_INPUTS = ("visitors", "signups", "waitlist", "downloads", "page_views", "followers")

_issue = gtm._issue
_ids = gtm._ids
_text = gtm._text
_cell = gtm._cell
_cite = gtm._cite


def _norm(s: str) -> str:
    s = s.lower().replace("’", "'").replace("‘", "'").replace("“", '"').replace("”", '"')
    s = re.sub(r"[\"'`.,!?;:()\[\]-]", " ", s)
    return " ".join(s.split())


# ----------------------------------------------------------------------------- spec and context
def load_spec(path: str) -> Dict:
    with open(path) as f:
        try:
            spec = yaml.safe_load(f) or {}
        except yaml.YAMLError as e:
            raise ValueError(f"{path} is not valid YAML ({str(e).splitlines()[0]}). Quote text that contains "
                             "commas, colons or [E-001] citations inside [flow, lists].\n" + str(e)) from None
    if not isinstance(spec, dict) or "discovery" not in spec:
        raise ValueError("discovery spec must be a YAML mapping with a 'discovery' section")
    return spec


def context(spec: Dict, base: str):
    """Ledger, profile.yaml and profile dir: the same resolution the GTM engine uses."""
    return gtm.resolve_context({"gtm": spec.get("discovery", {}) or {}}, base)


# ----------------------------------------------------------------------------- interview notes
OBS_RE = re.compile(r"^\s*[-*]\s*\[([a-z-]+)(?::([a-z0-9-]+))?\s*(-)?\]\s*(.*)$", re.I)
QUOTE_RE = re.compile(r"^\s*>\s*(.+?)\s*$")


def parse_notes(path: str) -> Tuple[Dict, List[Dict]]:
    """Parse one interview-notes file.  Returns (record, issues).

    Format (see assets/templates/interview-notes.md):
      front matter: interview, segment, date, participant (pseudonymous code), method, consent,
                    transcript (optional, relative path), evidence (optional ledger ID)
      - [code:theme] observation          coded observation (code from CODES)
      - [code:theme -] observation        the participant denied / did not have this
        > "verbatim words"                quotation supporting the observation above
      - [interpretation] text             the interviewer's interpretation (never evidence)
    """
    issues: List[Dict] = []
    rel = os.path.basename(path)
    text = open(path, encoding="utf-8").read()
    meta: Dict = {}
    body_start = 0
    if text.startswith("---"):
        end = text.find("\n---", 3)
        if end != -1:
            try:
                meta = yaml.safe_load(text[3:end]) or {}
            except yaml.YAMLError as e:
                issues.append(_issue("error", "notes", f"{rel}: front matter is not valid YAML ({e})"))
            body_start = text[:end + 4].count("\n")
    rid = str(meta.get("interview") or os.path.splitext(rel)[0])
    for f in ("interview", "segment", "date", "participant", "method"):
        if not meta.get(f):
            issues.append(_issue("error", "notes", f"{rel}: front matter needs '{f}'"))
    if meta.get("consent") is not True:
        issues.append(_issue("warning", "notes", f"{rel}: consent is not recorded as true; confirm consent before "
                                                 "using quotations"))
    part = str(meta.get("participant", ""))
    if re.fullmatch(r"[A-Z][a-z]+(?:\s+[A-Z][a-z]+)+", part):
        issues.append(_issue("warning", "notes", f"{rel}: participant '{part}' looks like a real name; use a "
                                                 "pseudonymous code (e.g. T-03) in research files"))
    transcript = None
    if meta.get("transcript"):
        tp = os.path.join(os.path.dirname(path), str(meta["transcript"]))
        if os.path.exists(tp):
            transcript = _norm(open(tp, encoding="utf-8").read())
        else:
            issues.append(_issue("error", "notes", f"{rel}: transcript '{meta['transcript']}' not found"))
    obs: List[Dict] = []
    for n, line in enumerate(text.split("\n")[body_start:], body_start + 1):
        m = OBS_RE.match(line)
        if m:
            code = m.group(1).lower()
            if code != INTERPRETATION and code not in CODES:
                issues.append(_issue("error", "notes", f"{rel}:{n}: unknown code '{code}' (use: "
                                                       f"{', '.join(CODES)}, {INTERPRETATION})"))
                continue
            obs.append({"code": code, "theme": (m.group(2) or "general").lower(), "negative": bool(m.group(3)),
                        "text": m.group(4).strip(), "line": n, "quotes": [],
                        "kind": "interpretation" if code == INTERPRETATION else "observation"})
            continue
        q = QUOTE_RE.match(line)
        if q:
            if not obs or obs[-1]["kind"] == "interpretation":
                issues.append(_issue("error", "notes", f"{rel}:{n}: quotation must follow a coded observation"))
                continue
            words = q.group(1).strip().strip('"“”').strip()
            verified = None
            if transcript is not None:
                verified = _norm(words) in transcript
                if not verified:
                    issues.append(_issue("error", "notes", f"{rel}:{n}: quotation not found in the transcript: "
                                                           f"'{words[:70]}'"))
            obs[-1]["quotes"].append({"text": words, "line": n, "verified": verified})
    if not [o for o in obs if o["kind"] == "observation"]:
        issues.append(_issue("warning", "notes", f"{rel}: no coded observations"))
    rec = {"id": rid, "file": path, "meta": meta, "segment": str(meta.get("segment", "")),
           "date": str(meta.get("date", "")), "method": meta.get("method", ""), "participant": part,
           "role": meta.get("role", ""), "evidence": _ids(meta.get("evidence")), "observations": obs,
           "has_transcript": transcript is not None}
    return rec, issues


def load_interviews(spec: Dict, base: str) -> Tuple[List[Dict], List[Dict]]:
    d = spec.get("discovery", {}) or {}
    folder = d.get("notes_dir")
    recs, issues = [], []
    if not folder:
        return recs, issues
    folder = folder if os.path.isabs(folder) else os.path.join(base, folder)
    if not os.path.isdir(folder):
        return recs, [_issue("error", "notes", f"notes_dir '{d.get('notes_dir')}' not found")]
    seen = set()
    for fn in sorted(os.listdir(folder)):
        if not fn.endswith(".md") or fn.lower().startswith(("readme", "_")):
            continue
        rec, iss = parse_notes(os.path.join(folder, fn))
        issues += iss
        if rec["id"] in seen:
            issues.append(_issue("error", "notes", f"duplicate interview id {rec['id']}"))
        seen.add(rec["id"])
        recs.append(rec)
    return recs, issues


def ledger_for_interview(rec: Dict, ledger: Ledger, base: str) -> Optional[str]:
    """Ledger entry recording an interview: the ID in its front matter, or an interview entry whose ref is the file."""
    for i in rec["evidence"]:
        if i in ledger:
            return i
    root = os.path.dirname(os.path.abspath(ledger.path)) if ledger.path else base
    target = os.path.normpath(os.path.abspath(rec["file"]))
    for e in ledger.entries:
        ref = str((e.source or {}).get("ref", ""))
        if (e.source or {}).get("type") != "interview" or not ref:
            continue
        if os.path.normpath(os.path.join(root, ref)) == target or os.path.normpath(os.path.join(base, ref)) == target:
            return e.id
    return None


def themes(interviews: List[Dict]) -> List[Dict]:
    """Aggregate coded observations into (segment, code, theme) rows with provenance."""
    agg: "OrderedDict[Tuple[str, str, str], Dict]" = OrderedDict()
    for rec in interviews:
        for o in rec["observations"]:
            if o["kind"] != "observation":
                continue
            key = (rec["segment"], o["code"], o["theme"])
            row = agg.setdefault(key, {"segment": key[0], "code": key[1], "theme": key[2], "positive": [],
                                       "negative": [], "items": []})
            (row["negative"] if o["negative"] else row["positive"]).append(rec["id"])
            row["items"].append({"interview": rec["id"], "text": o["text"], "line": o["line"], "negative": o["negative"],
                                 "quotes": o["quotes"], "file": os.path.basename(rec["file"]),
                                 "evidence": rec.get("ledger_id")})
    out = []
    for row in agg.values():
        row["positive"] = sorted(set(row["positive"]))
        row["negative"] = sorted(set(row["negative"]))
        row["contradictory"] = bool(row["positive"] and row["negative"])
        out.append(row)
    return out


def segment_differences(theme_rows: List[Dict], per_segment: Dict[str, int]) -> List[Dict]:
    """Themes mentioned in one segment and denied, or never raised, in another (only where both have interviews)."""
    by = {}
    for r in theme_rows:
        by.setdefault((r["code"], r["theme"]), {})[r["segment"]] = r
    diffs = []
    for (code, theme), segs in by.items():
        active = [s for s, n in per_segment.items() if n]
        if len(active) < 2:
            continue
        shares = {s: (len(segs[s]["positive"]) if s in segs else 0) / per_segment[s] for s in active}
        hi, lo = max(shares.values()), min(shares.values())
        if hi - lo >= 0.5:
            diffs.append({"code": code, "theme": theme, "shares": shares})
    return diffs


# ----------------------------------------------------------------------------- surveys
def load_survey(sv: Dict, base: str) -> Tuple[Dict, List[Dict]]:
    issues = []
    out = {"id": sv.get("id", "survey"), "segment": sv.get("segment"), "sample": sv.get("sample", "unknown"),
           "evidence": _ids(sv.get("evidence")), "n": 0, "pmf": None}
    p = sv.get("file")
    if not p:
        return out, [_issue("error", "surveys", f"survey {out['id']}: 'file' is required")]
    p = p if os.path.isabs(p) else os.path.join(base, p)
    if not os.path.exists(p):
        return out, [_issue("error", "surveys", f"survey {out['id']}: file not found")]
    with open(p, newline="", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    out["n"] = len(rows)
    col = sv.get("pmf_column")
    if col:
        if rows and col not in rows[0]:
            issues.append(_issue("error", "surveys", f"survey {out['id']}: column '{col}' not found"))
        else:
            counts = {"very": 0, "somewhat": 0, "not": 0, "other": 0}
            for r in rows:
                a = _norm(r.get(col, ""))
                k = "very" if a.startswith("very") else "somewhat" if a.startswith("somewhat") else (
                    "not" if a.startswith("not") else "other")
                counts[k] += 1
            out["pmf"] = counts
    return out, issues


# ----------------------------------------------------------------------------- segments
def segments_check(spec: Dict, per_segment: Dict[str, int]) -> Tuple[List[Dict], List[Dict]]:
    issues, rows = [], []
    segs = spec.get("segments", []) or []
    ids = [str(s.get("id")) for s in segs]
    if not segs:
        issues.append(_issue("error", "segments", "define at least one customer segment"))
    if len(set(ids)) != len(ids):
        issues.append(_issue("error", "segments", "segment ids must be unique"))
    types = gtm.model_types(spec)
    for s in segs:
        sid, name = str(s.get("id")), s.get("name", s.get("id"))
        side, market = s.get("side", "customer"), s.get("market")
        roles = s.get("roles", {}) or {}
        if side not in SIDES:
            issues.append(_issue("error", "segments", f"{sid}: side must be one of {', '.join(SIDES)}"))
        if market and market not in MARKETS:
            issues.append(_issue("warning", "segments", f"{sid}: market '{market}' is not one of {', '.join(MARKETS)}"))
        for r in ("user", "buyer"):
            if not roles.get(r):
                issues.append(_issue("warning", "segments", f"{sid}: name the {r} (roles.{r}); users and buyers "
                                                            "often differ"))
        if market in ("b2b", "b2g") and not roles.get("decision_maker"):
            issues.append(_issue("warning", "segments", f"{sid}: B2B segment without roles.decision_maker"))
        if not s.get("jobs"):
            issues.append(_issue("warning", "segments", f"{sid}: no jobs to be done recorded (hypotheses are fine)"))
        sc = s.get("scores") or {}
        crit = ("pain", "access", "willingness_to_pay", "reachable_size")
        prio = None
        if sc:
            bad = [c for c in crit if not isinstance(sc.get(c), (int, float)) or not 1 <= sc.get(c) <= 5]
            if bad:
                issues.append(_issue("error", "segments", f"{sid}: scores {', '.join(bad)} must be 1–5"))
            elif not _text(s.get("why")):
                issues.append(_issue("error", "segments", f"{sid}: prioritisation scores need a rationale ('why')"))
            else:
                prio = round(sum(float(sc[c]) for c in crit) / len(crit), 2)
        rows.append({"id": sid, "name": name, "side": side, "market": market, "roles": roles, "priority": prio,
                     "interviews": per_segment.get(sid, 0), "spec": s})
    sides = {r["side"] for r in rows}
    if any(t in gtm.MARKETPLACE_MODELS for t in types) and not {"supply", "demand"} <= sides:
        issues.append(_issue("error", "segments", "marketplace / multi-sided model: define supply and demand segments "
                                                  "separately (side: supply | demand)"))
    ranked = sorted([r for r in rows if r["priority"] is not None], key=lambda r: -r["priority"])
    for i, r in enumerate(ranked, 1):
        r["rank"] = i
    return rows, issues


# ----------------------------------------------------------------------------- hypotheses
def _entry_info(eid: str, ledger: Ledger) -> Dict:
    e = ledger.get(eid)
    if not e:
        return {"id": eid, "exists": False}
    src = (e.source or {}).get("type", "")
    sig = str(e.raw.get("signal", "") or "")
    return {"id": eid, "exists": True, "status": e.status, "source": src, "signal": sig,
            "customer": src in STRONG_SOURCES or sig in ("observed", "committed", "paid"),
            "commitment": sig in ("committed", "paid") and e.status in ("verified", "reported"),
            "valid": e.status in ("verified", "reported")}


def evidence_strength(sup: List[Dict], con: List[Dict]) -> str:
    good = [i for i in sup if i.get("valid") and i.get("customer")]
    if any(i["commitment"] for i in good):
        return "strong"
    if len(good) >= 3 and not con:
        return "strong"
    if good:
        return "moderate"
    if sup:
        return "weak"
    return "none"


def hypotheses_check(spec: Dict, ledger: Ledger, theme_rows: List[Dict], experiments: List[Dict]
                     ) -> Tuple[List[Dict], List[Dict]]:
    issues, out = [], []
    seg_ids = {str(s.get("id")) for s in spec.get("segments", []) or []}
    exp_by_h: Dict[str, List[Dict]] = {}
    for x in experiments:
        exp_by_h.setdefault(str(x["spec"].get("hypothesis")), []).append(x)
    theme_index = {f"{r['segment']}/{r['code']}:{r['theme']}": r for r in theme_rows}
    for h in spec.get("hypotheses", []) or []:
        hid = str(h.get("id", "?"))
        for f in ("statement", "category", "why_it_matters", "risk", "confidence", "validation_method",
                  "success_criteria", "status", "next_action"):
            if not h.get(f):
                issues.append(_issue("error", "hypotheses", f"{hid}: '{f}' is required"))
        cat, st = h.get("category"), h.get("status", "untested")
        if cat and cat not in HYPOTHESIS_CATEGORIES:
            issues.append(_issue("error", "hypotheses", f"{hid}: category must be one of "
                                                        f"{', '.join(HYPOTHESIS_CATEGORIES)}"))
        if st not in HYPOTHESIS_STATUSES:
            issues.append(_issue("error", "hypotheses", f"{hid}: status must be one of {', '.join(HYPOTHESIS_STATUSES)}"))
        for f in ("risk", "confidence"):
            if h.get(f) and h[f] not in LEVELS:
                issues.append(_issue("error", "hypotheses", f"{hid}: {f} must be high, medium or low"))
        if h.get("segment") and str(h["segment"]) not in seg_ids:
            issues.append(_issue("error", "hypotheses", f"{hid}: unknown segment '{h['segment']}'"))
        dim = h.get("dimension")
        if dim and dim not in PSF_DIMENSIONS:
            issues.append(_issue("error", "hypotheses", f"{hid}: dimension must be one of {', '.join(PSF_DIMENSIONS)}"))
        sup_ids, con_ids = _ids(h.get("supporting")), _ids(h.get("contradicting"))
        both = set(sup_ids) & set(con_ids)
        if both:
            issues.append(_issue("error", "hypotheses", f"{hid}: {', '.join(sorted(both))} cited as both supporting "
                                                        "and contradicting"))
        sup = [_entry_info(i, ledger) for i in sup_ids]
        con = [_entry_info(i, ledger) for i in con_ids]
        for i in sup + con:
            if not i["exists"]:
                issues.append(_issue("error", "hypotheses", f"{hid}: {i['id']} is not in the ledger"))
            elif i["signal"] and i["signal"] not in SIGNALS:
                issues.append(_issue("warning", "hypotheses", f"{hid}: {i['id']} has unknown signal '{i['signal']}'"))
        strength = evidence_strength(sup, con)
        linked = []
        for t in _ids(h.get("themes")):
            r = theme_index.get(t)
            if r is None:
                issues.append(_issue("warning", "hypotheses", f"{hid}: theme '{t}' does not occur in the interview "
                                                              "notes (format: SEGMENT/code:theme)"))
            else:
                linked.append({"key": t, "positive": len(r["positive"]), "negative": len(r["negative"])})
        exps = exp_by_h.get(hid, [])
        outcomes = [x["outcome"] for x in exps if x.get("outcome")]
        # --- status discipline
        if st == "supported":
            if strength in ("none", "weak"):
                issues.append(_issue("error", "hypotheses", f"{hid}: marked supported, but no verified/reported "
                                                            "customer evidence (interview, dataset, observed or "
                                                            "committed signal) is cited; founder belief, desk research "
                                                            "and assumptions are not validation"))
            if con and not _text(h.get("conflict_note")):
                issues.append(_issue("error", "hypotheses", f"{hid}: marked supported while contradicting evidence "
                                                            f"exists ({', '.join(con_ids)}); explain the conflict in "
                                                            "conflict_note or mark it 'inconclusive'"))
            elif con:
                issues.append(_issue("warning", "hypotheses", f"{hid}: supported despite contradicting evidence "
                                                              f"({', '.join(con_ids)}): {_text(h['conflict_note'])}"))
            if (cat == "pricing" or dim == "purchase-commitment") and not any(i.get("commitment") for i in sup):
                issues.append(_issue("error", "hypotheses", f"{hid}: willingness to pay or purchase commitment needs "
                                                            "committed or paid evidence (signal: committed | paid); "
                                                            "stated interest is not purchase intent"))
            if "failure" in outcomes:
                issues.append(_issue("error", "hypotheses", f"{hid}: marked supported but experiment "
                                                            f"{', '.join(x['id'] for x in exps if x.get('outcome') == 'failure')}"
                                                            " met its failure criteria"))
            if any(lt["negative"] > lt["positive"] for lt in linked):
                issues.append(_issue("warning", "hypotheses", f"{hid}: linked interview themes are denied more often "
                                                              "than confirmed"))
        if st == "contradicted" and not con and "failure" not in outcomes:
            issues.append(_issue("error", "hypotheses", f"{hid}: marked contradicted without contradicting evidence or "
                                                        "a failed experiment"))
        if st == "untested" and (any(i.get("customer") for i in sup + con) or outcomes):
            issues.append(_issue("info", "hypotheses", f"{hid}: customer evidence or experiment results exist; "
                                                       "update the status"))
        if sup and con and st not in ("inconclusive", "contradicted", "testing", "supported"):
            issues.append(_issue("warning", "hypotheses", f"{hid}: conflicting evidence ({', '.join(sup_ids)} vs "
                                                          f"{', '.join(con_ids)}); flagged as a conflict"))
        if h.get("confidence") == "high" and strength in ("none", "weak"):
            issues.append(_issue("warning", "hypotheses", f"{hid}: declared confidence is high but the evidence is "
                                                          f"{strength}"))
        critical = (h.get("risk") == "high" and strength in ("none", "weak")
                    and st in ("untested", "testing", "inconclusive"))
        out.append({"id": hid, "category": cat, "segment": h.get("segment"), "dimension": dim, "status": st,
                    "statement": h.get("statement", ""), "risk": h.get("risk"), "confidence": h.get("confidence"),
                    "strength": strength, "supporting": sup_ids, "contradicting": con_ids, "themes": linked,
                    "experiments": [x["id"] for x in exps], "critical": critical, "spec": h})
    order = {"high": 0, "medium": 1, "low": 2}
    out.sort(key=lambda r: (not r["critical"], order.get(r["risk"], 3), r["id"]))
    return out, issues


def unregistered_assumptions(spec: Dict, ledger: Ledger) -> List[Dict]:
    """Ledger assumptions/estimates/unverified entries that no hypothesis references: candidate hypotheses."""
    used = set()
    for h in spec.get("hypotheses", []) or []:
        used |= set(_ids(h.get("supporting"))) | set(_ids(h.get("contradicting"))) | set(_ids(h.get("source")))
    return [{"id": e.id, "claim": e.claim, "status": e.status} for e in ledger.entries
            if e.status in ("assumption", "estimate", "unverified") and e.id not in used]


# ----------------------------------------------------------------------------- experiments
def _criterion(c) -> Optional[Dict]:
    if isinstance(c, dict) and {"metric", "op", "value"} <= set(c):
        return c
    return None


def experiments_check(spec: Dict, ledger: Ledger) -> Tuple[List[Dict], List[Dict]]:
    issues, out = [], []
    hyps = {str(h.get("id")): h for h in spec.get("hypotheses", []) or []}
    for x in spec.get("experiments", []) or []:
        xid = str(x.get("id", "?"))
        miss = [f for f in EXPERIMENT_FIELDS if not x.get(f)]
        if miss:
            issues.append(_issue("error", "experiments", f"{xid}: missing {', '.join(miss)}"))
        typ = x.get("type")
        if typ not in EXPERIMENT_TYPES:
            issues.append(_issue("error", "experiments", f"{xid}: type must be one of {', '.join(EXPERIMENT_TYPES)}"))
        h = hyps.get(str(x.get("hypothesis")))
        if x.get("hypothesis") and h is None:
            issues.append(_issue("error", "experiments", f"{xid}: unknown hypothesis '{x.get('hypothesis')}'"))
        if x.get("success") and x.get("success") == x.get("failure"):
            issues.append(_issue("error", "experiments", f"{xid}: success and failure criteria are identical"))
        dr = x.get("decision_rule")
        if isinstance(dr, dict):
            for k in ("success", "failure"):
                if not dr.get(k):
                    issues.append(_issue("error", "experiments", f"{xid}: decision_rule needs '{k}'"))
            if not dr.get("inconclusive"):
                issues.append(_issue("warning", "experiments", f"{xid}: decision_rule has no 'inconclusive' branch"))
        elif dr:
            issues.append(_issue("warning", "experiments", f"{xid}: write decision_rule as {{success, failure, "
                                                           "inconclusive}} so every outcome has an action"))
        nums = re.search(r"\d", _text(x.get("success")) + _text(x.get("failure")))
        basis = x.get("threshold_basis")
        if nums and basis not in ("heuristic", "benchmark", "founder"):
            issues.append(_issue("error", "experiments", f"{xid}: thresholds need threshold_basis: heuristic | "
                                                         "benchmark | founder (no threshold is a universal standard)"))
        if basis == "benchmark" and not (x.get("benchmark_source") or _ids(x.get("evidence"))):
            issues.append(_issue("error", "experiments", f"{xid}: benchmark threshold needs benchmark_source or "
                                                         "evidence"))
        if h is not None and (h.get("category") == "pricing" or h.get("dimension") == "purchase-commitment") \
                and typ in INTEREST_ONLY:
            issues.append(_issue("warning", "experiments", f"{xid}: {typ} measures stated interest; it cannot "
                                                           "support a willingness-to-pay hypothesis (use pre-order, "
                                                           "paid-pilot or pricing)"))
        if re.search(r"\binterviews?\b.*\b(done|completed|conducted|held)\b|\b(complete|conduct|hold)\b.*\binterviews\b",
                     _text(x.get("success")), re.I):
            issues.append(_issue("warning", "experiments", f"{xid}: success measured as interviews completed is "
                                                           "activity, not evidence; state what the interviews must show"))
        res = x.get("results") or {}
        outcome = None
        status = res.get("status", "planned")
        if status == "complete":
            if not _ids(res.get("evidence")):
                issues.append(_issue("error", "experiments", f"{xid}: completed experiment needs results.evidence "
                                                             "(a ledger entry with the measured data)"))
            meas = res.get("measured") or {}
            sc, fc = _criterion(x.get("success")), _criterion(x.get("failure"))
            if sc and sc["metric"] in meas:
                v = float(meas[sc["metric"]])
                if OPS[sc["op"]](v, float(sc["value"])):
                    outcome = "success"
                elif fc and fc["metric"] in meas and OPS[fc["op"]](float(meas[fc["metric"]]), float(fc["value"])):
                    outcome = "failure"
                else:
                    outcome = "inconclusive"
            elif sc:
                issues.append(_issue("error", "experiments", f"{xid}: results.measured lacks '{sc['metric']}'"))
            declared = res.get("outcome")
            if declared and outcome and declared != outcome:
                issues.append(_issue("error", "experiments", f"{xid}: declared outcome '{declared}' but the measured "
                                                             f"results evaluate to '{outcome}'"))
            outcome = outcome or declared
        out.append({"id": xid, "type": typ, "hypothesis": x.get("hypothesis"), "status": status, "outcome": outcome,
                    "spec": x})
    return out, issues


# ----------------------------------------------------------------------------- problem-solution fit
def psf_assessment(hyps: List[Dict], hyp_issues: List[Dict]) -> Dict:
    bad = {re.match(r"^([^:]+):", i["message"]).group(1) for i in hyp_issues
           if i["level"] == "error" and re.match(r"^([^:]+):", i["message"])}
    dims = OrderedDict()
    for d, label in PSF_DIMENSIONS.items():
        hs = [h for h in hyps if h["dimension"] == d]
        sup = [h["id"] for h in hs if h["status"] == "supported" and h["id"] not in bad]
        con = [h["id"] for h in hs if h["status"] == "contradicted" and h["id"] not in bad]
        st = "mixed" if sup and con else "supported" if sup else "contradicted" if con else (
            "untested" if hs else "no hypothesis")
        dims[d] = {"label": label, "status": st, "supported": sup, "contradicted": con,
                   "untested": [h["id"] for h in hs if h["id"] not in sup + con]}
    s = {d: v["status"] for d, v in dims.items()}
    problem_ok = s["existence"] == "supported" and (s["severity"] == "supported" or s["frequency"] == "supported")
    problem_contra = any(s[d] in ("contradicted", "mixed") for d in ("existence", "frequency", "severity", "urgency"))
    if not s["existence"] == "supported":
        verdict = "Insufficient evidence: problem existence is not yet supported by customer evidence"
    elif problem_contra:
        verdict = "Mixed: some problem dimensions are contradicted; resolve before testing solutions"
    elif not problem_ok:
        verdict = "Problem exists, but severity and frequency are untested"
    elif s["solution-relevance"] != "supported":
        verdict = "Problem supported; solution untested"
    elif s["behaviour-change"] != "supported" and s["purchase-commitment"] != "supported":
        verdict = "Early problem-solution signals: no behaviour change or purchase commitment yet"
    else:
        verdict = "Problem-solution fit supported (provisional; keep testing)"
    return {"dimensions": dims, "verdict": verdict}


# ----------------------------------------------------------------------------- PMF signals
def pmf_signals(spec: Dict, ledger: Ledger, surveys: List[Dict]) -> Tuple[Dict, List[Dict]]:
    p = spec.get("pmf", {}) or {}
    issues: List[Dict] = []
    inputs = p.get("inputs", {}) or {}
    # input validation: counts are non-negative; ratio numerators cannot exceed denominators
    vals = {}
    for k, it in inputs.items():
        v = gtm._val(it)
        if v in (None, ""):
            continue
        try:
            vals[k] = float(v)
        except (TypeError, ValueError):
            continue
        if vals[k] < 0:
            issues.append(_issue("error", "pmf", f"input '{k}' is negative"))
    pairs = [(m[3][0], m[3][1]) for m in gtm.METRICS.values() if m[5] == "pct" and len(m[3]) == 2]
    pairs += [v[2] for v in PMF_EXTRA.values()]
    for num, den in pairs:
        if num in vals and den in vals and vals[num] > vals[den] and num not in ("net_revenue",):
            issues.append(_issue("error", "pmf", f"'{num}' ({vals[num]:g}) exceeds '{den}' ({vals[den]:g}); check "
                                                 "the period and definitions"))
    metrics: List[Dict] = []
    if inputs:
        sub = {"business_model": spec.get("business_model", {}),
               "metrics": {"inputs": inputs, "kpis": p.get("kpis", []), "currency": p.get("currency", "")},
               "pricing": spec.get("pricing", {}), "cohorts": p.get("cohorts", [])}
        metrics, _, mi = gtm.compute_metrics(sub, ledger)
        issues += mi
        for key, (name, formula, ins) in PMF_EXTRA.items():
            miss = [i for i in ins if i not in vals]
            row = {"key": key, "name": name, "stage": "Retention" if key == "repeat_usage" else "Acquisition",
                   "formula": formula, "inputs": list(ins), "missing": miss, "value": None, "display": "",
                   "status": None}
            if not miss and vals[ins[1]]:
                row["value"] = vals[ins[0]] / vals[ins[1]]
                row["display"] = f"{row['value'] * 100:.1f}%"
                row["status"] = gtm._worst([gtm._status_of(inputs[i], ledger) for i in ins])
            metrics.append(row)
    # Sean Ellis survey: from counts in the spec, or from a survey file's pmf_column
    sv = p.get("survey")
    survey = None
    if sv:
        c = {"very": sv.get("very_disappointed"), "somewhat": sv.get("somewhat_disappointed"),
             "not": sv.get("not_disappointed")}
        if any(v is None for v in c.values()):
            issues.append(_issue("error", "pmf", "survey needs very_disappointed, somewhat_disappointed and "
                                                 "not_disappointed counts; a percentage alone cannot be checked"))
        else:
            survey = {"counts": c, "sample": sv.get("sample", "unknown"), "evidence": _ids(sv.get("evidence")),
                      "source": "spec"}
            if not survey["evidence"]:
                issues.append(_issue("error", "pmf", "survey counts need evidence (the ledger entry for the survey "
                                                     "data)"))
    for s in surveys:
        if s.get("pmf") and survey is None:
            c = s["pmf"]
            survey = {"counts": {k: c[k] for k in ("very", "somewhat", "not")}, "sample": s["sample"],
                      "evidence": s["evidence"], "source": s["id"], "other": c.get("other", 0)}
    if survey:
        n = sum(survey["counts"].values())
        survey["n"] = n
        survey["share"] = survey["counts"]["very"] / n if n else None
        if n < 40:
            issues.append(_issue("warning", "pmf", f"Ellis survey has {n} responses; below ~40 (a practitioner "
                                                   "heuristic from Vohra's account) treat the result as directional"))
        if survey["sample"] != "active-users":
            issues.append(_issue("warning", "pmf", f"survey sample is '{survey['sample']}', not recent active users; "
                                                   "the very-disappointed share is not comparable to the 40% "
                                                   "heuristic"))
    vanity = [k for k in VANITY_INPUTS if k in vals]
    measured = [m for m in metrics if m["value"] is not None]
    if not measured and not survey:
        verdict = "No PMF data: nothing measured yet. Nothing has been estimated."
    else:
        verdict = "Early PMF signals only (one survey or a few metrics do not demonstrate product-market fit)"
    return {"metrics": metrics, "survey": survey, "vanity": vanity, "verdict": verdict}, issues


# ----------------------------------------------------------------------------- analysis
def analyze(spec_path: str) -> Dict:
    spec = load_spec(spec_path)
    base = os.path.dirname(os.path.abspath(spec_path))
    ledger, profile, prof_dir = context(spec, base)
    d = spec.get("discovery", {}) or {}
    issues: List[Dict] = []
    if not (d.get("profile") or d.get("evidence")):
        issues.append(_issue("warning", "evidence", "no profile or ledger configured; provenance cannot be checked"))
    issues += gtm.check_evidence_ids(spec, ledger)
    interviews, ni = load_interviews(spec, base)
    issues += ni
    seg_order = [str(s.get("id")) for s in spec.get("segments", []) or []]
    seg_ids = set(seg_order)
    per_segment = OrderedDict((sid, 0) for sid in seg_order)      # spec order: stable, readable reports
    for rec in interviews:
        if rec["segment"] not in seg_ids:
            issues.append(_issue("error", "notes", f"{rec['id']}: unknown segment '{rec['segment']}'"))
        else:
            per_segment[rec["segment"]] += 1
        rec["ledger_id"] = ledger_for_interview(rec, ledger, base)
        if not rec["ledger_id"]:
            issues.append(_issue("warning", "provenance", f"{rec['id']}: not recorded in the evidence ledger (run "
                                                          "'discovery analyze --record')"))
        for i in rec["evidence"]:
            if i not in ledger:
                issues.append(_issue("error", "provenance", f"{rec['id']}: evidence {i} is not in the ledger"))
    theme_rows = themes(interviews)
    surveys = []
    for sv in spec.get("surveys", []) or []:
        s, si = load_survey(sv, base)
        if not s["evidence"]:
            found = _survey_entry(sv, ledger, base)
            s["evidence"] = [found] if found else []
            if not s["evidence"]:
                si.append(_issue("warning", "provenance", f"survey {s['id']}: not recorded in the evidence ledger "
                                                          "(run 'discovery analyze --record')"))
        surveys.append(s)
        issues += si
    segments, si = segments_check(spec, per_segment)
    exps, ei = experiments_check(spec, ledger)
    hyps, hi = hypotheses_check(spec, ledger, theme_rows, exps)
    pmf, pi = pmf_signals(spec, ledger, surveys)
    issues += si + ei + hi + pi
    psf = psf_assessment(hyps, hi)
    gaps = []
    for s in segments:
        if not s["interviews"]:
            gaps.append(f"No interviews yet with segment {s['id']} ({s['name']})")
    for h in hyps:
        if h["critical"]:
            gaps.append(f"{h['id']} is high-risk with {h['strength']} evidence ({h['status']}): {h['statement']}")
    for dkey, dv in psf["dimensions"].items():
        if dv["status"] in ("untested", "no hypothesis"):
            gaps.append(f"Problem-solution fit: '{dv['label']}' is {dv['status']}")
    unreg = unregistered_assumptions(spec, ledger)
    missing_profile = []
    if prof_dir:
        from .profile import missing_information
        missing_profile = [m for m in missing_information(prof_dir) if m.split(":")[0] in ("customers.md",
                                                                                           "problem.md")]
    return {"spec": os.path.abspath(spec_path), "base": base, "profile_dir": prof_dir,
            "company": d.get("company") or profile.get("name", ""), "stage": d.get("stage") or profile.get("stage", ""),
            "types": gtm.model_types(spec), "segments": segments, "interviews": interviews,
            "per_segment": per_segment, "themes": theme_rows,
            "differences": segment_differences(theme_rows, per_segment), "surveys": surveys,
            "hypotheses": hyps, "experiments": exps, "psf": psf, "pmf": pmf, "gaps": gaps,
            "unregistered": unreg, "missing_profile": missing_profile, "issues": issues,
            "conflicts": [str(c) for c in ledger.conflicts()],
            "errors": sum(1 for i in issues if i["level"] == "error"),
            "warnings": sum(1 for i in issues if i["level"] == "warning"), "_spec": spec}


def _survey_entry(sv: Dict, ledger: Ledger, base: str) -> Optional[str]:
    root = os.path.dirname(os.path.abspath(ledger.path)) if ledger.path else base
    target = os.path.normpath(os.path.join(base, str(sv.get("file", ""))))
    for e in ledger.entries:
        ref = str((e.source or {}).get("ref", ""))
        if ref and os.path.normpath(os.path.join(root, ref)) == target:
            return e.id
    return None


def record(spec_path: str) -> List[str]:
    """Append a ledger entry for every interview and survey not yet recorded.  Never edits existing entries."""
    spec = load_spec(spec_path)
    base = os.path.dirname(os.path.abspath(spec_path))
    ledger, _, prof_dir = context(spec, base)
    d = spec.get("discovery", {}) or {}
    path = d.get("evidence") or (os.path.join(prof_dir, "evidence.yaml") if prof_dir else None)
    if not path:
        raise ValueError("no ledger configured (discovery.profile or discovery.evidence)")
    path = path if os.path.isabs(path) else os.path.join(base, path)
    interviews, _ = load_interviews(spec, base)
    segs = {str(s.get("id")): s for s in spec.get("segments", []) or []}
    new = []
    today = _dt.date.today().isoformat()
    for rec in interviews:
        if ledger_for_interview(rec, ledger, base):
            continue
        eid = ledger.next_id() if not new else "E-%03d" % (int(new[-1]["id"][2:]) + 1)
        seg = segs.get(rec["segment"], {})
        new.append({"id": eid, "claim": f"Customer interview {rec['id']} ({rec['segment']}: "
                                        f"{seg.get('name', '')}; {rec['method']}; participant {rec['participant']})",
                    "status": "reported", "confidence": "medium",
                    "source": {"type": "interview", "ref": os.path.relpath(rec["file"], os.path.dirname(path)),
                               "published": rec["date"] or None, "accessed": today},
                    "updated": today,
                    "notes": "Recorded by startup-kit discovery analyze --record. Statements are the participant's "
                             "own; interpretation lives in the notes file."})
    for sv in spec.get("surveys", []) or []:
        if _ids(sv.get("evidence")):
            continue
        ref = os.path.relpath(os.path.join(base, sv.get("file", "")), os.path.dirname(path))
        if _survey_entry(sv, ledger, base) or any(n["source"]["ref"] == ref for n in new):
            continue
        eid = ledger.next_id() if not new else "E-%03d" % (int(new[-1]["id"][2:]) + 1)
        new.append({"id": eid, "claim": f"Survey {sv.get('id', '')} responses ({sv.get('segment', '')}; sample "
                                        f"{sv.get('sample', 'unknown')})", "status": "reported", "confidence": "medium",
                    "source": {"type": "dataset", "ref": ref, "accessed": today}, "signal": "stated",
                    "updated": today})
    if new:
        with open(path, "a", encoding="utf-8") as f:
            f.write("\n" + yaml.safe_dump(new, sort_keys=False, allow_unicode=True))
    return [n["id"] for n in new]


# ----------------------------------------------------------------------------- interview guides
HYPOTHETICAL_RE = re.compile(r"^\s*(would|will|if (we|you|there)|imagine|suppose|how likely|what if)\b|\bwould you "
                             r"(use|buy|pay|like|want|try|switch|recommend)\b|\bwill you\b", re.I)
LEADING_RE = re.compile(r"\b(don'?t you (think|agree)|wouldn'?t (it|you)|isn'?t (it|that)|aren'?t you|"
                        r"how (great|much would you love)|you'd agree|right\?$|surely)\b", re.I)
PITCH_RE = re.compile(r"\b(our (product|app|platform|idea|solution|tool|feature)|we('re| are) (building|making)|"
                      r"do you like (it|this|the idea|our))\b", re.I)
CLOSED_RE = re.compile(r"^\s*(do|does|did|is|are|was|were|have|has|can|could|should)\b", re.I)
PAST_RE = re.compile(r"\b(last time|tell me about|walk me through|how do you (currently|today)|what did you|"
                     r"how did you|what happened|when was|how much did|how much do you (spend|pay)|who (decided|"
                     r"approved|pays)|what have you tried|how often|in the last)\b", re.I)


def lint_question(q: str) -> List[str]:
    probs = []
    s = q.strip()
    if HYPOTHETICAL_RE.search(s):
        probs.append("hypothetical (asks about future behaviour; ask about the last time instead)")
    if LEADING_RE.search(s):
        probs.append("leading (invites agreement)")
    if PITCH_RE.search(s):
        probs.append("pitches the idea (invites compliments)")
    if s.count("?") > 1 or re.search(r"\?\s*\b(and|or)\b|\b(and|or) (how|what|why|when|who)\b.*\?", s, re.I):
        probs.append("compound (ask one thing at a time)")
    if not probs and CLOSED_RE.search(s):
        probs.append("closed yes/no (fine as a follow-up; open with 'Tell me about…')")
    return probs


def lint_guide(text: str) -> Tuple[List[Dict], Dict]:
    """Lint every question line (ending with '?') in an interview guide."""
    issues, stats = [], {"questions": 0, "past_behaviour": 0, "flagged": 0}
    in_fence = False
    for n, line in enumerate(text.split("\n"), 1):
        s = line.strip()
        if s.startswith("```"):
            in_fence = not in_fence
        numbered = bool(re.match(r"^\d+[.)]\s", s))
        if in_fence or not (s.endswith("?") or numbered) or s.startswith(("#", "|", ">")):
            continue
        q = re.sub(r"^([-*]|\d+[.)])\s+", "", s)
        q = re.sub(r"^\*\*[^*]+\*\*\s*", "", q)
        stats["questions"] += 1
        stats["past_behaviour"] += bool(PAST_RE.search(q))
        for p in lint_question(q):
            lvl = "info" if p.startswith("closed") else "error"
            stats["flagged"] += lvl == "error"
            issues.append({"level": lvl, "line": n, "kind": "question", "message": f"line {n}: {p}: '{q[:90]}'"})
    if stats["questions"] and stats["past_behaviour"] / stats["questions"] < 0.4:
        issues.append({"level": "warning", "line": None, "kind": "question",
                       "message": f"only {stats['past_behaviour']} of {stats['questions']} questions ask about actual "
                                  "past behaviour (aim for most of them)"})
    return issues, stats


def _area(seg: Dict) -> str:
    if seg.get("problem_area"):
        return _text(seg["problem_area"]).rstrip(".")
    jobs = seg.get("jobs") or []
    j = _text(jobs[0]).rstrip(".") if jobs else ""
    if j and not re.match(r"(?i)^(when|while|before|after|if)\b", j):
        return j
    return "this part of your work"


def _front_matter(d: Dict) -> List[str]:
    return ["---", yaml.safe_dump(d, sort_keys=False, allow_unicode=True).strip(), "---", ""]


def interview_guide(spec: Dict, seg: Dict) -> str:
    """A non-leading, behaviour-first interview guide for one segment, built from its spec and hypotheses."""
    d = spec.get("discovery", {}) or {}
    sid, name = str(seg.get("id")), seg.get("name", seg.get("id"))
    roles = seg.get("roles", {}) or {}
    area = _area(seg)
    hyps = [h for h in spec.get("hypotheses", []) or [] if str(h.get("segment")) == sid]
    L = _front_matter({"title": f"Interview guide: {name}", "company": d.get("company", ""),
                       "doc_type": "interview-guide", "audience": "internal", "toc": False})
    L += [f"# Interview guide: {name} ({sid}, {seg.get('side', 'customer')} side)", "",
          "> [!NOTE] Planning document. It contains no customer evidence. Results are recorded in interview notes "
          "and the evidence ledger.", "", "## Research objectives", ""]
    objs = _ids(seg.get("objectives")) or _ids(d.get("objectives"))
    L += [f"- {o}" for o in objs] or [f"- Learn how this segment experiences and handles {area}."]
    L += ["", "**Hypotheses this round informs** (never mention them to the participant):", ""]
    L += [f"- {h.get('id')}: {h.get('statement')}" for h in hyps] or ["- None registered yet."]
    if seg.get("jobs"):
        L += ["", "**Job to explore:** " + "; ".join(_text(j) for j in seg["jobs"])]
    L += ["", "## Participants", ""]
    crit = _ids(seg.get("criteria"))
    L += [f"- {c}" for c in crit] or [f"- People who dealt with {area} in the last 3 months."]
    if roles:
        L += ["", "Roles to cover: " + "; ".join(f"{k.replace('_', ' ')}: {_text(v)}" for k, v in roles.items()) + "."]
    L += ["", "**Recruitment:** " + (_text(seg.get("recruitment")) or "from observable early-adopter signals "
                                    "(workarounds, public complaints, communities), not friends and family") + ".", "",
          "**Heuristic:** themes often start to repeat after about 10–15 interviews per segment. This is a "
          "practitioner rule of thumb, not a statistical requirement.", "",
          "## Script (30–40 minutes)", "", "### 1. Context", "",
          "1. Tell me about your role and what a normal week looks like.",
          f"2. Walk me through the last time you dealt with {area}.", "",
          "### 2. The problem, told as a story", "",
          "3. What was the hardest part of that?",
          "4. When did it last go wrong?",
          "5. What happened next?",
          "6. How often has that happened in the last month?",
          "7. What did that cost you in time or money?", "",
          "### 3. Current alternatives", "",
          "8. How do you handle this today?",
          "9. What have you tried before?",
          "10. Why did you stop using it?",
          "11. What do you still do by hand, in spreadsheets or in chat groups?", "",
          "### 4. Spending and decisions", "",
          "12. How much do you spend today on tools, services or people for this?",
          "13. Who decided on the current approach?",
          "14. Who pays for it?",
          "15. Tell me about the last time you paid for something to fix this."]
    if roles.get("decision_maker") or seg.get("market") in ("b2b", "b2g"):
        L += ["16. Walk me through how a new tool was last approved in your organisation."]
    L += ["", "### 5. Close and commitment", "",
          "- What else should I have asked about this?",
          "- Who else deals with this that I should talk to?",
          "- Commitment ask (pick one, and record the answer as evidence): a follow-up session, an introduction, a "
          "pilot slot, or a deposit.", "",
          "## Follow-up prompts", "", "- Tell me more about that.", "- Why was that important to you?",
          "- What happened after that?", "- Show me how you do it.", "",
          "## Avoid", "", "- Asking whether they would use or pay for an idea. That is hypothetical.",
          "- Describing the product before the problem section is finished.",
          "- Accepting compliments as evidence. Redirect to past behaviour.", "",
          "## Notes", "", "Use the interview-notes template. Code each observation (`[problem:theme]`, "
          "`[alternative:theme]`, `[spend:theme]` and so on), put verbatim quotes on `>` lines, and keep "
          "interpretation on `[interpretation]` lines.", ""]
    return "\n".join(L)


def notes_template(spec: Dict, seg: Dict) -> str:
    return "\n".join([
        "---", "interview: I-XX", f"segment: {seg.get('id')}", "date: YYYY-MM-DD",
        "participant: P-XX            # pseudonymous code, never a real name", "role: ''",
        "method: video call           # in person | phone | video call | chat | survey open text | support log",
        "consent: false               # set true only when the participant agreed to notes and quotes",
        "transcript: ''               # optional: relative path to the raw transcript (quotes are checked against it)",
        "---", "", "## Observations", "",
        "<!-- One coded line per observation; codes: " + ", ".join(CODES) + ". Add ' -' inside the brackets when the",
        "     participant did NOT have this (e.g. [problem:late-payments -]). Quotes go on '>' lines directly under",
        "     the observation, verbatim. Interpretation is never evidence: keep it on [interpretation] lines. -->", "",
        "- [problem:theme] What happened, in the participant's terms", "  > \"verbatim words\"",
        "- [alternative:theme] How they handle it today", "- [spend:theme] What they pay today, and who decides",
        "- [interpretation] What this might mean (yours, not theirs)", ""])


# ----------------------------------------------------------------------------- rendering
def _quote_md(q: Dict, item: Dict) -> str:
    where = f"{item['interview']}, notes line {q['line']}"
    tag = ("checked against the transcript" if q["verified"] else
           "NOT FOUND in the transcript" if q["verified"] is False else "from the notes; no transcript to check")
    return f'"{q["text"]}" ({where}; {tag})'


def themes_table(rep: Dict, codes: List[str]) -> List[str]:
    rows = [t for t in rep["themes"] if t["code"] in codes]
    if not rows:
        return ["No coded observations for this topic yet.", ""]
    L = ["| Segment | Theme | Mentioned | Denied | Interviews | Evidence |", "|---|---|---:|---:|---|---|"]
    for t in sorted(rows, key=lambda r: (r["segment"], -len(r["positive"]))):
        n = rep["per_segment"].get(t["segment"], 0) or 1
        ev = sorted({i["evidence"] for i in t["items"] if i.get("evidence")})
        L.append(f"| {t['segment']} | {t['code']}: {t['theme']} | {len(t['positive'])} of {n} | {len(t['negative'])} "
                 f"| {', '.join(t['positive'] + [x + ' (denied)' for x in t['negative']])} | "
                 f"{('[' + ', '.join(ev) + ']') if ev else 'not in ledger'} |")
    L.append("")
    L += ["**Customer statements** (verbatim, with provenance):", ""]
    nq = 0
    for t in rows:
        for it in t["items"]:
            for q in it["quotes"]:
                L.append(f"- *{t['segment']} · {t['code']}: {t['theme']}*: {_quote_md(q, it)}"
                         + (f" [{it['evidence']}]" if it.get("evidence") else ""))
                nq += 1
    if not nq:
        L.append("- No verbatim quotations recorded for this topic.")
    L.append("")
    return L


def hypothesis_table(rep: Dict) -> List[str]:
    if not rep["hypotheses"]:
        return ["No hypotheses registered.", ""]
    L = ["| ID | Hypothesis | Category and segment | Risk | Evidence strength (declared confidence) | Evidence for "
         "/ against | Status |", "|---|---|---|---|---|---|---|"]
    for h in rep["hypotheses"]:
        ev = (("for " + ", ".join(h["supporting"])) if h["supporting"] else "") + (
            ("; against " + ", ".join(h["contradicting"])) if h["contradicting"] else "")
        L.append(f"| {h['id']}{' †' if h['critical'] else ''} | {_cell(h['statement'])} | {h['category']} · "
                 f"{h['segment'] or '—'} | {h['risk']} | {h['strength']} ({h['confidence']}) | "
                 f"{('[' + ev.replace('for ', '').replace('; against ', '] against [') + ']') if ev else '—'} | "
                 f"{h['status']} |")
    L += ["", "† Critical: high risk, with no or weak evidence, and not yet resolved. *Evidence strength* is computed "
          "from the cited ledger entries (source type, status and signal). It is not declared.", ""]
    for h in rep["hypotheses"]:
        s = h["spec"]
        L += [f"**{h['id']}**: why it matters: {_text(s.get('why_it_matters'))} · validation: "
              f"{_text(s.get('validation_method'))} · success criteria: {_text(s.get('success_criteria'))} · next "
              f"action: {_text(s.get('next_action'))}"
              + (f" · conflict note: {_text(s.get('conflict_note'))}" if s.get("conflict_note") else ""), ""]
    return L


def experiment_cards(rep: Dict, only: Optional[str] = None) -> List[str]:
    L = []
    for x in rep["experiments"]:
        if only and x["id"] != only:
            continue
        s = x["spec"]
        L += [f"### {x['id']}: {s.get('name', x['type'])} ({x['type']}; tests {x['hypothesis']})", "",
              "| Field | Plan |", "|---|---|"]
        for f, label in EXPERIMENT_FIELDS.items():
            v = s.get(f)
            if isinstance(v, dict) and _criterion(v):
                v = f"{v['metric']} {v['op']} {v['value']}" + (f" ({v.get('note')})" if v.get("note") else "")
            L.append(f"| {label} | {_cell(v) or 'MISSING'} |")
        L.append(f"| Threshold basis | {_cell(s.get('threshold_basis')) or '—'}"
                 f"{' (' + _cell(s.get('benchmark_source')) + ')' if s.get('benchmark_source') else ''} |")
        res = s.get("results") or {}
        L.append(f"| Status | {x['status']}{' · outcome: ' + x['outcome'] if x['outcome'] else ''}"
                 f"{' · evidence: ' + ', '.join(_ids(res.get('evidence'))) if res.get('evidence') else ''} |")
        L.append("")
    return L or ["No experiments designed yet.", ""]


def report_md(rep: Dict, out_dir: str, sections: Optional[List[str]] = None, title: str = "") -> str:
    spec = rep["_spec"]
    d = spec.get("discovery", {}) or {}
    prof = os.path.relpath(rep["profile_dir"], out_dir) if rep["profile_dir"] else None
    fm = {"title": title or "Customer discovery report",
          "subtitle": d.get("subtitle", "What customers told us, what we know, and what we still need to test"),
          "company": rep["company"], "date": d.get("date", _dt.date.today().strftime("%B %Y")),
          "doc_type": "customer-discovery-report", "doc_type_label": "Customer discovery report",
          "confidentiality": d.get("confidentiality", "Confidential")}
    if prof:
        fm["profile"] = prof
    if d.get("illustrative"):
        fm["disclaimer"] = d["illustrative"]
    L = _front_matter(fm)
    n_int = len(rep["interviews"])
    all_secs = OrderedDict()

    def sec(key, title_, body):
        all_secs[key] = [f"# {title_}", ""] + body

    counts = ", ".join(f"{sid}: {n}" for sid, n in rep["per_segment"].items())
    sec("summary", "Executive summary", [
        _text(d.get("summary")) or "Summary to be written by the founder from the findings below.", "",
        f"> [!KEY] Evidence base: {n_int} interview record(s) ({counts or 'none'}); {len(rep['surveys'])} survey(s); "
        f"{sum(1 for h in rep['hypotheses'] if h['status'] == 'supported')} of {len(rep['hypotheses'])} hypotheses "
        f"supported; problem-solution fit: {rep['psf']['verdict'].split(':')[0]}.", ""])
    sec("objectives", "Research objectives", [f"- {o}" for o in _ids(d.get("objectives"))] or ["Not stated."])
    sec("methodology", "Research methodology", [
        _text(d.get("methodology")) or "Not stated.", "",
        "Observations are coded in interview notes. Quotations are verbatim and checked against transcripts where "
        "a transcript exists. Interpretation is kept separate and is never counted as evidence. Counts report how "
        "many interviews mentioned a theme. They describe these conversations only, not how common a theme is in "
        "the market.", ""])
    seg_rows = ["| ID | Segment | Side, market | User | Buyer | Decision-maker | Priority | Interviews |",
                "|---|---|---|---|---|---|---:|---:|"]
    for s in rep["segments"]:
        r = s["roles"]
        seg_rows.append(f"| {s['id']} | {_cell(s['name'])} | {s['side']}, {s['market'] or '—'} | "
                        f"{_cell(r.get('user')) or '—'} | {_cell(r.get('buyer')) or '—'} | "
                        f"{_cell(r.get('decision_maker')) or '—'} | "
                        f"{s['priority'] if s['priority'] is not None else '—'} | {s['interviews']} |")
    seg_rows += ["", "*Priority is the mean of the 1–5 scores for pain, access, willingness to pay and reachable "
                 "size. These are founder judgement unless the segment cites evidence. They decide whom to interview "
                 "first, and are not a market-size claim.*", ""]
    for s in rep["segments"]:
        sp = s["spec"]
        bits = [f"jobs: {_text(sp.get('jobs'))}" if sp.get("jobs") else "",
                f"influencers: {_text(s['roles'].get('influencers'))}" if s["roles"].get("influencers") else "",
                f"beneficiary: {_text(s['roles'].get('beneficiary'))}" if s["roles"].get("beneficiary") else "",
                f"needs and outcomes: {_text(sp.get('needs'))}" if sp.get("needs") else "",
                f"early-adopter signals: {_text(sp.get('early_adopter_signals'))}" if sp.get(
                    "early_adopter_signals") else "",
                f"profile: {_text(sp.get('profile'))}" if sp.get("profile") else ""]
        bits = [b for b in bits if b]
        if bits:
            seg_rows.append(f"- **{s['id']}** ({_text(sp.get('status', 'hypothesis'))}){_cite(_ids(sp.get('evidence')))}"
                            f": " + "; ".join(bits))
    seg_rows.append("")
    sec("segments", "Customer segments", seg_rows)
    part = ["| Interview | Segment | Date | Method | Participant (code) | Role | Transcript | Ledger |",
            "|---|---|---|---|---|---|---|---|"]
    for r in rep["interviews"]:
        part.append(f"| {r['id']} | {r['segment']} | {r['date']} | {_cell(r['method'])} | {_cell(r['participant'])} | "
                    f"{_cell(r['role'])} | {'yes' if r['has_transcript'] else 'no'} | "
                    f"{('[' + r['ledger_id'] + ']') if r['ledger_id'] else 'NOT RECORDED'} |")
    if not rep["interviews"]:
        part = ["No interviews have been conducted or recorded yet. Every customer statement in other documents is "
                "therefore a hypothesis."]
    sec("participants", "Interview participant summary", part + [""])
    sec("problems", "Key customer problems", themes_table(rep, ["problem"]))
    sec("jobs", "Jobs to be done", themes_table(rep, ["job", "outcome"]))
    sec("alternatives", "Existing alternatives", themes_table(rep, ["alternative"]))
    sec("behavior", "Customer behaviour findings", themes_table(rep, ["behavior", "trigger", "decision"]))
    wtp = themes_table(rep, ["spend", "wtp", "commitment"])
    wtp += ["Evidence ladder: *stated* (hypothetical) < *observed* (current spending) < *committed* (deposit, "
            "pre-order, signed pilot) < *paid*. Only committed or paid evidence can support a pricing hypothesis.", ""]
    sec("wtp", "Pricing and willingness-to-pay evidence", wtp)
    sec("objections", "Objections and unmet needs", themes_table(rep, ["objection", "unmet-need"]))
    comp = []
    contra = [t for t in rep["themes"] if t["contradictory"]]
    if rep["differences"]:
        comp += ["| Theme | " + " | ".join(rep["per_segment"]) + " |", "|---|" + "---:|" * len(rep["per_segment"])]
        for df in rep["differences"]:
            comp.append(f"| {df['code']}: {df['theme']} | " + " | ".join(
                f"{df['shares'].get(s, 0):.0%}" if s in df["shares"] else "—" for s in rep["per_segment"]) + " |")
        comp.append("")
    if contra:
        comp += ["**Contradictory feedback** (kept on both sides):", ""] + [
            f"- {t['segment']} · {t['code']}: {t['theme']}: mentioned in {', '.join(t['positive'])}; denied in "
            f"{', '.join(t['negative'])}" for t in contra] + [""]
    interp = [(r["id"], o) for r in rep["interviews"] for o in r["observations"] if o["kind"] == "interpretation"]
    if interp:
        comp += ["**Interpretation** (the interviewer's reading, not customer statements):", ""] + [
            f"- {rid}: {o['text']}" for rid, o in interp] + [""]
    sec("comparison", "Segment comparison", comp or ["Not enough interviews in two or more segments to compare.", ""])
    sec("hypotheses", "Hypothesis assessment", hypothesis_table(rep))
    psf = ["| Dimension | Status | Supported by | Contradicted by | Untested |", "|---|---|---|---|---|"]
    for dv in rep["psf"]["dimensions"].values():
        psf.append(f"| {dv['label']} | {dv['status']} | {', '.join(dv['supported']) or '—'} | "
                   f"{', '.join(dv['contradicted']) or '—'} | {', '.join(dv['untested']) or '—'} |")
    psf += ["", f"**Assessment:** {rep['psf']['verdict']}. Interest expressed in interviews does not count as fit.",
            ""]
    sec("psf", "Problem-solution fit assessment", psf)
    pm = rep["pmf"]
    pl = [f"**Assessment:** {pm['verdict']}", ""]
    known = [m for m in pm["metrics"] if m["value"] is not None and m["key"] != "cohorts"]
    if known:
        pl += ["| Signal | Value | Status | Formula |", "|---|---:|---|---|"] + [
            f"| {m['name']} | {m['display']} | {m['status']} | {m['formula']} |" for m in known] + [""]
    miss = [m for m in pm["metrics"] if m["value"] is None]
    if miss:
        pl += ["Not computed (inputs missing; nothing estimated):", "", "| Signal | Formula | Missing inputs |",
               "|---|---|---|"] + [f"| {m['name']} | {m['formula']} | {', '.join(m['missing'])} |" for m in miss] + [""]
    if pm["survey"]:
        s = pm["survey"]
        pl += [f"Ellis survey ({s['source']}, sample: {s['sample']}): {s['counts']['very']} of {s['n']} respondents "
               f"very disappointed ({(s['share'] or 0) * 100:.0f}%){_cite(s['evidence'])}. This is an early signal "
               "only; the ~40% reference point is a heuristic.", ""]
    if pm["vanity"]:
        pl += [f"Context only (not PMF signals): {', '.join(pm['vanity'])}.", ""]
    sec("pmf", "Product-market-fit signals", pl)
    gaps = [f"- {g}" for g in rep["gaps"]] or ["- None identified."]
    if rep["unregistered"]:
        gaps += ["", "Ledger assumptions not yet tested by any hypothesis:", ""] + [
            f"- {u['id']} ({u['status']}): {_cell(u['claim'])}" for u in rep["unregistered"]]
    if rep["conflicts"]:
        gaps += ["", "Ledger conflicts:", ""] + [f"- {c}" for c in rep["conflicts"]]
    sec("gaps", "Evidence gaps", gaps + [""])
    sec("experiments", "Recommended experiments", experiment_cards(rep))
    sec("next", "Next steps", [f"- {x}" for x in _ids(d.get("next_steps"))] or
        ["To be decided by the founder from the evidence gaps and experiments above."])
    keys = sections or list(all_secs)
    for k in keys:
        if k not in all_secs:
            raise ValueError(f"unknown section '{k}'; choose from {', '.join(all_secs)}")
        L += all_secs[k] + [""]
    return "\n".join(L)


REPORT_SECTIONS = ("summary", "objectives", "methodology", "segments", "participants", "problems", "jobs",
                   "alternatives", "behavior", "wtp", "objections", "comparison", "hypotheses", "psf", "pmf", "gaps",
                   "experiments", "next")


def analysis_md(rep: Dict) -> str:
    L = [f"## Customer discovery analysis: {rep['company']}", "",
         f"Interviews: {len(rep['interviews'])} · surveys: {len(rep['surveys'])} · hypotheses: "
         f"{len(rep['hypotheses'])} · experiments: {len(rep['experiments'])}", "",
         f"Problem-solution fit: **{rep['psf']['verdict']}**", "", f"PMF: **{rep['pmf']['verdict']}**", ""]
    L += ["### Themes", ""] + themes_table(rep, list(CODES))
    L += ["### Hypotheses", ""] + hypothesis_table(rep)
    if rep["gaps"]:
        L += ["### Evidence gaps", ""] + [f"- {g}" for g in rep["gaps"]] + [""]
    if rep["issues"]:
        L += ["### Engine findings", ""] + [f"- **{i['level']}** ({i['area']}): {i['message']}" for i in rep["issues"]]
    return "\n".join(L) + "\n"


def hypotheses_workbook(rep: Dict, path: str) -> str:
    import openpyxl
    from openpyxl.styles import Font, PatternFill
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Hypotheses"
    hdr = ["ID", "Category", "Segment", "Dimension", "Hypothesis", "Why it matters", "Risk", "Declared confidence",
           "Evidence strength (computed)", "Supporting evidence", "Contradicting evidence", "Validation method",
           "Success criteria", "Status", "Next action", "Experiments", "Critical"]
    for j, h in enumerate(hdr, 1):
        c = ws.cell(1, j, h)
        c.font = Font(bold=True)
        c.fill = PatternFill("solid", fgColor="F3F4F1")
        ws.column_dimensions[openpyxl.utils.get_column_letter(j)].width = 18 if j not in (5, 6, 13, 15) else 40
    for h in rep["hypotheses"]:
        s = h["spec"]
        ws.append([h["id"], h["category"], h["segment"], h["dimension"], h["statement"], _text(s.get("why_it_matters")),
                   h["risk"], h["confidence"], h["strength"], ", ".join(h["supporting"]),
                   ", ".join(h["contradicting"]), _text(s.get("validation_method")), _text(s.get("success_criteria")),
                   h["status"], _text(s.get("next_action")), ", ".join(h["experiments"]), "yes" if h["critical"] else ""])
    ws.freeze_panes = "B2"
    wb.properties.title = f"{rep['company']} hypothesis register"
    wb.properties.creator = "Startup Skills"
    os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
    wb.save(path)
    return path


# ----------------------------------------------------------------------------- document guard
INTERVIEW_COUNT_RE = re.compile(r"\b(?:interviewed|spoke (?:to|with)|talked (?:to|with)|surveyed)\s+(\d[\d,]*)\b|"
                                r"\b(\d[\d,]*)\s+(?:customer |user |discovery |problem |in-depth |structured )?"
                                r"(?:interviews|conversations|respondents|responses)\b", re.I)
SHARE_RE = re.compile(r"\b\d{1,3}(?:\.\d+)?\s?%\s+of\s+(?:the\s+)?(?:respondents|interviewees|participants|users|"
                      r"customers|teachers|learners|students|people|those)\b|\b\d+\s+(?:of|out of)\s+\d+\s+"
                      r"(?:respondents|interviewees|participants|users|customers|people)\b", re.I)
PROSE_QUOTE_RE = re.compile(r"[\"“]([^\"”]{12,})[\"”]")
# narrower than the GTM qualifiers: "would" inside a reported answer does not make a share hypothetical
PLAN_RE = re.compile(r"\b(target|goal|aim|hypothes\w*|assum\w*|estimat\w*|threshold|kill|illustrative|example|"
                     r"plan\w*|next|more|recruit|schedule|interview \d|run)\b|≥|≤|>=|<=", re.I)
QUOTE_VERB_RE = re.compile(r"\b(said|told us|says|explained|complained|mentioned|quote|in their words|put it)\b",
                           re.I)


def check_document(text: str, ledger: Optional[Ledger] = None, rep: Optional[Dict] = None,
                   where: str = "document") -> List[Dict]:
    """Claim guard for discovery documents.

    Reuses the GTM guard (market size, traction, validation language) and adds:
    invented quotations (not found in any interview notes), interview/response counts that
    exceed (or cannot be checked against) the recorded research, and uncited survey shares.
    Interview guides (doc_type: interview-guide) are linted for question quality instead.
    """
    meta = {}
    if text.startswith("---"):
        end = text.find("\n---", 3)
        if end != -1:
            try:
                meta = yaml.safe_load(text[3:end]) or {}
            except yaml.YAMLError:
                meta = {}
    if meta.get("doc_type") == "interview-guide":
        issues, _ = lint_guide(text)
        return issues
    issues = gtm.check_claims(text, ledger, where)
    corpus = []
    n_int = n_resp = None
    if rep is not None:
        n_int, n_resp = len(rep["interviews"]), sum(s["n"] for s in rep["surveys"])
        for r in rep["interviews"]:
            for o in r["observations"]:
                corpus += [_norm(q["text"]) for q in o["quotes"]]
    in_fence = False
    for n, line in enumerate(text.split("\n"), 1):
        s = line.strip()
        if s.startswith("```"):
            in_fence = not in_fence
        if in_fence or not s or s.startswith("#"):
            continue
        cited = bool(CITE_RE.search(s))
        for m in INTERVIEW_COUNT_RE.finditer(s):
            num = int((m.group(1) or m.group(2)).replace(",", ""))
            survey = bool(re.search(r"surveyed|respondents|responses", m.group(0), re.I))
            have, what = (n_resp, "survey responses") if survey else (n_int, "interviews")
            if have is not None:
                if num > have:
                    issues.append({"level": "error", "line": n, "kind": "count",
                                   "message": f"{where}:{n}: claims {num} {what} but the research spec records "
                                              f"{have}: '{s[:90]}'"})
            elif not cited and not PLAN_RE.search(s):
                issues.append({"level": "error", "line": n, "kind": "count",
                               "message": f"{where}:{n}: interview or response count without evidence: '{s[:90]}'"})
        if SHARE_RE.search(s) and not cited and not PLAN_RE.search(s) and not s.startswith("|"):
            issues.append({"level": "error", "line": n, "kind": "share",
                           "message": f"{where}:{n}: share of respondents without evidence: '{s[:90]}'"})
        is_quote_line = s.startswith(">") and not s.startswith("> [!")
        line_ids = re.findall(r"\bE-\d{3,}\b", s)
        interview_ids = [i for i in line_ids if ledger is not None and ledger.get(i) is not None
                         and (ledger.get(i).source or {}).get("type") == "interview"]
        # a quotation attributed to a non-interview ledger entry (desk research, a document) is sourced and is
        # not a customer statement; quotes attributed to interviews must still match the notes
        secondary = bool(line_ids) and ledger is not None and not interview_ids
        for m in PROSE_QUOTE_RE.finditer(s):
            if secondary or not (is_quote_line or QUOTE_VERB_RE.search(s) or s.startswith(("-", "*"))):
                continue
            q = _norm(m.group(1))
            if rep is not None:
                if q and not any(q in c or c in q for c in corpus if len(c) > 8):
                    issues.append({"level": "error", "line": n, "kind": "quote",
                                   "message": f"{where}:{n}: quotation not found in any interview notes: "
                                              f"'{m.group(1)[:70]}'"})
            elif not cited:
                issues.append({"level": "warning", "line": n, "kind": "quote",
                               "message": f"{where}:{n}: customer quotation without a source; pass --spec to verify "
                                          f"it against the notes: '{m.group(1)[:70]}'"})
    return issues
