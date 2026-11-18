"""investor-panel-evaluator engine: investor profiles, base read, question queue, output guards, sessions.

Judgement lives in the skill's Markdown; this module holds the mechanics only. It validates investor
profiles (guards P1–P11), inventories a startup workspace without writing anything, validates and renders
the base read (B1–B6 and the crosswalk divergence rule), orders interrogation questions deterministically,
checks output documents (O1–O8, O10, B4–B6, T1–T4, N2–N4), validates interrogation session files (I1–I3)
and appends founder-provided facts to the shared evidence ledger with the founder's agreement.

It reuses ``gtm.check_claims``, ``business_model.PROB_RE`` and ``Ledger`` by import and never edits them.
Every date that drives a rule can be injected (``today``); the wall clock is only the default.

Document conventions
====================

Polish-round changes: T6 stance consistency (needs the base read); concern rows on Unknown dimensions with
``gap:``; N2 now also covers initial positions matching member evaluations (N3 is stance changes only); O8
labelling of reported (founder or document) and estimate figures; claim-guard exemptions; kind ``report``;
archetypes; restricted mode and emphasis-first attribution in the queue; context staleness rule ``mtime``.

Re-audit round (structural): every business figure or event in an evaluation, panel, verdict or report needs a
citation, 'gap' or a calculation label (O8, ``_structural_passes``); a missing base read or ledger is an error
unless waived (``allow_no_base`` / ``allow_no_ledger``); T8 rejects stance words in prose and readiness claims
that disagree with the judgements; I2 adds "as well as", "followed by", "plus", "along with", parenthetical and
"i.e." compounds; negated interest is a boundary statement; P-W warns on unsupported praise.

Final small round: I2 treats a yes/no second clause (", and does that ...?") as compound and allows a context
statement before a semicolon; session ``queue:`` texts and saved queue documents (``check_queue_document``) are
checked; clauses that state the boundary ("gives no overall score", "never states what an investor would offer")
are skipped by O2, O5, O7 and B4; exchange rows accept lens ``base``; N6 warns when a divergence-map cell gives
no role (deciding, considered, not covered, outside expertise).

After the final audit: the stance comes from the base read (a deciding Weak at medium or high confidence forces
not-persuaded) and T7 requires a concern row for each Weak or Unknown deciding dimension; judgement tables are
checked against the base read with the gates of verdict.md (``judgement_gates``); O5 needs money for a share, an
investor party, a share taken or a price for the business; wider O2/O3/O7/B4/B5 phrase lists; O8 flags uncited
traction, revenue and growth figures; I2 flags compound questions; P9 warns on panel status older than six
months and P7 on a 'high' profile without recent stated views; ``check`` warns when the base read or ledger is
missing. These text guards are tripwires for common phrasings, not proof.

Round-three changes: the conditional stance label is "Conditional on evidence" (or "Conditional on <the
evidence>"), recognised only at the start of a line, a table cell or a bold span; the old "Interested,
conditional ..." label is retired (O7 anywhere, T1 in a Stance section); O7 rejects "interested" or "has shown
interest" with any investor, member, count of members, the panel, the sharks or the dragons as subject.

Round-two changes: panel member counts (1-7) in every common form are not traction claims, and neutralising
never crosses a line; optional base-read ``note:`` rendered under the title; ``base-read --out`` reports the
rendered document's warnings; T2 counts rows named in a non-empty "Outside documented expertise" section and
then fails as a warning only; ``queue`` says when it runs without the ledger. The rendered label's evidence
date is ``ledger_snapshot`` (the newest evidence), not ``as_of`` (the day the read was made).

Output documents are Markdown with front matter. ``check_document`` recognises these structures; the
skill's templates follow them. Matching is case-insensitive unless stated.

1. Front matter: ``doc_type: shark-tank``, ``simulation: true`` (required, O1), ``kind: evaluation | panel |
   verdict | report | debrief | base-read``, ``investors: [<profile id>, ...]`` (evaluation: exactly 1, or
   ``[]`` with ``archetypes: [<label>]``; panel: 3 to 7 and no archetypes), optional ``profile:`` (path to the
   startup profile, relative to the document) and ``date:``. An archetype's label contains "archetype, not a
   real investor"; O10 does not apply to it.
2. Simulation label (O1): the first content line after the front matter (blank lines and HTML comments are
   skipped) is ``> [!SIMULATION] Analytical simulation. Not a statement by, on behalf of, or a prediction of
   the decisions of <Name or names>. ...``; it may wrap over several ``>`` lines and must name every investor
   in ``investors:``. A document naming no investor writes "the decisions of any investor".
   Investor section: in a document with more than one investor, any heading whose text *begins* with an
   investor's profile name; its first content line must be a ``[!SIMULATION]`` label naming that investor.
3. Voice (O2, O3, O7): an investor's name (or, for investors in ``investors:``, their surname) never shares
   a sentence with quotation marks; a table cell counts as a sentence. No "<Name> said / says / would say /
   told / thinks / believes / loves / hates"; no line starting "<Name>:"; no first person ("I'm in", "I'm
   out", "I'll invest", "I would"); no "would invest / will invest / likely to invest / is interested in /
   has seen" with an investor, "the panel", "the sharks" or "the dragons" as subject; no probability of
   success. Questions read "A question raised through L3: ...?".
4. Offers (O5, O6): offer words (offer, stake, equity, valuation, valued at, royalty, deal, invest ... for)
   within 80 characters of a currency amount or a percentage are errors outside a scenario callout.
   "distribution/supply/retail/licensing/partnership/wholesale/channel/customer/reseller/pilot deal", "brand
   equity" and "product/service/value offer" are not offer language. A scenario callout is the run of ``>``
   lines starting ``> [!SCENARIO]``; it contains "Hypothetical scenario", an ``Assumptions`` line followed by
   at least one ``> - `` item, and no investor name.
5. Evidence (O8): cite ``[E-001]``; unbracketed ``E-001`` in table cells is resolved too. A figure in the
   segment of a sentence or table row that ends at a citation of a ``reported`` entry with ``source.type``
   ``founder`` or ``document`` needs "founder-provided", "company-provided", "reported", "by the company's own
   account" or "according to" in the sentence, row or table header (error); one citing an ``estimate`` needs
   "estimate(d)" (warning); a group that also cites a weaker status is satisfied by that word ("assumed").
   Claims pass ``gtm.check_claims`` after "4 of 5 members", "unanimous (4 of 4)", "retention at 90 days" as a
   metric name and dimension ids are neutralised.
6. Ratings (B4, B5): Strong, Adequate, Weak, Unknown ("Insufficiently evidenced" is a warning). No ``x/15``,
   "out of 15", average or total scores, "% of dimensions". A line pairing two or more rating names with
   counts must give the Unknown count. Fixed line: ``Base read (15 dimensions): Strong 2 · Adequate 5 · Weak 2
   · Unknown 6. Critical dimensions: D01 Adequate, D03 Unknown.``
7. Evaluation (kind evaluation): a ``Stance`` heading followed by exactly one stance label ("Persuaded on
   current evidence", "Conditional on <evidence>", "Not persuaded on current evidence", "Cannot form a
   view (insufficient evidence)"). A ``Point trace`` table with columns ``# | Kind | Point | Lens | Dimension
   (base rating) | Evidence`` (found by first word). Row ids: A attracts, C concern (C1 is the top concern),
   Q question, R evidence demanded, B potential deal-breaker, M recommendation. Lens cell starts with the
   investor's lens id (``L1``; ``L-1`` accepted) or ``base``; Dimension cell holds one ``D01``-``D15``;
   Evidence cell holds E-IDs or ``gap``.
   T1 lens ownership; a B row's lens has a ``decline_pattern`` (and reaches 2 sources at medium); low
   effective confidence allows no B rows and at most one lens-tagged A and C row. T2 at medium/high, at least
   half the A and C rows are lens-tagged. T3 (``--against``): identical top-three concern dimensions and
   question-dimension set while the profiles' emphasis differs is an error unless either document has a
   "Declared convergence" line or a ``> [!CONVERGENCE]`` callout. T4 (warning): two rows under different
   lenses with token-set similarity above 0.85. An Unknown critical or primary dimension also yields a concern
   row with ``gap: ...`` in Evidence. T6 (with the base read, ``--base-read`` or ``base-read.yaml`` beside the
   document): deciding set = critical or primary dimensions, counted once; first match of not-persuaded (a C or
   B row on a deciding Weak dimension), no-view (half or more Unknown), persuaded (all Adequate or Strong, no
   concern on Weak), conditional. Archetypes: header lens ids only (T1), medium for T2, critical set for T6.
8. Panel (kind panel): headings ``Initial positions``, ``Divergence map``, ``Discussion``, ``Competing
   priorities``, ``Disagreements explained``, ``Final positions``, ``Consensus``. N2: Initial positions
   precedes Discussion, and its stances (table ``Investor | Stance | ...``) match ``--against`` evaluations.
   T6: each initial stance follows from the base read. Discussion: an exchange table ``# | Dimension | Investor | Lens | Evidence or gap | Point``
   with row ids ``X1`` or ``X1a``/``X1b``, or the sentence "The panel converges on all critical dimensions".
   N4: every exchange row has an investor (id or name), that investor's lens and an E-ID or ``gap``; the
   Disagreements explained table has a ``Class`` column with ``different-priorities``,
   ``different-reading`` or ``evidence-gap``. Final positions ``Investor | Initial stance | Final stance |
   Cause``; N3: a changed stance cites an existing exchange id in Cause, otherwise "Unchanged".
9. Judgements (B6): a table with ``Judgement`` and ``Answer`` columns; the Judgement cell starts with J1-J5;
   Answer is Yes, No or Not yet determinable; a J2 row names ``venture``, ``operator-strategic`` or
   ``debt-or-revenue-based`` (one row per class). All five present; J3 Yes and J4 Yes never together; J5 Yes
   excludes J2 Yes and J3 Yes. A verdict has this table; a verdict or report ends with "This assessment reflects the evidence
   available on <date>. It is not a prediction of success, nor of any investor's decision."
10. Base read YAML: ``startup, as_of, ledger_snapshot, business_type, stage, ambition, [imported_from,
    imported_date], dimensions: {D01..D15: {rating, confidence, critical, explanation, evidence: {verified,
    reported, estimate, assumption, disputed, unknowns}, [ceiling, upgrade_if, downgrade_if, evaluator:
    {<evaluator key>: rating}, divergence_note]}}, [note], [judgements: {J1: {answer, reason, dimensions}, J2: [{class,
    answer, reason}], ...}]``.
11. Session YAML: ``session, mode (investor|panel|archetype), investors, budget, status, queue, turns: [{n,
    question: {id, dimension, lens, investor, text, follow_up_of}, answer, assessment, decision, new_facts}],
    pending_ledger: [{id, claim, key, value, unit, turn, proposed_status: reported}], next_action``.
"""
from __future__ import annotations

import datetime as _dt
import glob
import os
import re
from typing import Any, Dict, Iterable, List, Optional, Tuple

import yaml

from . import gtm
from .business_model import PROB_RE
from .docs.markdown import split_front_matter
from .evidence import CITE_RE, ID_RE, Ledger

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
SKILL_DIR = os.path.join(ROOT, "skills", "investor-panel-evaluator")
DEFAULT_LIBRARY = os.path.join(SKILL_DIR, "investors")

# ----------------------------------------------------------------------------- vocabulary (contract section 3)
DIMENSIONS = {
    "D01": "Problem severity", "D02": "Market opportunity", "D03": "Customer demand",
    "D04": "Competitive landscape", "D05": "Product differentiation", "D06": "Business model",
    "D07": "Unit economics", "D08": "Customer acquisition", "D09": "Distribution", "D10": "Scalability",
    "D11": "Operational complexity", "D12": "Financial sustainability", "D13": "Defensibility",
    "D14": "Founder execution capability", "D15": "Legal and regulatory risks"}
DECISIVE = {
    "D01": "What does the problem cost a specific customer today, and what do they already do or pay about it?",
    "D02": "How large is the bottom-up serviceable market (from sourced factors), and why is now the time?",
    "D03": "What have customers done (paid, committed, returned, re-ordered) that shows they want this product?",
    "D04": "What do target customers use today, and what evidence shows they would switch?",
    "D05": "On which buying criterion is it materially better, for whom, shown how?",
    "D06": "Who pays how much for what, and has anyone paid that price?",
    "D07": "Is contribution positive after all variable costs (and after acquisition cost, where relevant), "
           "and which input is it most sensitive to?",
    "D08": "Which channel produced the existing customers (or which will be tested first), at what cost per "
           "customer?",
    "D09": "What route gets the product to customers, who controls that route, and what does it cost?",
    "D10": "What breaks at 10x volume, and what does growth cost?",
    "D11": "What must go right every week, and is it under control at current volume?",
    "D12": "How many months of runway exist, and does the plan reach the next milestone inside them?",
    "D13": "Which specific moat exists or is accruing, and what evidence shows it?",
    "D14": "What has this team already shipped, sold or run that is relevant here?",
    "D15": "Which permissions, certifications or legal structures does the business need, and does it have "
           "them?"}
DIM_RE = re.compile(r"\bD(0[1-9]|1[0-5])\b")
RATINGS = ("strong", "adequate", "weak", "unknown")
LEVEL = {"weak": 1, "adequate": 2, "strong": 3}
CONFIDENCE = ("high", "medium", "low")
CONF_RANK = {"low": 1, "medium": 2, "high": 3}
BUCKETS = ("verified", "reported", "estimate", "assumption", "disputed", "unknowns")
BUCKET_STATUSES = {"verified": ("verified",), "reported": ("reported",), "estimate": ("estimate",),
                   "assumption": ("assumption",), "disputed": ("unverified", "contradicted")}
STAGES = ("pre-launch", "launched-pre-revenue", "early-revenue", "trading", "scaling")
AMBITIONS = ("venture", "growth", "lifestyle", "unknown")
JUDGEMENTS = {"J1": "Good business", "J2": "Investable business", "J3": "Investment-ready business",
              "J4": "Needs further validation", "J5": "Should not proceed in its current form"}
ANSWERS = ("yes", "no", "not-yet-determinable")
INVESTOR_CLASSES = ("venture", "operator-strategic", "debt-or-revenue-based")
STANCES = {"persuaded": "Persuaded on current evidence", "conditional": "Conditional on evidence",
           "not-persuaded": "Not persuaded on current evidence",
           "no-view": "Cannot form a view (insufficient evidence)"}
DOC_KINDS = ("evaluation", "panel", "verdict", "report", "debrief", "base-read")
ARCHETYPE_LABEL = "archetype, not a real investor"
SIM_LABEL = ("Analytical simulation. Not a statement by, on behalf of, or a prediction of the decisions of")
CLOSING_RE = re.compile(r"This assessment reflects the evidence available on [^.]+\. It is not a prediction of "
                        r"success, nor of any investor[’']s decision\.")
DISAGREEMENT_CLASSES = ("different-priorities", "different-reading", "evidence-gap")
ROLE_RE = re.compile(r"\bdeciding\b|\bconsidered\b|\bnot covered\b|\boutside (?:documented )?expertise\b", re.I)

# crosswalk (references/evaluator-crosswalk.md): relationship and the evaluator keys behind each dimension
CROSSWALK = {"D01": ("carried", ("problem-severity",)), "D02": ("merged", ("market", "timing")),
             "D03": ("derived-clarity", ("customer-clarity",)), "D04": ("new", ()),
             "D05": ("carried", ("differentiation",)), "D06": ("secondary", ("business-model",)),
             "D07": ("primary", ("business-model",)), "D08": ("primary", ("distribution",)),
             "D09": ("secondary", ("distribution",)), "D10": ("derived", ("execution-risk",)),
             "D11": ("derived", ("execution-risk",)), "D12": ("derived", ("execution-risk",)),
             "D13": ("carried", ("defensibility",)), "D14": ("carried", ("founder-market-fit",)),
             "D15": ("new", ())}

# ----------------------------------------------------------------------------- profile vocabulary
SOURCE_TYPES = ("own-statement", "official-bio", "broadcaster", "company", "filing", "press", "reference")
PRIMARY_TYPES = ("own-statement", "official-bio", "broadcaster", "company", "filing")
VERIFICATION = ("read-at-source", "url-verified")
PANEL_STATUS = ("current", "former", "unconfirmed", "dormant")
PROFILE_KINDS = ("programme-investor", "independent-investor")
ROLES = ("investor", "guest")
HISTORY_LEVELS = ("televised", "reported-closed", "verified-closed", "off-programme")
FACT_LISTS = (("business_background", "B"), ("major_ventures", "V"), ("documented_expertise", "X"),
              ("documented_philosophy", "P"), ("investment_history", "H"))
REQUIRED_FIELDS = ("id", "name", "type", "kind", "regions", "programmes", "last_verified", "profile_confidence",
                   "confidence_rationale", "sources", "business_background", "major_ventures",
                   "documented_expertise", "documented_philosophy", "investment_history", "known_gaps",
                   "evaluation_lenses", "dimension_emphasis", "simulation_only")
FORBIDDEN_KEYS = {"net_worth", "networth", "wealth", "quote", "quotes", "quotations", "catchphrase", "catchphrases",
                  "signature_phrases", "sayings", "personality", "temperament", "family", "spouse", "children",
                  "personal", "personal_life", "email", "phone", "address", "home_address"}
LENS_TEXT_FIELDS = ("label", "interpretation", "attracted_by", "concerned_by", "decline_pattern")
STALE_DAYS = 548        # 18 months: profile treated one level lower; a warning, because it flips with time
STATUS_DAYS = 183       # 6 months: panel line-ups change quickly; a warning
STATED_RECENT_DAYS = 1826   # 5 years: a 'high' profile needs a recent stated view (warning)
HIGH_DAYS = 365         # 12 months: the 'high' minimum
SLUG_RE = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
SRC_CITE_RE = re.compile(r"\[(S\d+(?:\s*,\s*S\d+)*)\]")
E_TOKEN_RE = re.compile(r"\[E-\d+")
QUOTE_CHARS_RE = re.compile(r"[\"“”]|‘[^’\n]+’")
EMAIL_RE = re.compile(r"\b[\w.+-]+@[\w-]+\.[a-z]{2,}\b", re.I)
PHONE_RE = re.compile(r"(?:\+\d{1,3}[\s.-]?)?\(?\b\d{3}\)?[\s.-]\d{3}[\s.-]\d{4}\b")
URL_RE = re.compile(r"https?://\S+")
ENDORSE_RE = re.compile(r"\b(?:would|will|wants? to|plans? to) invest in\b|\bis interested in\b|\bnet worth\b", re.I)


def _issue(level: str, rule: str, message: str, line: Optional[int] = None) -> Dict:
    return {"level": level, "rule": rule, "line": line, "message": message}


def _date(v) -> Optional[_dt.date]:
    if isinstance(v, _dt.datetime):
        return v.date()
    if isinstance(v, _dt.date):
        return v
    if isinstance(v, str) and re.fullmatch(r"\d{4}-\d{2}-\d{2}", v.strip()):
        try:
            return _dt.date.fromisoformat(v.strip())
        except ValueError:
            return None
    return None


def _today(today) -> _dt.date:
    return _date(today) or _dt.date.today()


def _list(v) -> List:
    if v is None or v == "":
        return []
    return list(v) if isinstance(v, (list, tuple)) else [v]


def _text(v) -> str:
    return "" if v is None else str(v).strip()


def counts(issues: Iterable[Dict]) -> Tuple[int, int]:
    issues = list(issues)
    return (sum(1 for i in issues if i["level"] == "error"), sum(1 for i in issues if i["level"] == "warning"))


# ============================================================================= investor profiles (P1–P11)
class Profile:
    """One investor profile file, validated."""

    def __init__(self, path: str):
        self.path = path
        self.file_id = os.path.splitext(os.path.basename(path))[0]
        self.meta: Dict[str, Any] = {}
        self.body = ""
        self.issues: List[Dict] = []
        self.supported: Optional[str] = None
        self.effective: Optional[str] = None
        self.age_days: Optional[int] = None

    @property
    def id(self) -> str:
        return _text(self.meta.get("id")) or self.file_id

    @property
    def name(self) -> str:
        return _text(self.meta.get("name")) or self.id

    @property
    def names(self) -> List[str]:
        return [n for n in [self.name] + [_text(v) for v in _list(self.meta.get("name_variants"))] if n]

    @property
    def declared(self) -> str:
        return _text(self.meta.get("profile_confidence")).lower()

    @property
    def errors(self) -> List[Dict]:
        return [i for i in self.issues if i["level"] == "error"]

    @property
    def ok(self) -> bool:
        return not self.errors

    @property
    def lenses(self) -> Dict[str, Dict]:
        out = {}
        for ln in _list(self.meta.get("evaluation_lenses")):
            if isinstance(ln, dict) and ln.get("id"):
                out[_text(ln["id"])] = ln
        return out

    @property
    def emphasis(self) -> Dict[str, Dict[str, str]]:
        e = self.meta.get("dimension_emphasis") or {}
        e = e if isinstance(e, dict) else {}
        return {"primary": {str(k): _text(v) for k, v in (e.get("primary") or {}).items()},
                "secondary": {str(k): _text(v) for k, v in (e.get("secondary") or {}).items()}}

    def emphasis_rank(self, dim: str) -> int:
        e = self.emphasis
        return 0 if dim in e["primary"] else 1 if dim in e["secondary"] else 2

    def lens_for(self, dim: str) -> Optional[str]:
        """The lens that generates questions on a dimension: the emphasis lens, else the first lens listing it."""
        e = self.emphasis
        for tier in ("primary", "secondary"):
            lid = e[tier].get(dim)
            if lid and dim in [str(d) for d in _list(self.lenses.get(lid, {}).get("dimensions"))]:
                return lid
        for lid, ln in self.lenses.items():
            if dim in [str(d) for d in _list(ln.get("dimensions"))]:
                return lid
        return None

    def lens_reach(self, lid: str) -> int:
        """Distinct sources a lens reaches through its derived_from entries."""
        facts = self._facts()
        srcs = set()
        for fid in _list(self.lenses.get(lid, {}).get("derived_from")):
            srcs.update(_text(s) for s in _list(facts.get(_text(fid), {}).get("sources")))
        return len(srcs)

    def _facts(self) -> Dict[str, Dict]:
        out = {}
        for key, _ in FACT_LISTS:
            for f in _list(self.meta.get(key)):
                if isinstance(f, dict) and f.get("id"):
                    out[_text(f["id"])] = f
        return out

    def summary(self) -> Dict:
        progs = [f"{p.get('programme')} ({p.get('panel_status')}, as of {p.get('status_checked')})"
                 for p in _list(self.meta.get("programmes")) if isinstance(p, dict)]
        e, w = counts(self.issues)
        return {"id": self.id, "name": self.name, "regions": [str(r) for r in _list(self.meta.get("regions"))],
                "programmes": progs, "declared": self.declared, "effective": self.effective,
                "sources": len(_list(self.meta.get("sources"))), "lenses": len(self.lenses),
                "errors": e, "warnings": w, "path": self.path}


def _walk_strings(obj, path=""):
    """Yield (path, key, string) for every string value in a nested structure."""
    if isinstance(obj, dict):
        for k, v in obj.items():
            yield from _walk_strings(v, f"{path}.{k}" if path else str(k))
    elif isinstance(obj, list):
        for i, v in enumerate(obj):
            yield from _walk_strings(v, f"{path}[{i}]")
    elif isinstance(obj, str):
        yield path, obj


def _walk_keys(obj, path=""):
    if isinstance(obj, dict):
        for k, v in obj.items():
            p = f"{path}.{k}" if path else str(k)
            yield p, str(k)
            yield from _walk_keys(v, p)
    elif isinstance(obj, list):
        for i, v in enumerate(obj):
            yield from _walk_keys(v, f"{path}[{i}]")


def validate_profile(path: str, today=None) -> Profile:
    """Load and validate one profile file against investor-profile-schema.md (P1–P11)."""
    today = _today(today)
    p = Profile(path)
    iss = p.issues

    def err(rule, msg):
        iss.append(_issue("error", rule, f"{p.file_id}: {msg}"))

    def warn(rule, msg):
        iss.append(_issue("warning", rule, f"{p.file_id}: {msg}"))

    try:
        text = open(path, encoding="utf-8").read()
    except OSError as e:
        err("P1", f"cannot read file ({e})")
        return p
    if not text.startswith("---\n"):
        err("P1", "no YAML front matter")
        return p
    try:
        meta, body = split_front_matter(text)
    except yaml.YAMLError as e:
        err("P1", f"front matter is not valid YAML ({str(e).splitlines()[0]})")
        return p
    if not isinstance(meta, dict):
        err("P1", "front matter is not a mapping")
        return p
    p.meta, p.body = meta, body
    m = meta

    # P1 required fields, id, enums
    for k in REQUIRED_FIELDS:
        if k not in m:
            err("P1", f"required field '{k}' is missing")
    pid = _text(m.get("id"))
    if pid and pid != p.file_id:
        err("P1", f"id '{pid}' does not equal the file name '{p.file_id}'")
    if pid and not SLUG_RE.match(pid):
        err("P1", f"id '{pid}' is not a lowercase slug")
    if "name" in m and not _text(m.get("name")):
        err("P1", "name is empty")
    if "type" in m and m.get("type") != "investor-profile":
        err("P1", "type must be 'investor-profile'")
    kind = _text(m.get("kind"))
    if "kind" in m and kind not in PROFILE_KINDS:
        err("P1", f"kind '{kind}' not in {PROFILE_KINDS}")
    regions = _list(m.get("regions"))
    if "regions" in m and (not regions or not all(re.fullmatch(r"[A-Z]{2}", str(r)) for r in regions)):
        err("P1", "regions must be a non-empty list of ISO 3166-1 alpha-2 codes (for example US, IN, GB)")
    if "profile_confidence" in m and p.declared not in CONFIDENCE:
        err("P1", f"profile_confidence '{p.declared}' not in {CONFIDENCE}")
    lv = _date(m.get("last_verified"))
    if "last_verified" in m and not lv:
        err("P1", "last_verified must be a date (YYYY-MM-DD)")

    # P2 sources
    sources = {}
    srcs = _list(m.get("sources"))
    if "sources" in m and len(srcs) < 2:
        err("P2", f"at least 2 sources are required ({len(srcs)} found)")
    for s in srcs:
        if not isinstance(s, dict):
            err("P2", "a source is not a mapping")
            continue
        sid = _text(s.get("id"))
        if not re.fullmatch(r"S\d+", sid):
            err("P2", f"source id '{sid}' must look like S1")
        if sid in sources:
            err("P2", f"duplicate source id {sid}")
        sources[sid] = s
        for f in ("title", "url", "publisher", "type", "accessed", "verification"):
            if not _text(s.get(f)):
                err("P2", f"{sid}: '{f}' is missing")
        if _text(s.get("url")) and not _text(s.get("url")).startswith("https://"):
            err("P2", f"{sid}: url must start with https://")
        if _text(s.get("type")) and s.get("type") not in SOURCE_TYPES:
            err("P2", f"{sid}: type '{s.get('type')}' not in {SOURCE_TYPES}")
        if _text(s.get("verification")) and s.get("verification") not in VERIFICATION:
            err("P2", f"{sid}: verification '{s.get('verification')}' not in {VERIFICATION}")
        if s.get("accessed") and not _date(s.get("accessed")):
            err("P2", f"{sid}: accessed must be a date")
        pub = s.get("published")
        if pub not in (None, "") and not _date(pub) and str(pub) != "undated" \
                and not re.fullmatch(r"\d{4}(-\d{2})?", str(pub)):
            err("P2", f"{sid}: published must be a date or 'undated'")

    def ras(sid):
        s = sources.get(sid)
        return bool(s) and s.get("verification") == "read-at-source" and s.get("type") != "reference"

    # P3 fact entries
    facts = {}
    for key, prefix in FACT_LISTS:
        for f in _list(m.get(key)):
            if not isinstance(f, dict):
                err("P3", f"{key}: an entry is not a mapping")
                continue
            fid = _text(f.get("id"))
            if not re.fullmatch(prefix + r"\d+", fid):
                err("P3", f"{key}: id '{fid}' must look like {prefix}1")
            if fid in facts:
                err("P3", f"duplicate fact id {fid}")
            facts[fid] = f
            cited = [_text(x) for x in _list(f.get("sources"))]
            if not cited:
                err("P3", f"{fid}: cites no source")
            for sid in cited:
                if sid not in sources:
                    err("P3", f"{fid}: cites undefined source {sid}")
            if cited and not any(ras(s) for s in cited):
                err("P3", f"{fid}: needs at least one read-at-source source that is not of type 'reference'")
            if key == "documented_philosophy":
                if f.get("kind") not in ("stated", "observed"):
                    err("P3", f"{fid}: kind must be 'stated' or 'observed'")
                if not _text(f.get("paraphrase")):
                    err("P3", f"{fid}: paraphrase is empty")
                if f.get("kind") == "stated" and not any(
                        sources.get(s, {}).get("type") in ("own-statement", "press") for s in cited):
                    err("P3", f"{fid}: 'stated' needs an own-statement source or a press interview")
            if key == "investment_history" and f.get("level") not in HISTORY_LEVELS:
                err("P3", f"{fid}: level '{f.get('level')}' not in {HISTORY_LEVELS}")
    if "investment_history" in m and not _list(m.get("investment_history")) \
            and not _text(m.get("investment_history_note")):
        err("P3", "investment_history is empty, so investment_history_note is required")

    # P4 programmes
    progs = _list(m.get("programmes"))
    if kind == "programme-investor" and not progs:
        err("P4", "a programme-investor needs at least one programmes entry")
    for pr in progs:
        if not isinstance(pr, dict):
            err("P4", "a programmes entry is not a mapping")
            continue
        slug = _text(pr.get("programme"))
        label = slug or "programme"
        if not SLUG_RE.match(slug):
            err("P4", f"programme slug '{slug}' must be lowercase [a-z0-9-]")
        if pr.get("role") not in ROLES:
            err("P4", f"{label}: role '{pr.get('role')}' not in {ROLES}")
        if not _text(pr.get("seasons")):
            err("P4", f"{label}: seasons is missing")
        if pr.get("panel_status") not in PANEL_STATUS:
            err("P4", f"{label}: panel_status '{pr.get('panel_status')}' not in {PANEL_STATUS}")
        if not _text(pr.get("status_note")):
            err("P4", f"{label}: status_note is missing")
        sc = _date(pr.get("status_checked"))
        if not sc:
            err("P4", f"{label}: status_checked must be a date")
        elif lv and sc > lv:
            err("P4", f"{label}: status_checked {sc} is after last_verified {lv}")
        elif sc > today:
            err("P9", f"{label}: status_checked {sc} is in the future")
        elif (today - sc).days > STATUS_DAYS:
            warn("P9", f"{label}: panel status '{pr.get('panel_status')}' was last checked on {sc}, more than six "
                       "months ago: re-verify it before presenting this person as part of the current panel")
        cited = [_text(x) for x in _list(pr.get("sources"))]
        if not cited:
            err("P4", f"{label}: cites no source for the panel status")
        for sid in cited:
            if sid not in sources:
                err("P4", f"{label}: cites undefined source {sid}")

    # P5 lenses
    lenses = _list(m.get("evaluation_lenses"))
    if "evaluation_lenses" in m and not 1 <= len(lenses) <= 6:
        err("P5", f"1 to 6 evaluation lenses are required ({len(lenses)} found)")
    lens_ids = set()
    for ln in lenses:
        if not isinstance(ln, dict):
            err("P5", "a lens is not a mapping")
            continue
        lid = _text(ln.get("id"))
        if not re.fullmatch(r"L\d+", lid):
            err("P5", f"lens id '{lid}' must look like L1")
        if lid in lens_ids:
            err("P5", f"duplicate lens id {lid}")
        lens_ids.add(lid)
        for f in ("label", "interpretation", "attracted_by", "concerned_by"):
            if not _text(ln.get(f)):
                err("P5", f"{lid}: '{f}' is missing")
        if _text(ln.get("interpretation")) and not _text(ln.get("interpretation")).startswith(
                "Analytical interpretation:"):
            err("P5", f"{lid}: interpretation must start with 'Analytical interpretation:'")
        der = [_text(x) for x in _list(ln.get("derived_from"))]
        if not der:
            err("P5", f"{lid}: derived_from is empty")
        for fid in der:
            if not re.fullmatch(r"[PX]\d+", fid):
                err("P5", f"{lid}: derived_from may list only P or X ids ('{fid}')")
            elif fid not in facts:
                err("P5", f"{lid}: derived_from cites undefined entry {fid}")
        dims = [str(d) for d in _list(ln.get("dimensions"))]
        if not dims:
            err("P5", f"{lid}: dimensions is empty")
        for d in dims:
            if d not in DIMENSIONS:
                err("P5", f"{lid}: unknown dimension '{d}'")
        if not _list(ln.get("evidence_demanded")):
            err("P5", f"{lid}: evidence_demanded is empty")
        if _text(ln.get("decline_pattern")) and p.lens_reach(lid) < 2:
            err("P5", f"{lid}: decline_pattern needs the lens to reach at least 2 sources through derived_from "
                      f"({p.lens_reach(lid)} reached)")

    # P6 emphasis
    emph = m.get("dimension_emphasis")
    if "dimension_emphasis" in m and not isinstance(emph, dict):
        err("P6", "dimension_emphasis must be {primary: {...}, secondary: {...}}")
    elif isinstance(emph, dict):
        for k in emph:
            if k not in ("primary", "secondary"):
                err("P6", f"dimension_emphasis: unknown key '{k}'")
        e = p.emphasis
        if len(e["primary"]) > 4:
            err("P6", f"at most 4 primary dimensions ({len(e['primary'])} found)")
        for tier in ("primary", "secondary"):
            for d, lid in e[tier].items():
                if d not in DIMENSIONS:
                    err("P6", f"{tier}: unknown dimension '{d}'")
                elif lid not in p.lenses:
                    err("P6", f"{tier} {d}: lens '{lid}' does not exist")
                elif d not in [str(x) for x in _list(p.lenses[lid].get("dimensions"))]:
                    err("P6", f"{tier} {d}: lens {lid} does not list {d}")
        for d in set(e["primary"]) & set(e["secondary"]):
            err("P6", f"{d} is both primary and secondary")

    # P7 confidence minimums (structural; age is handled under P9 as a warning)
    read = [s for s in sources.values() if s.get("verification") == "read-at-source"]
    primary = [s for s in read if s.get("type") in PRIMARY_TYPES]
    own = [s for s in read if s.get("type") == "own-statement"]
    reach = [p.lens_reach(lid) for lid in p.lenses]
    identity = any(_list(f.get("sources")) for f in _list(m.get("business_background")) + _list(
        m.get("major_ventures")) if isinstance(f, dict))
    status_sourced = kind == "independent-investor" or (progs and all(
        isinstance(pr, dict) and _list(pr.get("sources")) for pr in progs))
    if len(read) >= 6 and len(primary) >= 2 and own and reach and min(reach) >= 2:
        p.supported = "high"
    elif len(read) >= 3 and primary and reach and min(reach) >= 1:
        p.supported = "medium"
    elif len(read) >= 2 and identity and status_sourced:
        p.supported = "low"
    if p.declared in CONFIDENCE:
        if p.supported is None:
            err("P7", f"sources do not meet the 'low' minimum ({len(read)} read-at-source; identity and panel "
                      "status must be sourced): a profile below 'low' is not shipped")
        elif CONF_RANK[p.declared] > CONF_RANK[p.supported]:
            err("P7", f"profile_confidence '{p.declared}' exceeds what the sources support ('{p.supported}': "
                      f"{len(read)} read-at-source, {len(primary)} primary, {len(own)} own-statement, "
                      f"lens reach {min(reach) if reach else 0})")
    if p.declared == "high":
        recent = [f for f in _list(m.get("documented_philosophy")) if isinstance(f, dict) and f.get("kind") == "stated"
                  and any(_date(sources.get(_text(x), {}).get("published")) and
                          (today - _date(sources[_text(x)]["published"])).days <= STATED_RECENT_DAYS
                          for x in _list(f.get("sources")))]
        if not recent:
            warn("P7", "declared 'high' but no 'stated' philosophy entry cites a source published within five years: "
                       "the stated views may be out of date; consider 'medium' until a recent statement is added")
    if "confidence_rationale" in m and len(_text(m.get("confidence_rationale")).split()) < 15:
        err("P7", "confidence_rationale must be at least 15 words")

    # P8 forbidden keys and content
    for kpath, key in _walk_keys(m):
        if key.lower() in FORBIDDEN_KEYS:
            err("P8", f"forbidden field '{kpath}'")
    for spath, s in _walk_strings(m):
        if re.match(r"sources\[\d+\]\.(title|url|publisher)$", spath):
            continue
        plain = URL_RE.sub(" ", s)
        if ENDORSE_RE.search(plain):
            err("P8", f"{spath}: endorsement or wealth wording ('{ENDORSE_RE.search(plain).group(0)}')")
        if EMAIL_RE.search(plain) or PHONE_RE.search(plain):
            err("P8", f"{spath}: contact details are not allowed")
        if E_TOKEN_RE.search(s):
            err("P10", f"{spath}: '[E-…]' is reserved for the startup's evidence ledger")
        last = spath.rsplit(".", 1)[-1]
        in_lens = spath.startswith("evaluation_lenses")
        if (last == "paraphrase" or (in_lens and (last in LENS_TEXT_FIELDS
                                                  or re.search(r"evidence_demanded\[\d+\]$", spath)))) \
                and QUOTE_CHARS_RE.search(s):
            err("P8", f"{spath}: quotation marks are not allowed in paraphrases and lens text")
    body_plain = URL_RE.sub(" ", body)
    if ENDORSE_RE.search(body_plain):
        err("P8", f"body: endorsement or wealth wording ('{ENDORSE_RE.search(body_plain).group(0)}')")
    if EMAIL_RE.search(body_plain) or PHONE_RE.search(body_plain):
        err("P8", "body: contact details are not allowed")
    for q in re.finditer(r"[\"“]([^\"”\n]+)[\"”]", body):
        if len(q.group(1).split()) >= 6:
            err("P8", f"body: quotation '{q.group(1)[:50]}' (profiles hold paraphrase only)")

    # P9 dates
    if lv:
        p.age_days = (today - lv).days
        if lv > today:
            err("P9", f"last_verified {lv} is in the future")
    for sid, s in sources.items():
        for f in ("accessed", "published"):
            d = _date(s.get(f))
            if d and d > today:
                err("P9", f"{sid}: {f} {d} is in the future")
        acc = _date(s.get("accessed"))
        if acc and lv and acc > lv:
            warn("P9", f"{sid}: accessed {acc} is after last_verified {lv}; update last_verified")

    # P10 body citations
    for mm in SRC_CITE_RE.finditer(body):
        for sid in re.split(r"\s*,\s*", mm.group(1)):
            if sid not in sources:
                err("P10", f"body cites undefined source [{sid}]")
    if E_TOKEN_RE.search(body):
        err("P10", "body uses '[E-…]'; cite profile sources as [S1]")

    # P11
    if m.get("simulation_only") is not True:
        err("P11", "simulation_only must be true")

    # effective confidence (P9 staleness downgrade, a warning because it changes with the passage of time)
    if p.declared in CONFIDENCE and p.supported:
        eff = min(p.declared, p.supported, key=lambda c: CONF_RANK[c])
        if p.age_days is not None and p.age_days > STALE_DAYS:
            lowered = {"high": "medium", "medium": "low", "low": "low"}[eff]
            warn("P9", f"last_verified {lv} is more than 18 months old: treated as '{lowered}' until re-verified"
                 + (" (already 'low': re-verify before use)" if eff == "low" else ""))
            eff = lowered
        elif p.age_days is not None and p.age_days > HIGH_DAYS and eff == "high":
            warn("P9", f"last_verified {lv} is more than 12 months old: 'high' needs verification within 12 "
                       "months, treated as 'medium'")
            eff = "medium"
        p.effective = eff
    return p


def library_files(libraries: Iterable[str]) -> List[str]:
    out = []
    for lib in libraries:
        for f in sorted(glob.glob(os.path.join(lib, "*.md"))):
            if os.path.basename(f).lower() != "readme.md":
                out.append(f)
    return out


def load_library(libraries: Optional[Iterable[str]] = None, today=None,
                 include_default: bool = True) -> Tuple[Dict[str, Profile], List[Dict]]:
    """Validate every profile in the shipped library plus any extra libraries. Returns (profiles, issues)."""
    libs = ([DEFAULT_LIBRARY] if include_default else []) + [lb for lb in (libraries or [])]
    seen, out, issues = set(), {}, []
    for lib in libs:
        key = os.path.realpath(lib)
        if key in seen:
            continue
        seen.add(key)
        if not os.path.isdir(lib):
            if lib != DEFAULT_LIBRARY:
                issues.append(_issue("error", "P1", f"library not found: {lib}"))
            continue
        for f in library_files([lib]):
            prof = validate_profile(f, today)
            if prof.id in out:
                issues.append(_issue("error", "P1", f"{prof.id}: defined twice ({out[prof.id].path} and {f})"))
                continue
            out[prof.id] = prof
    return out, issues


# ============================================================================= context inventory (read-only)
SIBLING_KINDS = {"startup-analysis": "evaluation", "evaluation": "evaluation", "idea-evaluation": "evaluation",
                 "research": "research", "startup-research": "research", "customer-discovery": "discovery",
                 "discovery": "discovery", "business-model": "business model", "gtm": "GTM",
                 "financial-model": "financial model", "investor-pitch": "deck", "deck": "deck",
                 "pitch-deck": "deck", "business-proposal": "proposal", "proposal": "proposal",
                 "fundraising": "fundraising", "shark-tank": "shark-tank"}


def _ledger_latest(ledger: Ledger) -> Optional[_dt.date]:
    ds = [_date(e.updated) for e in ledger.entries]
    ds = [d for d in ds if d]
    return max(ds) if ds else None


def context(profile_dir: str) -> Dict:
    """Read-only inventory of a startup workspace. Never writes, never calls profile.report."""
    from .profile import load_profile, missing_information
    if not os.path.isdir(profile_dir):
        raise ValueError(f"profile directory not found: {profile_dir}")
    prof = load_profile(profile_dir)
    ev_path = os.path.join(profile_dir, "evidence.yaml")
    ledger = Ledger.load(ev_path)
    latest = _ledger_latest(ledger)
    workspace = os.path.dirname(os.path.abspath(profile_dir))
    founder = sum(1 for e in ledger.entries if e.status == "reported" and (e.source or {}).get("type") == "founder")
    ev_mtime = os.path.getmtime(ev_path) if os.path.exists(ev_path) else None
    outputs = []
    for d in sorted(os.listdir(workspace)):
        full = os.path.join(workspace, d)
        if d.startswith(".") or not os.path.isdir(full) or os.path.samefile(full, profile_dir):
            continue
        files = []
        for dp, dns, fns in os.walk(full):
            dns[:] = sorted(x for x in dns if not x.startswith("."))
            for fn in sorted(fns):
                if fn.startswith("."):
                    continue
                fp = os.path.join(dp, fn)
                mtime = os.path.getmtime(fp)
                mdate = _dt.date.fromtimestamp(mtime)
                rules = []
                if latest and mdate < latest:
                    rules.append("date")       # modified on a day before the ledger's latest `updated`
                if ev_mtime is not None and mtime < ev_mtime:
                    rules.append("mtime")      # modified before evidence.yaml was last written
                files.append({"path": os.path.relpath(fp, workspace), "modified": mdate.isoformat(),
                              "stale": bool(rules), "stale_rules": rules})
        item = {"folder": d, "kind": SIBLING_KINDS.get(d, "other"), "files": files,
                "modified": max((f["modified"] for f in files), default=None),
                "stale": any(f["stale"] for f in files),
                "stale_rules": sorted({r for f in files for r in f["stale_rules"]})}
        if d == "shark-tank":
            br = os.path.join(full, "base-read.yaml")
            if os.path.exists(br):
                try:
                    snap = _date((yaml.safe_load(open(br, encoding="utf-8")) or {}).get("ledger_snapshot"))
                except yaml.YAMLError:
                    snap = None
                item["base_read_snapshot"] = snap.isoformat() if snap else None
                item["base_read_stale"] = bool(latest and (not snap or snap < latest))
        outputs.append(item)
    return {"profile_dir": os.path.abspath(profile_dir), "workspace": workspace,
            "name": prof.get("name") or os.path.basename(workspace), "stage": prof.get("stage") or None,
            "has_profile_yaml": bool(prof), "ledger": ev_path if os.path.exists(ev_path) else None,
            "entries": len(ledger), "by_status": ledger.summary(), "founder_reported": founder,
            "ledger_latest_updated": latest.isoformat() if latest else None,
            "missing_information": len(missing_information(profile_dir)), "outputs": outputs}


STALE_RULES = {"date": "modified before the ledger's latest updated date",
               "mtime": "modified before evidence.yaml was last written"}


def _stale_text(rules: List[str]) -> str:
    return "; ".join(STALE_RULES[r] for r in rules)


def context_md(ctx: Dict) -> str:
    L = [f"Startup: {ctx['name']} · stage: {ctx['stage'] or 'not recorded'} · profile.yaml: "
         f"{'present' if ctx['has_profile_yaml'] else 'absent'}",
         f"Ledger: {ctx['entries']} entries ("
         + ", ".join(f"{k} {v}" for k, v in ctx["by_status"].items()) + f"); founder-reported {ctx['founder_reported']}"
         f"; latest updated {ctx['ledger_latest_updated'] or 'none recorded'}",
         f"Missing information: {ctx['missing_information']} items", "Sibling outputs:"]
    if not ctx["outputs"]:
        L.append("  none")
    for o in ctx["outputs"]:
        L.append(f"  {o['folder']} [{o['kind']}]: {len(o['files'])} files, last modified {o['modified'] or '-'}"
                 + (f"  STALE ({_stale_text(o['stale_rules'])})" if o["stale"] else ""))
        if "base_read_snapshot" in o:
            L.append(f"    base-read.yaml ledger_snapshot {o['base_read_snapshot']}"
                     + ("  STALE" if o["base_read_stale"] else ""))
        for f in o["files"][:12]:
            L.append(f"    {f['path']}  {f['modified']}" + (f"  stale: {_stale_text(f['stale_rules'])}"
                                                              if f["stale"] else ""))
        if len(o["files"]) > 12:
            L.append(f"    … {len(o['files']) - 12} more")
    return "\n".join(L)


# ============================================================================= base read (B1–B3, B6, crosswalk)
def load_yaml(path: str) -> Any:
    with open(path, encoding="utf-8") as f:
        return yaml.safe_load(f)


def evidence_ceiling(ids: Iterable[str], ledger: Ledger) -> str:
    """Highest supporting rating the cited evidence allows: strong, adequate or unknown."""
    ents = [ledger.get(i) for i in ids if ledger.get(i)]
    if any(e.status == "verified" or (e.status == "reported" and (e.source or {}).get("type") == "interview")
           for e in ents):
        return "strong"
    if any(e.status in ("reported", "estimate") for e in ents):
        return "adequate"
    return "unknown"


def weak_allowed(ids: Iterable[str], ledger: Ledger) -> bool:
    """Weak needs verified evidence or founder-provided (reported) evidence that goes against the founder."""
    return any(ledger.get(i) and ledger.get(i).status in ("verified", "reported") for i in ids)


def _dim_ids(d: Dict) -> List[str]:
    ev = d.get("evidence") or {}
    out = []
    for b in BUCKETS[:-1]:
        out += [str(x) for x in _list(ev.get(b))] if isinstance(ev, dict) else []
    return out


def _divergence_needed(dim: str, rating: str, ev: Dict[str, str]) -> Optional[str]:
    rel, _ = CROSSWALK[dim]
    if rel in ("carried", "primary"):
        e = ev.get(CROSSWALK[dim][1][0])
        if e and rating != e:
            return f"the evaluator rated {e}; this base read rates {rating}"
    elif rel == "merged":
        m, t = ev.get("market"), ev.get("timing")
        given = [x for x in (m, t) if x]
        if given:
            known = [x for x in given if x != "unknown"]
            start = min(known, key=lambda x: LEVEL[x]) if known else "unknown"
            if rating != start:
                return f"the evaluator's market/timing start from {start}; this base read rates {rating}"
    elif rel == "secondary":
        e = ev.get(CROSSWALK[dim][1][0])
        if e:
            if (e == "unknown") != (rating == "unknown"):
                return f"the evaluator rated {e}; this base read rates {rating}"
            if e != "unknown" and abs(LEVEL[e] - LEVEL[rating]) > 1:
                return f"more than one level from the evaluator's {e}"
    elif rel == "derived-clarity":
        if ev.get("customer-clarity") == "weak" and rating == "strong":
            return "D03 is Strong while the evaluator's customer clarity is Weak"
    return None


def validate_base_read(data: Any, ledger: Ledger, today=None) -> List[Dict]:
    today = _today(today)
    iss: List[Dict] = []

    def err(rule, msg):
        iss.append(_issue("error", rule, msg))

    def warn(rule, msg):
        iss.append(_issue("warning", rule, msg))

    if not isinstance(data, dict):
        return [_issue("error", "B1", "the base read is not a YAML mapping")]
    for k in ("startup", "as_of", "ledger_snapshot", "business_type", "stage", "ambition", "dimensions"):
        if k not in data:
            err("B1", f"'{k}' is missing")
    if data.get("note") is not None and not isinstance(data.get("note"), str):
        err("B1", "note must be a single line of text (for example 'Fictional example: not a real company')")
    if data.get("stage") is not None and data.get("stage") not in STAGES:
        err("B1", f"stage '{data.get('stage')}' not in {STAGES}")
    if data.get("ambition") is not None and data.get("ambition") not in AMBITIONS:
        err("B1", f"ambition '{data.get('ambition')}' not in {AMBITIONS}")
    for k in ("as_of", "ledger_snapshot"):
        if k in data and not _date(data.get(k)):
            err("B1", f"{k} must be a date (YYYY-MM-DD)")
        elif _date(data.get(k)) and _date(data.get(k)) > today:
            err("B1", f"{k} {data.get(k)} is in the future")
    latest = _ledger_latest(ledger)
    snap = _date(data.get("ledger_snapshot"))
    if latest and snap and snap < latest:
        warn("B1", f"ledger_snapshot {snap} is older than the ledger's latest update {latest}: re-read the "
                   "ledger before relying on this base read")
    dims = data.get("dimensions") or {}
    if not isinstance(dims, dict):
        return iss + [_issue("error", "B1", "dimensions must be a mapping D01..D15")]
    for d in dims:
        if d not in DIMENSIONS:
            err("B1", f"unknown dimension '{d}'")
    any_evaluator = False
    for dim, name in DIMENSIONS.items():
        d = dims.get(dim)
        tag = f"{dim} {name}"
        if not isinstance(d, dict):
            err("B1", f"{tag}: missing")
            continue
        rating = _text(d.get("rating")).lower()
        if rating not in RATINGS:
            hint = " (write 'unknown', never 'insufficient')" if rating.startswith("insufficient") else ""
            err("B1", f"{tag}: rating '{rating}' not in {RATINGS}{hint}")
        if _text(d.get("confidence")).lower() not in CONFIDENCE:
            err("B1", f"{tag}: confidence '{d.get('confidence')}' not in {CONFIDENCE}")
        if not isinstance(d.get("critical"), bool):
            err("B1", f"{tag}: 'critical' must be true or false")
        if not _text(d.get("explanation")):
            err("B1", f"{tag}: explanation is empty")
        ev = d.get("evidence")
        if not isinstance(ev, dict):
            err("B1", f"{tag}: evidence block with the six buckets is missing")
            continue
        for b in BUCKETS:
            if b not in ev:
                err("B1", f"{tag}: evidence bucket '{b}' is missing (write [] when empty)")
        for b in ev:
            if b not in BUCKETS:
                err("B1", f"{tag}: unknown evidence bucket '{b}'")
        # B2 cited IDs exist and sit in the right bucket
        for b, statuses in BUCKET_STATUSES.items():
            for eid in _list(ev.get(b)):
                eid = str(eid)
                e = ledger.get(eid)
                if not e:
                    err("B2", f"{tag}: {eid} is not in the ledger")
                elif e.status not in statuses:
                    err("B2", f"{tag}: {eid} has status '{e.status}' but is listed under '{b}'")
        for u in _list(ev.get("unknowns")):
            if ID_RE.fullmatch(str(u).strip()):
                err("B2", f"{tag}: unknowns are open questions with no ledger entry; {u} belongs in a bucket")
        # B3 evidence ceiling against real ledger statuses
        ids = _dim_ids(d)
        ceil = evidence_ceiling(ids, ledger)
        if rating in ("strong", "adequate") and LEVEL[rating] > LEVEL.get(ceil, 0):
            need = ("a verified entry (or interview-reported behavioural evidence)" if rating == "strong"
                    else "at least one verified, reported or estimate entry")
            err("B3", f"{tag}: rated {rating.capitalize()} but the cited evidence allows at most "
                      f"{ceil.capitalize()}; {rating.capitalize()} needs {need}")
        if rating == "weak" and not weak_allowed(ids, ledger):
            err("B3", f"{tag}: rated Weak without verified or founder-provided evidence; rate it Unknown")
        dc = _text(d.get("ceiling")).lower()
        if dc:
            if dc not in RATINGS:
                err("B1", f"{tag}: ceiling '{dc}' not in {RATINGS}")
            elif dc in LEVEL and LEVEL[dc] > LEVEL.get(ceil, 0):
                err("B3", f"{tag}: declared ceiling {dc} is above what the ledger allows ({ceil})")
        # crosswalk divergence notes
        evr = d.get("evaluator")
        if evr is not None:
            any_evaluator = True
            if not isinstance(evr, dict):
                err("B1", f"{tag}: evaluator must map evaluator dimension keys to ratings")
                continue
            allowed = CROSSWALK[dim][1]
            ok = {}
            for k, v in evr.items():
                k, v = str(k).lower(), _text(v).lower()
                if k not in allowed:
                    err("B1", f"{tag}: evaluator key '{k}' does not map to {dim}"
                              + (f" (expected {', '.join(allowed)})" if allowed else
                                 " (no evaluator dimension maps here)"))
                elif v not in RATINGS:
                    err("B1", f"{tag}: evaluator rating '{v}' not in {RATINGS}")
                else:
                    ok[k] = v
            why = _divergence_needed(dim, rating, ok) if rating in RATINGS else None
            note = _text(d.get("divergence_note"))
            if why and not note:
                err("B1", f"{tag}: divergence note required ({why}); name the evaluator report, both ratings and "
                          "the ledger IDs")
            elif why and not ID_RE.search(note):
                warn("B1", f"{tag}: the divergence note should cite the ledger IDs that justify the difference")
    if any_evaluator and not _text(data.get("imported_from")):
        warn("B1", "evaluator ratings are declared but 'imported_from' does not name the evaluator report")
    if data.get("judgements") is not None:
        iss += check_judgements(data.get("judgements"), dims, data.get("ambition"), ledger)
    return iss


def _rating(dims, dim) -> str:
    return _text((dims.get(dim) or {}).get("rating")).lower()


def _conf(dims, dim) -> str:
    return _text((dims.get(dim) or {}).get("confidence")).lower()


def _ev(dims, dim, bucket) -> List:
    ev = (dims.get(dim) or {}).get("evidence") or {}
    return _list(ev.get(bucket)) if isinstance(ev, dict) else []


def weak_decides(dims: Dict, dim: str) -> bool:
    """A Weak rating decides a judgement or a stance only at medium or high confidence, on verified or reported
    (founder-provided, against interest) evidence."""
    return (_rating(dims, dim) == "weak" and _conf(dims, dim) in ("medium", "high")
            and bool(_ev(dims, dim, "verified") or _ev(dims, dim, "reported")))


def unknown_like(dims: Dict, dim: str) -> bool:
    """Unknown, or Weak held at low confidence (which counts as Unknown for judgements and stances)."""
    r = _rating(dims, dim)
    return r == "unknown" or (r == "weak" and not weak_decides(dims, dim))


REVENUE_RE = re.compile(r"\brevenue\b|\bpaid (?:the|an?|annual|monthly|for|in)\b|\bpaying (?:customers|cooperatives|users|"
                        r"subscribers|clients|schools)\b|\binvoices?\b|\bsales (?:of|to|revenue|records?)\b|"
                        r"\bprepa(?:id|yments?)\b|\bmrr\b|\barr\b|\bturnover\b|\breceipts\b", re.I)
REVENUE_KEY_RE = re.compile(r"^(?:traction\.(?:revenue|paying|paid|sales|mrr|arr|orders)|revenue|finance\.revenue)", re.I)
MITIGATION_RE = re.compile(r"mitigat\w*|credible (?:path|route|fix|change|remedy)|can be (?:fixed|changed|addressed|"
                           r"remedied)\b[^.]{0,30}\b(?:inside|within) the current|(?:inside|within) the current "
                           r"(?:segment|model|channel|price)", re.I)
J2_CLASS_DIMS = {"venture": ("D02", "D10", "D13"), "operator-strategic": ("D09", "D11", "D12"),
                 "debt-or-revenue-based": ("D12",)}
_ADQ = ("strong", "adequate")


def has_verified_revenue(ledger: Optional[Ledger]) -> Optional[bool]:
    if ledger is None:
        return None
    def says_revenue(claim: str) -> bool:
        for m in REVENUE_RE.finditer(claim):     # "no ... revenue data" records the absence of revenue
            if not re.search(r"\b(?:no|not|zero|without|none|nil|nothing)\b", claim[max(0, m.start() - 60):m.start()],
                             re.I):
                return True
        return False
    return any(e.status == "verified" and (REVENUE_KEY_RE.search(str(e.key or "")) or says_revenue(e.claim))
               for e in ledger.entries)


def _ans_name(a: str) -> str:
    return {"yes": "Yes", "no": "No", "not-yet-determinable": "Not yet determinable"}.get(a, a)


def judgement_gates(ans: Dict[str, Any], reasons: Dict[str, str], dims: Dict, ambition: Optional[str] = None,
                    ledger: Optional[Ledger] = None) -> List[str]:
    """The judgement rules of references/verdict.md against the base read. `ans` maps J1, J3, J4, J5 to an answer
    and J2 to a list of (class, answer). A Weak at low confidence counts as Unknown. Returns error messages."""
    out = []
    crit = [d for d in DIMENSIONS if (dims.get(d) or {}).get("critical") is True]
    core = ("D01", "D03", "D06", "D07")

    def want(k, got, allowed, why):
        if got and got not in allowed:
            out.append(f"{k} {JUDGEMENTS[k]} is {_ans_name(got)} but the base read gives "
                       f"{' or '.join(_ans_name(x) for x in allowed)}: {why}")

    j1 = ans.get("J1")
    cw = [d for d in core if weak_decides(dims, d)]
    cu = [d for d in core if unknown_like(dims, d)]
    if cw:
        want("J1", j1, ["no"], f"{', '.join(cw)} Weak at medium or high confidence")
    elif cu:
        want("J1", j1, ["not-yet-determinable"], f"{', '.join(cu)} Unknown (or Weak at low confidence)")
    else:
        blockers = [d for d in crit if weak_decides(dims, d)] + (["D12"] if weak_decides(dims, "D12") else [])
        if blockers:
            want("J1", j1, ["no", "not-yet-determinable"], f"{', '.join(sorted(set(blockers)))} Weak")
        else:
            want("J1", j1, ["yes"], "D01, D03, D06 and D07 are at least Adequate, D12 is not Weak and no critical "
                                    "dimension is Weak")
    revenue = has_verified_revenue(ledger)
    for cls, a in ans.get("J2", []):
        if cls not in J2_CLASS_DIMS:
            continue
        cd = J2_CLASS_DIMS[cls]
        tag = f"J2 Investable business ({cls})"
        if j1 == "no":
            allowed, why = ["no"], "J1 is No"
        elif cls == "debt-or-revenue-based" and revenue is False:
            allowed, why = ["no"], "no verified revenue in the ledger"
        elif [d for d in cd if weak_decides(dims, d)]:
            allowed, why = ["no"], f"{', '.join(d for d in cd if weak_decides(dims, d))} Weak"
        elif [d for d in cd if unknown_like(dims, d)]:
            allowed, why = ["not-yet-determinable"], f"{', '.join(d for d in cd if unknown_like(dims, d))} Unknown"
        else:
            if cls == "venture":
                ok = all(_rating(dims, d) in _ADQ for d in cd) and ambition == "venture"
                why = "D02, D10, D13 at least Adequate and ambition 'venture'"
            elif cls == "operator-strategic":
                ok = (_rating(dims, "D09") in _ADQ or _rating(dims, "D11") in _ADQ) and _rating(dims, "D12") in _ADQ
                why = "D09 or D11, and D12, at least Adequate"
            else:
                ok = _rating(dims, "D12") in _ADQ and revenue is not False
                why = "D12 at least Adequate with verified revenue"
            allowed, why = (["yes"], why) if ok else (["no"], "the class conditions are not met (" + why + ")")
        if a and a not in allowed:
            out.append(f"{tag} is {_ans_name(a)} but the base read gives {' or '.join(map(_ans_name, allowed))}: {why}")
    cu_all = [d for d in crit if unknown_like(dims, d)]
    if ans.get("J3") == "yes":
        if not any(a == "yes" for _, a in ans.get("J2", [])):
            out.append("J3 Investment-ready Yes needs J2 Yes for at least one investor class")
        if cu_all:
            out.append(f"J3 Investment-ready Yes with critical dimensions Unknown ({', '.join(cu_all)})")
        if weak_decides(dims, "D15"):
            out.append("J3 Investment-ready Yes with D15 Legal and regulatory risks Weak")
    thin = [d for d in crit if _rating(dims, d) == "adequate" and not _ev(dims, d, "verified")
            and not _ev(dims, d, "reported")]
    j4_yes = bool(cu_all or thin)
    want("J4", ans.get("J4"), ["yes"] if j4_yes else ["no"],
         (f"critical {', '.join(cu_all)} Unknown" if cu_all else
          f"critical {', '.join(thin)} Adequate on assumptions and estimates only" if thin else
          "every critical dimension rests on verified or reported evidence"))
    cweak = [d for d in crit if weak_decides(dims, d)]
    j5 = ans.get("J5")
    if cweak:
        if j5 == "no" and not MITIGATION_RE.search(reasons.get("J5", "")):
            out.append(f"J5 Should not proceed is No while critical {', '.join(cweak)} is Weak at medium or high "
                       "confidence: answer Yes, or name the credible mitigation inside the current form in the reason")
        elif j5 == "not-yet-determinable":
            out.append("J5 Should not proceed is not answered 'Not yet determinable': answer Yes or No")
    elif j5 == "yes":
        out.append("J5 Should not proceed Yes needs a critical dimension rated Weak at medium or high confidence on "
                   "verified or founder-provided evidence")
    return out


def check_judgements(j: Any, dims: Dict, ambition: Optional[str] = None,
                     ledger: Optional[Ledger] = None) -> List[Dict]:
    """B6: the five judgements in a base read: presence, classes, combinations and the gates of verdict.md."""
    iss: List[Dict] = []

    def err(msg):
        iss.append(_issue("error", "B6", msg))

    if not isinstance(j, dict):
        return [_issue("error", "B6", "judgements must be a mapping J1..J5")]
    ans: Dict[str, Any] = {"J2": []}
    reasons: Dict[str, str] = {}
    for k in JUDGEMENTS:
        if k not in j:
            err(f"{k} {JUDGEMENTS[k]} is missing")
            continue
        for it in (_list(j[k]) if k == "J2" else [j[k]]):
            if not isinstance(it, dict):
                err(f"{k}: must be a mapping with answer and reason")
                continue
            a = _text(it.get("answer")).lower().replace(" ", "-")
            if a not in ANSWERS:
                err(f"{k}: answer '{it.get('answer')}' not in {ANSWERS}")
                continue
            if not _text(it.get("reason")):
                err(f"{k}: reason is empty")
            if k == "J2":
                c = _text(it.get("class")).lower()
                if c not in INVESTOR_CLASSES:
                    err(f"J2 must name an investor class {INVESTOR_CLASSES} (got '{it.get('class') or ''}')")
                ans["J2"].append((c, a))
            else:
                ans[k] = a
                reasons[k] = _text(it.get("reason"))
    for k in j:
        if k not in JUDGEMENTS:
            err(f"unknown judgement '{k}'")
    iss += _combination_errors(ans)
    if dims:
        for m in judgement_gates(ans, reasons, dims, ambition, ledger):
            err(m)
    return iss


def _combination_errors(ans: Dict[str, Any], where: str = "") -> List[Dict]:
    out = []
    pre = f"{where}: " if where else ""
    j2_yes = any(a == "yes" for _, a in ans.get("J2", []))
    if ans.get("J3") == "yes" and ans.get("J4") == "yes":
        out.append(_issue("error", "B6", pre + "J3 Investment-ready Yes and J4 Needs further validation Yes cannot "
                                               "both hold"))
    if ans.get("J5") == "yes" and (j2_yes or ans.get("J3") == "yes"):
        out.append(_issue("error", "B6", pre + "J5 Should not proceed Yes excludes J2 Yes and J3 Yes for the current "
                                               "form"))
    return out


def evidence_profile_line(dims: Dict) -> str:
    """The fixed summary line. It always shows the Unknown count and never a numeric aggregate."""
    c = {r: 0 for r in RATINGS}
    for dim in DIMENSIONS:
        r = _rating(dims, dim)
        if r in c:
            c[r] += 1
    crit = [f"{d} {_rating(dims, d).capitalize()}" for d in DIMENSIONS
            if (dims.get(d) or {}).get("critical") is True and _rating(dims, d) in RATINGS]
    return (f"Base read (15 dimensions): Strong {c['strong']} · Adequate {c['adequate']} · Weak {c['weak']} · "
            f"Unknown {c['unknown']}. Critical dimensions: {', '.join(crit) if crit else 'none declared'}.")


def _ev_line(label: str, ids: List[str], ledger: Ledger) -> str:
    if not ids:
        return f"- {label}: none"
    parts = []
    for eid in ids:
        e = ledger.get(eid)
        if not e:
            parts.append(f"[{eid}]")
            continue
        st = (e.source or {}).get("type", "")
        tagname = ("founder-provided" if e.status == "reported" and st == "founder" else
                   f"reported, {st}" if e.status == "reported" else e.status)
        parts.append(f"[{eid}] {e.claim.replace('|', '/')} ({tagname})")
    return f"- {label}: " + "; ".join(parts)


def render_base_read(data: Dict, ledger: Ledger, profile_rel: Optional[str] = None) -> str:
    dims = data.get("dimensions") or {}
    name = _text(data.get("startup")) or "startup"
    as_of, snap = _text(data.get("as_of")), _text(data.get("ledger_snapshot"))
    fm = {"title": f"{name}: base read", "doc_type": "shark-tank", "simulation": True, "kind": "base-read",
          "investors": [], "date": as_of}
    if profile_rel:
        fm["profile"] = profile_rel
    L = ["---", yaml.safe_dump(fm, sort_keys=False, allow_unicode=True).strip(), "---", "",
         f"> [!SIMULATION] {SIM_LABEL} any investor. Based on public sources as of {as_of} and the startup evidence "
         f"available on {snap}.", "", f"# {name}: base read", ""]
    if _text(data.get("note")):
        L += [f"*{_text(data.get('note'))}*", ""]
    L += [
         f"Stage: {data.get('stage')} · Business type: {', '.join(str(x) for x in _list(data.get('business_type')))}"
         f" · Ambition: {data.get('ambition')} · Ledger snapshot: {snap}", "",
         evidence_profile_line(dims), "",
         "Ratings are Strong, Adequate, Weak or Unknown (not enough evidence to judge). They are never added up. "
         "For D11 and D15, Strong means the risk is low or well controlled.", "",
         "## Critical dimensions", "", "| Dimension | Rating | Confidence | Decisive question |", "|---|---|---|---|"]
    for dim, dn in DIMENSIONS.items():
        d = dims.get(dim) or {}
        if d.get("critical") is True:
            L.append(f"| {dim} {dn} | {_rating(dims, dim).capitalize()} | {_text(d.get('confidence'))} | "
                     f"{DECISIVE[dim]} |")
    L += ["", "## Dimensions", ""]
    labels = (("verified", "Verified"), ("reported", "Founder-provided or reported"), ("estimate", "Estimates"),
              ("assumption", "Assumptions"), ("disputed", "Unverified or disputed"))
    for dim, dn in DIMENSIONS.items():
        d = dims.get(dim) or {}
        ev = d.get("evidence") or {}
        r = _rating(dims, dim)
        L += [f"### {dim} {dn}: {r.capitalize()} (confidence: {_text(d.get('confidence'))})"
              + (" [critical]" if d.get("critical") is True else ""), "",
              _text(d.get("explanation")), "", f"Decisive question: {DECISIVE[dim]}", ""]
        for key, lab in labels:
            L.append(_ev_line(lab, [str(x) for x in _list(ev.get(key))], ledger))
        unk = [str(u) for u in _list(ev.get("unknowns"))]
        L.append(f"- Unknowns: {'; '.join(unk) if unk else 'none'}")
        ceil = evidence_ceiling(_dim_ids(d), ledger)
        L.append(f"- Ceiling from the ledger: {ceil.capitalize()}")
        if _text(d.get("upgrade_if")):
            L.append(f"- Upgrade if: {_text(d.get('upgrade_if'))}")
        if _text(d.get("downgrade_if")):
            L.append(f"- Downgrade if: {_text(d.get('downgrade_if'))}")
        L.append("")
    notes = [(dim, dims[dim]) for dim in DIMENSIONS
             if isinstance(dims.get(dim), dict) and _text(dims[dim].get("divergence_note"))]
    if notes:
        L += ["## Divergences from the idea evaluation", "",
              f"Evaluator report: {_text(data.get('imported_from')) or 'not named'}"
              + (f" ({_text(data.get('imported_date'))})" if data.get("imported_date") else "")
              + ". Re-run the startup-idea-evaluator so the two reports agree.", ""]
        for dim, d in notes:
            evr = ", ".join(f"{k} {v}" for k, v in (d.get("evaluator") or {}).items())
            L.append(f"- {dim} {DIMENSIONS[dim]}: evaluator {evr or 'n/a'}; base read {_rating(dims, dim)}. "
                     f"{_text(d.get('divergence_note'))}")
        L.append("")
    j = data.get("judgements")
    if isinstance(j, dict):
        L += ["## Five judgements", "", "| Judgement | Answer | Reason | Deciding dimensions |", "|---|---|---|---|"]
        for k, jn in JUDGEMENTS.items():
            for it in (_list(j.get(k)) if k == "J2" else [j.get(k)]):
                if not isinstance(it, dict):
                    continue
                a = _text(it.get("answer")).replace("-", " ").capitalize()
                lab = f"{k} {jn}" + (f" ({_text(it.get('class'))})" if k == "J2" else "")
                L.append(f"| {lab} | {a} | {_text(it.get('reason')).replace('|', '/')} | "
                         f"{', '.join(str(x) for x in _list(it.get('dimensions')))} |")
        L.append("")
    return "\n".join(L).rstrip() + "\n"


# ============================================================================= question queue
def queue(base: Dict, profiles: List[Profile], budget: int = 10, ledger: Optional[Ledger] = None) -> List[Dict]:
    """Deterministic interrogation priority (design 5.3).

    Tiers: 1 critical Unknown; 2 critical Weak; 3 critical Adequate resting only on founder-provided or estimate
    evidence (no verified entry, no interview-reported entry when the ledger is given); 4 non-critical with
    primary emphasis (for any selected investor), Unknown or Weak; 5 other Unknown. Within a tier: best emphasis
    across the investors (primary, secondary, standard), then dimension number. Each row is attributed among the
    investors with a lens on the dimension: the best emphasis for that dimension first (primary, then secondary,
    then standard), then members not in restricted mode, then the fewest rows so far, then the order given, so
    lenses rotate across equals without changing tier order. A member whose effective confidence is low is in
    restricted mode: its rows carry lens 'base'. Rows no lens covers are attributed to 'base'.
    """
    dims = base.get("dimensions") or {}
    rows = []
    for dim in DIMENSIONS:
        d = dims.get(dim) or {}
        r, crit = _rating(dims, dim), d.get("critical") is True
        ev = d.get("evidence") or {}
        primary = any(p.emphasis_rank(dim) == 0 for p in profiles)
        tier = None
        if crit and r == "unknown":
            tier = 1
        elif crit and r == "weak":
            tier = 2
        elif crit and r == "adequate" and not _list(ev.get("verified")) and not (ledger and any(
                ledger.get(str(i)) and (ledger.get(str(i)).source or {}).get("type") == "interview"
                for i in _list(ev.get("reported")))):
            tier = 3
        elif not crit and primary and r in ("unknown", "weak"):
            tier = 4
        elif r == "unknown":
            tier = 5
        if tier:
            rank = min((p.emphasis_rank(dim) for p in profiles), default=2)
            rows.append((tier, rank, int(dim[1:]), dim, r))
    rows.sort()
    used = {p.id: 0 for p in profiles}
    out = []
    for tier, rank, _, dim, r in rows:
        cands = [p for p in profiles if p.lens_for(dim)]
        restricted = False
        if cands:
            # primary before secondary before standard; full-confidence members before restricted ones;
            # rotation (fewest rows so far, then the order given) only among equals
            pick = min(cands, key=lambda p: (p.emphasis_rank(dim), p.effective == "low", used[p.id],
                                             profiles.index(p)))
            used[pick.id] += 1
            restricted = pick.effective == "low"
            inv, lens = pick.id, ("base" if restricted else pick.lens_for(dim))
            emph = ("primary", "secondary", "standard")[pick.emphasis_rank(dim)]
        else:
            inv, lens, emph = "base", "base", "standard"
        out.append({"tier": tier, "dimension": dim, "name": DIMENSIONS[dim], "rating": r, "investor": inv,
                    "lens": lens, "emphasis": emph, "restricted": restricted, "decisive_question": DECISIVE[dim]})
        if len(out) >= budget:
            break
    return out


# ============================================================================= stance rule
def _deciding(base: Dict, profile) -> List[str]:
    dims = (base or {}).get("dimensions") or {}
    primary = set(profile.emphasis["primary"]) if isinstance(profile, Profile) else set()
    return [d for d in DIMENSIONS if (dims.get(d) or {}).get("critical") is True or d in primary]


def expected_stance(base: Dict, profile: Optional[Profile], rows: Optional[List[Dict]] = None) -> Tuple[str, Dict]:
    """The stance the base read and profile call for (individual-evaluation.md, Stance), with the counts.

    It is decided from the base read alone, never from which rows the author chose to write. Deciding set:
    dimensions critical for the startup or `primary` for the investor, each counted once. A Weak held at low
    confidence counts as Unknown. In order: not-persuaded (a deciding dimension Weak at medium or high
    confidence); no-view (half or more of the deciding set Unknown); persuaded (every deciding dimension
    Adequate or Strong and no concern row on a Weak rating); otherwise conditional.
    """
    dims = (base or {}).get("dimensions") or {}
    deciding = _deciding(base, profile)
    weak = [d for d in deciding if weak_decides(dims, d)]
    unknown = [d for d in deciding if unknown_like(dims, d)]
    if rows is not None:
        concern_dims = {r["dimension"] for r in rows if r["kind"] in "CB" and r["dimension"]}
        concern_on_weak = any(_rating(dims, d) == "weak" for d in concern_dims)
    else:
        lens_dims = {str(x) for ln in (profile.lenses.values() if profile else []) for x in _list(ln.get("dimensions"))}
        concern_on_weak = any(_rating(dims, d) == "weak" for d in lens_dims)
    info = {"deciding": deciding, "weak": weak, "unknown": unknown}
    if weak:
        return "not-persuaded", info
    if deciding and 2 * len(unknown) >= len(deciding):
        return "no-view", info
    if all(_rating(dims, d) in _ADQ for d in deciding) and not concern_on_weak:
        return "persuaded", info
    return "conditional", info


def missing_concern_rows(base: Dict, profile, rows: List[Dict]) -> List[Tuple[str, str]]:
    """Deciding dimensions the procedure says must carry a row: a concern or potential deal-breaker on each Weak
    (medium or high confidence), and a concern worded as an evidence gap on each Unknown (or low-confidence Weak)."""
    dims = (base or {}).get("dimensions") or {}
    have = {r["dimension"] for r in rows if r["kind"] in "CB" and r["dimension"]}
    out = []
    for d in _deciding(base, profile):
        if d in have:
            continue
        if weak_decides(dims, d):
            out.append((d, "Weak"))
        elif unknown_like(dims, d):
            out.append((d, "Unknown"))
    return out


def _stance_why(info: Dict) -> str:
    return (f"{len(info['unknown'])} of {len(info['deciding'])} critical-or-primary dimensions Unknown"
            + (f" ({', '.join(info['unknown'])})" if info["unknown"] else "")
            + f", {len(info['weak'])} Weak" + (f" ({', '.join(info['weak'])})" if info["weak"] else ""))


# ============================================================================= output guards
REPORTED_LABEL_RE = re.compile(r"founder[- ]provided|company[- ]provided|\breported\b|founder[- ]reported|"
                               r"by the company['’]s own account|\baccording to\b", re.I)
ESTIMATE_LABEL_RE = re.compile(r"\bestimat(?:e|ed|es)\b", re.I)
WEAK_LABEL_RE = re.compile(r"\bassum\w*|\bestimat\w*|\bunverified\b|\bprojected\b|\bdisputed\b", re.I)
SHORT_ID_RE = re.compile(r"\b(?:E-\d{3,}|[A-Z]{1,2}\d{1,3}[a-z]?)\b")
# honest panel and metric wording that gtm.check_claims would read as a traction or market-size claim; each is
# neutralised (digits removed, line structure kept) before the claim guard runs on a shark-tank document
_N = r"[1-7]"
_OF = r"[ \t]*(?:(?:out[ \t]+)?of(?:[ \t]+the)?|/)[ \t]*"
_WHO = r"(?:panel[ \t]+)?(?:members|investors)\b"
PANEL_VERBS = (r"(?:cannot|can|could|list|lists|listed|hold|holds|held|agree|agrees|agreed|share|shares|shared|rate|"
               r"rated|read|reads|put|puts|record|records|recorded|treat|treats|treated|disagree|disagreed|differ|"
               r"differed|converge|converged|remain|remained|keep|kept|change|changed|find|found|place|placed|name|"
               r"named|raise|raised|flag|flagged|are[ \t]+(?:not[ \t]+)?persuaded|were[ \t]+(?:not[ \t]+)?persuaded)\b")
CLAIM_EXEMPT = (
    # panel member counts ("3 of 3 members", "2 out of 3 members", "3/3 members", "unanimous (3 of 3)",
    # "the 3 members", "panel of 3 members", "2 members cannot form a view"); a count of 8 or more is left to
    # the traction guard, because a panel has 3 to 7 members and a business's own members are not panellists
    (re.compile(r"\b" + _N + _OF + _N + r"[ \t]+" + _WHO, re.I), "several of the members"),
    (re.compile(r"\b(unanimous|majority|split|no consensus|consensus)[ \t]*[(:,]?[ \t]*" + _N + _OF + _N + r"[ \t]*\)?", re.I),
     r"\1 (counted)"),
    (re.compile(r"\b(all|the|both|other|remaining)[ \t]+" + _N + r"[ \t]+" + _WHO, re.I), r"\1 the members"),
    (re.compile(r"\b(panel|consensus) of[ \t]+" + _N + r"[ \t]+" + _WHO, re.I), r"\1 of the members"),
    (re.compile(r"\b" + _N + r"[ \t]+" + _WHO + r"(?=[ \t]+(?:also[ \t]+|still[ \t]+)?" + PANEL_VERBS + ")", re.I),
     "several members"),
    (re.compile(r"\bretention at \d+[- ]?days?\b", re.I), "retention-at-n-days"),
    # profile verification is not business validation: "validated profiles", "the profile is validated"
    (re.compile(r"\bvalidated(?=[ \t]+(?:investor[ \t]+)?profiles?\b)", re.I), "checked"),
    (re.compile(r"(\bprofiles?[ \t]+(?:is|are|was|were|has been|have been)[ \t]+)validated\b", re.I), r"\1checked"),
    (DIM_RE, "Dnn"),
)


def _claims_text(text: str) -> str:
    for rx, sub in CLAIM_EXEMPT:
        text = rx.sub(sub, text)
    return text
CONVERGENCE_RE = re.compile(r"declared convergence|\[!CONVERGENCE\]", re.I)
STANCE_PATTERNS = {"not-persuaded": re.compile(r"\bnot persuaded on current evidence\b", re.I),
                   "persuaded": re.compile(r"(?<!not )\bpersuaded on current evidence\b", re.I),
                   # anchored: at the start of a line, of a table cell or of a bold span, so that prose such as
                   # "the reading is conditional on D07" inside another stance's explanation is not a second label
                   "conditional": re.compile(r"(?:^|\||\*\*|__)[ \t]*(?:[-*>][ \t]*)*(?:\*\*|__)?[ \t]*"
                                             r"(?<!interested, )conditional on\b", re.I | re.M),
                   "no-view": re.compile(r"\bcannot form a view\b", re.I)}
ROW_ID_RE = re.compile(r"^([ACQRBM])(\d+)$")
EXCHANGE_ID_RE = re.compile(r"^X(\d+)([a-z]?)$")
KIND_OF = {"A": "attracts", "C": "concern", "Q": "question", "R": "evidence demanded",
           "B": "potential deal-breaker", "M": "recommendation"}


def _clean_cell(c: str) -> str:
    return re.sub(r"[*_`]", "", c).strip()


def _cells(line: str) -> List[str]:
    s = line.strip()
    if s.startswith("|"):
        s = s[1:]
    if s.endswith("|"):
        s = s[:-1]
    return [c.strip() for c in re.split(r"(?<!\\)\|", s)]


class _Doc:
    """A parsed output document: lines with numbers, fences, scenario blocks, headings and tables."""

    def __init__(self, text: str):
        self.text = text
        self.meta, self.meta_error = {}, None
        lines = text.split("\n")
        start = 0
        if text.startswith("---\n"):
            end = next((i for i in range(1, len(lines)) if lines[i].strip() == "---"), None)
            if end is not None:
                try:
                    self.meta = yaml.safe_load("\n".join(lines[1:end])) or {}
                except yaml.YAMLError as e:
                    self.meta_error = str(e).splitlines()[0]
                if not isinstance(self.meta, dict):
                    self.meta = {}
                start = end + 1
        self.lines = [(n + 1, ln) for n, ln in enumerate(lines) if n >= start]
        self.content: List[Tuple[int, str]] = []    # non-fenced, non-comment lines
        self.scenario: set = set()                  # line numbers inside [!SCENARIO] callouts
        self.scenarios: List[List[Tuple[int, str]]] = []
        self.headings: List[Tuple[int, int, str]] = []
        fence, comment, in_scn = False, False, False
        for n, ln in self.lines:
            s = ln.strip()
            if s.startswith("```") or s.startswith("~~~"):
                fence = not fence
                continue
            if fence:
                continue
            if comment or s.startswith("<!--"):
                comment = "-->" not in s
                continue
            if s.startswith(">"):
                inner = s.lstrip(">").strip()
                if re.match(r"^\[!SCENARIO\]", inner, re.I):
                    in_scn = True
                    self.scenarios.append([])
                elif re.match(r"^\[!\w+\]", inner):
                    in_scn = False
                if in_scn:
                    self.scenario.add(n)
                    self.scenarios[-1].append((n, inner))
            else:
                in_scn = False
            m = re.match(r"^(#{1,6})\s+(.*)$", s)
            if m:
                self.headings.append((n, len(m.group(1)), _clean_cell(m.group(2))))
            self.content.append((n, ln))

    def first_content(self, after: int = 0) -> Tuple[Optional[int], str]:
        """The first content block after line `after`; a callout's '>' lines are joined."""
        it = [(n, ln) for n, ln in self.content if n > after and ln.strip()]
        if not it:
            return None, ""
        n0, first = it[0]
        if not first.strip().startswith(">"):
            return n0, first.strip()
        buf = []
        prev = n0 - 1
        for n, ln in it:
            if n != prev + 1 or not ln.strip().startswith(">"):
                break
            inner = ln.strip().lstrip(">").strip()
            if buf and re.match(r"^\[!\w+\]", inner):
                break
            buf.append(inner)
            prev = n
        return n0, " ".join(buf)

    def section(self, name: str) -> Optional[Tuple[int, int]]:
        """Line range (heading line, end) of the first heading containing `name`."""
        for i, (n, lvl, t) in enumerate(self.headings):
            if name.lower() in t.lower():
                end = next((m for m, l2, _ in self.headings[i + 1:] if l2 <= lvl), 10 ** 9)
                return n, end
        return None

    def tables(self, rng: Optional[Tuple[int, int]] = None) -> List[Dict]:
        out, cur = [], None
        prev = None
        for n, ln in self.content:
            s = ln.strip()
            if rng and not (rng[0] < n < rng[1]):
                continue
            if s.startswith("|") and prev is not None and prev[0] == n - 1:
                if cur is None and re.match(r"^\|?\s*:?-{2,}", s) and prev[1].strip().startswith("|"):
                    cur = {"line": prev[0], "header": [_clean_cell(c).lower() for c in _cells(prev[1])],
                           "rows": []}
                    out.append(cur)
                elif cur is not None:
                    cur["rows"].append((n, _cells(s)))
            elif not s.startswith("|"):
                cur = None
            prev = (n, ln)
        return out


def _col(table: Dict, *names: str) -> Optional[int]:
    for i, h in enumerate(table["header"]):
        first = h.split()[0] if h.split() else h
        if any(first == nm or h.startswith(nm) for nm in names):
            return i
    return None


def _cell(row: List[str], i: Optional[int]) -> str:
    return row[i] if i is not None and i < len(row) else ""


def _units(line: str) -> List[str]:
    s = line.strip()
    if s.startswith("|"):
        return [c for c in _cells(s) if c]
    s = re.sub(r"^(?:>\s*)+", "", s)
    s = re.sub(r"^(?:[-*+]|\d+[.)])\s+", "", s)
    return [u for u in SENT_RE.split(s) if u.strip()]


def _strip_code(s: str) -> str:
    return re.sub(r"`[^`]*`", " ", URL_RE.sub(" ", s))


def _name_res(profiles: Dict[str, Profile], doc_ids: List[str]):
    """Regexes for investor names: full names and variants for every library profile; surnames for the
    document's own investors."""
    names = []
    for p in profiles.values():
        names += p.names
    full = re.compile(r"\b(?:" + "|".join(re.escape(n) for n in sorted(set(names), key=len, reverse=True))
                      + r")\b", re.I) if names else None
    sur = []
    for i in doc_ids:
        p = profiles.get(i)
        if p and len(p.name.split()) > 1 and len(p.name.split()[-1]) >= 3:
            sur.append(p.name.split()[-1])
    surname = re.compile(r"\b(?:" + "|".join(re.escape(s) for s in sorted(set(sur))) + r")\b") if sur else None
    return full, surname


def _has_name(s: str, full, surname) -> Optional[str]:
    for rx in (full, surname):
        if rx:
            m = rx.search(s)
            if m:
                return m.group(0)
    return None


# retired label (polish round three): it implied interest, which the skill forbids
OLD_CONDITIONAL_RE = re.compile(r"\binterested,?[ \t]+conditional\b", re.I)


def stance_of(text: str) -> List[str]:
    """Stance keys found in a Stance section (pass its lines joined with newlines) or a table cell."""
    text = OLD_CONDITIONAL_RE.sub(" ", text)        # never recognised; reported separately
    return [k for k, rx in STANCE_PATTERNS.items() if rx.search(text)]


def parse_trace(doc: "_Doc") -> List[Dict]:
    rng = doc.section("point trace")
    rows = []
    for t in doc.tables(rng):
        ci, ck, cl, cd = _col(t, "#", "id"), _col(t, "kind"), _col(t, "lens"), _col(t, "dimension")
        if cl is None or cd is None or (ck is None and rng is None):
            continue
        cp, ce = _col(t, "point"), _col(t, "evidence")
        for n, row in t["rows"]:
            rid = _clean_cell(_cell(row, ci if ci is not None else 0))
            m = ROW_ID_RE.match(rid)
            if not m:
                continue
            lens_cell = _clean_cell(_cell(row, cl))
            lm = re.match(r"^(?:L-?(\d+)\b|(base)\b)", lens_cell, re.I)
            lens = None if not lm else ("base" if lm.group(2) else f"L{lm.group(1)}")
            dm = DIM_RE.search(_cell(row, cd))
            rows.append({"line": n, "id": rid, "kind": m.group(1), "num": int(m.group(2)), "lens": lens,
                         "lens_cell": lens_cell, "dimension": dm.group(0) if dm else None,
                         "point": _cell(row, cp), "evidence": _cell(row, ce)})
    return rows


def _tokens(s: str, strip: Iterable[str]) -> set:
    s = s.lower()
    for x in strip:
        if x:
            s = s.replace(x.lower(), " ")
    s = re.sub(r"\bl-?\d+\b|\bd\d\d\b|\be-\d+\b", " ", s)
    stop = {"the", "and", "for", "with", "that", "this", "from", "are", "was", "not", "but", "has", "have", "its"}
    return {w for w in re.findall(r"[a-z0-9]+", s) if len(w) > 2 and w not in stop}


def _similar(a: set, b: set) -> float:
    return len(a & b) / len(a | b) if a and b else 0.0


# ----------------------------------------------------------------------------- voice, offer, odds and claim guards
# These are tripwires for common phrasings, not proof: a determined writer can always paraphrase past a list.
NUMWORD = (r"(?:one|two|three|four|five|six|seven|eight|nine|ten|eleven|twelve|thirteen|fourteen|fifteen|sixteen|"
           r"seventeen|eighteen|nineteen|twenty|thirty|forty|fifty|sixty|seventy|eighty|ninety|hundred|dozen)")
NUM = r"(?:\d[\d,.]*|" + NUMWORD + r"(?:[- ]" + NUMWORD + r")*)"
CUR_WORD = r"(?:rupees?|dollars?|pounds?|euros?|USD|AUD|GBP|EUR|INR|NPR|NRs|Rs\.?|lakhs?|crores?)"
MONEY_P = (r"(?:[$£€₹]\s?\d[\d,.]*\s*(?:k|m|mn|bn|million|billion|thousand|lakhs?|crores?)?\b|\b(?:USD|GBP|EUR|INR|AUD|"
           r"NPR|NRs|Rs\.?)\s?\d[\d,.]*|\b" + NUM + r"\s*(?:k|m|mn|bn|million|billion|thousand|lakhs?|crores?)\b"
           r"(?:\s+" + CUR_WORD + r")?|\b" + NUM + r"\s+" + CUR_WORD + r"\b)")
PCT_P = r"(?:\b" + NUM + r"\s*(?:%|percent\b|per cent\b))"
FRAC_P = r"(?:\b(?:a|one)\s+(?:tenth|fifth|quarter|third|half)\b|\bhalf\b)"
EQUITY_OBJ = r"(?:of\s+(?:the\s+)?(?:company|business|startup|firm|shares|equity)\b|stake\b|shareholding\b|equity\b|shares\b)"
MONEY_RE = re.compile(MONEY_P + "|" + PCT_P, re.I)
TERMS_RE = re.compile(
    MONEY_P + r"[^.\n]{0,40}?\b(?:for|in exchange for|in return for)\b[^.\n]{0,15}?(?:" + PCT_P + "|" + FRAC_P + ")"
    r"|" + MONEY_P + r"[^.\n]{0,40}?\bagainst\b[^.\n]{0,15}?(?:" + PCT_P + "|" + FRAC_P + r")\s+(?:of\s+(?:the\s+)?)?"
    r"(?:shares|equity|company|business|startup|stake|firm)\b"
    r"|(?:" + PCT_P + "|" + FRAC_P + r")[^.\n]{0,30}?\bfor\b[^.\n]{0,20}?" + MONEY_P
    + r"|\ban offer of\b[^.\n]{0,15}" + MONEY_P, re.I)
TAKE_RE = re.compile(r"\b(?:take|takes|taking|took|acquire|acquires|buy|buys|get|gets|want|wants|receive|ask(?:s|ing)? "
                     r"for|demand(?:s|ing)?|hold out for)\b[^.\n]{0,25}?(?:" + PCT_P + "|" + FRAC_P + r")[^.\n]{0,20}?"
                     + EQUITY_OBJ, re.I)
PRICE_RE = re.compile(r"\b(?:price|valuation|value|worth)\b[^.\n]{0,25}\b(?:the|this) (?:business|company|startup)\b"
                      r"[^.\n]{0,60}" + MONEY_P + r"|\b(?:the|this) (?:business|company|startup)\b[^.\n]{0,30}"
                      r"\b(?:is worth|valued at|valuation of)\b[^.\n]{0,20}" + MONEY_P, re.I)
VALUATION_RE = re.compile(r"\bvaluations?\b|\bvalued at\b", re.I)
# release round: equity and price wording that need no "offer" word. Shares or equity with money in the sentence,
# pre- or post-money with money or a multiple, and pricing the business at a multiple of its revenue or profit.
SHARES_RE = re.compile(r"\b(?:shares|equity|shareholding|share capital)\b", re.I)
PREMONEY_RE = re.compile(r"\b(?:pre|post)[- ]money\b", re.I)
MULTIPLE_P = (r"\b" + NUM + r"\s*(?:x|times)\s+(?:(?:multiple|multiples)\s+(?:on|of)\s+)?(?:(?:its|the|their|annual|yearly|recurring|current|trailing|forward|"
              r"net|gross|this|next|year['’]s)\s+){0,4}(?:revenues?|ARR|MRR|sales|earnings|EBITDA|profits?|turnover|"
              r"GMV|bookings)\b")
MULTIPLE_RE = re.compile(MULTIPLE_P, re.I)
PRICE_VERB_RE = re.compile(r"\b(?:price[sd]?|pricing|valu(?:e|es|ed|ing)|valuation|worth|pay|pays|paid|fetch(?:es|ed)?|"
                           r"multiples?|deal|buy(?:s|ing)?|sell(?:s|ing)?|sale|exit)\b", re.I)
STAKE_PCT_RE = re.compile(r"(?:" + PCT_P + "|" + FRAC_P + r")\s+(?:equity\s+)?(?:stake|shareholding)\b", re.I)
OWNED_SHARES_RE = re.compile(r"\b(?:own|owns|owned|hold|holds|held|issued|register)\b[^.\n]{0,25}\b(?:shares|equity|stake|shareholding)\b",
                             re.I)
VALUER_RE = re.compile(r"\b(?:customers?|users?|buyers?|clients?|members?|cooperatives?|shoppers?|subscribers?)\s+$", re.I)
PRICE_AT_RE = re.compile(r"\b(?:price[sd]?|pricing|valu(?:e|es|ed|ing))\s+(?:the\s+(?:business|company|startup)|"
                         r"(?-i:[A-Z][\w-]+))\s+at\b[^.\n]{0,40}(?:" + MONEY_P + "|" + MULTIPLE_P + ")", re.I)
THIRD_PARTY_RE = re.compile(r"cooperative|customer|supplier|farmer|famil|\bstock\b|inventory|asset|\bplant\b|\bland\b|"
                            r"property|dairy|retailer|distributor|vendor", re.I)
ROYALTY_RE = re.compile(r"\broyalt(?:y|ies)\b(?!-free)", re.I)
_LB = "".join(f"(?<!{w} )" for w in ("distribution", "supply", "retail", "licensing", "partnership", "wholesale",
                                      "channel", "customer", "reseller", "pilot", "framework", "vendor"))
DEAL_RE = re.compile(_LB + r"\bdeals?\b(?! flow)", re.I)
PARTY_TERMS = (r"(?:offers?|offered|stake|equity|valuation|valued at|royalt(?:y|ies)|deal|shareholding|cheque|check|"
               r"ask|put in|puts in|invest(?:s|ed|ing)?|take|takes|buy|acquire|loan|terms|shares|pre-money|"
               r"post-money)")
QUOTE_RE = re.compile(r"[\"“”]|‘[^’\n]{2,}’|(?<![A-Za-z])'[^'\n]{3,}'(?![A-Za-z])")
SENT_RE = re.compile(r"(?<=[.!?])\s+(?=[A-Z0-9*\[(“\"‘'])")
SPEECH_VERBS = (r"(?:said|says|say|told|tells|tell|thinks|thought|believes|believed|loves|loved|hates|hated|feels|"
                r"point(?:s|ed)? out|argue[sd]?|argue|note[sd]?|ask(?:s|ed)?|insist(?:s|ed)?|stress(?:es|ed)?|"
                r"maintain(?:s|ed)?|claim(?:s|ed)?|made clear|makes clear|make clear|warn(?:s|ed)?|remark(?:s|ed)?|"
                r"object(?:s|ed)?|repl(?:y|ies|ied)|retort(?:s|ed)?|explain(?:s|ed)?|recommend(?:s|ed)?)")
FIRST_PERSON_RE = re.compile(
    r"\bI(?:['’]m| am) (?:out|in)\b(?!\s+(?:the|a|an|my|our|charge|touch|favou?r)\b)|\bI(?:['’]ll| will) "
    r"(?:invest|offer|do the deal|give you|take (?:it|the deal))\b|\bI would\b|\bI['’]d (?:invest|offer|do|give|"
    r"want|like|need|be)\b|\bmy offer\b|\bcount me (?:in|out)\b|\bnot for me\b|\bwe(?:['’]re| are) (?:out|in)\b"
    r"(?!\s+(?:the|a|an|this|that)\b)|\byou(?:['’]ve| have) got (?:a|yourself a) deal\b|\btake it or leave it\b", re.I)
IMPERATIVE_RE = re.compile(r"^(?:show me|come back (?:when|once|after|with)|bring me|convince me|prove (?:it|to me)|"
                           r"talk to me|give me)\b|^(?:out|sold|deal)[.!?]?$", re.I)
FIRST_PERSON_CHAT_RE = re.compile(
    r"\bI(?:['’]m| am) (?:out|in)(?:[.!,]|\s*$)|\bI(?:['’]m| am) in for\b|\bI(?:['’]d|['’]ll| would| will) put in\b|"
    r"\bI(?:['’]ll| will) (?:invest|do the deal|back)\b|\bI(?:['’]ll| will) offer\b"
    r"(?=[^.\n]{0,40}(?:\d|%|stake|equity|shares|deal|royalt))|\bI(?:['’]d| would) (?:invest|back|fund|offer\b(?=[^.\n]"
    r"{0,40}(?:\d|%|stake|equity|shares|deal|royalt)))|\bmy offer\b|\bcount me (?:in|out)\b|\bwe(?:['’]re| are) "
    r"out[.!,]|\byou(?:['’]ve| have) got (?:a|yourself a) deal\b|\btake it or leave it\b|\bnot for me\b(?! to\b)", re.I)
FIRST_PERSON_DEBRIEF_RE = re.compile(r"\bI(?:['’]m| am) (?:out|in)[.!,]|\bI(?:['’]ll| will) (?:invest|offer)\b|"
                                     r"\bmy offer\b|\bcount me (?:in|out)\b|\bwe(?:['’]re| are) out\b", re.I)
PROB_EXTRA_RE = re.compile(r"\b(?:chance|likelihood|probability|odds) of (?:success|succeeding|investment|a deal|"
                           r"getting (?:a )?deal|funding|being funded)\b|\blikely to (?:succeed|get funded|get a deal)\b",
                           re.I)
ODDS_RE = re.compile(r"\blong shot\b|\bmore likely than not\b|\b(?:good|fair|poor|slim|long|short) odds\b|\bodds (?:are|of|"
                     r"that|for)\b|\bchances? (?:of|for|that|are|is)\b|\bslim chances?\b|\b(?:shot|chance) at\b|\b"
                     + NUM + r"[- ]in[- ]" + NUM + r"\b", re.I)
SUCCESS_CTX_RE = re.compile(r"succe\w*|\bfund\w*|\bdeal\b|\braise[sd]?\b|\braising\b|\bround\b|invest\w*|\bback(?:ing|ed)\b|"
                            r"\boffer\b|\bwin\w*", re.I)
AGG_RE = re.compile(r"(?<![/\d])\b\d{1,2}\s*/\s*15\b(?!/)|\bout of (?:15|fifteen)\b|\baverage (?:rating|score)\b|"
                    r"\b(?:overall|total|aggregate|composite) score\b|\bscores? (?:of )?(?:\d|" + NUMWORD + r"\b)|"
                    r"\b\d{1,3}\s?% of (?:the )?dimensions\b|\breadiness (?:score|%|percentage)|"
                    r"\b(?:scores?|scored|rates?|rated|rating)\b[^.\n]{0,20}\b(?:\d{1,2}|" + NUMWORD + r")\s+(?:out\s+)?of\s+"
                    r"(?:the\s+)?(?:15|fifteen)\b", re.I)
OF15_DIMS_RE = re.compile(r"\b(?:\d{1,2}|" + NUMWORD + r")\s+(?:out\s+)?of\s+(?:the\s+)?(?:15|fifteen)\s+"
                          r"(?:dimensions|ratings)\b", re.I)
RATING_COUNT_RE = re.compile(r"\b(Strong|Adequate|Weak|Unknown)\s*:?\s*(\d+|" + NUMWORD + r")\b|\b(\d+|" + NUMWORD
                             + r"|no|zero)\s+(Strong|Adequate|Weak|Unknown)\b", re.I)
QUANT_SUMMARY_RE = re.compile(r"\b(?:most|many|majority|nearly all|almost all|all but \w+|several|few)\b[^.\n]{0,30}"
                              r"\b(?:dimensions|ratings)\b|\bbase read is (?:\w+\s+){0,2}(?:positive|negative|favourable|"
                              r"favorable|encouraging|strong|weak|good|poor|solid)\b|\brates? (?:well|highly|strongly|"
                              r"poorly) on\b", re.I)
RATING_WORD_RE = re.compile(r"\b(?:strong|adequate|weak|well|better|positive|favourable|good|highly|poorly)\b", re.I)
INSUFF_RE = re.compile(r"\bInsufficiently evidenced\b", re.I)
TRACTION_NOUNS = (r"(?:customers|clients|users|subscribers|cooperatives|orders|stores|renewals|sign-?ups|downloads|"
                  r"accounts|schools|teachers|learners|students|buyers|households|merchants|sellers|restaurants|clinics|"
                  r"retailers|patients|farmers|units sold|(?:paying|active) members)")
UNCITED_TRACTION_RE = re.compile(
    r"\b" + NUM + r"\s+(?:[\w-]+\s+){0,2}?" + TRACTION_NOUNS + r"\b|\b" + NUM + r"\s+(?:[\w-]+\s+){0,2}?(?:renewed|"
    r"re-?ordered|signed up|subscribed|churned)\b|\b(?:grew|grown|doubled|tripled|quadrupled|increased|rose)\b[^.\n]{0,30}"
    r"(?:\d|\b" + NUMWORD + r"\b)|\b\d+(?:\.\d+)?x (?:growth|increase|year[- ]on[- ]year)\b|\b(?:revenue|sales|MRR|ARR|GMV|"
    r"turnover|bookings)\b[^.\n]{0,30}(?:\d|\b" + NUMWORD + r"\b)", re.I)
LEDGER_GAP_RE = re.compile(r"not (?:yet )?in the ledger|no (?:single )?ledger entry|not (?:yet )?(?:verified|recorded)|unverified|"
                           r"unconfirmed|to be verified|pending|\bunknowns?\b|\bno evidence\b|\bgap\b|\bmissing\b|"
                           r"outside (?:this|the) ledger|not part of the ledger|by (?:its|their|his|her) own account|"
                           r"not (?:yet )?(?:described|stated|given|documented|measured|known|available|tested)|untested",
                           re.I)
SOURCE_CITE_RE = re.compile(r"\[S\d+(?:\s*,\s*S\d+)*\]")


_RV = (r"(?:give|state|say|offer|provide|make|include|report|assign|estimate|put|quote|imply|attach|use|show|"
       r"present|claim|predict|guess|speculate|tell|attribute|calculate|compute)")
NEG_BOUNDARY_RE = re.compile(
    r"\b(?:gives?|states?|says?|offers?|provides?|makes?|includes?|reports?|assigns?|estimates?|puts?|quotes?|implies|"
    r"attaches?|uses?|shows?|presents?|claims?|attributes?)\s+no\b"
    r"|\b(?:does|do|did|will|would|can|should|must|may)\s*(?:not|n['’]t)\s+(?:\w+\s+)?" + _RV + r"\b"
    r"|\bnever\s+(?:\w+\s+)?" + _RV + r"(?:s|es)?\b"
    r"|\bno\s+(?:[\w%$,.-]+\s+){0,10}(?:is|are|was|were)\s+(?:ever\s+)?(?:given|stated|offered|made|provided|included|"
    r"reported|assigned|estimated|quoted|implied|attached|used|shown|presented|predicted|attributed|calculated)\b"
    r"|\b(?:without|refuses? to|declines? to|avoids?)\s+(?:\w+\s+)?(?:giving|stating|saying|offering|predicting|"
    r"implying|quoting|attributing|any|a|an)\b"
    r"|\b(?:nothing|no part|none|no one|no member|no investor|neither)\b(?:\s+\w+){0,4}?\s+(?:here\s+|in this \w+\s+)?"
    r"(?:suggests?|implies|imply|says?|shows?|indicates?|means|states?|is (?:said|shown|described|taken|presented)|"
    r"are (?:said|shown|described|taken|presented))\b"
    r"|\bno (?:panel )?(?:member|investor|one)\b[^.]{0,40}\b(?:interested|interest)\b", re.I)
NO_BEFORE_RE = re.compile(r"\bno\s+(?:(?:overall|total|aggregate|composite|average|per-dimension|single|numeric|"
                          r"readiness)\s+)?$", re.I)
CLAUSE_SPLIT_RE = re.compile(r";|,\s*(?:and|but|yet|so)\b|\bbut\b|\bhowever\b|\bwhereas\b|\bwhile\b", re.I)


def _clauses(units: List[str]) -> List[Tuple[str, bool]]:
    """(clause, states-the-boundary) for each clause; a clause that negates a reporting verb ("gives no overall
    score", "does not state odds", "never states what an investor would offer") describes what the simulation
    does not do."""
    out = []
    for u in units:
        for c in CLAUSE_SPLIT_RE.split(u):
            if c.strip():
                out.append((c, bool(NEG_BOUNDARY_RE.search(c))))
    return out


def voice_res(profiles: Dict[str, "Profile"], ids: List[str]) -> Dict[str, Any]:
    """Compiled patterns for the guards that depend on investor names (built once per document or session)."""
    full, surname = _name_res(profiles, ids)
    names = [x for x in ([full.pattern] if full else []) + ([surname.pattern] if surname else [])]
    subj = r"(?:" + "|".join(names + [r"\bthe panel\b", r"\bthe sharks\b", r"\bthe dragons\b", r"\bthis investor\b"]) + ")"
    subj2 = (r"(?:" + subj + r"|\bpanel members?\b|\b(?:each|every|a|one|another) (?:panel )?member\b|\bthe members\b|"
             r"\b(?:each|every) investor\b)")
    isubj = (r"(?:" + subj + r"|\b(?:an?|the|each|every|this|that|one|other|another)\s+(?:panel\s+)?(?:member|investor|"
             r"panellist|shark|dragon)\b|\b(?:panel\s+)?(?:members|investors|panellists|sharks|dragons)\b|"
             r"\b\d+\s*(?:(?:out\s+)?of|/)\s*\d+\b|\b(?:one|two|three|four|five|six|seven|all|both|most|none|some|"
             r"several|neither|either)(?:\s+of)?\s+(?:the\s+)?(?:\d+|three|four|five|six|seven|members|investors|"
             r"them|panel)\b|(?<!\bno )\b(?:one|two|three|four|five|six|seven)(?=\s+(?:is|are|was|were|remains?|stays?)\s))")
    aux = (r"(?:is|are|was|were|would|will|could|might|may|should|be|been|being|seems?|seemed|appears?|appeared|remains?|"
           r"remained|stays?|stayed|becomes?|became|gets?|got|feels?|felt|very|really|quite|genuinely|clearly|keenly|"
           r"likely|probably|definitely|certainly|still|also|now|not|more|most|less|already|to|only|partly|then|said|"
           r"reported|thought|believed|known|described|shown|understood|rumoured|rumored)")
    poss = r"(?:" + "|".join(names) + r")['’]s" if names else r"(?!x)x"
    return {
        "full": full, "surname": surname,
        "interest": re.compile(
            subj + r"(?:['’]s)?\s+(?:" + aux + r"\s+){0,4}(?:invest|back|fund|make an offer)\b|" + subj +
            r"\s+(?:has|have|had)\s+(?:already\s+)?(?:seen|reviewed|been shown|been contacted|heard of|looked at)\b|"
            + isubj + r"(?:['’]s)?\s+(?:" + aux + r"\s+){1,4}interested\b|" + isubj +
            r"\s+(?:(?:has|have|had|shows?|showed|shown|expressed|expresses|signals?|signall?ed|registers?|registered|"
            r"declares?|declared)\s+){1,2}(?:(?:an?|some|strong|real|clear|keen|no|little|its|their|his|her)\s+)?"
            r"interest\b|" + subj2 + r"\s+(?:" + aux + r"\s+){0,4}(?:keen|excited|enthusiastic|eager|tempted|drawn|"
            r"attracted|impressed|sold on|won over|a fan|smitten|delighted|thrilled|warm(?:s|ed)? to)\b|" + subj2 +
            r"\s+(?:" + aux + r"\s+){0,3}(?:likes?|liked|loves?|loved|want(?:s|ed)? (?:a piece|to be involved|in|a stake|"
            r"to invest|to back|to partner)|leave the door open|champion|chase|fight for)\b|\b(?:a\s+)?(?:natural|good|"
            r"great|strong|perfect|obvious|clear) fit for (?:" + subj + r"|her|his|their)(?:['’]s)? (?:portfolio|fund|"
            r"investments?)\b", re.I),
        "speech": re.compile(subj + r"(?:['’]s)?\s+(?:(?:would|will|might|could|probably|also|once|has|have|had|then)\s+)"
                             r"{0,2}" + SPEECH_VERBS + r"\b|\baccording to " + subj + r"|\bin " + poss + r" (?:own )?words\b|"
                             + poss + r" (?:reaction|response|verdict|answer|feeling|opinion|retort)\b|" + poss +
                             r" view (?:would be|will be|is that)\b", re.I),
        "her_words": re.compile(r"\bin (?:his|her|their) (?:own )?words\b", re.I),
        "script": re.compile(r"^\s*(?:[-*>]\s*)*\**\s*" + subj + r"\s*\**\s*:", re.I),
        "party": re.compile(r"(?:" + subj2 + r"|\b(?:an?|the|this) investor\b)[^.\n]{0,60}\b" + PARTY_TERMS + r"\b", re.I),
    }


def _o5_hit(u: str, R: Dict[str, Any]) -> Optional[str]:
    """Offer-shaped terms in one sentence: money for a share, an investor or the panel with offer terms and money,
    taking a share of the company, a price for the business, a valuation, royalty or deal with money."""
    money = MONEY_RE.search(u)
    pa = PRICE_AT_RE.search(u)
    if pa and VALUER_RE.search(u[:pa.start()]):
        pa = None                                   # "customers value Acme at $20 a month" is willingness to pay
    m = TERMS_RE.search(u) or TAKE_RE.search(u) or PRICE_RE.search(u) or pa
    if m:
        return m.group(0)
    mult = MULTIPLE_RE.search(u)
    if mult and PRICE_VERB_RE.search(u):
        return mult.group(0)
    pm = PREMONEY_RE.search(u)
    if pm and (money or mult):
        return pm.group(0)
    if not money:
        return None
    st_ = STAKE_PCT_RE.search(u)
    if st_ and money and not THIRD_PARTY_RE.search(u) and not OWNED_SHARES_RE.search(u):
        return st_.group(0)
    sh = SHARES_RE.search(u)
    if sh and not THIRD_PARTY_RE.search(u) and not OWNED_SHARES_RE.search(u) and any(
            abs(mm.start() - sh.start()) <= 40 for mm in MONEY_RE.finditer(u)):
        return sh.group(0)
    if R["party"].search(u):
        return R["party"].search(u).group(0)
    v = VALUATION_RE.search(u)
    if v and not THIRD_PARTY_RE.search(u):
        return v.group(0)
    spans = [mm.span() for mm in MONEY_RE.finditer(u)]
    for rx in (ROYALTY_RE, DEAL_RE):
        for x in rx.finditer(u):
            if any(max(0, a - x.end(), x.start() - b) <= 30 for a, b in spans):
                return x.group(0)
    return None


def line_issues(s: str, R: Dict[str, Any], kind: str, in_scn: bool = False) -> List[Tuple[str, str, str]]:
    """Voice, offer, odds, rating-summary and uncited-claim guards for one line: (level, rule, message)."""
    out: List[Tuple[str, str, str]] = []
    plain = _strip_code(s)
    heading = s.startswith("#")
    if R["script"].search(plain) and not heading:
        out.append(("error", "O3", f"script format ('<Name>:') is not allowed: '{s[:80]}'"))
    # a debrief or a chat reply speaks as the assistant ("I would suggest"); only investor-voice phrases count
    fm = {"debrief": FIRST_PERSON_DEBRIEF_RE, "chat": FIRST_PERSON_CHAT_RE}.get(kind, FIRST_PERSON_RE).search(plain)
    if fm:
        out.append(("error", "O3", f"first-person investor phrase '{fm.group(0)}'"))
    units = _units(plain)
    for u in units:
        uu = u.strip().strip("*_ ")
        # a chat reply may ask the founder for something ("give me the amount"); investor-voice commands still count
        if kind != "debrief" and not heading and IMPERATIVE_RE.search(uu) and not (
                kind == "chat" and re.match(r"(?:give|talk to) me\b", uu, re.I)):
            out.append(("error", "O3", f"direct address in an investor's voice: '{uu[:80]}'"))
        nm = _has_name(u, R["full"], R["surname"])
        if nm and QUOTE_RE.search(u):
            out.append(("error", "O2", f"quotation marks in the same sentence as '{nm}': '{u.strip()[:80]}'"))
    clauses = _clauses(units)
    live = [c for c, neg in clauses if not neg]          # clauses that do not merely state the boundary
    sm = next((m for m in (R["speech"].search(c) or (kind in ("evaluation", "panel", "verdict", "report")
                                                      and R["her_words"].search(c)) for c in live) if m), None)
    if sm:
        out.append(("error", "O2", f"words or a reaction attributed to an investor ('{sm.group(0)}')"))
    pm = next((m for m in (PROB_RE.search(c) or PROB_EXTRA_RE.search(c) for c in live) if m), None)
    if not pm:
        for c in live:
            om = ODDS_RE.search(c)
            if om and SUCCESS_CTX_RE.search(c):
                pm = om
                break
    if pm:
        out.append(("error", "O7", f"probability or odds of success ('{pm.group(0)}')"))
    im = next((m for m in (R["interest"].search(c) for c in live) if m), None)
    if im:
        out.append(("error", "O7", f"implies an investor's interest or decision ('{im.group(0)}')"))
    om = OLD_CONDITIONAL_RE.search(plain)
    if om:
        out.append(("error", "O7", f"'{om.group(0)}' is the retired stance label and implies interest: write "
                                   f"'{STANCES['conditional']}' (or 'Conditional on <the evidence>')"))
    if not in_scn:
        for u in units:
            if any(neg for c, neg in _clauses([u])) and not any(_o5_hit(c, R) for c, neg in _clauses([u]) if not neg):
                continue
            hit = _o5_hit(u, R)
            if hit:
                out.append(("error", "O5", f"offer-shaped terms ('{hit.strip()[:60]}') outside a [!SCENARIO] callout: "
                                           "rephrase, or, if the user asked for terms, write a hypothetical scenario "
                                           "by investor class"))
                break
    # a score named only to deny it ("there is no overall score", "no per-dimension score") asserts no score;
    # only B4 reads "no" this way: "no chance of a deal" is still an odds statement for O7
    am = next((m for c in live for m in AGG_RE.finditer(c) if not NO_BEFORE_RE.search(c[:m.start()])), None)
    if not am:
        for u in units:       # "N of 15 dimensions" is fine only as an Unknown count
            om15 = OF15_DIMS_RE.search(u)
            if om15 and "unknown" not in u.lower():
                if re.search(r"\b(?:strong|adequate|weak)\b", u, re.I):
                    out.append(("error", "B5", f"a rating summary must include the Unknown count ('{u.strip()[:60]}')"))
                else:
                    am = om15
                break
    if am:
        out.append(("error", "B4", f"numeric aggregate of ratings ('{am.group(0)}'); ratings are never added up"))
    for u in units:
        counted = {(rm.group(1) or rm.group(4)).lower() for rm in RATING_COUNT_RE.finditer(u)}
        if len(counted) >= 2 and "unknown" not in counted:
            out.append(("error", "B5", "a rating summary must include the Unknown count"))
            break
        if not counted and QUANT_SUMMARY_RE.search(u) and RATING_WORD_RE.search(u) and "unknown" not in u.lower():
            out.append(("error", "B5", f"a rating summary in words hides the counts: give each rating's count, "
                                       f"including Unknown ('{u.strip()[:60]}')"))
            break
    if INSUFF_RE.search(plain):
        out.append(("warning", "B5", "write 'Unknown' (not enough evidence to judge), not 'Insufficiently evidenced'"))
    # uncited traction, revenue and growth figures (O8), in every simulation document
    if not heading and not in_scn:
        row = plain.startswith("|")
        for u in ([plain] if row else units):
            if u.rstrip().endswith("?") or re.match(r"^\W*A question raised through", u):
                continue
            if CITE_RE.search(u) or SOURCE_CITE_RE.search(u) or ID_RE.search(u):
                continue
            neutral = SHORT_ID_RE.sub(" ", _claims_text(u))
            neutral = re.sub(r"\b(?:19|20)\d\d(?:-\d\d(?:-\d\d)?)?\b", " ", neutral)
            tm = UNCITED_TRACTION_RE.search(neutral)
            if tm and not LEDGER_GAP_RE.search(u) and not gtm.QUALIFIER_RE.search(u):
                out.append(("error", "O8", f"traction, revenue or growth figure without a ledger citation in the same "
                                           f"sentence or row ('{tm.group(0).strip()}'): cite the [E-…] entry or say it "
                                           "is not in the ledger"))
                break
    return out


# ----------------------------------------------------------------------------- chat replies (release round)
# guards.md "Chat replies": a reply needs the simulation label only when it gives an investor-specific reading,
# a sentence that names an investor together with a stance, a lens or a point (a dimension, a concern, a gap)
READING_RE = re.compile(r"\bL\d\b|\bD(?:0[1-9]|1[0-5])\b|\blens(?:es)?\b|\bstance\b|\bpersuaded\b|"
                        r"\bconditional on\b|\bcannot form a view\b|\bconcerns?\b|\bpoints?\b|\b(?:documented|known) "
                        r"gaps?\b|\boutside (?:documented|(?:his|her|their) documented) expertise\b|\bdeciding\b|"
                        r"\bemphasis\b|\bprimary\b|\bwould (?:raise|ask|weigh|flag|question|hold|read)\b", re.I)
BACK_REF_RE = re.compile(r"\b(?:his|her|their|this (?:member|investor)['’]s?|the investor['’]s?)\b", re.I)


def check_chat(text: str, ledger: Optional[Ledger] = None, profiles: Optional[Dict[str, Profile]] = None,
               where: str = "reply") -> List[Dict]:
    """Guards for a chat reply (``check --chat``): every voice, offer, odds, rating-summary and figure guard of a
    document, without the document rules (front matter, sections, closing line, base read). The simulation label
    (O1) is required only when a sentence gives an investor-specific reading, and must then name every investor
    such sentences name."""
    profiles = profiles or {}
    doc = _Doc(text)
    iss: List[Dict] = []
    R = voice_res(profiles, [])
    named: Dict[str, Profile] = {}
    by_name = {nm.lower(): p for p in profiles.values() for nm in p.names}
    mentioned: Dict[str, Profile] = {}            # every investor the reply names, the label line included
    back_ref = False                              # a reading that points back by pronoun ("his lenses")
    for n, ln in doc.content:
        s = ln.strip()
        if not s:
            continue
        for level, rule, msg in line_issues(s, R, "chat", n in doc.scenario):
            iss.append(_issue(level, rule, f"{where}:{n}: {msg}", n))
        if R["full"] is None:
            continue
        for m in R["full"].finditer(_strip_code(s)):
            p = by_name.get(m.group(0).lower())
            if p:
                mentioned[p.id] = p
        if s.lstrip("> ").startswith("[!SIMULATION]"):
            continue
        for u in ([s] if s.startswith("|") else _units(_strip_code(s))):
            if not READING_RE.search(u):
                continue
            hits = {m.group(0).lower() for m in R["full"].finditer(u)}
            for h in hits:
                p = by_name.get(h)
                if p:
                    named[p.id] = p
            if not hits and BACK_REF_RE.search(u):
                back_ref = True
    # the document pass for uncited figures, limited in chat to lines with an amount or a percentage: a reply has
    # no sections to exempt panel counts or planned evidence ("eight weeks of logged hours"), but uncited money
    # ("USD 38,000 in cash") is the fabrication risk
    lines = dict(doc.content)
    iss += [i for i in _structural_passes(doc, R, "chat", where, None) if i["rule"] == "P-W" or (
        i["rule"] == "O8" and MONEY_RE.search(SHORT_ID_RE.sub(" ", lines.get(i.get("line"), ""))))]
    if back_ref and len(mentioned) == 1:
        named.update(mentioned)                   # one investor named, read through "his/her/their" elsewhere
    if named:
        n0, first = doc.first_content()
        if not first.startswith("[!SIMULATION]") or SIM_LABEL.lower() not in first.lower():
            iss.append(_issue("error", "O1", f"{where}:{n0}: the reply gives an investor-specific reading of "
                                             f"{', '.join(p.name for p in named.values())}, so its first line is the "
                                             "'> [!SIMULATION] Analytical simulation. …' label", n0))
        else:
            for p in named.values():
                if not any(nm.lower() in first.lower() for nm in p.names):
                    iss.append(_issue("error", "O1", f"{where}:{n0}: the simulation label does not name {p.name}", n0))
    for blk in doc.scenarios:
        body = "\n".join(t for _, t in blk)
        if "hypothetical scenario" not in body.lower():
            iss.append(_issue("error", "O6", f"{where}:{blk[0][0]}: a [!SCENARIO] callout must say 'Hypothetical "
                                             "scenario'", blk[0][0]))
        nm = _has_name(body, R["full"], R["surname"])
        if nm:
            iss.append(_issue("error", "O6", f"{where}:{blk[0][0]}: a [!SCENARIO] callout must not name an investor "
                                             f"('{nm}')", blk[0][0]))
    gtm_lines = {i.get("line") for i in iss if i["rule"] == "O8"}
    for i in gtm.check_claims(_claims_text(text), ledger, where):
        if i.get("line") in gtm_lines and i.get("kind") in ("traction", "market-size"):
            continue
        iss.append({"level": i["level"], "rule": "O8", "line": i.get("line"), "message": i["message"]})
    return iss


# founder answers are founder-provided ('reported'); a debrief or session claim that calls one verified is I3
# "verified evidence", "verified entries", "verified or founder-against-interest" name an evidence class, not a fact
VERIFIED_WORD_RE = re.compile(r"(?<![\w-])verified\b(?!\s+(?:evidence|entr(?:y|ies)|(?:ledger\s+)?status|or\s+"
                              r"founder))|\bverifie[sd] (?:by|against|through|with)\b", re.I)
VERIFIED_NEG_RE = re.compile(r"\b(?:not|never|no|nothing|none|neither|nor|without|un|yet to be|to be|cannot be|"
                             r"can't be|isn't|aren't|wasn't|weren't|until)\b[^.;\n]{0,30}$", re.I)


def _verified_spans(text: str) -> List[int]:
    """Positions where the text calls something verified other than in a denial ("not verified", "unverified",
    "until verified")."""
    t = re.sub(r"\blast_verified\b|\bunverified\b", lambda m: " " * len(m.group(0)), text, flags=re.I)
    return [m.start() for m in VERIFIED_WORD_RE.finditer(t) if not VERIFIED_NEG_RE.search(t[:m.start()])]


def _verified_hits(text: str) -> bool:
    return bool(_verified_spans(text))


CITE_GROUP_RE = re.compile(r"\[?\bE-\d{3,}\b(?:\s*,\s*E-\d{3,}\b)*\]?")


def _verified_claims(content: List[Tuple[int, str]], ledger: Optional["Ledger"]) -> List[Tuple[int, str]]:
    """Debrief lines that describe a figure or answer as verified. Each 'verified' must belong to a citation
    of `verified` ledger entries (earlier evidence, not the founder's answer): the first citation after it in
    the sentence or row, or else the last one before it. Without a ledger a cited 'verified' is not judged."""
    out = []
    for n, ln in content:
        s = _strip_code(ln.strip())
        if not s or s.startswith("#") or s.lstrip("> ").startswith("[!SIMULATION]"):
            continue
        for u in ([s] if s.startswith("|") else _units(s)):
            groups = [(m.start(), ID_RE.findall(m.group(0))) for m in CITE_GROUP_RE.finditer(u)]
            bad = False
            for p in _verified_spans(u):
                after = [g for pos, g in groups if pos > p]
                before = [g for pos, g in groups if pos < p]
                grp = after[0] if after else (before[-1] if before else None)
                if grp is None:
                    bad = True
                elif ledger is not None and not all(ledger.get(x) and ledger.get(x).status == "verified"
                                                    for x in grp):
                    bad = True
                if bad:
                    break
            if bad:
                out.append((n, "a founder answer is founder-provided ('reported') and never verified: write "
                               "founder-provided, or cite the verified ledger entry it refers to "
                               f"('{u.strip()[:70]}')"))
                break
    return out


# ----------------------------------------------------------------------------- structural passes (final round)
FULL_KINDS = ("evaluation", "panel", "verdict", "report")
QTY_WORDS = (r"(?:hundreds?|thousands?|millions?|billions?|lakhs?|crores?|dozens?|half|halved|doubled|tripled|"
             r"quadrupled|tenfold|twofold|threefold|percent|per cent)")
SMALL_NUM = r"(?:one|two|three|four|five|six|seven|eight|nine|ten|eleven|twelve|twenty|thirty|forty|fifty|sixty|" \
            r"seventy|eighty|ninety)"
BUSINESS_NOUNS = (r"(?:customers?|clients?|users?|subscribers?|cooperatives?|orders?|stores?|renewals?|sign-?ups?|"
                  r"downloads?|accounts?|schools?|teachers?|learners?|students?|buyers?|households?|merchants?|sellers?|"
                  r"restaurants?|clinics?|retailers?|patients?|farmers?|agents?|employees?|staff|units?|"
                  r"pilots?|courses?|sales|deals?|contracts?|invoices?|payments?|months?|weeks?|days?|hours?|years? of|"
                  r"locations?|branches?|markets?|countries|regions?|partners?|distributors?|suppliers?|products?|"
                  r"cohorts?|transactions?|slips?)")
# numbers that are not business figures: ids, dates, ratings counts, panel and question bookkeeping
NONFIG_RES = (
    re.compile(r"\b(?:E-\d{3,}|[DLSJQXACRBMH]\d{1,3}[a-z]?|L-\d+)\b"),
    re.compile(r"\b(?:19|20)\d\d(?:[-/]\d\d(?:[-/]\d\d)?)?(?:/\d\d)?\b"),
    re.compile(r"\b(?:January|February|March|April|May|June|July|August|September|October|November|December|Jan|Feb|"
               r"Mar|Apr|Jun|Jul|Aug|Sep|Sept|Oct|Nov|Dec)\.?\s+\d{1,2}\b|\b\d{1,2}\s+(?:January|February|March|April|"
               r"May|June|July|August|September|October|November|December)\b", re.I),
    re.compile(r"\b(?:season|seasons|series|episode|episodes|tier|tiers|section|sections|step|steps|stage|stages|"
               r"turn|turns|question|questions|row|rows|version|page|pages|round|wave|phase|level|chapter|part|"
               r"sources?|lenses|lens|criteria|criterion|follow-ups?)\s*:?\s*\d+(?:\s*[–-]\s*\d+)?\b", re.I),
    re.compile(r"\b\d+(?:\s*[–-]\s*\d+)?\s+(?:of\s+(?:the\s+)?\d+\s+)?(?:\w+[- ])?(?:dimensions?|lenses|lens|members?|"
               r"investors?|questions?|rows?|sections?|judgements?|criteria|exchanges?|points?|stances?|turns?|"
               r"follow-ups?|sources?|profiles?|seasons?|series|tiers?|steps?|stages?|panellists?|ratings?)\b", re.I),
    re.compile(r"\b(?:Strong|Adequate|Weak|Unknown)\s*:?\s*\d+\b|\b\d+\s+(?:Strong|Adequate|Weak|Unknown)\b", re.I),
    re.compile(r"\b(?:B2[BCG]|D2C|C2C|P2P|[2-5]G|24/7)\b", re.I),
    re.compile(r"\b(?:topic|item|entry|entries|criterion)\s+\d+\b|\b\d+\s+(?:ledger\s+)?(?:entries|entry)\b", re.I),
    re.compile(r"\bQ\d+\s+of\s+\d+\b|\b\d+\s+of\s+\d+\b(?=\s*(?:[·|)]|$))|\b\d{1,2}\s+(?:out\s+)?of\s+(?:the\s+)?15\b",
               re.I),
)
CALC_LABEL_RE = re.compile(r"calculat\w*|computed|derived from|\bworked\b|arithmetic|shown calculation|[=×]", re.I)
# references that carry their own evidence: profile sources (S3) and trace rows (A2, C1), which cite the ledger
REF_CITE_RE = re.compile(r"\bS\d+\b|\((?:[ACBX]\d+[a-z]?)(?:\s*(?:,|and)\s*[ACBX]\d+[a-z]?)*\)")
# forward-looking or bookkeeping sections: planned evidence, conditions, experiments and plans are not claims
NONCLAIM_SECTION_RE = re.compile(r"recommend|evidence (?:that would be )?demanded|action plan|experiment|conditions that "
                                 r"would|what would make|question|upgrade|practice|sources|divergence map|competing "
                                 r"priorities|panel and method|roster|how the founder|method|next steps|30|60|90",
                                 re.I)
NONCLAIM_LINE_RE = re.compile(r"^\W*(?:Profile confidence|Profile sources|Programmes?|Lenses applied|Profile:|Sources?:|"
                              r"[RMQ]\d+[a-z]?\b|\d+\s*(?:[–-]\s*\d+\s*)?(?:days?|weeks?|months?)\W*$)", re.I)
CONDITIONAL_RE = re.compile(r"\b(?:if|unless|would|could|should|needs?|need to|target|threshold|at least|upgrade|"
                            r"downgrade|test|experiment|plan(?:s|ned)?|whether|until|expected|scenario|hypothes\w*|"
                            r"assum\w*|estimat\w*|goal|aim|budget|minimum|maximum|by \w+ \d|within)\b", re.I)
EVENT_RE = re.compile(r"(?:^\W*|\b(?:[A-Z][\w-]+|[Ii]t|[Tt]he (?:company|startup|business|founders?|team)|[Ww]e)\s+)"
                      r"(?:(?:has|have|had|now|already|recently|just|also)\s+)*(?:signed|onboarded|won|landed|secured|"
                      r"serves|served|supplies|sells to|partnered with|launched (?:in|with)|went live (?:in|with)|"
                      r"is used by)\b(?! as\b)")
STANCE_WORDS = (r"(?:persuaded(?! on current evidence)|convinced|unconvinced|unpersuaded|impressed|won over|sold on|"
                r"satisfied|reassured|comfortable with|positive about|negative about|enthusiastic|sceptical|skeptical|"
                r"leaning|leans|lean towards|inclined|favourably disposed|onside|on side)")
READINESS_RE = re.compile(r"\b(?:investment[- ]ready|ready for investment|ready to raise|investable|"
                          r"(?:a\s+)?(?:good|sound|viable) business)\b", re.I)
PRAISE_RE = re.compile(r"\b(?:outstanding|impressive|excellent|exceptional|a clear winner|clear winner|a bright future|"
                       r"world[- ]class|compelling|remarkable|stellar|brilliant|superb|extraordinary)\b", re.I)


def _figure_units(doc: "_Doc", R) -> List[Tuple[int, str, str]]:
    """(line, unit, whole row or sentence context) for every prose sentence and table cell outside headings,
    scenarios, the label callout and judgement or positions bookkeeping."""
    out = []
    tables = doc.tables()
    for n, ln in doc.content:
        s = ln.strip()
        if not s or s.startswith("#") or n in doc.scenario or re.match(r"^>\s*\[!SIMULATION\]", s):
            continue
        if s.startswith("|"):
            if re.match(r"^\|?\s*:?-{2,}", s):
                continue
            if any(t["line"] == n for t in tables):       # header row
                continue
            for c in _cells(s):
                out.append((n, c, s))
        else:
            for u in _units(_strip_code(s)):
                out.append((n, u, u))
    return out


def _is_figure(u: str) -> Optional[str]:
    t = _claims_text(u)
    for rx in NONFIG_RES:
        t = rx.sub(" ", t)
    m = (re.search(r"[$£€₹]\s?\d|\d", t) or re.search(r"\b" + QTY_WORDS + r"\b", t, re.I)
         or re.search(r"\b" + SMALL_NUM + r"(?:[- ]" + SMALL_NUM + r")?\s+(?:[\w-]+\s+){0,2}?" + BUSINESS_NOUNS + r"\b", t, re.I)
         or re.search(r"\b\d+(?:\.\d+)?x\b", t))
    return m.group(0) if m else None


def _structural_passes(doc: "_Doc", R: Dict[str, Any], kind: str, where: str, base: Optional[Dict]) -> List[Dict]:
    """O8 uncited figures and business events, T8 stance and readiness stated in prose, P-W praise (warning)."""
    iss: List[Dict] = []

    def add(level, rule, msg, n):
        iss.append(_issue(level, rule, f"{where}:{n}: {msg}", n))

    # sections whose content is the controlled stance or judgement vocabulary
    skip = []
    for name in ("stance", "initial positions", "final positions", "consensus"):
        r = doc.section(name)
        if r:
            skip.append(r)
    jtable_rows = {n for t in doc.tables() if _col(t, "judgement", "judgment") is not None for n, _ in t["rows"]}
    nonclaim = [(n, end) for i, (n, lvl, t) in enumerate(doc.headings) if NONCLAIM_SECTION_RE.search(t)
                for end in [next((m for m, l2, _ in doc.headings[i + 1:] if l2 <= lvl), 10 ** 9)]]
    subj = (r"(?:" + "|".join(x for x in ([R["full"].pattern] if R["full"] else []) +
                              ([R["surname"].pattern] if R["surname"] else []) +
                              [r"\b(?:the|our|this) panel\b", r"\bthe sharks\b", r"\bthe dragons\b",
                               r"\bthis investor\b", r"\bthe lenses\b", r"\b(?:each|every|a|one|no) (?:panel )?member\b",
                               r"\b(?:panel )?members\b", r"\bthe investors?\b"]) + ")")
    stance_re = re.compile(subj + r"(?:['’]s)?\s+(?:lenses\s+)?(?:(?:is|are|was|were|would|will|could|might|may|be|been|"
                                  r"seems?|appears?|remains?|feels?|very|really|quite|clearly|still|also|now|not|more|"
                                  r"most|less|already|broadly|largely|firmly)\s+){0,4}" + STANCE_WORDS + r"\b"
                           r"|\bleaning towards? (?:a )?(?:yes|no)\b", re.I)
    table_ans: Dict[str, Any] = {"J2": []}
    for t in doc.tables():
        cj, ca = _col(t, "judgement", "judgment"), _col(t, "answer")
        if cj is None or ca is None:
            continue
        for n, row in t["rows"]:
            jc = _clean_cell(_cell(row, cj))
            m = re.match(r"^(J[1-5])\b", jc)
            if m:
                a = _clean_cell(_cell(row, ca)).lower().replace(" ", "-")
                if m.group(1) == "J2":
                    table_ans["J2"].append((_j2_class(jc), a))
                else:
                    table_ans[m.group(1)] = a
    if len(table_ans) == 1 and not table_ans["J2"] and isinstance((base or {}).get("judgements"), dict):
        bj = base["judgements"]
        for k in ("J1", "J3"):
            if isinstance(bj.get(k), dict):
                table_ans[k] = _text(bj[k].get("answer")).lower()
        for it in _list(bj.get("J2")):
            if isinstance(it, dict):
                table_ans["J2"].append((_text(it.get("class")).lower(), _text(it.get("answer")).lower()))
    have_j = len(table_ans) > 1 or bool(table_ans["J2"])
    for n, u, ctx in _figure_units(doc, R):
        in_skip = any(a < n < b for a, b in skip) or n in jtable_rows
        cited = bool(CITE_RE.search(ctx) or ID_RE.search(ctx) or SOURCE_CITE_RE.search(ctx) or REF_CITE_RE.search(ctx)
                     or re.search(r"\bgap\b", ctx, re.I) or CALC_LABEL_RE.search(ctx))
        planned = any(a < n < b for a, b in nonclaim) or bool(NONCLAIM_LINE_RE.search(u)) \
            or bool(NONCLAIM_LINE_RE.search(ctx.lstrip("| ")))
        negated_boundary = bool(NEG_BOUNDARY_RE.search(u))
        question = u.rstrip().endswith("?") or bool(re.match(r"^\W*A question raised through", u))
        # O8: every quantity about the business carries a citation, the word gap or a calculation label
        if not cited and not question and not in_skip and not planned and not negated_boundary \
                and not CONDITIONAL_RE.search(u) \
                and not LEDGER_GAP_RE.search(u):
            fig = _is_figure(u)
            if fig:
                add("error", "O8", f"figure without a ledger citation, 'gap' or a calculation label in the same "
                                   f"sentence, cell or row ('{fig.strip()}'): '{u.strip()[:70]}'", n)
            elif EVENT_RE.search(u) and not negated_boundary:
                add("error", "O8", f"business event without a ledger citation ('{EVENT_RE.search(u).group(0)}'): "
                                   f"'{u.strip()[:70]}'", n)
        if in_skip or negated_boundary:
            continue
        # T8: stance or readiness in prose
        sm = stance_re.search(u)
        if sm:
            add("error", "T8", f"stance stated in prose ('{sm.group(0)}'): state stances only in the Stance section "
                               "and the positions tables, with the stance labels", n)
        rm = READINESS_RE.search(u)
        if rm and not re.search(r"\bJ[1-5]\b", u):
            neg = bool(re.search(r"\b(?:not|never|no longer|isn['’]t|nor)\b(?:\s+\w+){0,3}\s*$", u[:rm.start()], re.I))
            word = rm.group(0).lower()
            jid = "J3" if "ready" in word else "J2" if "investable" in word else "J1"
            claim = "no" if neg else "yes"
            if jid == "J2":
                got = [a for _, a in table_ans["J2"]]
                agree = (claim == "yes" and "yes" in got) or (claim == "no" and got and "yes" not in got)
            else:
                agree = table_ans.get(jid) == claim
            if not have_j:
                add("error", "T8", f"'{rm.group(0)}' is a judgement ({jid} {JUDGEMENTS[jid]}) but no judgement table or "
                                   "base-read judgements are available to support it", n)
            elif not agree:
                add("error", "T8", f"'{rm.group(0)}' contradicts {jid} {JUDGEMENTS[jid]} "
                                   f"({', '.join(_ans_name(a) for _, a in table_ans['J2']) if jid == 'J2' else _ans_name(table_ans.get(jid) or 'missing')})", n)
        # praise without evidence (warning)
        pm = PRAISE_RE.search(u)
        if pm and not cited and not re.search(r"\b(?:not|no|never|more|would|could|less)\s+(?:\w+\s+)?"
                                              + re.escape(pm.group(0)), u, re.I):
            add("warning", "P-W", f"unsupported praise ('{pm.group(0)}') with no citation or gap in the sentence", n)
    return iss


def check_document(text: str, ledger: Optional[Ledger] = None, profiles: Optional[Dict[str, Profile]] = None,
                   against: Optional[List[Tuple[str, str]]] = None, where: str = "document",
                   base: Optional[Dict] = None, allow_no_base: bool = False,
                   allow_no_ledger: bool = False) -> List[Dict]:
    """Output guards O1–O8, O10, B4–B6, T1–T4, N2–N4 for a shark-tank document (see "Document conventions").

    For kinds evaluation, panel, verdict and report a missing base read or ledger is an error, so a weakened check
    never passes quietly; ``allow_no_base`` / ``allow_no_ledger`` (CLI ``--no-base-read`` / ``--no-ledger``) turn
    it into a counted warning that names the guards not run."""
    profiles = profiles or {}
    doc = _Doc(text)
    iss: List[Dict] = []

    def err(rule, msg, line=None):
        iss.append(_issue("error", rule, f"{where}:{line}: {msg}" if line else f"{where}: {msg}", line))

    def warn(rule, msg, line=None):
        iss.append(_issue("warning", rule, f"{where}:{line}: {msg}" if line else f"{where}: {msg}", line))

    meta = doc.meta
    if doc.meta_error:
        err("O1", f"front matter is not valid YAML ({doc.meta_error})")
    if meta.get("simulation") is not True:
        err("O1", "front matter must say 'simulation: true'")
    if meta.get("doc_type") != "shark-tank":
        warn("O1", "front matter doc_type should be 'shark-tank'")
    kind = _text(meta.get("kind")).lower()
    if kind not in DOC_KINDS:
        err("O1", f"front matter kind '{kind}' not in {DOC_KINDS}")
    full_kind = kind in FULL_KINDS
    if base is None and full_kind:
        (warn if allow_no_base else err)(
            "T6", "no base read: the stance (T6), concern-row (T7), judgement (B6) and prose-readiness (T8) gates "
                  "were not run; pass --base-read, keep base-read.yaml beside the document, or pass --no-base-read to "
                  "accept a weaker check")
    ids = [str(i) for i in _list(meta.get("investors"))]
    arch = [_text(a.get("name") or a.get("id") or a.get("label")) if isinstance(a, dict) else _text(a)
            for a in _list(meta.get("archetypes"))]

    # O10 investors exist and validate; panel size (archetypes are not profiles and are not panel members)
    for i in ids:
        p = profiles.get(i)
        if not p:
            err("O10", f"investor '{i}' is not in any profile library")
        elif not p.ok:
            err("O10", f"investor '{i}' has a profile that fails validation ({len(p.errors)} errors)")
    if kind == "panel" and not 3 <= len(ids) <= 7:
        err("O10", f"a panel has 3 to 7 investors ({len(ids)} listed)")
    if kind == "panel" and arch:
        err("O10", f"an archetype cannot be a panel member ({', '.join(arch)}); a panel has 3 to 7 validated profiles")
    if kind == "evaluation" and len(ids) + len(arch) != 1:
        err("O10", f"an evaluation names exactly one investor in 'investors:' or one archetype in 'archetypes:' "
                   f"({len(ids)} investors, {len(arch)} archetypes listed)")
    full, surname = _name_res(profiles, ids)
    doc_profiles = [profiles[i] for i in ids if i in profiles]

    # O1 label first, and at each investor section
    n0, first = doc.first_content()
    if not first.startswith("[!SIMULATION]") or SIM_LABEL.lower() not in first.lower():
        err("O1", "the first content line must be the '> [!SIMULATION] Analytical simulation. Not a statement by, "
                  "on behalf of, or a prediction of the decisions of …' label", n0)
    else:
        for p in doc_profiles:
            if not any(nm.lower() in first.lower() for nm in p.names):
                err("O1", f"the simulation label does not name {p.name}", n0)
        if arch and ARCHETYPE_LABEL not in first.lower():
            err("O1", f"the simulation label of an archetype must contain the words '{ARCHETYPE_LABEL}'", n0)
    if len(ids) > 1:
        for hn, _, ht in doc.headings:
            for p in doc_profiles:
                if any(ht.lower().startswith(nm.lower()) for nm in p.names):
                    ln, lab = doc.first_content(hn)
                    if not lab.startswith("[!SIMULATION]") or not any(nm.lower() in lab.lower() for nm in p.names):
                        err("O1", f"investor section '{ht}' must start with a simulation label naming {p.name}", hn)
    if kind in ("verdict", "report") and not CLOSING_RE.search(re.sub(r"\s+", " ", text)):
        err("O1", f"a {kind} ends with 'This assessment reflects the evidence available on <date>. It is not a "
                  "prediction of success, nor of any investor's decision.'")

    R = voice_res(profiles, ids)
    gtm_lines = {i.get("line") for i in gtm.check_claims(_claims_text(text)) if i.get("kind") in ("traction", "market-size")}
    for n, ln in doc.content:
        s = ln.strip()
        if not s:
            continue
        for level, rule, msg in line_issues(s, R, kind, n in doc.scenario):
            if rule == "O8" and n in gtm_lines:
                continue                        # already reported by the inherited claim guard
            (err if level == "error" else warn)(rule, msg, n)

    if kind == "debrief":
        iss += [_issue("error", "I3", f"{where}:{n}: {msg}", n) for n, msg in _verified_claims(doc.content, ledger)]

    if full_kind:
        iss += _structural_passes(doc, R, kind, where, base)

    # O6 scenarios
    for blk in doc.scenarios:
        body = "\n".join(t for _, t in blk)
        ln0 = blk[0][0]
        if "hypothetical scenario" not in body.lower():
            err("O6", "a [!SCENARIO] callout must say 'Hypothetical scenario'", ln0)
        if not re.search(r"(?im)^\**assumptions\**\s*:?\**\s*\n(?:.*\n)*?\s*[-*]\s+\S", body + "\n"):
            err("O6", "a [!SCENARIO] callout needs an 'Assumptions' list", ln0)
        nm = _has_name(body, full, surname)
        if nm:
            err("O6", f"a [!SCENARIO] callout must not name an investor ('{nm}'); frame it by investor class", ln0)

    # O8 claims and evidence
    for i in gtm.check_claims(_claims_text(text), ledger, where):
        iss.append({"level": i["level"], "rule": "O8", "line": i.get("line"), "message": i["message"]})
    if ledger is not None:
        bracketed = set()
        for m in CITE_RE.finditer(text):
            bracketed.update(re.split(r"\s*,\s*", m.group(1)))
        for n, ln in doc.content:
            for m in ID_RE.finditer(ln):
                if m.group(0) not in bracketed and m.group(0) not in ledger:
                    err("O8", f"{m.group(0)} is not in the ledger", n)
                    bracketed.add(m.group(0))
        reported = {e.id for e in ledger.entries if e.status == "reported"
                    and (e.source or {}).get("type") in ("founder", "document")}
        estimates = {e.id for e in ledger.entries if e.status == "estimate"}
        all_tables = doc.tables()
        for n, ln in doc.content:
            s = ln.strip()
            row = s.startswith("|")
            hdr = ""
            if row:
                for t in all_tables:
                    if any(rn == n for rn, _ in t["rows"]):
                        hdr = " ".join(t["header"])
            # A figure belongs to the citation that follows it: the segment from the previous citation (or the
            # sentence start) to this one must hold a number. The label may sit anywhere in the sentence, or
            # anywhere in a table row or its header. A group that also cites an assumption, estimate or
            # unverified entry is satisfied by that weaker status word.
            for u in ([s] if row else _units(s)):
                occ = [(m.end(), re.split(r"\s*,\s*", m.group(1)), False) for m in CITE_RE.finditer(u)]
                if row:      # unbracketed IDs (point-trace Evidence cells) vouch for the whole row
                    inside = {x for _, grp, _ in occ for x in grp}
                    bare = sorted({x for x in ID_RE.findall(u) if x not in inside})
                    if bare:
                        occ.append((len(u), bare, True))
                prev = 0
                ctx = u + " " + hdr
                for pos, grp, whole in occ:
                    seg = u if whole else u[prev:pos]
                    prev = pos if not whole else prev
                    g = set(grp)
                    if not g & (reported | estimates):
                        continue
                    if not re.search(r"\d", SHORT_ID_RE.sub(" ", DIM_RE.sub(" ", seg))):
                        continue
                    weaker = any(ledger.get(x) and ledger.get(x).status in ("assumption", "estimate", "unverified",
                                                                             "contradicted") for x in g)
                    weak_ok = weaker and WEAK_LABEL_RE.search(ctx)
                    if g & reported and not (REPORTED_LABEL_RE.search(ctx) or weak_ok):
                        err("O8", f"figure citing reported evidence ({', '.join(sorted(g & reported))}) must say "
                                  "founder-provided, company-provided, reported, by the company's own account or "
                                  f"according to: '{u.strip()[:80]}'", n)
                    if g & estimates and not ESTIMATE_LABEL_RE.search(ctx):
                        warn("O8", f"figure citing an estimate ({', '.join(sorted(g & estimates))}) should say "
                                   f"estimate or estimated: '{u.strip()[:80]}'", n)
    else:
        (warn if (allow_no_ledger or not full_kind) else err)(
            "O8", "no ledger: evidence IDs, founder and estimate labels and citation checks were not run; pass "
                  "--profile, set 'profile:' in the front matter, or pass --no-ledger to accept a weaker check")

    # B6 judgement tables
    iss += _check_judgement_tables(doc, kind, where, base, ledger)

    # evaluation: stance, trace, T1–T2
    traces = {}
    if kind == "evaluation":
        rng = doc.section("stance")
        st = []
        if not rng:
            err("T1", "an evaluation needs a 'Stance' section")
        else:
            body = "\n".join(ln.strip() for n, ln in doc.content if rng[0] < n < rng[1])
            st = stance_of(body)
            if len(st) != 1:
                err("T1", "the Stance section must give exactly one of: " + "; ".join(STANCES.values())
                    + (f" (found {', '.join(st)})" if st else "")
                    + (f"; 'Interested, conditional on …' is retired: write '{STANCES['conditional']}'"
                       if OLD_CONDITIONAL_RE.search(body) else ""), rng[0])
        rows = parse_trace(doc)
        if not rows:
            err("T1", "an evaluation needs a 'Point trace' table (# | Kind | Point | Lens | Dimension | Evidence)")
        p = doc_profiles[0] if len(doc_profiles) == 1 else None
        if p is None and len(arch) == 1 and not ids:
            lens_ids = _archetype_lenses(doc)
            if lens_ids:                      # lens ownership against the lenses written in the header
                iss += _check_trace(rows, _Archetype(arch[0], lens_ids), where)
        if (p or (len(arch) == 1 and not ids)) and base and rng and len(st) == 1:
            for dmiss, why in missing_concern_rows(base, p if p else None, rows):
                err("T7", f"deciding dimension {dmiss} {DIMENSIONS[dmiss]} is {why} in the base read but has no "
                          + ("concern or potential deal-breaker row" if why == "Weak" else
                             "concern row worded as an evidence gap (gap: in the Evidence column)"), rng[0])
            want, info = expected_stance(base, p, rows)
            if st[0] != want:
                err("T6", f"stance '{STANCES[st[0]]}' does not follow from the base read: expected '{STANCES[want]}' "
                          f"({_stance_why(info)}"
                          + ")", rng[0])
        if p:
            iss += _check_trace(rows, p, where, _expertise_section(doc))
            if p.effective == "low":
                top = " ".join(ln for n, ln in doc.content[:25]).lower()
                if "low confidence" not in top and "low-confidence" not in top:
                    warn("T2", f"{p.name}'s profile is low confidence: add the low-confidence notice to the header")
        traces[ids[0] if ids else ""] = rows
        # T4 within the document
        strip = [nm for q in doc_profiles for nm in q.names] + [_text(ln.get("label")) for q in doc_profiles
                                                                   for ln in q.lenses.values()]
        tagged = [r for r in rows if r["lens"] and r["lens"] != "base"]
        for a_i, a in enumerate(tagged):
            for b in tagged[a_i + 1:]:
                if a["lens"] != b["lens"] and _similar(_tokens(a["point"], strip), _tokens(b["point"], strip)) > 0.85 \
                        and len(_tokens(a["point"], strip)) >= 4:
                    warn("T4", f"{a['id']} ({a['lens']}) and {b['id']} ({b['lens']}) are near-identical under different "
                               "lenses: the lens did not shape the point", b["line"])

    # pairwise against other documents
    others = []
    for name, otext in against or []:
        od = _Doc(otext)
        oids = [str(i) for i in _list(od.meta.get("investors"))]
        others.append((name, od, oids))
    if kind == "evaluation" and len(doc_profiles) == 1:
        p = doc_profiles[0]
        mine = traces.get(p.id) or []
        conv = bool(CONVERGENCE_RE.search(text))
        for name, od, oids in others:
            if _text(od.meta.get("kind")).lower() != "evaluation" or len(oids) != 1 or oids[0] == p.id:
                continue
            q = profiles.get(oids[0])
            theirs = parse_trace(od)
            sig_a = ([r["dimension"] for r in sorted((r for r in mine if r["kind"] == "C"), key=lambda r: r["num"])][:3],
                     {r["dimension"] for r in mine if r["kind"] == "Q"})
            sig_b = ([r["dimension"] for r in sorted((r for r in theirs if r["kind"] == "C"), key=lambda r: r["num"])][:3],
                     {r["dimension"] for r in theirs if r["kind"] == "Q"})
            if q and (sig_a[0] or sig_a[1]) and sig_a == sig_b and p.emphasis != q.emphasis \
                    and not conv and not CONVERGENCE_RE.search(od.text):
                err("T3", f"possible name-swapped output: same top concerns {sig_a[0]} and question dimensions "
                          f"{sorted(sig_a[1])} as {name} ({q.name}) although the profiles' emphasis differs; add a "
                          "'Declared convergence' note if both lenses really point there")
            strip = [nm for x in (p, q) if x for nm in x.names] + [_text(ln.get("label")) for x in (p, q) if x
                                                                    for ln in x.lenses.values()]
            for a in mine:
                if not a["lens"] or a["lens"] == "base":
                    continue
                ta = _tokens(a["point"], strip)
                if len(ta) < 4:
                    continue
                for b in theirs:
                    if b["lens"] and b["lens"] != "base" and _similar(ta, _tokens(b["point"], strip)) > 0.85:
                        warn("T4", f"{a['id']} is near-identical to {b['id']} in {name} under a different "
                                   "investor's lens", a["line"])
                        break

    if kind == "panel":
        iss += _check_panel(doc, profiles, ids, others, where, base)
    return iss


class _Archetype:
    """An unnamed investor type: lenses written in the evaluation header, treated as medium, no decline patterns."""

    def __init__(self, name: str, lens_ids: Iterable[str]):
        self.name, self.id, self.names = name, name, []
        self.lenses = {lid: {} for lid in lens_ids}
        self.effective = "medium"

    def lens_reach(self, lid):
        return 0


def _archetype_lenses(doc: "_Doc") -> List[str]:
    """Lens ids defined in an archetype evaluation's header (before the Stance or Point trace section)."""
    stop = min([n for n, _, t in doc.headings if re.search(r"stance|point trace", t, re.I)] or [10 ** 9])
    out = []
    for n, ln in doc.content:
        if n >= stop:
            break
        for m in re.finditer(r"(?:^|[\s(*-])(?:id:\s*)?(L\d+)\b", ln):
            if m.group(1) not in out:
                out.append(m.group(1))
    return out


def _check_trace(rows: List[Dict], p, where: str, expertise: Optional[Tuple[bool, set]] = None) -> List[Dict]:
    iss = []

    def err(rule, msg, line):
        iss.append(_issue("error", rule, f"{where}:{line}: {msg}", line))

    for r in rows:
        if r["lens"] is None:
            err("T1", f"{r['id']}: the Lens cell must start with a lens id of {p.name} or 'base' "
                      f"('{r['lens_cell']}')", r["line"])
            continue
        if r["lens"] != "base" and r["lens"] not in p.lenses:
            err("T1", f"{r['id']}: lens {r['lens']} does not belong to {p.name}'s profile", r["line"])
            continue
        if not r["dimension"]:
            err("T1", f"{r['id']}: the Dimension cell must name one of D01–D15", r["line"])
        if r["kind"] == "B":
            if p.effective == "low":
                err("T1", f"{r['id']}: a low-confidence profile allows no investor-specific potential deal-breakers",
                    r["line"])
            elif r["lens"] == "base" or not _text(p.lenses[r["lens"]].get("decline_pattern")):
                err("T1", f"{r['id']}: a potential deal-breaker needs a lens with a documented decline_pattern",
                    r["line"])
            elif p.effective == "medium" and p.lens_reach(r["lens"]) < 2:
                err("T1", f"{r['id']}: at medium confidence a deal-breaker needs a lens that reaches 2 sources",
                    r["line"])
        if r["kind"] in "ACQRB" and not (ID_RE.search(r["evidence"]) or re.search(r"\bgap\b", r["evidence"], re.I)):
            err("T1", f"{r['id']}: the Evidence cell needs E-IDs or 'gap'", r["line"])
    ac = [r for r in rows if r["kind"] in "AC" and r["lens"]]
    tagged = [r for r in ac if r["lens"] != "base"]
    if p.effective == "low":
        for k, label in (("A", "attraction"), ("C", "concern")):
            if sum(1 for r in tagged if r["kind"] == k) > 1:
                iss.append(_issue("error", "T2", f"{where}: a low-confidence profile allows at most one lens-tagged "
                                                 f"{label} row"))
    elif p.effective in ("medium", "high") and ac and len(tagged) * 2 < len(ac):
        has_gap, listed = expertise or (False, set())
        if has_gap:
            # rows re-tagged base because they fall in a documented gap count as lens-attributed
            attributed = len(tagged) + sum(1 for r in ac if r["lens"] == "base" and r["id"] in listed)
            if attributed * 2 < len(ac):
                iss.append(_issue("warning", "T2", f"{where}: only {attributed} of {len(ac)} attraction and concern "
                                                   "rows are lens-tagged or listed under Outside documented expertise: "
                                                   f"{p.name}'s documented record gives little basis for reading this "
                                                   "startup"))
        else:
            iss.append(_issue("error", "T2", f"{where}: generic: only {len(tagged)} of {len(ac)} attraction and concern "
                                             "rows are lens-tagged; it reads as the base read with a name attached"))
    return iss


def _expertise_section(doc: "_Doc") -> Tuple[bool, set]:
    """(non-empty, row ids listed) for the 'Outside documented expertise' section. 'None.' counts as empty."""
    rng = doc.section("outside documented expertise")
    if not rng:
        return False, set()
    body = " ".join(ln.strip() for n, ln in doc.content if rng[0] < n < rng[1]).strip()
    if not body or re.match(r"^(?:[-*]\s*)?\**none\b", body, re.I):
        return False, set()
    return True, set(re.findall(r"\b[AC]\d+\b", body))


def _resolve_investor(cell: str, profiles: Dict[str, Profile], ids: List[str]) -> Optional[str]:
    c = _clean_cell(cell).lower()
    c = re.sub(r"\s*\(.*\)$", "", c)
    for i in ids:
        p = profiles.get(i)
        if c == i or (p and any(c == nm.lower() for nm in p.names)):
            return i
    return None


def _check_panel(doc: "_Doc", profiles: Dict[str, Profile], ids: List[str], others, where: str,
                 base: Optional[Dict] = None) -> List[Dict]:
    iss = []

    def err(rule, msg, line=None):
        iss.append(_issue("error", rule, f"{where}:{line}: {msg}" if line else f"{where}: {msg}", line))

    init, disc = doc.section("initial positions"), doc.section("discussion")
    if not init:
        err("N2", "a panel report needs an 'Initial positions' section")
    if not disc:
        err("N2", "a panel report needs a 'Discussion' section")
    if init and disc and init[0] > disc[0]:
        err("N2", "'Initial positions' must come before 'Discussion'", disc[0])
    # initial positions match the stage-1 evaluations given with --against
    initial = {}
    if init:
        for t in doc.tables(init):
            ci, cs = _col(t, "investor"), _col(t, "stance")
            if ci is None or cs is None:
                continue
            for n, row in t["rows"]:
                inv = _resolve_investor(_cell(row, ci), profiles, ids)
                if not inv:
                    err("N4", f"initial positions: unknown investor '{_cell(row, ci)}'", n)
                    continue
                initial[inv] = (n, stance_of(_cell(row, cs)))
    member_rows = {}
    for name, od, oids in others:
        if _text(od.meta.get("kind")).lower() == "evaluation" and len(oids) == 1 and oids[0] in initial:
            member_rows[oids[0]] = parse_trace(od)
            rng = od.section("stance")
            st = stance_of("\n".join(ln.strip() for n, ln in od.content if rng and rng[0] < n < rng[1]))
            n, mine = initial[oids[0]]
            if st and mine and st != mine:
                err("N2", f"initial position of {oids[0]} ({mine[0]}) differs from its evaluation {name} ({st[0]})", n)
    # T6: each member's initial stance follows from the base read and that member's profile
    if base:
        for inv, (n, mine) in initial.items():
            if len(mine) != 1 or inv not in profiles:
                continue
            want, info = expected_stance(base, profiles[inv], member_rows.get(inv))
            if mine[0] != want:
                err("T6", f"initial stance of {inv} '{STANCES[mine[0]]}' does not follow from the base read: expected "
                          f"'{STANCES[want]}' ({_stance_why(info)})", n)
    # divergence map: each member cell gives the member's role for the dimension (warning, N6)
    dmap = doc.section("divergence map")
    if dmap:
        for t in doc.tables(dmap):
            member_cols = [i for i, h in enumerate(t["header"]) if _resolve_investor(h, profiles, ids)]
            for n, row in t["rows"]:
                if re.match(r"^\W*stances?\b", _clean_cell(_cell(row, 0)), re.I):
                    continue
                for i in member_cols:
                    c = _cell(row, i)
                    if c and not ROLE_RE.search(c):
                        iss.append(_issue("warning", "N6", f"{where}:{n}: divergence-map cell '{c[:40]}' gives no role: "
                                                           "write deciding, considered, not covered or outside "
                                                           "expertise", n))
    # discussion exchange rows
    xids = set()
    if disc:
        found = False
        for t in doc.tables(disc):
            ci, cl, ce = _col(t, "investor"), _col(t, "lens"), _col(t, "evidence")
            if ci is None or cl is None:
                continue
            found = True
            cx = _col(t, "#", "id", "exchange")
            for n, row in t["rows"]:
                xid = _clean_cell(_cell(row, cx if cx is not None else 0))
                m = EXCHANGE_ID_RE.match(xid)
                if not m:
                    err("N4", f"exchange row id '{xid}' must look like X1 or X1a", n)
                    continue
                xids.add(f"X{m.group(1)}")
                xids.add(xid)
                inv = _resolve_investor(_cell(row, ci), profiles, ids)
                lens = _clean_cell(_cell(row, cl))
                lm = re.match(r"^L-?(\d+)\b", lens)
                is_base = bool(re.match(r"^base\b", lens, re.I))  # a dimension none of the member's lenses covers
                evid = _cell(row, ce)
                if not inv:
                    err("N4", f"{xid}: investor '{_cell(row, ci)}' is not on this panel", n)
                if not lm and not is_base:
                    err("N4", f"{xid}: the Lens cell must name the investor's lens (L1) or 'base'", n)
                elif lm and inv and profiles.get(inv) and f"L{lm.group(1)}" not in profiles[inv].lenses:
                    err("T1", f"{xid}: lens L{lm.group(1)} does not belong to {inv}", n)
                if not (ID_RE.search(evid) or re.search(r"\bgap\b", evid, re.I)):
                    err("N4", f"{xid}: the exchange needs evidence (E-IDs) or 'gap'", n)
        body = " ".join(ln for n, ln in doc.content if disc[0] < n < disc[1]).lower()
        if not found and "converges on all critical dimensions" not in body:
            err("N4", "Discussion has neither an exchange table (# | Dimension | Investor | Lens | Evidence or gap) "
                      "nor the convergence statement", disc[0])
    dis = doc.section("disagreements explained")
    if dis:
        for t in doc.tables(dis):
            cc = _col(t, "class")
            if cc is None:
                err("N4", "the 'Disagreements explained' table needs a Class column", t["line"])
                continue
            for n, row in t["rows"]:
                c = _clean_cell(_cell(row, cc)).lower().replace(" ", "-")
                if c not in DISAGREEMENT_CLASSES:
                    err("N4", f"disagreement class '{_cell(row, cc)}' not in {DISAGREEMENT_CLASSES}", n)
    fin = doc.section("final positions")
    if fin:
        for t in doc.tables(fin):
            ci, cin, cfi, cca = _col(t, "investor"), _col(t, "initial"), _col(t, "final"), _col(t, "cause")
            if ci is None or cin is None or cfi is None:
                continue
            for n, row in t["rows"]:
                a, b = stance_of(_cell(row, cin)), stance_of(_cell(row, cfi))
                if a and b and a != b:
                    cited = re.findall(r"\bX\d+[a-z]?\b", _cell(row, cca))
                    if not cited:
                        err("N3", f"stance change for '{_cell(row, ci)}' must cite an exchange row (X1) as its cause", n)
                    for x in cited:
                        if x not in xids:
                            err("N3", f"stance change cites {x}, which is not an exchange row in Discussion", n)
    return iss


J2_CLASS_RE = (("debt-or-revenue-based", r"debt|revenue[- ]based"),
               ("operator-strategic", r"operator[- /]+strategic|\boperator\b"), ("venture", r"\bventure\b"))


def _j2_class(text: str) -> Optional[str]:
    t = text.lower()
    return next((c for c, rx in J2_CLASS_RE if re.search(rx, t)), None)


def _check_judgement_tables(doc: "_Doc", kind: str, where: str, base: Optional[Dict] = None,
                            ledger: Optional[Ledger] = None) -> List[Dict]:
    iss = []
    ans: Dict[str, Any] = {"J2": []}
    reasons: Dict[str, str] = {}
    first_line = None
    for t in doc.tables():
        cj, ca, cr = _col(t, "judgement", "judgment"), _col(t, "answer"), _col(t, "reason")
        if cj is None or ca is None:
            continue
        for n, row in t["rows"]:
            jc = _clean_cell(_cell(row, cj))
            m = re.match(r"^(J[1-5])\b", jc)
            if not m:
                continue
            first_line = first_line or n
            a = _clean_cell(_cell(row, ca)).lower().replace(" ", "-")
            if a not in ANSWERS:
                iss.append(_issue("error", "B6", f"{where}:{n}: {m.group(1)} answer '{_cell(row, ca)}' must be Yes, No "
                                                 "or Not yet determinable", n))
            if m.group(1) == "J2":
                cls = _j2_class(jc) or _j2_class(" ".join(row))     # the Judgement cell first
                if not cls:
                    iss.append(_issue("error", "B6", f"{where}:{n}: J2 must name an investor class (venture, "
                                                     "operator-strategic, debt-or-revenue-based)", n))
                ans["J2"].append((cls, a))
            else:
                ans[m.group(1)] = a
                reasons[m.group(1)] = _cell(row, cr) if cr is not None else " ".join(row)
    if first_line is None:
        if kind == "verdict":
            iss.append(_issue("error", "B6", f"{where}: a verdict needs the five-judgement table (Judgement | Answer | "
                                             "Reason | Deciding dimensions)"))
        return iss
    for k in JUDGEMENTS:
        if k not in ans and not (k == "J2" and ans["J2"]):
            iss.append(_issue("error", "B6", f"{where}: judgement {k} {JUDGEMENTS[k]} is missing"))
    iss += _combination_errors(ans, where)
    if base:
        for m in judgement_gates(ans, reasons, base.get("dimensions") or {}, base.get("ambition"), ledger):
            iss.append(_issue("error", "B6", f"{where}:{first_line}: {m}", first_line))
    return iss


# ============================================================================= sessions (I1–I3) and record
SESSION_MODES = ("investor", "panel", "archetype")
SESSION_STATUS = ("setup", "awaiting-answer", "debrief", "closed", "paused")
CRITERIA = ("specificity", "evidence", "financial", "strategic", "customer", "execution", "risk")
CRITERION_VALUES = ("clear", "partial", "missing", "n/a")
DECISIONS = ("follow-up", "move-on", "stop")
Q_FIRST_PERSON_RE = re.compile(r"\bI(?:['’]d|['’]m| would| want| am| need)\b|\bmy (?:offer|concern|view)\b", re.I)


QWORD = r"(?:what|how|which|when|who|whom|whose|why|where|whether)"
AUX = r"(?:does|do|did|is|are|was|were|can|could|will|would|has|have|had|should)"
QSTART_RE = re.compile(r"^\W*(?:" + QWORD + "|" + AUX + r")\b", re.I)
COMPOUND_RES = (
    (re.compile(r";"), "a semicolon joins two questions"),
    (re.compile(r"(?:,|\band\b|\bor\b)\s*(?:\w+\s+){0,2}?" + QWORD + r"\b", re.I),
     "a second question word follows a comma, 'and' or 'or'"),
    (re.compile(r"\band (?:your|the|its|their) [\w-]+(?: [\w-]+)? and (?:your|the|its|their)\b|,\s*(?:your|the) [\w-]+,?"
                r" and (?:your|the)\b", re.I), "several items are asked for at once"),
    (re.compile(r"\b(?:as well as|followed by|plus|along with|together with|in addition to|alongside|and also)\b", re.I),
     "a second item is added with 'as well as', 'followed by', 'plus' or 'along with'"),
    (re.compile(r"\((?:and|or|plus|also|as well as|with|including)\b|\b(?:i\.?e|e\.?g)\.?,?\s[^?]*\band\b", re.I),
     "a second request sits in parentheses or after an 'i.e.' gloss"),
    (re.compile(r"(?:,|\band\b|\bor\b)\s*" + AUX + r"\s+(?:it|that|this|they|he|she|you|we|there|the|those|these|an?|"
                r"any|each|[A-Z][\w-]*)\b"), "a second, yes/no clause follows a comma, 'and' or 'or'"),
)


def question_problems(text: str) -> List[str]:
    """I2: one question per turn means one decisive unknown. A second interrogative clause (after a comma, 'and',
    'or' or a semicolon), or a list of items, is a compound question. 'and' that binds a figure to its unit, date or
    basis is allowed when no second question word follows ("What was revenue in October and November?")."""
    t = text.strip()
    out = []
    if t.count("?") != 1 or not t.endswith("?"):
        out.append("the question text must hold exactly one question and end with '?'")
    if ";" in t:
        head, _, t = t.partition(";")          # context; then the question: compound only if the head asks too
        if QSTART_RE.search(head) or head.rstrip().endswith("?"):
            out.append(f"compound question ({COMPOUND_RES[0][1]}): ask one decisive unknown per turn")
            return out
    first = re.search(r"\b(?:" + QWORD + "|" + AUX + r")\b|^\W*(?:give|state|tell|show|list|provide|name|share|send|"
                      r"describe|explain)\b", t, re.I)
    start = first.end() if first else 0
    for rx, why in COMPOUND_RES[1:]:
        if rx.search(t[start:]):
            out.append(f"compound question ({why}): ask one decisive unknown per turn")
            break
    return out


def validate_session(data: Any, profiles: Optional[Dict[str, Profile]] = None) -> List[Dict]:
    iss: List[Dict] = []

    def err(rule, msg):
        iss.append(_issue("error", rule, msg))

    def warn(rule, msg):
        iss.append(_issue("warning", rule, msg))

    if not isinstance(data, dict):
        return [_issue("error", "I1", "the session file is not a YAML mapping")]
    if not _text(data.get("session")):
        err("I1", "'session' id is missing")
    mode = data.get("mode")
    if mode not in SESSION_MODES:
        err("I1", f"mode '{mode}' not in {SESSION_MODES}")
    invs = [str(i) for i in _list(data.get("investors"))]
    if mode == "investor" and len(invs) != 1:
        err("I1", f"investor mode names exactly one investor ({len(invs)} listed)")
    if mode == "panel" and not 3 <= len(invs) <= 7:
        err("I1", f"panel mode names 3 to 7 investors ({len(invs)} listed)")
    if profiles is not None:
        for i in invs:
            if i not in profiles:
                err("I1", f"investor '{i}' is not in any profile library")
    budget = data.get("budget", 10)
    if not isinstance(budget, int) or not 1 <= budget <= 20:
        err("I1", f"budget must be a whole number from 1 to 20 ({budget!r})")
        budget = 20
    elif budget < 5:
        warn("I1", f"budget {budget} is outside the usual 5–20")
    if data.get("status") not in SESSION_STATUS:
        err("I1", f"status '{data.get('status')}' not in {SESSION_STATUS}")
    for q in _list(data.get("queue")):
        if not isinstance(q, dict) or str(q.get("dimension")) not in DIMENSIONS:
            err("I1", f"queue item {q!r:.60} needs a valid dimension")
            continue
        if q.get("tier") not in (1, 2, 3, 4, 5):
            err("I1", f"queue item {q.get('id')}: tier must be 1 to 5")
        if _text(q.get("text")):                 # prepared questions are checked before they are asked
            for prob in question_problems(_text(q.get("text"))):
                err("I2", f"queue item {q.get('id')}: {prob}")
    turns = _list(data.get("turns"))
    R = voice_res(profiles or {}, invs)
    qids, roots, followups, main = {}, {}, {}, 0
    for k, t in enumerate(turns, 1):
        if not isinstance(t, dict):
            err("I1", f"turn {k} is not a mapping")
            continue
        if t.get("n") != k:
            err("I1", f"turn {k}: n must be {k} (turns are numbered in order)")
        q = t.get("question")
        if isinstance(q, list):
            err("I1", f"turn {k}: exactly one question per turn ({len(q)} given)")
            continue
        if not isinstance(q, dict):
            err("I1", f"turn {k}: the question is missing")
            continue
        qid = _text(q.get("id"))
        if not qid:
            err("I1", f"turn {k}: question id is missing")
        elif qid in qids:
            err("I1", f"turn {k}: question id {qid} was already asked in turn {qids[qid]}")
        if str(q.get("dimension")) not in DIMENSIONS:
            err("I1", f"turn {k}: question dimension '{q.get('dimension')}' is not one of D01–D15")
        txt = _text(q.get("text"))
        for prob in question_problems(txt):
            err("I2", f"turn {k}: {prob}")
        if Q_FIRST_PERSON_RE.search(txt) or QUOTE_RE.search(txt):
            err("I2", f"turn {k}: a question is raised through a lens, never spoken in the investor's voice")
        for level, rule, msg in line_issues(txt, R, "session"):
            if rule in ("O3", "O5", "O7"):
                err(rule, f"turn {k}: {msg}")
        inv = _text(q.get("investor"))
        if inv and invs and inv not in invs and inv != "base":
            err("I1", f"turn {k}: investor '{inv}' is not in this session")
        if inv and profiles and inv in profiles and _text(q.get("lens")) and _text(q.get("lens")) != "base" \
                and _text(q.get("lens")) not in profiles[inv].lenses:
            err("I1", f"turn {k}: lens {q.get('lens')} does not belong to {inv}")
        fu = q.get("follow_up_of")
        if fu:
            fu = _text(fu)
            if fu not in qids:
                err("I1", f"turn {k}: follow_up_of '{fu}' is not an earlier question")
                root = fu
            else:
                root = roots.get(fu, fu)
            followups[root] = followups.get(root, 0) + 1
            if followups[root] > 2:
                err("I1", f"turn {k}: more than two follow-ups on topic {root}")
            roots[qid] = root
        else:
            main += 1
            roots[qid] = qid
        qids[qid] = k
        a = t.get("assessment")
        if a is not None:
            if not isinstance(a, dict):
                err("I1", f"turn {k}: assessment must be a mapping")
            else:
                for c, v in a.items():
                    if c not in CRITERIA:
                        err("I1", f"turn {k}: unknown assessment criterion '{c}'")
                    elif _text(v) not in CRITERION_VALUES:
                        err("I1", f"turn {k}: {c} '{v}' not in {CRITERION_VALUES}")
        if t.get("decision") is not None and t.get("decision") not in DECISIONS:
            err("I1", f"turn {k}: decision '{t.get('decision')}' not in {DECISIONS}")
        for f in _list(t.get("new_facts")):
            if not isinstance(f, dict) or f.get("proposed_status") != "reported":
                err("I3", f"turn {k}: every new fact has proposed_status: reported")
            elif _verified_hits(_text(f.get("claim"))):
                err("I3", f"turn {k}: a new fact's claim calls it verified; a founder answer is founder-provided")
    if main > budget:
        err("I1", f"{main} questions asked (follow-ups excluded) exceeds the budget of {budget}")
    pend_ids = set()
    for f in _list(data.get("pending_ledger")):
        if not isinstance(f, dict):
            err("I3", "a pending_ledger item is not a mapping")
            continue
        if f.get("proposed_status", "reported") != "reported" or str(f.get("status", "reported")) != "reported":
            err("I3", f"pending item {f.get('id')}: only 'reported' may be proposed; nothing from a session is "
                      "verified")
        if not _text(f.get("claim")):
            err("I3", f"pending item {f.get('id')}: claim is empty")
        elif _verified_hits(_text(f.get("claim"))):
            err("I3", f"pending item {f.get('id')}: the claim calls the fact verified; nothing from a session is "
                      "verified")
        fid = _text(f.get("id"))
        if fid and fid in pend_ids:
            err("I3", f"pending item id {fid} is used twice")
        pend_ids.add(fid)
    return iss


def check_queue_document(text: str, profiles: Optional[Dict[str, Profile]] = None,
                         where: str = "queue.md") -> List[Dict]:
    """I2 (and O3, O5, O7) on the prepared questions in a queue document: every cell of a table column headed
    'Question…' (or 'Text'), and every planned follow-up bullet written as '- Q1a: <question>'."""
    iss: List[Dict] = []
    doc = _Doc(text)
    meta_ids = [str(i) for i in _list(doc.meta.get("investors"))]
    R = voice_res(profiles or {}, meta_ids or list((profiles or {}).keys()))
    found = []
    for t in doc.tables():
        cq = next((i for i, h in enumerate(t["header"]) if h.startswith("question") or h == "text"), None)
        cid = _col(t, "q", "#", "id")
        if cq is None:
            continue
        for n, row in t["rows"]:
            found.append((n, _clean_cell(_cell(row, cid)) if cid is not None else "", _cell(row, cq)))
    for n, ln in doc.content:
        m = re.match(r"^\s*[-*]\s+\**(Q\d+[a-z]?)\**\s*[:.]\s*(.+)$", ln)
        if m:
            found.append((n, m.group(1), m.group(2).strip()))
    if not found:
        iss.append(_issue("warning", "I2", f"{where}: no prepared questions found (a table column headed 'Question' or "
                                           "bullets '- Q1a: …')"))
    for n, qid, q in found:
        for prob in question_problems(q):
            iss.append(_issue("error", "I2", f"{where}:{n}: {qid or 'question'}: {prob}", n))
        for level, rule, msg in line_issues(q, R, "session"):
            if rule in ("O3", "O5", "O7"):
                iss.append(_issue(level, rule, f"{where}:{n}: {qid or 'question'}: {msg}", n))
    return iss


OPINION_RE = re.compile(r"\blens\b|\bsimulat\w*|\bthe panel\b|\bthe sharks\b|\bthe dragons\b", re.I)


def record(session_path: str, profile_dir: str, confirmed: bool = False, today=None,
           profiles: Optional[Dict[str, Profile]] = None) -> List[str]:
    """Append the session's pending facts to the ledger as founder-provided ('reported'). Append-only,
    idempotent, refuses without explicit confirmation, never writes 'verified'."""
    if not confirmed:
        raise ValueError("refusing to write: record needs --confirmed (the founder must agree first)")
    today = _today(today).isoformat()
    data = load_yaml(session_path)
    errs = [i for i in validate_session(data, None) if i["level"] == "error"]
    if errs:
        raise ValueError("the session file fails validation: " + "; ".join(i["message"] for i in errs[:3]))
    path = os.path.join(profile_dir, "evidence.yaml")
    if not os.path.isfile(path):
        raise ValueError(f"no evidence ledger at {path}; record writes only to the existing shared ledger")
    sid = _text(data.get("session"))
    ledger = Ledger.load(path)
    refs = {str((e.source or {}).get("ref", "")) for e in ledger.entries}
    names = [nm.lower() for p in (profiles or {}).values() for nm in p.names]
    new = []
    for k, f in enumerate(_list(data.get("pending_ledger")), 1):
        fid = _text(f.get("id")) or f"F{k}"
        ref = f"shark-tank-interrogation/{sid}#{fid}"
        if ref in refs:
            continue
        claim = _text(f.get("claim"))
        if OPINION_RE.search(claim) or any(nm in claim.lower() for nm in names):
            raise ValueError(f"pending item {fid} reads as simulated investor opinion; only founder facts are "
                             "recorded")
        eid = ledger.next_id() if not new else "E-%03d" % (int(new[-1]["id"][2:]) + 1)
        entry = {"id": eid, "claim": claim}
        for key in ("key", "value", "unit"):
            if f.get(key) is not None:
                entry[key] = f[key]
        conf = _text(f.get("confidence")).lower()
        entry.update({"status": "reported", "confidence": conf if conf in ("low", "medium") else "low",
                      "source": {"type": "founder", "ref": ref, "accessed": today}, "updated": today,
                      "notes": f"Founder-provided in shark-tank interrogation session {sid}"
                               + (f", turn {f.get('turn')}" if f.get("turn") else "")
                               + "; recorded with the founder's agreement. Not independently verified."})
        new.append(entry)
    if new:
        with open(path, "a", encoding="utf-8") as fh:
            fh.write("\n" + yaml.safe_dump(new, sort_keys=False, allow_unicode=True))
    return [n["id"] for n in new]
