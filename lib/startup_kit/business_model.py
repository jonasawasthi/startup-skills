"""Business model engine: the deterministic half of the business-model-designer skill.

The skill reasons about which business model to recommend; this module keeps the
design honest and traceable:

* a nine-block Business Model Canvas whose every item carries a *basis*
  (evidence, founder, hypothesis, recommendation, unknown); "evidence" on a
  customer-facing block needs customer evidence from the ledger, never a
  founder's opinion or desk research;
* Value Proposition Canvases per segment with a computed fit ladder;
* a business-model taxonomy (SaaS, marketplace, commission, ... hybrid) with the
  structural requirements each type implies;
* revenue streams on a stage ladder (proposed → tested → available → generating
  → repeatable) where each step needs specific evidence;
* a cost structure that keeps fixed, variable and unknown costs apart;
* marketplace modelling: sides, funnel from registered to repeat transactions,
  liquidity claims gated on measured data, GMV vs platform revenue vs seller
  earnings;
* financial definitions (GMV, gross/net revenue, take rate, margins, ...)
  computed only when every input exists (reusing the GTM metrics engine);
* payment, payout and regulatory dependencies that must be verified, never
  assumed; a guard against confusing in-person cross-border QR with
  international online checkout;
* alternatives compared on defined qualitative scales (numeric scores rejected);
* an assumption register on the shared ledger and discovery register (append-only
  ``--record``);
* stress tests with break-even and headroom arithmetic and founder-defined
  scenarios (no probabilities, no invented shocks);
* a maturity verdict that never confuses a coherent canvas with a working business;
* a Markdown+ report for ``startup-kit doc``, an XLSX workbook and a document guard.

Spec format: skills/business-model-designer/references/business-model-spec.md
"""
from __future__ import annotations

import datetime as _dt
import os
import re
from collections import OrderedDict
from typing import Any, Callable, Dict, List, Optional, Tuple

import yaml

from . import customer_discovery as cd
from . import gtm
from .evidence import CITE_RE, Ledger

_issue = gtm._issue
_ids = gtm._ids
_text = gtm._text
_cell = gtm._cell
_cite = gtm._cite
_worst = gtm._worst
_val = gtm._val

# ----------------------------------------------------------------------------- vocabularies
BLOCKS = OrderedDict([
    ("customer_segments", "Customer Segments"),
    ("value_propositions", "Value Propositions"),
    ("channels", "Channels"),
    ("customer_relationships", "Customer Relationships"),
    ("revenue_streams", "Revenue Streams"),
    ("key_resources", "Key Resources"),
    ("key_activities", "Key Activities"),
    ("key_partnerships", "Key Partnerships"),
    ("cost_structure", "Cost Structure"),
])
CUSTOMER_BLOCKS = ("customer_segments", "value_propositions", "channels", "customer_relationships", "revenue_streams")
BASES = OrderedDict([
    ("evidence", "Evidence-backed"),
    ("founder", "Founder-provided"),
    ("hypothesis", "Hypothesis"),
    ("recommendation", "Recommendation"),
    ("unknown", "Unknown"),
])
VALID = ("verified", "reported")

# taxonomy: key -> (label, dimension)
BM_TYPES = OrderedDict([
    ("saas", ("SaaS", "revenue")), ("subscription", ("Subscription", "revenue")),
    ("freemium", ("Freemium", "revenue")), ("marketplace", ("Marketplace", "structure")),
    ("transaction", ("Transaction-based", "revenue")), ("commission", ("Commission-based", "revenue")),
    ("digital-products", ("Digital products", "revenue")), ("education", ("Courses and education", "revenue")),
    ("services", ("Service-based", "revenue")), ("consulting", ("Consulting", "revenue")),
    ("advertising", ("Advertising-supported", "revenue")), ("licensing", ("Licensing", "revenue")),
    ("usage-based", ("Usage-based", "revenue")), ("ecommerce", ("E-commerce", "revenue")),
    ("direct-sales", ("Direct sales", "structure")), ("b2b", ("B2B", "orientation")),
    ("b2c", ("B2C", "orientation")), ("b2b2c", ("B2B2C", "orientation")), ("hybrid", ("Hybrid", "structure")),
])
MECHANISMS = ("one-time", "subscription", "transaction-fee", "commission", "usage", "licensing", "service-fee",
              "advertising", "bundle", "tiered", "hybrid")
STREAM_STAGES = OrderedDict([
    ("proposed", "Proposed: designed, not yet offered"),
    ("tested", "Tested: offer or price put in front of customers"),
    ("available", "Available: customers can actually pay today"),
    ("generating", "Generating revenue: payments received"),
    ("repeatable", "Demonstrated and repeatable: repeat or retained payments measured"),
])
COST_CATEGORIES = ("fixed", "variable", "semi-variable")
COST_TYPES = ("delivery", "infrastructure", "payment-processing", "acquisition", "support", "operations", "personnel",
              "compliance", "administrative", "partner", "incentives", "other")
MARKETPLACE_CONFIGS = ("two-sided", "three-sided", "service", "digital-product", "education", "managed", "hybrid-saas")
SIDE_ROLES = ("supply", "demand", "third-party")
FUNNEL = OrderedDict([
    ("registered_supply", "Registered supply"), ("active_supply", "Active supply"),
    ("available_supply", "Available supply (live listings or open capacity)"),
    ("registered_demand", "Registered demand"), ("active_demand", "Active demand"),
    ("demand_requests", "Actual demand (searches, requests or checkouts started)"),
    ("matches", "Successful matches"), ("completed_transactions", "Completed transactions"),
    ("repeat_transactions", "Repeat transactions"),
])
FUNNEL_ORDER = (("active_supply", "registered_supply"), ("active_demand", "registered_demand"),
                ("completed_transactions", "matches"), ("repeat_transactions", "completed_transactions"))
FUNNEL_RATIOS = OrderedDict([
    ("supply_activation", ("Supply activation", "active_supply ÷ registered_supply", ("active_supply", "registered_supply"))),
    ("demand_activation", ("Demand activation", "active_demand ÷ registered_demand", ("active_demand", "registered_demand"))),
    ("match_rate", ("Match rate", "matches ÷ demand_requests", ("matches", "demand_requests"))),
    ("completion_rate", ("Transaction completion", "completed_transactions ÷ matches", ("completed_transactions", "matches"))),
    ("repeat_rate", ("Repeat transaction share", "repeat_transactions ÷ completed_transactions",
                     ("repeat_transactions", "completed_transactions"))),
])
DEP_TYPES = ("payment", "payout", "banking", "regulatory", "tax", "legal", "partner", "technology", "other")
DEP_STATUSES = ("verified", "in-progress", "unverified", "assumed", "blocked")
ADVISERS = ("legal", "tax", "payment-provider", "bank", "regulator", "accountant", "partner")
ASSUMPTION_CATEGORIES = ("wtp", "pricing", "revenue", "acquisition", "retention", "costs", "margins", "volume",
                         "liquidity", "partnerships", "payments", "operations", "regulatory")
COMMIT_CATS = ("wtp", "pricing", "revenue")
MEASURED_CATS = ("retention", "volume", "liquidity", "margins", "acquisition")
INTERNAL_CATS = ("costs", "payments", "partnerships", "operations", "regulatory")
LEVEL_WORDS = ("high", "medium", "low")
DECISIONS = ("recommended", "viable", "reject", "undecided")
ALT_FIELDS = OrderedDict([
    ("description", "Model description"), ("target_customers", "Target customers"),
    ("value_proposition", "Value proposition"), ("revenue", "Revenue architecture"),
    ("costs", "Cost implications"), ("complexity", "Operational complexity"), ("capital", "Capital requirements"),
    ("distribution", "Distribution requirements"), ("dependencies", "Dependencies"), ("risks", "Risks"),
    ("validation", "Validation requirements"), ("tradeoffs", "Strategic trade-offs"),
])
DEFAULT_SCALE = OrderedDict([
    ("favourable", "Evidence or a clear structural reason makes this criterion work in the model's favour"),
    ("mixed", "Some factors help and some hurt, or it depends on an untested assumption"),
    ("unfavourable", "This criterion works against the model as designed"),
    ("unknown", "Not enough information to judge"),
])
DEFAULT_CRITERIA = OrderedDict([
    ("customer_fit", "Customer fit"), ("revenue_clarity", "Clarity of who pays and for what"),
    ("operational_complexity", "Operational complexity"), ("capital_needs", "Capital requirements"),
    ("distribution", "Distribution requirements"), ("dependency_risk", "Dependency risk"),
    ("validation_burden", "Validation burden before commitment"),
])
# revenue families: two types from one family (SaaS + subscription) are not a hybrid
REVENUE_FAMILY = {"saas": "recurring", "subscription": "recurring", "freemium": "recurring", "usage-based": "usage",
                  "transaction": "transaction", "commission": "transaction", "digital-products": "one-time",
                  "ecommerce": "one-time", "education": "one-time", "services": "services", "consulting": "services",
                  "advertising": "advertising", "licensing": "licensing"}
NUMERIC_RANK_KEYS = ("score", "scores", "rank", "ranking", "total", "weight", "weighted", "points")
PROBABILITY_KEYS = ("probability", "probabilities", "likelihood", "chance", "odds")

MATURITY = OrderedDict([
    ("incomplete", "Incomplete: the model is not yet fully described"),
    ("coherent", "Conceptually coherent: complete and internally consistent, not yet supported by customers"),
    ("customer-evidence", "Supported by customer evidence: customers confirm the problem and value"),
    ("economic-viability", "Demonstrated economic viability: paid transactions with positive measured contribution"),
    ("repeatable", "Repeatable commercial performance: repeat revenue and measured acquisition cost"),
])

# ----------------------------------------------------------------------------- stress cards
# key: (title, question, driver inputs, assumption categories, dependency types)
STRESS_CARDS = OrderedDict([
    ("wtp", ("Weak willingness to pay", "What is the lowest price at which each transaction still contributes?",
             ("price", "take_rate", "payment_fee_rate", "delivery_cost", "support_cost"), ("wtp", "pricing"), ())),
    ("cac", ("High acquisition costs", "How much can a customer cost to acquire before lifetime contribution is "
             "negative?", ("price", "take_rate", "purchases_per_customer", "cac"), ("acquisition",), ())),
    ("retention", ("Low retention", "How many purchases per customer are needed to repay acquisition?",
                   ("cac", "price", "take_rate"), ("retention",), ())),
    ("volume", ("Insufficient transaction volume", "How many transactions a month cover fixed costs?",
                ("fixed_costs_month", "price", "take_rate", "transactions_per_month"), ("volume",), ())),
    ("payment_fees", ("High payment processing costs", "What fee rate would wipe out the platform's contribution?",
                      ("price", "take_rate", "payment_fee_rate"), ("payments",), ("payment",))),
    ("liquidity", ("Low marketplace liquidity", "What happens if listings or requests do not turn into completed "
                   "transactions?", (), ("liquidity",), ())),
    ("seller_churn", ("High seller churn", "What if suppliers leave after their first sales, or take buyers "
                      "off-platform?", (), ("liquidity", "retention"), ())),
    ("support", ("High support costs", "What support cost per transaction would make transactions unprofitable?",
                 ("support_cost", "price", "take_rate"), ("operations", "costs"), ())),
    ("margins", ("Poor margins", "What contribution margin remains after variable costs?",
                 ("price", "take_rate", "delivery_cost"), ("margins", "costs"), ())),
    ("partner", ("Partner dependency", "What if a critical partner changes terms or withdraws?", (),
                 ("partnerships",), ("partner", "banking"))),
    ("regulatory", ("Regulatory constraints", "What if a licence, tax ruling or platform obligation changes the "
                    "model?", (), ("regulatory",), ("regulatory", "tax", "legal"))),
    ("international", ("International payment limitations", "What if customers or sellers abroad cannot pay or be "
                       "paid?", (), ("payments",), ("payment", "payout"))),
    ("capacity", ("Founder capacity limitations", "Does the model need more founder hours than exist?",
                  ("founder_hours_per_week", "hours_required_per_week"), ("operations",), ())),
])
STRESS_INPUTS = ("price", "take_rate", "payment_fee_rate", "fee_bearer", "delivery_cost", "support_cost",
                 "transactions_per_month", "fixed_costs_month", "cac", "new_customers_month",
                 "purchases_per_customer", "founder_hours_per_week", "hours_required_per_week")
RATE_INPUTS = ("take_rate", "payment_fee_rate")

# ----------------------------------------------------------------------------- financial definitions
# key: (name, formula, inputs, fn, kind)
FIN_METRICS: "OrderedDict[str, Tuple[str, str, Tuple[str, ...], Callable, str]]" = OrderedDict([
    ("commission_revenue", ("Commission revenue (platform share of GMV)", "gmv × take_rate", ("gmv", "take_rate"),
                            lambda v: v["gmv"] * v["take_rate"], "money")),
    ("net_revenue", ("Net revenue", "gross_revenue − refunds − discounts", ("gross_revenue", "refunds", "discounts"),
                     lambda v: v["gross_revenue"] - v["refunds"] - v["discounts"], "money")),
    ("realised_take_rate", ("Realised take rate", "net_revenue ÷ gmv", ("net_revenue", "gmv"),
                            lambda v: v["net_revenue"] / v["gmv"], "pct")),
    ("aov", ("Average order value", "gmv ÷ orders", ("gmv", "orders"), lambda v: v["gmv"] / v["orders"], "money")),
    ("revenue_per_transaction", ("Revenue per transaction", "net_revenue ÷ transactions",
                                 ("net_revenue", "transactions"), lambda v: v["net_revenue"] / v["transactions"],
                                 "money")),
    ("revenue_per_customer", ("Average revenue per customer", "net_revenue ÷ customers", ("net_revenue", "customers"),
                              lambda v: v["net_revenue"] / v["customers"], "money")),
    ("recurring_share", ("Recurring revenue share", "recurring_revenue ÷ net_revenue",
                         ("recurring_revenue", "net_revenue"), lambda v: v["recurring_revenue"] / v["net_revenue"],
                         "pct")),
    ("gross_margin", ("Gross margin", "(net_revenue − direct_costs) ÷ net_revenue", ("net_revenue", "direct_costs"),
                      lambda v: (v["net_revenue"] - v["direct_costs"]) / v["net_revenue"], "pct")),
    ("contribution_margin", ("Contribution margin", "(net_revenue − variable_costs) ÷ net_revenue",
                             ("net_revenue", "variable_costs"),
                             lambda v: (v["net_revenue"] - v["variable_costs"]) / v["net_revenue"], "pct")),
    ("payment_processing_cost", ("Payment processing cost", "payment_volume × payment_fee_rate",
                                 ("payment_volume", "payment_fee_rate"),
                                 lambda v: v["payment_volume"] * v["payment_fee_rate"], "money")),
    ("refund_rate", ("Refund rate", "refunded_orders ÷ orders", ("refunded_orders", "orders"),
                     lambda v: v["refunded_orders"] / v["orders"], "pct")),
    ("seller_earnings", ("Seller earnings", "gmv − commission_revenue − seller_fees",
                         ("gmv", "commission_revenue", "seller_fees"),
                         lambda v: v["gmv"] - v["commission_revenue"] - v["seller_fees"], "money")),
])
FIN_DISTINCTIONS = [
    ("GMV", "Platform revenue", "GMV is the total value buyers pay for completed transactions. Platform revenue is "
                                "only the share the platform keeps (commission or fees), unless the platform is the "
                                "principal and recognises gross revenue; even then GMV is not profit."),
    ("Revenue", "Cash received", "Revenue is recognised when value is delivered. Cash can arrive earlier "
                                 "(prepayments) or later (settlement delays, refund holds)."),
    ("Gross revenue", "Net revenue", "Net revenue deducts refunds, discounts and chargebacks from gross revenue."),
    ("Revenue", "Profit", "Profit deducts direct, variable and fixed costs from revenue."),
    ("Seller earnings", "Platform earnings", "Seller earnings are GMV minus the platform's commission and any fees "
                                             "the seller bears; they are a liability until paid out, not platform "
                                             "income."),
    ("Bookings", "Recognised revenue", "Bookings are the value of signed commitments; revenue is recognised as the "
                                       "service is delivered. Letters of intent and verbal agreements are neither."),
]


# ----------------------------------------------------------------------------- loading and context
def load_spec(path: str) -> Dict:
    with open(path) as f:
        try:
            spec = yaml.safe_load(f) or {}
        except yaml.YAMLError as e:
            raise ValueError(f"{path} is not valid YAML ({str(e).splitlines()[0]}). Quote text that contains "
                             "commas, colons or [E-001] citations inside [flow, lists].\n" + str(e)) from None
    if not isinstance(spec, dict) or "design" not in spec:
        raise ValueError("business model spec must be a YAML mapping with a 'design' section")
    return spec


def context(spec: Dict, base: str):
    """Ledger, profile.yaml and profile dir: the same resolution as the GTM and discovery engines."""
    return gtm.resolve_context({"gtm": spec.get("design", {}) or {}}, base)


def discovery_context(spec: Dict, base: str) -> Tuple[Optional[Dict], List[Dict]]:
    """Analyse the linked customer-discovery spec, if any (read-only: never records)."""
    p = (spec.get("design", {}) or {}).get("discovery")
    if not p:
        return None, []
    p = p if os.path.isabs(p) else os.path.normpath(os.path.join(base, p))
    if not os.path.exists(p):
        return None, [_issue("error", "discovery", f"linked discovery spec not found: {p}")]
    try:
        return cd.analyze(p), []
    except ValueError as e:
        return None, [_issue("error", "discovery", f"linked discovery spec could not be read: {e}")]


def segments_of(spec: Dict, drep: Optional[Dict]) -> List[Dict]:
    segs = spec.get("segments")
    if segs is None and drep is not None:
        segs = drep["_spec"].get("segments", [])
    return [s for s in (segs or []) if isinstance(s, dict)]


def _info(eid: str, ledger: Ledger) -> Dict:
    """Ledger entry facts, shared with the discovery engine (customer evidence, commitment signals)."""
    i = cd._entry_info(eid, ledger)
    if i.get("exists"):
        i["measured"] = i["valid"] and (i["source"] == "dataset" or i["signal"] in ("observed", "paid"))
        i["founder_only"] = i["source"] == "founder"
    return i


def _status(ids: List[str], ledger: Ledger, default: str = "") -> str:
    sts = [ledger.get(i).status for i in ids if ledger.get(i)]
    return _worst(sts) if sts else default


def _num(x) -> Optional[float]:
    v = _val(x)
    if v in (None, "", "unknown"):
        return None
    if isinstance(v, bool):
        return None
    try:
        return float(v)
    except (TypeError, ValueError):
        return None


def _input_status(item: Any, ledger: Ledger) -> str:
    return gtm._status_of(item, ledger)


def _walk_keys(o, keys, path="") -> List[str]:
    """Paths of mapping keys (anywhere below o) that are in `keys`."""
    out = []
    if isinstance(o, dict):
        for k, v in o.items():
            p = f"{path}.{k}" if path else str(k)
            if str(k).lower() in keys:
                out.append(p)
            out += _walk_keys(v, keys, p)
    elif isinstance(o, list):
        for n, v in enumerate(o):
            out += _walk_keys(v, keys, f"{path}[{n}]")
    return out


def _strings(o) -> List[str]:
    if isinstance(o, str):
        return [o]
    if isinstance(o, dict):
        return [s for v in o.values() for s in _strings(v)]
    if isinstance(o, list):
        return [s for v in o for s in _strings(v)]
    return []


def split_values(o, path: str = "") -> List[str]:
    """Paths of keys with no value: usually an unquoted comma inside a YAML {flow: mapping} that split a value.

    `{why: Payments, settlement and disputes}` parses as {'why': 'Payments', 'settlement and disputes': None}:
    the text is silently cut. Keys with spaces or digits are almost always this mistake.
    """
    out = []
    if isinstance(o, dict):
        for k, v in o.items():
            p = f"{path}.{k}" if path else str(k)
            if v is None:
                out.append(p)
            else:
                out += split_values(v, p)
    elif isinstance(o, list):
        for n, v in enumerate(o):
            out += split_values(v, f"{path}[{n}]")
    return out


# ----------------------------------------------------------------------------- canvas items
QUOTE_IN_ITEM_RE = re.compile(r"[\"“]([^\"”]{12,})[\"”]")


def check_item(item: Any, where: str, ledger: Ledger, customer_facing: bool,
               hyp_ids: Optional[set] = None) -> Tuple[Dict, List[Dict]]:
    """Normalise one canvas / value-map item and enforce its basis label."""
    issues: List[Dict] = []
    if isinstance(item, str):
        item = {"text": item}
    if not isinstance(item, dict):
        return {"text": str(item), "basis": "unknown", "evidence": [], "status": ""}, [
            _issue("error", "canvas", f"{where}: item must be text or a mapping")]
    text = _text(item.get("text"))
    basis = item.get("basis")
    ids = _ids(item.get("evidence"))
    con = _ids(item.get("contradicting"))
    if not text:
        issues.append(_issue("error", "canvas", f"{where}: item has no text"))
    if basis not in BASES:
        issues.append(_issue("error", "canvas", f"{where}: '{text[:50]}' needs basis: "
                                                f"{' | '.join(BASES)} (never leave evidence and assumption unlabelled)"))
        basis = "unknown" if basis is None else basis
    infos = [_info(i, ledger) for i in ids]
    existing = [i for i in infos if i.get("exists")]
    if basis == "evidence":
        if not ids:
            issues.append(_issue("error", "canvas", f"{where}: '{text[:50]}' is labelled evidence but cites no ledger "
                                                    "entry"))
        bad = [i for i in existing if not i["valid"]]
        if bad:
            issues.append(_issue("error", "canvas", f"{where}: '{text[:50]}' is labelled evidence but cites "
                                                    f"{', '.join(i['id'] + ' (' + i['status'] + ')' for i in bad)}; "
                                                    "label it hypothesis or founder"))
        if existing and all(i["founder_only"] for i in existing):
            issues.append(_issue("error", "canvas", f"{where}: '{text[:50]}' rests only on founder statements; a "
                                                    "founder's opinion is basis 'founder', not evidence"))
        elif customer_facing and existing and not any(i["customer"] and i["valid"] for i in existing):
            issues.append(_issue("error", "canvas", f"{where}: '{text[:50]}' is customer-facing; 'evidence' needs "
                                                    "customer evidence (interview, dataset, or an observed, committed "
                                                    "or paid signal). Desk research and founder belief are "
                                                    "'hypothesis' or 'founder'"))
    if basis == "hypothesis" and item.get("hypothesis") and hyp_ids is not None:
        for h in _ids(item.get("hypothesis")):
            if h not in hyp_ids:
                issues.append(_issue("error", "canvas", f"{where}: hypothesis {h} is not in the discovery register"))
    if basis == "recommendation" and not _text(item.get("rationale")):
        issues.append(_issue("warning", "canvas", f"{where}: recommendation '{text[:50]}' has no rationale"))
    m = QUOTE_IN_ITEM_RE.search(text)
    if m and not any(i.get("source") == "interview" and i["valid"] for i in existing):
        issues.append(_issue("error", "canvas", f"{where}: quotation '{m.group(1)[:50]}' is not attributed to an "
                                                "interview in the ledger; never invent customer quotes"))
    for i in [_info(c, ledger) for c in con]:
        if i.get("exists"):
            issues.append(_issue("warning", "canvas", f"{where}: '{text[:50]}' has contradicting evidence {i['id']}; "
                                                      "it stays visible in every output"))
    out = {"text": text, "basis": basis, "evidence": ids, "contradicting": con,
           "status": _status(ids, ledger), "hypothesis": _ids(item.get("hypothesis")),
           "rationale": _text(item.get("rationale")), "segment": item.get("segment"), "id": item.get("id")}
    return out, issues


def canvas_check(canvas: Any, ledger: Ledger, hyp_ids: Optional[set] = None) -> Tuple[Dict, List[Dict]]:
    """All nine blocks: items with basis labels; empty or missing blocks are errors."""
    issues: List[Dict] = []
    blocks: "OrderedDict[str, Dict]" = OrderedDict()
    canvas = canvas or {}
    if not isinstance(canvas, dict):
        return {}, [_issue("error", "canvas", "canvas must be a mapping of the nine blocks")]
    for k in canvas:
        if k not in BLOCKS:
            issues.append(_issue("error", "canvas", f"unknown canvas block '{k}'; blocks: {', '.join(BLOCKS)}"))
    for key, label in BLOCKS.items():
        raw = canvas.get(key)
        rationale = ""
        if isinstance(raw, dict):
            rationale = _text(raw.get("rationale"))
            raw = raw.get("items")
        items = []
        for n, it in enumerate(raw or [], 1):
            norm, iss = check_item(it, f"{label} #{n}", ledger, key in CUSTOMER_BLOCKS, hyp_ids)
            items.append(norm)
            issues += iss
        if not items:
            issues.append(_issue("error", "canvas", f"block '{label}' is missing; record what is known, or an item "
                                                    "with basis 'unknown'"))
        counts = OrderedDict((b, sum(1 for i in items if i["basis"] == b)) for b in BASES)
        if items and counts["unknown"] == len(items):
            issues.append(_issue("warning", "canvas", f"block '{label}' is entirely unknown"))
        blocks[key] = {"key": key, "label": label, "items": items, "rationale": rationale, "counts": counts}
    return blocks, issues


# ----------------------------------------------------------------------------- value proposition canvas
def _vpc_items(raw, prefix: str, where: str, ledger: Ledger, hyp_ids, customer_facing: bool = True
               ) -> Tuple[List[Dict], List[Dict]]:
    """Profile items and value-map claims are customer-facing; a product's existence is not (code proves it)."""
    out, issues = [], []
    for n, it in enumerate(raw or [], 1):
        norm, iss = check_item(it, f"{where} {prefix}{n}", ledger, customer_facing, hyp_ids)
        norm["id"] = str((it.get("id") if isinstance(it, dict) else None) or f"{prefix}{n}")
        norm["addresses"] = _ids(it.get("addresses")) if isinstance(it, dict) else []
        norm["severity"] = it.get("severity") if isinstance(it, dict) else None
        out.append(norm)
        issues += [dict(i, area="value-proposition") for i in iss]
    return out, issues


def value_proposition_check(spec: Dict, ledger: Ledger, seg_ids: set, hyp_ids: Optional[set] = None
                            ) -> Tuple[List[Dict], List[Dict]]:
    issues: List[Dict] = []
    out = []
    seen = set()
    for n, v in enumerate(spec.get("value_propositions", []) or [], 1):
        seg = str(v.get("segment", ""))
        where = f"VPC {seg or n}"
        if not seg:
            issues.append(_issue("error", "value-proposition", f"{where}: each canvas belongs to one segment"))
        elif seg_ids and seg not in seg_ids:
            issues.append(_issue("error", "value-proposition", f"{where}: unknown segment '{seg}'"))
        if seg in seen:
            issues.append(_issue("warning", "value-proposition", f"{where}: two canvases for one segment; merge them"))
        seen.add(seg)
        prof = v.get("customer_profile", v)
        vmap = v.get("value_map", v)
        jobs, i1 = _vpc_items(prof.get("jobs"), "J", where, ledger, hyp_ids)
        pains, i2 = _vpc_items(prof.get("pains"), "P", where, ledger, hyp_ids)
        gains, i3 = _vpc_items(prof.get("gains"), "G", where, ledger, hyp_ids)
        products, i4 = _vpc_items(vmap.get("products"), "S", where, ledger, hyp_ids, customer_facing=False)
        relievers, i5 = _vpc_items(vmap.get("pain_relievers"), "R", where, ledger, hyp_ids)
        creators, i6 = _vpc_items(vmap.get("gain_creators"), "C", where, ledger, hyp_ids)
        issues += i1 + i2 + i3 + i4 + i5 + i6
        if not jobs:
            issues.append(_issue("warning", "value-proposition", f"{where}: no customer jobs"))
        if not pains and not gains:
            issues.append(_issue("error", "value-proposition", f"{where}: a customer profile needs pains or gains"))
        if not products:
            issues.append(_issue("warning", "value-proposition", f"{where}: value map lists no products or services"))
        pain_ids = {p["id"] for p in pains}
        gain_ids = {g["id"] for g in gains}
        for r in relievers:
            for a in r["addresses"]:
                if a not in pain_ids:
                    issues.append(_issue("error", "value-proposition", f"{where}: pain reliever {r['id']} addresses "
                                                                       f"unknown pain '{a}'"))
            if not r["addresses"]:
                issues.append(_issue("warning", "value-proposition", f"{where}: pain reliever {r['id']} names no "
                                                                     "pain (addresses: [P1])"))
        for c in creators:
            for a in c["addresses"]:
                if a not in gain_ids:
                    issues.append(_issue("error", "value-proposition", f"{where}: gain creator {c['id']} addresses "
                                                                       f"unknown gain '{a}'"))
        addressed_p = {a for r in relievers for a in r["addresses"]} & pain_ids
        addressed_g = {a for c in creators for a in c["addresses"]} & gain_ids
        ev_profile = [x for x in jobs + pains + gains if x["basis"] == "evidence"]
        ev_pains_addr = [p for p in pains if p["id"] in addressed_p and p["basis"] == "evidence"]
        ev_value = [x for x in relievers + creators if x["basis"] == "evidence"]
        if not ev_profile:
            verdict = "Conceptual fit only: no customer evidence for jobs, pains or gains"
        elif not ev_pains_addr:
            verdict = "Customer evidence exists, but no evidence-backed pain is addressed by the value map"
        elif not ev_value:
            verdict = (f"Problem side evidenced: {len(ev_pains_addr)} of {len(addressed_p)} addressed pains are "
                       "backed by customer evidence; the value map is untested")
        else:
            verdict = (f"Early evidence of fit: {len(ev_pains_addr)} addressed pains and {len(ev_value)} value-map "
                       "items backed by customer evidence")
        out.append({"segment": seg, "jobs": jobs, "pains": pains, "gains": gains, "products": products,
                    "relievers": relievers, "creators": creators,
                    "unaddressed_pains": [p["id"] for p in pains if p["id"] not in addressed_p],
                    "unaddressed_gains": [g["id"] for g in gains if g["id"] not in addressed_g],
                    "evidence_items": len(ev_profile) + len(ev_value), "verdict": verdict})
    for s in seg_ids:
        if s not in seen and spec.get("value_propositions"):
            issues.append(_issue("info", "value-proposition", f"segment {s} has no value proposition canvas"))
    return out, issues


# ----------------------------------------------------------------------------- classification
def _requirements(ctx: Dict) -> Dict[str, List[Tuple[str, bool]]]:
    mech = ctx["mechanisms"]
    acat = ctx["assumption_categories"]
    dtype = ctx["dependency_types"]
    ctype = ctx["cost_types"]
    has_mk = ctx["marketplace"]
    pay = bool({"payment", "payout"} & dtype)
    return {
        "marketplace": [("marketplace section (sides, matching, liquidity)", has_mk),
                        ("liquidity assumption", "liquidity" in acat),
                        ("payment collection and payout dependency", pay)],
        "commission": [("commission or transaction-fee revenue stream", bool({"commission", "transaction-fee"} & mech)),
                       ("payment dependency", pay), ("payment-processing cost", "payment-processing" in ctype)],
        "transaction": [("transaction-fee or commission revenue stream",
                         bool({"commission", "transaction-fee"} & mech)), ("payment dependency", pay),
                        ("payment-processing cost", "payment-processing" in ctype)],
        "saas": [("recurring revenue stream", bool({"subscription", "tiered"} & mech)),
                 ("retention assumption", "retention" in acat)],
        "subscription": [("subscription revenue stream", bool({"subscription", "tiered"} & mech)),
                         ("retention assumption", "retention" in acat)],
        "freemium": [("paid upgrade stream", bool({"subscription", "tiered", "one-time"} & mech)),
                     ("free-to-paid conversion assumption", bool({"pricing", "wtp"} & acat))],
        "advertising": [("advertising revenue stream", "advertising" in mech),
                        ("audience volume assumption", "volume" in acat)],
        "usage-based": [("usage revenue stream", "usage" in mech)],
        "licensing": [("licensing revenue stream", "licensing" in mech)],
        "services": [("service-fee revenue stream", "service-fee" in mech),
                     ("delivery capacity assumption", "operations" in acat)],
        "consulting": [("service-fee revenue stream", "service-fee" in mech),
                       ("delivery capacity assumption", "operations" in acat)],
        "ecommerce": [("one-time sales stream", bool({"one-time", "bundle"} & mech)),
                      ("direct delivery cost", "delivery" in ctype)],
        "digital-products": [("one-time, bundle or subscription stream", bool({"one-time", "bundle", "subscription"}
                                                                               & mech))],
        "education": [("one-time, bundle or subscription stream", bool({"one-time", "bundle", "subscription",
                                                                        "commission"} & mech))],
        "direct-sales": [("acquisition cost", "acquisition" in ctype)],
        "hybrid": [("at least two revenue mechanisms", len(mech) >= 2)],
    }


def classify(types: List[str], ctx: Optional[Dict] = None) -> Tuple[Dict, List[Dict]]:
    """Validate model types; report the structural requirements each type implies."""
    issues: List[Dict] = []
    types = [str(t) for t in types or []]
    unknown = [t for t in types if t not in BM_TYPES]
    for t in unknown:
        issues.append(_issue("error", "classification", f"unknown business model type '{t}'; choose from "
                                                        f"{', '.join(BM_TYPES)}"))
    known = [t for t in types if t in BM_TYPES]
    revenue = [t for t in known if BM_TYPES[t][1] == "revenue"]
    orient = [t for t in known if BM_TYPES[t][1] == "orientation"]
    families = {REVENUE_FAMILY[t] for t in revenue}
    hybrid = len(families) >= 2 or "hybrid" in known or ("marketplace" in known and "saas" in known)
    if not orient and known:
        issues.append(_issue("warning", "classification", "say who the model serves: add b2b, b2c or b2b2c"))
    if "hybrid" in known and len(families) < 2:
        issues.append(_issue("warning", "classification", "'hybrid' needs at least two revenue model types"))
    reqs = []
    if ctx is not None:
        table = _requirements(ctx)
        for t in known:
            for label, ok in table.get(t, []):
                reqs.append({"type": t, "requirement": label, "met": ok})
                if not ok:
                    issues.append(_issue("warning", "classification", f"{BM_TYPES[t][0]} model: {label} is missing"))
    return {"types": known, "labels": [BM_TYPES[t][0] for t in known], "revenue_models": revenue,
            "orientation": orient, "hybrid": hybrid, "requirements": reqs}, issues


# ----------------------------------------------------------------------------- dependencies and payments
PROVIDER_RE = re.compile(r"\b(stripe|paypal|braintree|adyen|razorpay|payoneer|wise|international card acquiring|"
                         r"card acquiring|visa|mastercard|apple pay|google pay)\b", re.I)
QR_RE = re.compile(r"\b(QR|UPI)\b", re.I)
VISITOR_RE = re.compile(r"\b(tourists?|visitors?|travell?ers?|in[- ]person|point of sale|at (?:the )?(?:shop|counter|"
                        r"merchant)|Indian (?:users|visitors|travell?ers)|foreign visitors?)\b", re.I)
ONLINE_RE = re.compile(r"\b(online|e-?commerce|checkout|marketplace|creators?|sellers?|payouts?|settle\w*|"
                       r"international (?:cards?|payments?)|global (?:buyers|learners|customers))\b", re.I)
QR_NEG_RE = re.compile(r"\b(not|cannot|can't|isn't|doesn't|does not|do not|no|only|unlike|distinct|different|"
                       r"confus\w*|separate|never|unrelated|≠)\b", re.I)
SENT_SPLIT_RE = re.compile(r"(?<=[.!?])\s+|\n+")


def qr_confusion(text: str) -> List[str]:
    """Sentences that use in-person cross-border QR acceptance as if it enabled international online payments."""
    out = []
    for s in SENT_SPLIT_RE.split(text or ""):
        if QR_RE.search(s) and VISITOR_RE.search(s) and ONLINE_RE.search(s) and not QR_NEG_RE.search(s):
            out.append(s.strip())
    return out


def dependencies_check(spec: Dict, ledger: Ledger, geos: List[str]) -> Tuple[List[Dict], List[Dict]]:
    issues: List[Dict] = []
    out = []
    ids = set()
    nepal = any("nepal" in str(g).lower() for g in geos)
    for d in spec.get("dependencies", []) or []:
        did = str(d.get("id", "?"))
        ids.add(did)
        typ, st = d.get("type"), d.get("status", "unverified")
        ev = _ids(d.get("evidence"))
        infos = [_info(i, ledger) for i in ev]
        if typ not in DEP_TYPES:
            issues.append(_issue("error", "dependencies", f"{did}: type must be one of {', '.join(DEP_TYPES)}"))
        if st not in DEP_STATUSES:
            issues.append(_issue("error", "dependencies", f"{did}: status must be one of {', '.join(DEP_STATUSES)}"))
        if not _text(d.get("name")):
            issues.append(_issue("error", "dependencies", f"{did}: name is required"))
        if st == "verified":
            if not any(i.get("exists") and i["valid"] for i in infos):
                issues.append(_issue("error", "dependencies", f"{did}: marked verified without verified or reported "
                                                              "evidence (a provider contract, approval letter, live "
                                                              "test or official document)"))
            if typ in ("regulatory", "tax", "legal") and not _text(d.get("confirmed_by")):
                issues.append(_issue("error", "dependencies", f"{did}: a {typ} dependency is verified only when a "
                                                              "qualified adviser, the regulator or the provider "
                                                              "confirmed it (confirmed_by)"))
        else:
            if not _text(d.get("question")):
                issues.append(_issue("warning", "dependencies", f"{did}: state the open question to confirm"))
            cw = _ids(d.get("confirm_with"))
            if not cw:
                issues.append(_issue("warning", "dependencies", f"{did}: name who must confirm it (confirm_with: "
                                                                f"{', '.join(ADVISERS)})"))
            for c in cw:
                if c not in ADVISERS:
                    issues.append(_issue("warning", "dependencies", f"{did}: unusual confirm_with '{c}'"))
        for s in qr_confusion(" ".join(_strings(d))):
            issues.append(_issue("error", "payments", f"{did}: in-person cross-border QR acceptance (visitors paying "
                                                      "local merchants) is not international online checkout or "
                                                      f"seller settlement: '{s[:90]}'"))
        out.append({"id": did, "name": _text(d.get("name")), "type": typ, "status": st,
                    "country": d.get("country"), "provider": _text(d.get("provider")), "evidence": ev,
                    "evidence_status": _status(ev, ledger), "question": _text(d.get("question")),
                    "confirm_with": _ids(d.get("confirm_with")), "confirmed_by": _text(d.get("confirmed_by")),
                    "blocks": _ids(d.get("blocks")), "spec": d})
    # every payment provider named anywhere must be registered as a dependency
    named = {}
    for s in _strings({k: v for k, v in spec.items() if k != "dependencies"}):
        for m in PROVIDER_RE.finditer(s):
            named.setdefault(m.group(1).lower(), s)
    dep_text = " ".join(_strings(spec.get("dependencies", []) or [])).lower()
    for p, s in named.items():
        if p not in dep_text:
            issues.append(_issue("error", "payments", f"'{p}' is named in the spec but its availability is not "
                                                      "registered as a dependency; never assume a payment provider is "
                                                      f"available in a country: '{s[:80]}'"))
    for s in qr_confusion(" ".join(_strings({k: v for k, v in spec.items() if k != "dependencies"}))):
        issues.append(_issue("error", "payments", "in-person cross-border QR acceptance is not international online "
                                                  f"checkout or seller settlement: '{s[:90]}'"))
    if nepal:
        intl = [d for d in out if PROVIDER_RE.search(d["name"] + " " + d["provider"])]
        for d in intl:
            if d["status"] == "verified" and d["country"] and "nepal" in str(d["country"]).lower():
                issues.append(_issue("warning", "payments", f"{d['id']}: {d['name']} verified for Nepal; make sure "
                                                            "the evidence is the provider's own confirmation for a "
                                                            "Nepal-registered entity"))
    return out, issues


# ----------------------------------------------------------------------------- revenue streams
def revenue_check(spec: Dict, ledger: Ledger, seg_ids: set, deps: List[Dict]) -> Tuple[List[Dict], List[Dict]]:
    issues: List[Dict] = []
    out = []
    dep_by_id = {d["id"]: d for d in deps}
    cur = (spec.get("design", {}) or {}).get("currency", "")
    for s in spec.get("revenue_streams", []) or []:
        sid = str(s.get("id", "?"))
        where = f"{sid} {_text(s.get('name'))}".strip()
        for f in ("name", "payer", "value", "mechanism", "billing", "stage"):
            if not s.get(f):
                issues.append(_issue("error", "revenue", f"{where}: '{f}' is required"))
        mech, stage = s.get("mechanism"), s.get("stage", "proposed")
        if mech and mech not in MECHANISMS:
            issues.append(_issue("error", "revenue", f"{where}: mechanism must be one of {', '.join(MECHANISMS)}"))
        if stage not in STREAM_STAGES:
            issues.append(_issue("error", "revenue", f"{where}: stage must be one of {', '.join(STREAM_STAGES)}"))
        payer = str(s.get("payer", ""))
        if seg_ids and payer and payer not in seg_ids:
            issues.append(_issue("error", "revenue", f"{where}: payer '{payer}' is not a segment id"))
        for f in ("structure", "recognition", "risks"):
            if not s.get(f):
                issues.append(_issue("warning", "revenue", f"{where}: describe '{f}'"))
        ev = _ids(s.get("evidence"))
        infos = [i for i in (_info(x, ledger) for x in ev) if i.get("exists")]
        # price and take rate: hypotheses unless evidenced
        price = s.get("price")
        p_val = _num(price)
        p_status = _input_status(price, ledger) if price is not None else ""
        if price is not None and p_val is None and _val(price) not in (None, "", "unknown"):
            issues.append(_issue("error", "revenue", f"{where}: price is not a number: {_val(price)!r}"))
        if p_val is not None and isinstance(price, dict) and not (price.get("evidence") or price.get("status")):
            issues.append(_issue("warning", "revenue", f"{where}: price has neither evidence nor status; treated as "
                                                       "an assumption"))
        tr = s.get("take_rate")
        tr_val = _num(tr)
        if mech in ("commission", "transaction-fee"):
            if tr_val is None and _num(s.get("fee")) is None:
                issues.append(_issue("error", "revenue", f"{where}: a {mech} stream needs take_rate (0–1) or a fee"))
        if tr_val is not None and not 0 < tr_val < 1:
            issues.append(_issue("error", "revenue", f"{where}: take_rate {tr_val} must be between 0 and 1"))
        # stage gates
        order = list(STREAM_STAGES)
        k = order.index(stage) if stage in order else 0
        cust = [i for i in infos if i["customer"] and i["valid"]]
        paid = [i for i in infos if i["signal"] == "paid" and i["valid"]]
        rev = s.get("revenue")
        rev_val = _num(rev)
        rev_status = _input_status(rev, ledger) if rev is not None else ""
        if k >= 1 and not cust:
            issues.append(_issue("error", "revenue", f"{where}: stage '{stage}' needs customer evidence that the offer "
                                                     "was put in front of customers (interview, dataset or a signal); "
                                                     "a proposed price is not a test"))
        if k >= 2:
            sdeps = _ids(s.get("dependencies"))
            unverified = [d for d in sdeps if d in dep_by_id and dep_by_id[d]["status"] != "verified"]
            if unverified:
                issues.append(_issue("error", "revenue", f"{where}: stage '{stage}' but dependencies "
                                                         f"{', '.join(unverified)} are not verified; customers "
                                                         "cannot reliably pay yet"))
            if not any(i["valid"] and not i["founder_only"] for i in infos):
                issues.append(_issue("error", "revenue", f"{where}: stage '{stage}' needs verified or reported "
                                                         "evidence that customers can pay today (live checkout)"))
        if k >= 3 and not paid and not (rev_val is not None and rev_status in VALID):
            issues.append(_issue("error", "revenue", f"{where}: stage '{stage}' needs paid evidence (signal: paid) or "
                                                     "measured revenue with verified or reported evidence"))
        if k >= 4:
            rep_ev = [_info(x, ledger) for x in _ids(s.get("repeat_evidence"))]
            if not any(i.get("exists") and i["valid"] and i["measured"] for i in rep_ev):
                issues.append(_issue("error", "revenue", f"{where}: 'repeatable' needs measured repeat or retained "
                                                         "payments (repeat_evidence: dataset or paid signal)"))
        if rev is not None and k < 3:
            issues.append(_issue("error", "revenue", f"{where}: a '{stage}' stream cannot report revenue; proposed "
                                                     "pricing is not actual revenue"))
        if rev is not None and rev_val is not None and rev_status not in VALID:
            issues.append(_issue("error", "revenue", f"{where}: revenue {rev_val:g} is '{rev_status}'; revenue must be "
                                                     "measured (verified or reported), never assumed"))
        recog = str(s.get("recognition", "") or "")
        if mech in ("commission", "transaction-fee") and re.search(r"\bgross\b", recog, re.I):
            issues.append(_issue("warning", "revenue", f"{where}: gross recognition treats the platform as principal "
                                                       "(seller of record); confirm with an accountant. GMV is still "
                                                       "not the platform's share or its profit"))
        for d in _ids(s.get("dependencies")):
            if deps and d not in dep_by_id:
                issues.append(_issue("error", "revenue", f"{where}: dependency '{d}' is not in the dependency list"))
        if mech and mech not in ("advertising",) and not _ids(s.get("dependencies")):
            issues.append(_issue("warning", "revenue", f"{where}: no payment dependency linked; how is money "
                                                       "collected?"))
        p_disp = "not set"
        if p_val is not None:
            pc = (price.get("currency") if isinstance(price, dict) else None) or cur
            p_disp = f"{gtm.fmt_value(p_val, 'money', pc)} ({p_status or 'assumption'})"
        out.append({"id": sid, "name": _text(s.get("name")), "payer": payer, "value": _text(s.get("value")),
                    "mechanism": mech, "billing": _text(s.get("billing")), "structure": _text(s.get("structure")),
                    "recognition": recog, "dependencies": _ids(s.get("dependencies")), "stage": stage,
                    "price": p_val, "price_status": p_status, "price_display": p_disp, "take_rate": tr_val,
                    "take_rate_status": _input_status(tr, ledger) if tr is not None else "",
                    "evidence": ev, "evidence_status": _status(ev, ledger, "none"), "risks": _text(s.get("risks")),
                    "revenue": rev_val if k >= 3 else None, "spec": s})
    if not out:
        issues.append(_issue("warning", "revenue", "no revenue streams defined"))
    return out, issues


# ----------------------------------------------------------------------------- costs
def costs_check(spec: Dict, ledger: Ledger, types: List[str]) -> Tuple[Dict, List[Dict]]:
    issues: List[Dict] = []
    rows = []
    cur = (spec.get("design", {}) or {}).get("currency", "")
    for c in spec.get("costs", []) or []:
        cid = str(c.get("id", "?"))
        where = f"{cid} {_text(c.get('name'))}".strip()
        cat, typ = c.get("category"), c.get("type")
        if cat not in COST_CATEGORIES:
            issues.append(_issue("error", "costs", f"{where}: category must be fixed, variable or semi-variable"))
        if typ not in COST_TYPES:
            issues.append(_issue("warning", "costs", f"{where}: type should be one of {', '.join(COST_TYPES)}"))
        amt = c.get("amount")
        val = _num(amt)
        st = ""
        if amt is not None and val is None and _val(amt) not in (None, "", "unknown"):
            issues.append(_issue("error", "costs", f"{where}: amount is not a number: {_val(amt)!r}"))
        if val is not None:
            if val < 0:
                issues.append(_issue("error", "costs", f"{where}: amount is negative"))
            st = _input_status(amt, ledger)
            if isinstance(amt, dict) and not (amt.get("evidence") or amt.get("status")):
                issues.append(_issue("error", "costs", f"{where}: a numeric cost needs evidence or a status "
                                                       "(estimate, assumption); never present a guess as known"))
            if st == "estimate" and not (_ids(amt.get("evidence")) if isinstance(amt, dict) else []) and not _text(
                    amt.get("basis") if isinstance(amt, dict) else None):
                issues.append(_issue("error", "costs", f"{where}: an estimate needs its source or calculation "
                                                       "(basis)"))
            if not (isinstance(amt, dict) and amt.get("unit")):
                issues.append(_issue("error", "costs", f"{where}: amount needs a unit (e.g. per month, per transaction, "
                                                       "share of payment)"))
        if cat == "variable" and not _text(c.get("driver")):
            issues.append(_issue("warning", "costs", f"{where}: a variable cost needs its driver (what makes it grow)"))
        unit = str((amt or {}).get("unit", "") if isinstance(amt, dict) else "")
        rows.append({"id": cid, "name": _text(c.get("name")), "category": cat, "type": typ,
                     "driver": _text(c.get("driver")), "value": val, "unit": unit, "status": st if val is not None
                     else "unknown", "basis": _text((amt or {}).get("basis") if isinstance(amt, dict) else ""),
                     "evidence": _ids(amt.get("evidence")) if isinstance(amt, dict) else [],
                     "known": val is not None, "notes": _text(c.get("notes"))})
    fixed_month = [r for r in rows if r["category"] == "fixed" and r["known"] and "month" in r["unit"].lower()]
    pct = [r for r in rows if r["category"] == "variable" and r["known"] and re.search(r"share|%|percent|rate",
                                                                                      r["unit"], re.I)]
    per_tx = [r for r in rows if r["category"] == "variable" and r["known"] and re.search(
        r"per (transaction|order|sale|unit|purchase)", r["unit"], re.I)]
    for r in pct:
        if not 0 <= r["value"] <= 1:
            issues.append(_issue("error", "costs", f"{r['id']}: a share-of-payment cost must be between 0 and 1"))
    totals = {
        "fixed_month": sum(r["value"] for r in fixed_month) if fixed_month else None,
        "fixed_month_status": _worst([r["status"] for r in fixed_month]) if fixed_month else "",
        "fixed_month_items": [r["id"] for r in fixed_month],
        "variable_rate": sum(r["value"] for r in pct) if pct else None,
        "variable_rate_status": _worst([r["status"] for r in pct]) if pct else "",
        "variable_per_tx": sum(r["value"] for r in per_tx) if per_tx else None,
        "variable_per_tx_status": _worst([r["status"] for r in per_tx]) if per_tx else "",
        "unknown": [r["id"] for r in rows if not r["known"]], "currency": cur,
        "excluded_fixed": [r["id"] for r in rows if r["category"] == "fixed" and r["known"] and r not in fixed_month],
    }
    present = {r["type"] for r in rows}
    expected = ["personnel", "acquisition", "infrastructure"]
    if set(types) & {"marketplace", "commission", "transaction", "ecommerce", "education", "digital-products"}:
        expected += ["payment-processing", "support"]
    if "marketplace" in types:
        expected += ["incentives"]
    if set(types) & {"services", "consulting", "ecommerce"}:
        expected += ["delivery"]
    for t in expected:
        if t not in present:
            issues.append(_issue("warning", "costs", f"no '{t}' cost recorded; add it, even as unknown (founder time "
                                                     "is a cost even when unpaid)" if t == "personnel" else
                                                     f"no '{t}' cost recorded; add it, even as unknown"))
    if not rows:
        issues.append(_issue("warning", "costs", "no costs defined"))
    return {"rows": rows, "totals": totals}, issues


# ----------------------------------------------------------------------------- financial architecture
def financials(spec: Dict, ledger: Ledger, extra: Optional[Dict] = None) -> Tuple[List[Dict], List[Dict]]:
    """Compute each definition whose inputs all exist; list formulas and missing inputs otherwise."""
    issues: List[Dict] = []
    raw = dict((spec.get("financials", {}) or {}).get("inputs", {}) or {})
    for k, v in (extra or {}).items():
        raw.setdefault(k, v)
    cur = (spec.get("design", {}) or {}).get("currency", "")
    values, statuses = {}, {}
    for k, item in raw.items():
        v = _num(item)
        if v is None:
            if _val(item) not in (None, "", "unknown"):
                issues.append(_issue("error", "financials", f"input '{k}' is not a number: {_val(item)!r}"))
            continue
        if v < 0:
            issues.append(_issue("error", "financials", f"input '{k}' is negative"))
            continue
        if k in RATE_INPUTS and v > 1:
            issues.append(_issue("error", "financials", f"input '{k}' ({v}) must be a share between 0 and 1"))
            continue
        values[k] = v
        statuses[k] = _input_status(item, ledger)
    types = _types(spec)
    if "revenue" in values and "gmv" in values and values["revenue"] == values["gmv"] and \
            set(types) & {"marketplace", "commission", "transaction"}:
        issues.append(_issue("error", "financials", "revenue equals GMV in a commission or transaction model; GMV is "
                                                    "what buyers pay, platform revenue is the share the platform keeps"))
    if "gross_revenue" in values and "gmv" in values and values["gross_revenue"] == values["gmv"] and \
            "commission" in types and not (spec.get("financials", {}) or {}).get("principal"):
        issues.append(_issue("error", "financials", "gross_revenue equals GMV but the platform is not declared the "
                                                    "principal (financials.principal: true, confirmed by an "
                                                    "accountant)"))
    if "net_revenue" in values and "gmv" in values and values["net_revenue"] > values["gmv"]:
        issues.append(_issue("error", "financials", "net revenue exceeds GMV"))
    rows = []
    for key, (name, formula, inputs, fn, kind) in FIN_METRICS.items():
        missing = [i for i in inputs if i not in values]
        row = {"key": key, "name": name, "formula": formula, "inputs": list(inputs), "missing": missing,
               "value": None, "status": None, "display": ""}
        if key in values:          # supplied directly (e.g. net revenue from accounts)
            row.update(value=values[key], status=statuses[key], formula=f"supplied as '{key}'", missing=[],
                       display=gtm.fmt_value(values[key], kind, cur))
        elif not missing:
            try:
                v = fn(values)
                row.update(value=v, status=_worst([statuses[i] for i in inputs]), display=gtm.fmt_value(v, kind, cur))
                values[key] = v
                statuses[key] = row["status"]
            except ZeroDivisionError:
                row["missing"] = [f"non-zero {i}" for i in inputs]
                row["display"] = "undefined (division by zero)"
        rows.append(row)
    for k in ("cash_received", "bookings", "profit"):
        if k in values:
            rows.append({"key": k, "name": k.replace("_", " ").capitalize(), "formula": f"supplied as '{k}'",
                         "inputs": [k], "missing": [], "value": values[k], "status": statuses[k],
                         "display": gtm.fmt_value(values[k], "money", cur)})
    return rows, issues


def _types(spec: Dict) -> List[str]:
    d = spec.get("design", {}) or {}
    t = d.get("types") or []
    if not t:
        rec = d.get("recommended")
        for a in spec.get("alternatives", []) or []:
            if rec and str(a.get("id")) == str(rec):
                t = a.get("types") or []
    return [str(x) for x in (t if isinstance(t, list) else [t])]


# ----------------------------------------------------------------------------- marketplace
def marketplace_check(spec: Dict, ledger: Ledger, segs: List[Dict], deps: List[Dict], streams: List[Dict]
                      ) -> Tuple[Dict, List[Dict]]:
    mk = spec.get("marketplace")
    types = _types(spec)
    issues: List[Dict] = []
    if not mk:
        if "marketplace" in types:
            issues.append(_issue("error", "marketplace", "a marketplace model needs a 'marketplace' section (sides, "
                                                         "matching, payments, liquidity)"))
        return {}, issues
    seg_by_id = {str(s.get("id")): s for s in segs}
    cfg = mk.get("type")
    if cfg not in MARKETPLACE_CONFIGS:
        issues.append(_issue("error", "marketplace", f"type must be one of {', '.join(MARKETPLACE_CONFIGS)}"))
    sides = []
    for s in mk.get("sides", []) or []:
        seg, role = str(s.get("segment", "")), s.get("role")
        if role not in SIDE_ROLES:
            issues.append(_issue("error", "marketplace", f"side {seg}: role must be supply, demand or third-party"))
        if seg_by_id and seg not in seg_by_id:
            issues.append(_issue("error", "marketplace", f"side {seg}: not a segment id"))
        sg = seg_by_id.get(seg, {})
        if sg.get("side") in ("supply", "demand") and role in ("supply", "demand") and sg["side"] != role:
            issues.append(_issue("error", "marketplace", f"side {seg}: segment is '{sg['side']}' but listed as {role}"))
        for f in ("acquisition", "value", "pays"):
            if not _text(s.get(f)):
                issues.append(_issue("warning", "marketplace", f"side {seg}: describe '{f}'"))
        if s.get("brings_other_side"):
            ev = [_info(i, ledger) for i in _ids(s.get("evidence"))]
            if not (s.get("assumption") or s.get("hypothesis")) and not any(
                    i.get("exists") and i["measured"] for i in ev):
                issues.append(_issue("error", "marketplace", f"side {seg}: 'brings the other side' is an untested "
                                                             "assumption; more supply does not create demand by "
                                                             "itself. Link an assumption or hypothesis, or measured "
                                                             "evidence"))
        sides.append({"segment": seg, "name": _text(sg.get("name")) or seg, "role": role,
                      "acquisition": _text(s.get("acquisition")), "value": _text(s.get("value")),
                      "pays": _text(s.get("pays")), "subsidy": _text(s.get("subsidy")),
                      "brings_other_side": bool(s.get("brings_other_side")),
                      "assumption": _text(s.get("assumption") or s.get("hypothesis"))})
    roles = [s["role"] for s in sides]
    if "supply" not in roles or "demand" not in roles:
        issues.append(_issue("error", "marketplace", "a marketplace needs at least one supply side and one demand side, "
                                                     "modelled separately"))
    if cfg == "three-sided" and len(sides) < 3:
        issues.append(_issue("error", "marketplace", "a three-sided marketplace needs three sides"))
    design_fields = OrderedDict([
        ("matching", "matching mechanism"), ("trust_safety", "trust and safety"),
        ("transaction_flow", "transaction completion flow"), ("leakage", "leakage (disintermediation) defence"),
        ("cold_start", "cold-start strategy"), ("network_effects", "network effects (type and evidence)"),
        ("pricing", "multi-sided pricing (who pays what)")])
    for f, label in design_fields.items():
        if not mk.get(f):
            issues.append(_issue("warning", "marketplace", f"describe {label}"))
    pay = mk.get("payments") or {}
    paid = [s for s in streams if s["mechanism"] in ("commission", "transaction-fee", "one-time", "bundle")]
    for f in ("collection", "payout", "refunds", "disputes", "fee_bearer"):
        if not pay.get(f):
            issues.append(_issue("error" if paid and f in ("collection", "payout") else "warning", "marketplace",
                                 f"payments.{f} is not described"))
    for f in ("collection", "payout"):
        d = pay.get(f)
        if isinstance(d, dict) and d.get("dependency"):
            dep = next((x for x in deps if x["id"] == str(d["dependency"])), None)
            if dep is None:
                issues.append(_issue("error", "marketplace", f"payments.{f}: dependency {d['dependency']} not found"))
    if pay.get("fee_bearer") and pay["fee_bearer"] not in ("platform", "seller", "buyer", "split"):
        issues.append(_issue("error", "marketplace", "payments.fee_bearer must be platform, seller, buyer or split"))
    cs = mk.get("cold_start") or {}
    first = cs.get("first_side") if isinstance(cs, dict) else None
    if first and first not in [s["segment"] for s in sides]:
        issues.append(_issue("error", "marketplace", f"cold_start.first_side '{first}' is not a side"))
    # funnel: measured counts only
    funnel = mk.get("funnel", {}) or {}
    vals, sts = {}, {}
    for k, item in funnel.items():
        if k not in FUNNEL and k not in ("gmv", "platform_revenue", "listings_live", "listings_with_sale"):
            issues.append(_issue("warning", "marketplace", f"unknown funnel stage '{k}'"))
        v = _num(item)
        if v is None:
            continue
        if v < 0:
            issues.append(_issue("error", "marketplace", f"funnel '{k}' is negative"))
            continue
        vals[k], sts[k] = v, _input_status(item, ledger)
    for a, b in FUNNEL_ORDER:
        if a in vals and b in vals and vals[a] > vals[b]:
            issues.append(_issue("error", "marketplace", f"{FUNNEL[a]} ({vals[a]:g}) exceeds {FUNNEL[b].lower()} "
                                                         f"({vals[b]:g})"))
    stages = []
    for k, label in FUNNEL.items():
        measured = k in vals and sts[k] in VALID
        stages.append({"key": k, "label": label, "value": vals.get(k), "status": sts.get(k, "not measured"),
                       "measured": measured})
    if "registered_supply" in vals and "active_supply" not in vals:
        issues.append(_issue("info", "marketplace", "registered supply is recorded but active supply is not; "
                                                    "registrations are not active participants"))
    if "registered_demand" in vals and "active_demand" not in vals:
        issues.append(_issue("info", "marketplace", "registered demand is recorded but active demand is not"))
    if "matches" in vals and "completed_transactions" not in vals:
        issues.append(_issue("info", "marketplace", "matches are recorded but completed transactions are not; a match "
                                                    "is not a completed transaction"))
    ratios = []
    for key, (name, formula, (num, den)) in FUNNEL_RATIOS.items():
        r = {"key": key, "name": name, "formula": formula, "missing": [x for x in (num, den) if x not in vals],
             "value": None, "status": None, "measured": False}
        if not r["missing"] and vals[den]:
            r["value"] = vals[num] / vals[den]
            r["status"] = _worst([sts[num], sts[den]])
            r["measured"] = r["status"] in VALID
        ratios.append(r)
    if "listings_live" in vals and "listings_with_sale" in vals and vals["listings_live"]:
        name, _, formula, _, fn, _ = gtm.METRICS["liquidity"]
        st = _worst([sts["listings_live"], sts["listings_with_sale"]])
        ratios.append({"key": "liquidity", "name": name, "formula": formula, "missing": [], "measured": st in VALID,
                       "value": fn(vals), "status": st})
    # money: GMV vs platform revenue vs seller earnings
    tr_item = mk.get("take_rate")
    tr = _num(tr_item)
    if tr is not None and not 0 < tr < 1:
        issues.append(_issue("error", "marketplace", f"take_rate {tr} must be between 0 and 1"))
        tr = None
    money = {"take_rate": tr, "take_rate_status": _input_status(tr_item, ledger) if tr_item is not None else ""}
    if "gmv" in vals:
        money["gmv"] = vals["gmv"]
        money["gmv_status"] = sts["gmv"]
        if "platform_revenue" in vals:
            if vals["platform_revenue"] > vals["gmv"]:
                issues.append(_issue("error", "marketplace", "platform revenue exceeds GMV"))
            elif vals["gmv"]:
                money["realised_take_rate"] = vals["platform_revenue"] / vals["gmv"]
            money["platform_revenue"] = vals["platform_revenue"]
            money["seller_earnings"] = vals["gmv"] - vals["platform_revenue"]
            money["basis"] = "measured platform revenue"
        elif tr is not None:
            money["platform_revenue"] = vals["gmv"] * tr
            money["seller_earnings"] = vals["gmv"] * (1 - tr)
            money["basis"] = "GMV × design take rate"
        money["status"] = _worst([sts["gmv"]] + ([sts["platform_revenue"]] if "platform_revenue" in vals else
                                                 [money["take_rate_status"] or "assumption"]))
    # liquidity claims need measured completed (and ideally repeat) transactions
    liq = mk.get("liquidity") or {}
    claim = liq.get("status", "not-measured") if isinstance(liq, dict) else "not-measured"
    if claim not in ("not-measured", "not-yet", "emerging", "achieved"):
        issues.append(_issue("error", "marketplace", "liquidity.status must be not-measured, not-yet, emerging or "
                                                     "achieved"))
    if claim in ("emerging", "achieved"):
        ok = any(s["key"] == "completed_transactions" and s["measured"] and s["value"] for s in stages)
        liq_ev = [_info(i, ledger) for i in _ids(liq.get("evidence"))]
        if not ok or not any(i.get("exists") and i["measured"] for i in liq_ev):
            issues.append(_issue("error", "marketplace", f"liquidity claimed '{claim}' without measured completed "
                                                         "transactions and measured liquidity evidence (dataset); "
                                                         "registrations and listings are not liquidity"))
        if claim == "achieved" and not any(r["key"] in ("repeat_rate", "liquidity") and r["measured"]
                                           for r in ratios):
            issues.append(_issue("error", "marketplace", "liquidity 'achieved' needs a measured repeat or sell-through "
                                                         "rate"))
    return {"type": cfg, "sides": sides, "stages": stages, "ratios": ratios, "money": money,
            "liquidity": claim, "payments": pay, "cold_start": cs, "spec": mk}, issues


# ----------------------------------------------------------------------------- assumptions
def assumptions_check(spec: Dict, ledger: Ledger, drep: Optional[Dict], types: List[str]
                      ) -> Tuple[List[Dict], List[Dict]]:
    issues: List[Dict] = []
    out = []
    hyps = {h["id"]: h for h in (drep or {}).get("hypotheses", [])}
    seen = set()
    for a in spec.get("assumptions", []) or []:
        aid = str(a.get("id", "?"))
        if aid in seen:
            issues.append(_issue("error", "assumptions", f"{aid}: duplicate id"))
        seen.add(aid)
        for f in ("description", "category", "why", "impact", "validation", "status"):
            if not a.get(f):
                issues.append(_issue("error", "assumptions", f"{aid}: '{f}' is required"))
        cat, st = a.get("category"), a.get("status", "untested")
        if cat and cat not in ASSUMPTION_CATEGORIES:
            issues.append(_issue("error", "assumptions", f"{aid}: category must be one of "
                                                         f"{', '.join(ASSUMPTION_CATEGORIES)}"))
        if st == "validated":
            issues.append(_issue("error", "assumptions", f"{aid}: use 'supported' (with evidence), not 'validated'"))
        elif st not in cd.HYPOTHESIS_STATUSES:
            issues.append(_issue("error", "assumptions", f"{aid}: status must be one of "
                                                         f"{', '.join(cd.HYPOTHESIS_STATUSES)}"))
        if a.get("impact") and a["impact"] not in LEVEL_WORDS:
            issues.append(_issue("error", "assumptions", f"{aid}: impact must be high, medium or low"))
        sup_ids, con_ids = _ids(a.get("evidence")), _ids(a.get("contradicting"))
        sup = [_info(i, ledger) for i in sup_ids]
        con = [_info(i, ledger) for i in con_ids]
        for i in sup + con:
            if not i["exists"]:
                issues.append(_issue("error", "assumptions", f"{aid}: {i['id']} is not in the ledger"))
        sup = [i for i in sup if i["exists"]]
        con = [i for i in con if i["exists"]]
        strength = cd.evidence_strength(sup, con)
        hid = a.get("hypothesis")
        h = None
        if hid:
            if drep is None:
                issues.append(_issue("info", "assumptions", f"{aid}: linked to {hid}, but no discovery spec is linked "
                                                            "(design.discovery) to check it"))
            elif str(hid) not in hyps:
                issues.append(_issue("error", "assumptions", f"{aid}: hypothesis {hid} is not in the discovery "
                                                             "register"))
            else:
                h = hyps[str(hid)]
        if st == "supported":
            if cat in INTERNAL_CATS:
                if not any(i["valid"] and not i["founder_only"] for i in sup):
                    issues.append(_issue("error", "assumptions", f"{aid}: marked supported without verified or "
                                                                 "reported documentary evidence; a founder's opinion "
                                                                 "is not validation"))
            else:
                if strength in ("none", "weak"):
                    issues.append(_issue("error", "assumptions", f"{aid}: marked supported without verified or reported "
                                                                 "customer evidence; founder opinion, desk research and "
                                                                 "waitlists are not validation"))
                if cat in COMMIT_CATS and not any(i["commitment"] for i in sup):
                    issues.append(_issue("error", "assumptions", f"{aid}: willingness to pay, pricing and revenue need "
                                                                 "committed or paid evidence; stated interest is not "
                                                                 "a transaction"))
                if cat in MEASURED_CATS and not any(i["measured"] for i in sup):
                    issues.append(_issue("error", "assumptions", f"{aid}: {cat} needs measured data (dataset or paid "
                                                                 "signal), not opinions or interviews alone"))
            if con and not _text(a.get("conflict_note")):
                issues.append(_issue("error", "assumptions", f"{aid}: supported while contradicting evidence exists "
                                                             f"({', '.join(con_ids)}); explain it in conflict_note or "
                                                             "mark it inconclusive"))
            if h is not None and h["status"] != "supported":
                issues.append(_issue("error", "assumptions", f"{aid}: supported here but the discovery register says "
                                                             f"{h['id']} is '{h['status']}'"))
        if st == "contradicted" and not con:
            issues.append(_issue("error", "assumptions", f"{aid}: marked contradicted without contradicting evidence"))
        if con and st not in ("supported", "contradicted", "inconclusive", "testing"):
            issues.append(_issue("warning", "assumptions", f"{aid}: contradicting evidence {', '.join(con_ids)} is "
                                                           "recorded; update the status"))
        critical = a.get("impact") == "high" and strength in ("none", "weak") and st != "supported"
        out.append({"id": aid, "description": _text(a.get("description")), "category": cat, "status": st,
                    "why": _text(a.get("why")), "impact": a.get("impact"), "validation": _text(a.get("validation")),
                    "evidence": sup_ids, "contradicting": con_ids, "strength": strength,
                    "evidence_status": _status(sup_ids, ledger, "none"), "hypothesis": str(hid) if hid else "",
                    "hypothesis_status": h["status"] if h else "", "critical": critical,
                    "conflict_note": _text(a.get("conflict_note")), "spec": a})
    cats = {r["category"] for r in out}
    need = {"wtp"} | ({"liquidity", "payments"} if "marketplace" in types else set()) | (
        {"retention"} if set(types) & {"saas", "subscription"} else set()) | (
        {"payments"} if set(types) & {"commission", "transaction"} else set())
    for c in sorted(need - cats):
        issues.append(_issue("warning", "assumptions", f"no '{c}' assumption registered; the model depends on it"))
    order = {"high": 0, "medium": 1, "low": 2}
    out.sort(key=lambda r: (not r["critical"], order.get(r["impact"], 3), r["id"]))
    return out, issues


def unregistered(spec: Dict, ledger: Ledger) -> List[Dict]:
    """Ledger assumptions, estimates and unverified entries that nothing in the spec cites: candidate assumptions."""
    used = set(re.findall(r"\bE-\d{3,}\b", yaml.safe_dump(spec, allow_unicode=True)))
    return [{"id": e.id, "claim": e.claim, "status": e.status} for e in ledger.entries
            if e.status in ("assumption", "estimate", "unverified") and e.id not in used]


# ----------------------------------------------------------------------------- stress tests
def _economics(v: Dict[str, float], bearer: str) -> Dict[str, Any]:
    """Per-transaction platform economics from available inputs; None where an input is missing."""
    r: Dict[str, Any] = {}
    have = lambda *ks: all(k in v for k in ks)  # noqa: E731
    t = v.get("take_rate")
    fee_on_platform = bearer in ("platform", "")
    if have("price", "take_rate"):
        r["platform_revenue_per_tx"] = v["price"] * t
    if have("price", "take_rate") and t < 1:      # a seller exists only when the platform keeps a share
        r["seller_earnings_per_tx"] = v["price"] * (1 - t) - (v["price"] * v["payment_fee_rate"]
                                                              if bearer == "seller" and "payment_fee_rate" in v else 0)
    if have("price", "take_rate", "payment_fee_rate", "delivery_cost", "support_cost"):
        pf = v["price"] * v["payment_fee_rate"] if fee_on_platform else 0
        r["contribution_per_tx"] = v["price"] * t - pf - v["delivery_cost"] - v["support_cost"]
        if v["price"]:
            r["contribution_margin_on_gmv"] = r["contribution_per_tx"] / v["price"]
        denom = t - (v["payment_fee_rate"] if fee_on_platform else 0)
        r["min_viable_price"] = (v["delivery_cost"] + v["support_cost"]) / denom if denom > 0 else None
        if fee_on_platform and v["price"]:
            r["max_fee_rate"] = t - (v["delivery_cost"] + v["support_cost"]) / v["price"]
        if v["price"] * t > 0:
            r["max_support_cost"] = v["price"] * t - pf - v["delivery_cost"]
    c = r.get("contribution_per_tx")
    if c is not None and "transactions_per_month" in v:
        r["monthly_contribution"] = c * v["transactions_per_month"]
    if c is not None and "fixed_costs_month" in v:
        r["break_even_tx_month"] = v["fixed_costs_month"] / c if c > 0 else None
        if "monthly_contribution" in r:
            r["operating_result_month"] = r["monthly_contribution"] - v["fixed_costs_month"]
    if "operating_result_month" in r and have("cac", "new_customers_month"):
        r["result_after_acquisition_month"] = r["operating_result_month"] - v["cac"] * v["new_customers_month"]
    if c is not None and "purchases_per_customer" in v:
        r["max_cac"] = c * v["purchases_per_customer"]
    if c is not None and c > 0 and "cac" in v:
        r["purchases_to_repay_cac"] = v["cac"] / c
    if have("founder_hours_per_week", "hours_required_per_week"):
        r["capacity_gap_hours"] = v["hours_required_per_week"] - v["founder_hours_per_week"]
    return r


ECON_LABELS = OrderedDict([
    ("platform_revenue_per_tx", ("Platform revenue per transaction", "price × take_rate", "money")),
    ("seller_earnings_per_tx", ("Seller earnings per transaction", "price × (1 − take_rate) − seller-borne fees",
                                "money")),
    ("contribution_per_tx", ("Contribution per transaction", "price × take_rate − platform-borne payment fee − "
                                                             "delivery_cost − support_cost", "money")),
    ("contribution_margin_on_gmv", ("Contribution as share of price", "contribution_per_tx ÷ price", "pct")),
    ("min_viable_price", ("Lowest price with positive contribution", "(delivery + support) ÷ (take_rate − fee rate)",
                          "money")),
    ("max_fee_rate", ("Highest payment fee rate before contribution turns negative",
                      "take_rate − (delivery + support) ÷ price", "pct")),
    ("max_support_cost", ("Highest support cost per transaction before contribution turns negative",
                          "price × take_rate − payment fee − delivery_cost", "money")),
    ("monthly_contribution", ("Monthly contribution", "contribution_per_tx × transactions_per_month", "money")),
    ("break_even_tx_month", ("Break-even transactions per month", "fixed_costs_month ÷ contribution_per_tx", "num")),
    ("operating_result_month", ("Monthly result before acquisition", "monthly contribution − fixed costs", "money")),
    ("result_after_acquisition_month", ("Monthly result after acquisition", "operating result − cac × new customers",
                                        "money")),
    ("max_cac", ("Highest affordable CAC", "contribution_per_tx × purchases_per_customer", "money")),
    ("purchases_to_repay_cac", ("Purchases needed to repay CAC", "cac ÷ contribution_per_tx", "num")),
    ("capacity_gap_hours", ("Founder capacity gap (hours/week)", "hours_required − hours_available", "num")),
])
ECON_INPUTS = {
    "platform_revenue_per_tx": ("price", "take_rate"), "seller_earnings_per_tx": ("price", "take_rate"),
    "contribution_per_tx": ("price", "take_rate", "payment_fee_rate", "delivery_cost", "support_cost"),
    "contribution_margin_on_gmv": ("price", "take_rate", "payment_fee_rate", "delivery_cost", "support_cost"),
    "min_viable_price": ("take_rate", "payment_fee_rate", "delivery_cost", "support_cost"),
    "max_fee_rate": ("price", "take_rate", "delivery_cost", "support_cost"),
    "max_support_cost": ("price", "take_rate", "payment_fee_rate", "delivery_cost"),
    "monthly_contribution": ("price", "take_rate", "payment_fee_rate", "delivery_cost", "support_cost",
                             "transactions_per_month"),
    "break_even_tx_month": ("price", "take_rate", "payment_fee_rate", "delivery_cost", "support_cost",
                            "fixed_costs_month"),
    "operating_result_month": ("price", "take_rate", "payment_fee_rate", "delivery_cost", "support_cost",
                               "transactions_per_month", "fixed_costs_month"),
    "result_after_acquisition_month": ("price", "take_rate", "payment_fee_rate", "delivery_cost", "support_cost",
                                       "transactions_per_month", "fixed_costs_month", "cac", "new_customers_month"),
    "max_cac": ("price", "take_rate", "payment_fee_rate", "delivery_cost", "support_cost", "purchases_per_customer"),
    "purchases_to_repay_cac": ("price", "take_rate", "payment_fee_rate", "delivery_cost", "support_cost", "cac"),
    "capacity_gap_hours": ("founder_hours_per_week", "hours_required_per_week"),
}
CARD_METRICS = {"wtp": ["min_viable_price"], "cac": ["max_cac"], "retention": ["purchases_to_repay_cac"],
                "volume": ["break_even_tx_month", "operating_result_month"], "payment_fees": ["max_fee_rate"],
                "support": ["max_support_cost"], "margins": ["contribution_margin_on_gmv"],
                "capacity": ["capacity_gap_hours"]}


def _apply(v: Dict[str, float], changes: Dict, name: str, issues: List[Dict]) -> Dict[str, float]:
    out = dict(v)
    for k, ch in (changes or {}).items():
        if k not in v:
            issues.append(_issue("error", "stress", f"scenario '{name}' changes '{k}', which has no base value"))
            continue
        if isinstance(ch, dict) and len(ch) == 1 and next(iter(ch)) in ("multiply", "add", "set"):
            op, x = next(iter(ch.items()))
            try:
                x = float(x)
            except (TypeError, ValueError):
                issues.append(_issue("error", "stress", f"scenario '{name}': {k}.{op} is not a number"))
                continue
            out[k] = v[k] * x if op == "multiply" else v[k] + x if op == "add" else x
        else:
            issues.append(_issue("error", "stress", f"scenario '{name}': change for '{k}' must be "
                                                    "{multiply|add|set: number}"))
        if k in RATE_INPUTS and not 0 <= out.get(k, 0) <= 1:
            issues.append(_issue("error", "stress", f"scenario '{name}': {k} leaves the 0–1 range"))
    return out


def stress_test(spec: Dict, ledger: Ledger, assumptions: List[Dict], deps: List[Dict]) -> Tuple[Dict, List[Dict]]:
    st = spec.get("stress", {}) or {}
    issues: List[Dict] = []
    for p in _walk_keys(st, PROBABILITY_KEYS) + _walk_keys(spec.get("alternatives", []), PROBABILITY_KEYS):
        issues.append(_issue("error", "stress", f"'{p}': probabilities are not supported; scenarios are "
                                                "what-ifs, not forecasts"))
    raw = st.get("inputs", {}) or {}
    v, sts = {}, {}
    for k, item in raw.items():
        if k == "fee_bearer":
            continue
        if k not in STRESS_INPUTS:
            issues.append(_issue("warning", "stress", f"unknown stress input '{k}'; known: {', '.join(STRESS_INPUTS)}"))
        x = _num(item)
        if x is None:
            if _val(item) not in (None, "", "unknown"):
                issues.append(_issue("error", "stress", f"input '{k}' is not a number: {_val(item)!r}"))
            continue
        if x < 0:
            issues.append(_issue("error", "stress", f"input '{k}' is negative"))
            continue
        if k in RATE_INPUTS and x > 1:
            issues.append(_issue("error", "stress", f"input '{k}' must be a share between 0 and 1"))
            continue
        if isinstance(item, dict) and not (item.get("evidence") or item.get("status")):
            issues.append(_issue("warning", "stress", f"input '{k}' has neither evidence nor status; treated as an "
                                                      "assumption"))
        v[k], sts[k] = x, _input_status(item, ledger)
    bearer = str(_val(raw.get("fee_bearer")) or "platform")
    base = _economics(v, bearer)
    status = _worst(list(sts.values())) if sts else ""
    metrics = []
    for key, (label, formula, kind) in ECON_LABELS.items():
        need = ECON_INPUTS[key]
        miss = [i for i in need if i not in v]
        val = base.get(key)
        metrics.append({"key": key, "label": label, "formula": formula, "kind": kind, "value": val,
                        "missing": miss, "status": _worst([sts[i] for i in need if i in sts]) if not miss else None})
    scenarios = []
    for sc in st.get("scenarios", []) or []:
        name = _text(sc.get("name")) or "scenario"
        if not _text(sc.get("rationale")):
            issues.append(_issue("error", "stress", f"scenario '{name}' needs a rationale for its changes"))
        sv = _apply(v, sc.get("changes"), name, issues)
        res = _economics(sv, bearer)
        scenarios.append({"name": name, "rationale": _text(sc.get("rationale")), "changes": sc.get("changes") or {},
                          "inputs": sv, "results": res, "complete": "contribution_per_tx" in res})
    mitig = st.get("mitigations", {}) or {}
    for k in mitig:
        if k not in STRESS_CARDS:
            issues.append(_issue("warning", "stress", f"mitigation for unknown stress test '{k}'"))
    cards = []
    for key, (title, question, drivers, cats, dtypes) in STRESS_CARDS.items():
        linked_a = [a["id"] for a in assumptions if a["category"] in cats]
        linked_d = [d["id"] for d in deps if d["type"] in dtypes]
        mets = [m for m in metrics if m["key"] in CARD_METRICS.get(key, [])]
        computed = [m for m in mets if m["value"] is not None]
        missing = sorted({i for m in mets for i in m["missing"]})
        cards.append({"key": key, "title": title, "question": question, "assumptions": linked_a,
                      "dependencies": linked_d, "metrics": mets, "quantified": bool(computed),
                      "missing": missing, "mitigation": _text(mitig.get(key)),
                      "unverified_deps": [d["id"] for d in deps if d["type"] in dtypes and d["status"] != "verified"]})
    return {"inputs": v, "input_status": sts, "status": status, "bearer": bearer, "metrics": metrics,
            "scenarios": scenarios, "cards": cards}, issues


# ----------------------------------------------------------------------------- alternatives
def alternatives_check(spec: Dict, ledger: Ledger) -> Tuple[Dict, List[Dict]]:
    issues: List[Dict] = []
    comp = spec.get("comparison", {}) or {}
    criteria = OrderedDict()
    for c in comp.get("criteria", []) or []:
        key = str(c.get("key", ""))
        scale = c.get("scale") or {}
        if not key or not isinstance(scale, dict) or not scale:
            issues.append(_issue("error", "alternatives", f"criterion '{key or '?'}' needs a key and a defined scale "
                                                          "(level: definition)"))
            continue
        for lvl, d in scale.items():
            if isinstance(lvl, (int, float)) and not isinstance(lvl, bool):
                issues.append(_issue("error", "alternatives", f"criterion '{key}': numeric scale level {lvl}; use "
                                                              "named qualitative levels with definitions"))
            if not _text(d):
                issues.append(_issue("error", "alternatives", f"criterion '{key}': level '{lvl}' has no definition"))
        criteria[key] = {"label": _text(c.get("label")) or key, "scale": OrderedDict((str(k), _text(x))
                                                                                       for k, x in scale.items())}
    if not criteria:
        criteria = OrderedDict((k, {"label": lbl, "scale": DEFAULT_SCALE}) for k, lbl in DEFAULT_CRITERIA.items())
    for p in _walk_keys(spec.get("alternatives", []), NUMERIC_RANK_KEYS) + _walk_keys(comp, NUMERIC_RANK_KEYS):
        issues.append(_issue("error", "alternatives", f"'{p}': numerical scores, weights and rankings are not "
                                                      "accepted; rate each criterion on its defined scale and explain "
                                                      "the evidence"))
    alts = []
    rec = []
    design_rec = (spec.get("design", {}) or {}).get("recommended")
    for a in spec.get("alternatives", []) or []:
        aid = str(a.get("id", "?"))
        where = f"{aid} {_text(a.get('name'))}".strip()
        cls, ci = classify(_ids(a.get("types")))
        issues += ci
        if not cls["types"]:
            issues.append(_issue("error", "alternatives", f"{where}: list its model types"))
        if not _text(a.get("fit")):
            issues.append(_issue("warning", "alternatives", f"{where}: explain why these model types fit (fit)"))
        for f, label in ALT_FIELDS.items():
            if not a.get(f):
                issues.append(_issue("warning", "alternatives", f"{where}: '{label}' ({f}) is not described"))
        dec = a.get("decision", "undecided")
        if dec not in DECISIONS:
            issues.append(_issue("error", "alternatives", f"{where}: decision must be one of {', '.join(DECISIONS)}"))
        if dec in ("recommended", "reject", "viable") and not _text(a.get("decision_reason")):
            issues.append(_issue("error", "alternatives", f"{where}: a '{dec}' decision needs decision_reason"))
        if dec == "recommended":
            rec.append(aid)
            if not _ids(a.get("validation")):
                issues.append(_issue("error", "alternatives", f"{where}: a recommendation must list what has to be "
                                                              "tested before the founder commits (validation)"))
        ratings = OrderedDict()
        for ck, r in (a.get("ratings", {}) or {}).items():
            if ck not in criteria:
                issues.append(_issue("error", "alternatives", f"{where}: unknown criterion '{ck}'"))
                continue
            if not isinstance(r, dict):
                r = {"level": r}
            lvl = r.get("level")
            if isinstance(lvl, (int, float)) and not isinstance(lvl, bool):
                issues.append(_issue("error", "alternatives", f"{where}: {ck} rated {lvl}; numerical scores are "
                                                              "rejected, use the defined scale "
                                                              f"({', '.join(criteria[ck]['scale'])})"))
                continue
            if str(lvl) not in criteria[ck]["scale"]:
                issues.append(_issue("error", "alternatives", f"{where}: {ck} level '{lvl}' is not on its scale "
                                                              f"({', '.join(criteria[ck]['scale'])})"))
            if not _text(r.get("why")):
                issues.append(_issue("error", "alternatives", f"{where}: rating '{ck}' needs 'why' (the evidence or "
                                                              "reasoning behind it)"))
            ev = _ids(r.get("evidence"))
            infos = [i for i in (_info(x, ledger) for x in ev) if i.get("exists")]
            basis = "evidence" if any(i["valid"] for i in infos) else "judgement"
            if ck == "customer_fit" and lvl == "favourable" and not any(i["customer"] and i["valid"] for i in infos):
                issues.append(_issue("warning", "alternatives", f"{where}: customer fit rated favourable without "
                                                                "customer evidence; this is a judgement"))
            ratings[ck] = {"level": str(lvl), "why": _text(r.get("why")), "evidence": ev, "basis": basis,
                           "status": _status(ev, ledger)}
        for ck in criteria:
            if ck not in ratings:
                ratings[ck] = {"level": "unknown", "why": "not rated", "evidence": [], "basis": "none", "status": ""}
        alts.append({"id": aid, "name": _text(a.get("name")), "classification": cls, "decision": dec,
                     "decision_reason": _text(a.get("decision_reason")), "fit": _text(a.get("fit")),
                     "ratings": ratings, "fields": OrderedDict((f, _text(a.get(f))) for f in ALT_FIELDS),
                     "validation": _ids(a.get("validation")), "spec": a})
    if len(rec) > 1:
        issues.append(_issue("error", "alternatives", f"more than one recommended model ({', '.join(rec)}); recommend "
                                                      "one and mark the others viable"))
    if design_rec and rec and str(design_rec) not in rec:
        issues.append(_issue("error", "alternatives", f"design.recommended is {design_rec} but {rec[0]} is marked "
                                                      "recommended"))
    if alts and len(alts) < 2:
        issues.append(_issue("warning", "alternatives", "compare at least two plausible business models"))
    if alts and not rec:
        issues.append(_issue("info", "alternatives", "no model is recommended yet"))
    return {"criteria": criteria, "alternatives": alts, "recommended": rec[0] if rec else None}, issues


# ----------------------------------------------------------------------------- maturity
def maturity(canvas: Dict, canvas_issues: List[Dict], vpcs: List[Dict], assumptions: List[Dict],
             streams: List[Dict], stress: Dict, drep: Optional[Dict], metrics_measured: Dict) -> Dict:
    met, unmet = [], []
    complete = bool(canvas) and all(b["items"] for b in canvas.values())
    consistent = not any(i["level"] == "error" for i in canvas_issues)
    c1 = complete and consistent
    (met if c1 else unmet).append(("coherent", "all nine canvas blocks described, every item labelled, no "
                                               "inconsistencies"))
    cust_items = any(i["basis"] == "evidence" for k in ("customer_segments", "value_propositions")
                     for i in (canvas.get(k, {}) or {}).get("items", []))
    vpc_ev = any(v["evidence_items"] for v in vpcs)
    psf = (drep or {}).get("psf", {}).get("verdict", "")
    psf_ok = bool(psf) and not psf.startswith(("Insufficient", "No ", "Mixed"))
    a_ok = any(a["status"] == "supported" and a["category"] not in INTERNAL_CATS for a in assumptions)
    c2 = c1 and (cust_items or vpc_ev) and (psf_ok or a_ok)
    (met if c2 else unmet).append(("customer-evidence", "customer evidence on segments or value propositions, and "
                                                        "a supported customer-side assumption or problem-solution fit"))
    gen = [s for s in streams if s["stage"] in ("generating", "repeatable")]
    contrib = next((m for m in stress.get("metrics", []) if m["key"] == "contribution_per_tx"), None)
    contrib_ok = bool(contrib and contrib["value"] is not None and contrib["value"] > 0 and contrib["status"] in VALID)
    c3 = c2 and bool(gen) and contrib_ok
    (met if c3 else unmet).append(("economic-viability", "a revenue stream generating paid revenue, and positive "
                                                         "contribution per transaction from measured inputs"))
    rep = [s for s in streams if s["stage"] == "repeatable"]
    cac_ok = stress.get("input_status", {}).get("cac") in VALID
    c4 = c3 and bool(rep) and cac_ok
    (met if c4 else unmet).append(("repeatable", "a repeatable revenue stream and a measured acquisition cost"))
    level = "repeatable" if c4 else "economic-viability" if c3 else "customer-evidence" if c2 else (
        "coherent" if c1 else "incomplete")
    return {"level": level, "label": MATURITY[level], "met": met, "unmet": unmet,
            "discovery_psf": psf, "discovery_pmf": (drep or {}).get("pmf", {}).get("verdict", "")}


# ----------------------------------------------------------------------------- analysis
def analyze(spec_path: str, model: Optional[str] = None) -> Dict:
    spec = load_spec(spec_path)
    base = os.path.dirname(os.path.abspath(spec_path))
    ledger, profile, prof_dir = context(spec, base)
    d = spec.get("design", {}) or {}
    issues: List[Dict] = []
    if not (d.get("profile") or d.get("evidence")):
        issues.append(_issue("warning", "evidence", "no profile or ledger configured; provenance cannot be checked"))
    issues += gtm.check_evidence_ids(spec, ledger)
    for p in split_values(spec):
        key = p.rsplit(".", 1)[-1]
        likely = " " in key.strip() or key.strip().replace(",", "").replace(".", "").isdigit()
        issues.append(_issue("error" if likely else "warning", "spec",
                             f"'{p}' has no value: if it is text cut by an unquoted comma inside a {{flow: mapping}}, "
                             "quote the whole value; otherwise remove the empty field"))
    drep, di = discovery_context(spec, base)
    issues += di
    hyp_ids = {h["id"] for h in drep["hypotheses"]} if drep else None
    segs = segments_of(spec, drep)
    seg_ids = {str(s.get("id")) for s in segs}
    if not segs:
        issues.append(_issue("warning", "segments", "no segments: define them here or link a discovery spec"))
    geos = _ids(d.get("geography")) or _ids(profile.get("geography"))
    deps, de = dependencies_check(spec, ledger, geos)
    streams, re_ = revenue_check(spec, ledger, seg_ids, deps)
    types = _types(spec)
    costs, ce = costs_check(spec, ledger, types)
    canvas_src = spec.get("canvas")
    if model:
        alt = next((a for a in spec.get("alternatives", []) or [] if str(a.get("id")) == model), None)
        if alt is None:
            raise ValueError(f"unknown model '{model}'")
        if not alt.get("canvas"):
            raise ValueError(f"model {model} has no canvas of its own; describe one under alternatives[{model}].canvas")
        canvas_src = alt["canvas"]
    canvas, ci = canvas_check(canvas_src, ledger, hyp_ids)
    vpcs, vi = value_proposition_check(spec, ledger, seg_ids, hyp_ids)
    mk, mi = marketplace_check(spec, ledger, segs, deps, streams)
    extra = {}
    if mk:
        for k in ("gmv", "platform_revenue"):
            item = (mk["spec"].get("funnel", {}) or {}).get(k)
            if item is not None:
                extra["gross_revenue" if k == "platform_revenue" else k] = item
        if (mk["spec"].get("funnel", {}) or {}).get("completed_transactions") is not None:
            extra["transactions"] = mk["spec"]["funnel"]["completed_transactions"]
            extra["orders"] = mk["spec"]["funnel"]["completed_transactions"]
    fin, fi = financials(spec, ledger, extra)
    assumptions, ai = assumptions_check(spec, ledger, drep, types)
    stress, si = stress_test(spec, ledger, assumptions, deps)
    alts, ali = alternatives_check(spec, ledger)
    ctx = {"mechanisms": {s["mechanism"] for s in streams if s["mechanism"]},
           "assumption_categories": {a["category"] for a in assumptions},
           "dependency_types": {x["type"] for x in deps}, "cost_types": {r["type"] for r in costs["rows"]},
           "marketplace": bool(mk)}
    cls, cli = classify(types, ctx)
    if not types:
        issues.append(_issue("warning", "classification", "no model types: set design.types or recommend an "
                                                          "alternative"))
    issues += de + re_ + ce + ci + vi + mi + fi + ai + si + ali + cli
    mat = maturity(canvas, ci, vpcs, assumptions, streams, stress, drep, {})
    claimed = d.get("claimed_maturity")
    if claimed:
        order = list(MATURITY)
        if claimed not in order:
            issues.append(_issue("error", "maturity", f"claimed_maturity must be one of {', '.join(order)}"))
        elif order.index(claimed) > order.index(mat["level"]):
            issues.append(_issue("error", "maturity", f"claimed maturity '{claimed}' exceeds what the evidence shows "
                                                      f"('{mat['level']}'); a coherent canvas is not proof the "
                                                      "business works"))
    gaps = []
    for a in assumptions:
        if a["critical"]:
            ev = "no" if a["strength"] == "none" else a["strength"]
            gaps.append(f"{a['id']} ({a['category']}, high impact) has {ev} evidence: {a['description']}")
    for x in deps:
        if x["status"] != "verified" and x["type"] in ("payment", "payout", "regulatory", "tax", "legal", "banking"):
            gaps.append(f"{x['id']} {x['name']} is {x['status']}: {x['question'] or 'confirm before launch'}")
    missing_profile = []
    if prof_dir:
        from .profile import missing_information
        missing_profile = [m for m in missing_information(prof_dir) if m.split(":")[0] in ("business-model.md",
                                                                                           "customers.md")]
    return {"spec": os.path.abspath(spec_path), "base": base, "profile_dir": prof_dir,
            "company": d.get("company") or profile.get("name", ""), "stage": d.get("stage") or profile.get("stage", ""),
            "geography": geos, "currency": d.get("currency", ""), "model": model, "types": types,
            "classification": cls, "segments": segs, "canvas": canvas, "value_propositions": vpcs,
            "revenue": streams, "costs": costs, "financials": fin, "marketplace": mk, "dependencies": deps,
            "assumptions": assumptions, "unregistered": unregistered(spec, ledger), "stress": stress,
            "alternatives": alts, "maturity": mat, "discovery": drep is not None, "gaps": gaps,
            "missing_profile": missing_profile, "conflicts": [str(c) for c in ledger.conflicts()],
            "issues": issues, "errors": sum(1 for i in issues if i["level"] == "error"),
            "warnings": sum(1 for i in issues if i["level"] == "warning"), "_spec": spec}


# ----------------------------------------------------------------------------- ledger recording
def record(spec_path: str) -> List[str]:
    """Append one ledger 'assumption' entry per register item not yet recorded. Never edits existing entries.

    Items that already cite ledger evidence are not re-recorded (the evidence is already in the ledger).
    Idempotent: an entry is matched by its source.ref (spec path#assumption id).
    """
    spec = load_spec(spec_path)
    base = os.path.dirname(os.path.abspath(spec_path))
    ledger, _, prof_dir = context(spec, base)
    d = spec.get("design", {}) or {}
    path = d.get("evidence") or (os.path.join(prof_dir, "evidence.yaml") if prof_dir else None)
    if not path:
        raise ValueError("no ledger configured (design.profile or design.evidence)")
    path = path if os.path.isabs(path) else os.path.join(base, path)
    rel = os.path.relpath(os.path.abspath(spec_path), os.path.dirname(os.path.abspath(path)))
    refs = {str((e.source or {}).get("ref", "")) for e in ledger.entries}
    today = _dt.date.today().isoformat()
    new = []
    for a in spec.get("assumptions", []) or []:
        aid = str(a.get("id", ""))
        ref = f"{rel}#{aid}"
        if not aid or ref in refs or _ids(a.get("evidence")) or _ids(a.get("ledger")):
            continue
        eid = ledger.next_id() if not new else "E-%03d" % (int(new[-1]["id"][2:]) + 1)
        entry = {"id": eid, "claim": f"Business model assumption {aid}: {_text(a.get('description'))}",
                 "key": f"business_model.assumption.{aid.lower()}", "status": "assumption", "confidence": "low",
                 "source": {"type": "analysis", "ref": ref}, "owner": _text(a.get("owner")) or "founder (to confirm)",
                 "updated": today, "validate": _text(a.get("validation")),
                 "notes": "Recorded by startup-kit business-model assumptions --record. Untested until evidence is "
                          "added as a new entry."}
        new.append(entry)
    if new:
        with open(path, "a", encoding="utf-8") as f:
            f.write("\n" + yaml.safe_dump(new, sort_keys=False, allow_unicode=True))
    return [n["id"] for n in new]


# ----------------------------------------------------------------------------- design inventory
LEDGER_BLOCK = (("pricing.", "revenue_streams"), ("cost.", "cost_structure"), ("gtm.", "channels"),
                ("market.", "customer_segments"), ("ue.", "cost_structure"), ("traction.", "revenue_streams"))


def inventory(profile_dir: str, discovery_spec: Optional[str] = None) -> Tuple[str, Dict]:
    """What the profile, ledger and discovery register already say about the business model.

    Returns a Markdown inventory and a starter spec. The starter spec only carries what exists: ledger entries
    become items labelled by their status, everything else is an explicit 'unknown'.
    """
    from .profile import NARRATIVE_FILES, _strip_frontmatter, ledger_for, load_profile, missing_information
    prof = load_profile(profile_dir)
    ledger = ledger_for(profile_dir)
    name = prof.get("name", "") or os.path.basename(os.path.abspath(profile_dir))
    L = [f"# Business model inventory: {name}", "",
         "What already exists in the startup profile, evidence ledger and discovery register. Nothing here is "
         "new evidence; gaps are listed, not filled.", ""]
    for fn in ("business-model.md", "customers.md", "products.md"):
        p = os.path.join(profile_dir, fn)
        if fn in NARRATIVE_FILES and os.path.exists(p):
            body = _strip_frontmatter(open(p, encoding="utf-8").read()).strip()
            body = re.sub(r"<!--.*?-->", "", body, flags=re.S).strip()
            body = re.sub(r"^# .*\n", "", body).strip()
            L += [f"## From {fn} (founder-provided or earlier analysis)", "", body or "_Empty._", ""]
    blocks: Dict[str, List[Dict]] = {k: [] for k in BLOCKS}
    rows = ["| ID | Claim | Status | Source | Canvas block |", "|---|---|---|---|---|"]
    for e in ledger.entries:
        key = str(e.key or "")
        blk = next((b for pre, b in LEDGER_BLOCK if key.startswith(pre)), None)
        if not blk:
            continue
        src = (e.source or {}).get("type", "")
        customer = src in cd.STRONG_SOURCES or str(e.raw.get("signal", "")) in ("observed", "committed", "paid")
        if e.status in VALID and src != "founder" and (blk not in CUSTOMER_BLOCKS or customer):
            basis = "evidence"
        elif e.status in VALID and src == "founder":
            basis = "founder"
        else:
            basis = "hypothesis"
        blocks[blk].append({"text": e.claim, "basis": basis, "evidence": [e.id]})
        rows.append(f"| {e.id} | {_cell(e.claim)} | {e.status} | {src} | {BLOCKS[blk]} |")
    L += ["## Ledger entries that bear on the business model", ""]
    L += rows if len(rows) > 2 else ["_No keyed pricing, cost, market or GTM entries._"]
    L.append("")
    conf = ledger.conflicts()
    if conf:
        L += ["## Contradictions in the ledger", ""] + [f"- {c.message}" for c in conf] + [""]
    assum = [e for e in ledger.entries if e.status in ("assumption", "estimate", "unverified")]
    if assum:
        L += ["## Candidate assumptions (ledger entries that are not evidence)", "",
              "| ID | Claim | Status |", "|---|---|---|"]
        L += [f"| {e.id} | {_cell(e.claim)} | {e.status} |" for e in assum] + [""]
    segs = []
    hyps = []
    if discovery_spec:
        drep = cd.analyze(discovery_spec)
        segs = drep["_spec"].get("segments", []) or []
        hyps = drep["hypotheses"]
        L += ["## Customer discovery register", "", f"Problem-solution fit: **{drep['psf']['verdict']}**", "",
              f"PMF: **{drep['pmf']['verdict']}**", "", "| Hypothesis | Category | Status | Evidence strength |",
              "|---|---|---|---|"]
        L += [f"| {h['id']} {_cell(h['statement'])} | {h['category']} | {h['status']} | {h['strength']} |"
              for h in hyps] + [""]
    miss = [m for m in missing_information(profile_dir) if m.split(":")[0] in ("business-model.md", "customers.md",
                                                                               "financials.md")]
    if miss:
        L += ["## Missing information", ""] + [f"- [ ] {m}" for m in miss] + [""]
    empty = [BLOCKS[k] for k, v in blocks.items() if not v]
    L += ["## Questions for the founder", "",
          "Ask only what the material above does not answer:", ""]
    L += [f"- {b}: what is known today, and what is it based on?" for b in empty]
    L += ["- Which payment provider will collect money and pay out sellers, and has it confirmed this in writing?",
          "- Which costs are known from invoices or quotes, and which are estimates?", ""]
    for k, v in blocks.items():
        if not v:
            v.append({"text": f"TODO: {BLOCKS[k]} not yet described", "basis": "unknown"})
    starter = {"design": {"company": name, "profile": os.path.abspath(profile_dir), "stage": prof.get("stage", ""),
                          "geography": prof.get("geography") or [], "currency": "", "types": [],
                          "date": _dt.date.today().strftime("%B %Y")},
               "canvas": blocks}
    if discovery_spec:
        starter["design"]["discovery"] = os.path.abspath(discovery_spec)
    else:
        starter["segments"] = []
    starter.update({"value_propositions": [], "revenue_streams": [], "costs": [], "dependencies": [],
                    "assumptions": [], "alternatives": [], "stress": {"inputs": {}, "scenarios": []}})
    return "\n".join(L) + "\n", starter


# ----------------------------------------------------------------------------- rendering
def _cites(ids: List[str]) -> str:
    return f"[{', '.join(ids)}]" if ids else "—"


def _fmt(v: Optional[float], kind: str, cur: str) -> str:
    if v is None:
        return "—"
    if kind == "num":
        return f"{v:,.1f}"
    return gtm.fmt_value(v, kind, cur)


def canvas_table(rep: Dict) -> List[str]:
    L = ["| Block | Evidence-backed | Founder-provided | Hypotheses | Recommendations | Unknowns |",
         "|---|---:|---:|---:|---:|---:|"]
    for b in rep["canvas"].values():
        c = b["counts"]
        L.append(f"| {b['label']} | {c['evidence']} | {c['founder']} | {c['hypothesis']} | {c['recommendation']} | "
                 f"{c['unknown']} |")
    L.append("")
    for b in rep["canvas"].values():
        L += [f"## {b['label']}", ""]
        if b["rationale"]:
            L += [b["rationale"], ""]
        L += ["| Item | Basis | Evidence | Evidence status | Notes |", "|---|---|---|---|---|"]
        for i in b["items"]:
            note = "; ".join(x for x in (i["rationale"], f"hypothesis {', '.join(i['hypothesis'])}"
                                         if i["hypothesis"] else "", f"contradicted by {_cites(i['contradicting'])}"
                                         if i["contradicting"] else "") if x)
            L.append(f"| {_cell(i['text'])} | {BASES.get(i['basis'], i['basis'])} | {_cites(i['evidence'])} | "
                     f"{i['status'] or '—'} | {_cell(note) or '—'} |")
        L.append("")
    return L


def vpc_md(rep: Dict, segment: Optional[str] = None) -> List[str]:
    L = []
    seg_names = {str(s.get("id")): _text(s.get("name")) for s in rep["segments"]}
    vpcs = [v for v in rep["value_propositions"] if not segment or v["segment"] == segment]
    if not vpcs:
        return ["No value proposition canvas recorded" + (f" for segment {segment}" if segment else "") + ".", ""]
    for v in vpcs:
        L += [f"## {v['segment']}: {seg_names.get(v['segment'], '')}".rstrip(": "), "",
              f"> [!KEY] Fit: {v['verdict']}.", ""]
        for title, key in (("Customer jobs", "jobs"), ("Pains", "pains"), ("Gains", "gains"),
                           ("Products and services", "products"), ("Pain relievers", "relievers"),
                           ("Gain creators", "creators")):
            L += [f"### {title}", ""]
            if not v[key]:
                L += ["None recorded.", ""]
                continue
            L += ["| ID | Item | Basis | Evidence | Evidence status | Addresses |", "|---|---|---|---|---|---|"]
            for i in v[key]:
                L.append(f"| {i['id']} | {_cell(i['text'])} | {BASES.get(i['basis'], i['basis'])} | "
                         f"{_cites(i['evidence'])} | {i['status'] or '—'} | {', '.join(i['addresses']) or '—'} |")
            L.append("")
        if v["unaddressed_pains"]:
            L += [f"Pains not addressed by the value map: {', '.join(v['unaddressed_pains'])}.", ""]
    return L


def classification_md(rep: Dict) -> List[str]:
    c = rep["classification"]
    L = [f"Model types: **{', '.join(c['labels']) or 'not set'}**" + (" (hybrid)" if c["hybrid"] else "") + ".", ""]
    if c["requirements"]:
        L += ["| Model type | Structural requirement | Present in this design |", "|---|---|---|"]
        L += [f"| {BM_TYPES[r['type']][0]} | {r['requirement']} | {'yes' if r['met'] else 'missing'} |"
              for r in c["requirements"]] + [""]
    return L


def revenue_md(rep: Dict) -> List[str]:
    if not rep["revenue"]:
        return ["No revenue streams defined.", ""]
    L = ["Stages: " + "; ".join(STREAM_STAGES.values()) + ". A proposed price is a hypothesis, never revenue.", "",
         "| ID | Stream | Payer | Mechanism | Billing | Price (status) | Stage | Dependencies |",
         "|---|---|---|---|---|---|---|---|"]
    for s in rep["revenue"]:
        L.append(f"| {s['id']} | {_cell(s['name'])} | {s['payer']} | {s['mechanism']} | "
                 f"{_cell(s['billing'])} | {_cell(s['price_display'])} | {s['stage']} | "
                 f"{', '.join(s['dependencies']) or '—'} |")
    L.append("")
    for s in rep["revenue"]:
        tr = f"{s['take_rate'] * 100:.0f}% ({s['take_rate_status'] or 'assumption'})" if s["take_rate"] else "—"
        L += [f"### {s['id']}: {s['name']}", "",
              f"- **Value the payer receives:** {s['value'] or 'not described'}",
              f"- **Transaction structure:** {s['structure'] or 'not described'}",
              f"- **Take rate:** {tr}",
              f"- **Revenue recognition (to confirm with an accountant):** {s['recognition'] or 'not described'}",
              f"- **Evidence (status: {s['evidence_status']}):** {_cites(s['evidence'])}",
              f"- **Risks:** {s['risks'] or 'not described'}", ""]
    return L


def costs_md(rep: Dict) -> List[str]:
    c = rep["costs"]
    cur = c["totals"]["currency"]
    if not c["rows"]:
        return ["No costs defined.", ""]
    L = ["| ID | Cost | Fixed or variable | Type | Driver | Amount | Status | Basis or evidence |",
         "|---|---|---|---|---|---|---|---|"]
    for r in c["rows"]:
        amt = f"{r['value']:,.2f} {r['unit']}" if r["known"] else "unknown"
        if r["known"] and re.search(r"share|%|percent|rate", r["unit"], re.I):
            amt = f"{r['value'] * 100:.1f}% {r['unit']}"
        L.append(f"| {r['id']} | {_cell(r['name'])} | {r['category']} | {r['type']} | {_cell(r['driver']) or '—'} | "
                 f"{_cell(amt)} | {r['status']} | {_cell(r['basis']) or _cites(r['evidence'])} |")
    t = c["totals"]
    L += ["", "**Totals (known values only; unknown costs are not filled in):**", ""]
    if t["fixed_month"] is not None:
        L.append(f"- Known fixed costs per month: {gtm.fmt_value(t['fixed_month'], 'money', cur)} "
                 f"({', '.join(t['fixed_month_items'])}; status {t['fixed_month_status']}).")
    if t["variable_rate"] is not None:
        L.append(f"- Variable costs charged as a share of each payment: {t['variable_rate'] * 100:.1f}% "
                 f"(status {t['variable_rate_status']}).")
    if t["variable_per_tx"] is not None:
        L.append(f"- Variable costs per transaction: {gtm.fmt_value(t['variable_per_tx'], 'money', cur)} "
                 f"(status {t['variable_per_tx_status']}).")
    if t["unknown"]:
        L.append(f"- Unknown: {', '.join(t['unknown'])}. They stay unknown until quoted or measured.")
    return L + [""]


def financials_md(rep: Dict) -> List[str]:
    cur = rep["currency"]
    L = ["Definitions are computed only when every input exists. Missing inputs are listed, never estimated.", "",
         "| Metric | Formula | Value | Status | Missing inputs |", "|---|---|---|---|---|"]
    for r in rep["financials"]:
        L.append(f"| {r['name']} | {r['formula']} | {r['display'] or 'not computed'} | {r['status'] or '—'} | "
                 f"{', '.join(r['missing']) or '—'} |")
    L += ["", "**Do not confuse:**", "", "| This | Is not | Why |", "|---|---|---|"]
    L += [f"| {a} | {b} | {w} |" for a, b, w in FIN_DISTINCTIONS]
    return L + [""]


def marketplace_md(rep: Dict) -> List[str]:
    mk = rep["marketplace"]
    cur = rep["currency"]
    if not mk:
        return ["Not a marketplace model.", ""]
    s = mk["spec"]
    applies = f" Applies to alternative {s['applies_to']}, not the recommended model." if s.get("applies_to") else ""
    L = [f"Configuration: **{mk['type']}**. Liquidity status: **{mk['liquidity']}**.{applies}", "",
         "| Side | Role | How it is acquired | Value it receives | What it pays | Subsidy |", "|---|---|---|---|---|---|"]
    for x in mk["sides"]:
        L.append(f"| {x['segment']} {_cell(x['name'])} | {x['role']} | {_cell(x['acquisition']) or '—'} | "
                 f"{_cell(x['value']) or '—'} | {_cell(x['pays']) or '—'} | {_cell(x['subsidy']) or '—'} |")
    L += ["", "### Marketplace flow", ""]
    for f, label in (("cold_start", "Cold start"), ("matching", "Matching"), ("transaction_flow", "Transaction flow"),
                     ("trust_safety", "Trust and safety"), ("leakage", "Leakage defence"),
                     ("network_effects", "Network effects"), ("pricing", "Multi-sided pricing")):
        L.append(f"- **{label}:** {_text(s.get(f)) or 'not described'}")
    pay = mk["payments"]
    L += ["", "### Money flow", ""]
    for f, label in (("collection", "Payment collection"), ("payout", "Seller payout and settlement"),
                     ("refunds", "Refunds"), ("disputes", "Disputes"), ("fee_bearer", "Who bears payment fees")):
        L.append(f"- **{label}:** {_text(pay.get(f)) or 'not described'}")
    L += ["", "### Funnel (measured counts only)", "", "| Stage | Count | Status |", "|---|---:|---|"]
    for st in mk["stages"]:
        count = "—" if st["value"] is None else f"{st['value']:,.0f}"
        L.append(f"| {st['label']} | {count} | {st['status']} |")
    L += ["", "| Ratio | Formula | Value | Status |", "|---|---|---|---|"]
    for r in mk["ratios"]:
        val = f"{r['value'] * 100:.1f}%" if r["value"] is not None else "missing " + ", ".join(r["missing"])
        L.append(f"| {r['name']} | {r['formula']} | {val} | {r['status'] or '—'} |")
    m = mk["money"]
    L += ["", "### GMV, platform revenue and seller earnings", ""]
    if m.get("gmv") is not None:
        L.append(f"- GMV: {gtm.fmt_value(m['gmv'], 'money', cur)} ({m['gmv_status']}).")
        if m.get("platform_revenue") is not None:
            L.append(f"- Platform revenue: {gtm.fmt_value(m['platform_revenue'], 'money', cur)} ({m['basis']}; "
                     f"status {m['status']}).")
            L.append(f"- Seller earnings: {gtm.fmt_value(m['seller_earnings'], 'money', cur)}; owed to sellers, "
                     "not platform income.")
        else:
            L.append("- Platform revenue: not computable (no measured platform revenue and no take rate).")
    else:
        L.append("- GMV not measured: no platform revenue or seller earnings can be computed.")
    if m.get("take_rate") is not None:
        L.append(f"- Design take rate: {m['take_rate'] * 100:.0f}% ({m['take_rate_status'] or 'assumption'}).")
    return L + [""]


def payments_md(rep: Dict) -> List[str]:
    deps = rep["dependencies"]
    L = [f"Geography: **{', '.join(rep['geography']) or 'not stated'}**. Payment, payout and regulatory items are "
         "dependencies to verify, never assumptions to rely on. This section is not legal, tax or payment advice.", ""]
    if not deps:
        return L + ["No dependencies registered.", ""]
    L += ["| ID | Dependency | Type | Country | Status | Evidence | Open question | Confirm with |",
          "|---|---|---|---|---|---|---|---|"]
    for d in deps:
        L.append(f"| {d['id']} | {_cell(d['name'])} | {d['type']} | {_cell(d['country']) or '—'} | {d['status']} | "
                 f"{_cites(d['evidence'])} | {_cell(d['question']) or '—'} | {', '.join(d['confirm_with']) or '—'} |")
    qs = [d for d in deps if d["status"] != "verified" and d["question"]]
    if qs:
        L += ["", "**Questions for qualified advisers and providers:**", ""]
        L += [f"- ({', '.join(d['confirm_with']) or 'adviser'}) {d['question']}" for d in qs]
    return L + [""]


def alternatives_md(rep: Dict, only: Optional[str] = None) -> List[str]:
    a = rep["alternatives"]
    alts = [x for x in a["alternatives"] if not only or x["id"] == only]
    if not alts:
        return ["No alternatives recorded.", ""]
    L = ["**Rating scales** (qualitative; no numerical scores are computed):", ""]
    if all(c["scale"] == DEFAULT_SCALE for c in a["criteria"].values()):
        L += ["Every criterion uses one scale: " + "; ".join(f"*{lvl}*: {d}" for lvl, d in DEFAULT_SCALE.items())
              + ".", "", "Criteria: " + ", ".join(c["label"] for c in a["criteria"].values()) + "."]
    else:
        for k, c in a["criteria"].items():
            L.append(f"- **{c['label']}**: " + "; ".join(f"*{lvl}*: {d}" for lvl, d in c["scale"].items()))
    L += ["", "| Criterion | " + " | ".join(f"{x['id']} {_cell(x['name'])}" for x in alts) + " |",
          "|---|" + "---|" * len(alts)]
    for k, c in a["criteria"].items():
        L.append(f"| {c['label']} | " + " | ".join(f"{x['ratings'][k]['level']} ({x['ratings'][k]['basis']})"
                                                   for x in alts) + " |")
    L.append("| **Decision** | " + " | ".join(f"**{x['decision']}**" for x in alts) + " |")
    L.append("")
    for x in alts:
        L += [f"### {x['id']}: {x['name']} ({x['decision']})", "",
              f"Model types: {', '.join(x['classification']['labels']) or 'not set'}. Why they fit: "
              f"{x['fit'] or 'not explained'}.", ""]
        for f, label in ALT_FIELDS.items():
            if x["fields"][f]:
                L.append(f"- **{label}:** {_cell(x['fields'][f])}")
        L += ["", "| Criterion | Level | Why | Evidence | Evidence status |", "|---|---|---|---|---|"]
        for k, r in x["ratings"].items():
            L.append(f"| {a['criteria'][k]['label']} | {r['level']} | {_cell(r['why'])} | {_cites(r['evidence'])} | "
                     f"{r['status'] or '—'} |")
        L += ["", f"**Decision reason:** {x['decision_reason'] or 'not given'}", ""]
    return L


def assumptions_md(rep: Dict) -> List[str]:
    if not rep["assumptions"]:
        return ["No assumptions registered.", ""]
    L = ["| ID | Assumption | Category | Why it matters | Impact if false | Evidence | Evidence status | Strength | "
         "Contradicting | Status | Validation method | Hypothesis |", "|---|---|---|---|---|---|---|---|---|---|---|---|"]
    for a in rep["assumptions"]:
        h = f"{a['hypothesis']} ({a['hypothesis_status']})" if a["hypothesis_status"] else (a["hypothesis"] or "—")
        L.append(f"| {a['id']}{' †' if a['critical'] else ''} | {_cell(a['description'])} | {a['category']} | "
                 f"{_cell(a['why'])} | {a['impact']} | {_cites(a['evidence'])} | {a['evidence_status']} | "
                 f"{a['strength']} | {_cites(a['contradicting'])} | {a['status']} | {_cell(a['validation'])} | {h} |")
    L += ["", "† critical: high impact with no or weak evidence. Statuses follow the discovery rules: *supported* "
              "needs customer evidence; willingness to pay needs committed or paid evidence; volume, retention and "
              "liquidity need measured data.", ""]
    return L


def stress_md(rep: Dict) -> List[str]:
    s = rep["stress"]
    cur = rep["currency"]
    L = ["Stress tests show where the model breaks. Values are computed only from recorded inputs; scenarios are "
         "founder-defined what-ifs, not forecasts, and no probabilities are assigned.", ""]
    if s["inputs"]:
        L += ["| Input | Value | Status |", "|---|---|---|"]
        for k, v in s["inputs"].items():
            kind = "pct" if k in RATE_INPUTS else "num"
            L.append(f"| {k} | {_fmt(v, kind, cur)} | {s['input_status'].get(k, '')} |")
        L += ["", f"Payment fees borne by: {s['bearer']}.", ""]
    L += ["| Result | Formula | Value | Status | Missing inputs |", "|---|---|---|---|---|"]
    for m in s["metrics"]:
        L.append(f"| {m['label']} | {m['formula']} | {_fmt(m['value'], m['kind'], cur)} | {m['status'] or '—'} | "
                 f"{', '.join(m['missing']) or '—'} |")
    L.append("")
    if s["scenarios"]:
        keys = ("contribution_per_tx", "break_even_tx_month", "operating_result_month")
        L += ["### Scenarios (hypothetical)", "", "| Scenario | Changes | Rationale | " +
              " | ".join(ECON_LABELS[k][0] for k in keys) + " |", "|---|---|---|" + "---|" * len(keys)]
        for sc in s["scenarios"]:
            ch = "; ".join(f"{k} {next(iter(v))} {next(iter(v.values()))}" for k, v in sc["changes"].items()
                           if isinstance(v, dict) and v) or "base"
            L.append(f"| {sc['name']} | {_cell(ch)} | {_cell(sc['rationale'])} | " +
                     " | ".join(_fmt(sc["results"].get(k), ECON_LABELS[k][2], cur) for k in keys) + " |")
        L.append("")
    L += ["### Stress cards", "", "| Test | Question | Computed threshold | Linked assumptions | Unverified "
                                  "dependencies | Mitigation |", "|---|---|---|---|---|---|"]
    for c in s["cards"]:
        thr = "; ".join(f"{m['label']}: {_fmt(m['value'], m['kind'], cur)}" for m in c["metrics"]
                        if m["value"] is not None)
        if not thr:
            thr = ("qualitative (missing " + ", ".join(c["missing"]) + ")") if c["missing"] else "qualitative"
        L.append(f"| {c['title']} | {c['question']} | {_cell(thr)} | {', '.join(c['assumptions']) or '—'} | "
                 f"{', '.join(c['unverified_deps']) or '—'} | {_cell(c['mitigation']) or 'to be defined'} |")
    return L + [""]


def maturity_md(rep: Dict) -> List[str]:
    m = rep["maturity"]
    L = [f"> [!KEY] Business model maturity: **{m['label']}**.", "",
         "| Level | Criterion | Met |", "|---|---|---|"]
    for lvl, crit in m["met"]:
        L.append(f"| {lvl} | {crit} | yes |")
    for lvl, crit in m["unmet"]:
        L.append(f"| {lvl} | {crit} | no |")
    L.append("")
    if m["discovery_psf"]:
        L += [f"Customer discovery register: problem-solution fit is *{m['discovery_psf']}*; "
              f"PMF: *{m['discovery_pmf']}*", ""]
    L += ["A complete, coherent canvas describes a business model. It does not show that customers want it, that "
          "it makes money, or that it repeats.", ""]
    return L


def decision_md(rep: Dict) -> List[str]:
    d = rep["_spec"].get("design", {}) or {}
    a = rep["alternatives"]
    rec = next((x for x in a["alternatives"] if x["id"] == a["recommended"]), None)
    L = [_text(d.get("decision")) or "Decision summary to be written by the founder from the analysis.", ""]
    if rec:
        L += [f"- **Recommended model:** {rec['id']} {rec['name']}. {rec['decision_reason']}"]
    for x in a["alternatives"]:
        if x["decision"] in ("viable", "reject"):
            L.append(f"- **{'Viable alternative' if x['decision'] == 'viable' else 'Rejected'}:** {x['id']} "
                     f"{x['name']}. {x['decision_reason']}")
    L.append(f"- **Maturity:** {rep['maturity']['label']}.")
    crit = [x for x in rep["assumptions"] if x["critical"]]
    if crit:
        L.append("- **Test before committing:** " + "; ".join(f"{x['id']} {x['description']}" for x in crit[:6]) + ".")
    blk = [x for x in rep["dependencies"] if x["status"] != "verified" and x["type"] in ("payment", "payout",
                                                                                        "regulatory", "tax")]
    if blk:
        L.append("- **Confirm before launch:** " + "; ".join(f"{x['id']} {x['name']} ({x['status']})"
                                                            for x in blk) + ".")
    return L + [""]


REPORT_SECTIONS = ("summary", "decision", "maturity", "canvas", "value-proposition", "classification", "revenue",
                   "costs", "financials", "marketplace", "payments", "alternatives", "assumptions", "stress",
                   "gaps", "next")


def report_md(rep: Dict, out_dir: str, sections: Optional[List[str]] = None, title: str = "",
              segment: Optional[str] = None, only_model: Optional[str] = None) -> str:
    spec = rep["_spec"]
    d = spec.get("design", {}) or {}
    # realpath both sides: on macOS /var is a symlink to /private/var, so a plain relpath can walk out of the wrong tree
    prof = os.path.relpath(os.path.realpath(rep["profile_dir"]), os.path.realpath(out_dir)) if rep["profile_dir"] else None
    fm = {"title": title or "Business model design",
          "subtitle": d.get("subtitle", "How value is created, delivered and captured, and what must be tested "
                                        "before committing"),
          "company": rep["company"], "date": d.get("date", _dt.date.today().strftime("%B %Y")),
          "doc_type": "business-model", "doc_type_label": "Business model design",
          "confidentiality": d.get("confidentiality", "Confidential")}
    if prof:
        fm["profile"] = prof
    if d.get("illustrative"):
        fm["disclaimer"] = d["illustrative"]
    L = cd._front_matter(fm)
    secs: "OrderedDict[str, List[str]]" = OrderedDict()

    def sec(key, heading, body):
        secs[key] = [f"# {heading}", ""] + body

    sec("summary", "Executive summary", [
        _text(d.get("summary")) or "Summary to be written by the founder from the analysis below.", "",
        f"> [!KEY] Maturity: {rep['maturity']['label']}. Model types: "
        f"{', '.join(rep['classification']['labels']) or 'not set'}. Revenue streams: {len(rep['revenue'])} "
        f"({', '.join(sorted({s['stage'] for s in rep['revenue']})) or 'none'}). Assumptions: "
        f"{len(rep['assumptions'])}, of which {sum(1 for a in rep['assumptions'] if a['critical'])} critical.", ""])
    sec("decision", "Founder decision summary", decision_md(rep))
    sec("maturity", "Evidence and maturity", maturity_md(rep))
    sec("canvas", "Business Model Canvas", canvas_table(rep))
    sec("value-proposition", "Value Proposition Canvas", vpc_md(rep, segment))
    sec("classification", "Business model classification", classification_md(rep))
    sec("revenue", "Revenue architecture", revenue_md(rep))
    sec("costs", "Cost structure", costs_md(rep))
    sec("financials", "Financial architecture", financials_md(rep))
    sec("marketplace", "Marketplace model", marketplace_md(rep))
    sec("payments", "Payments, geography and regulation", payments_md(rep))
    sec("alternatives", "Business model alternatives", alternatives_md(rep, only_model))
    sec("assumptions", "Assumption register", assumptions_md(rep))
    sec("stress", "Stress tests", stress_md(rep))
    sec("gaps", "Evidence gaps", [f"- {g}" for g in rep["gaps"]] or ["No critical gaps recorded."])
    sec("next", "Next steps", [f"- {x}" for x in _ids(d.get("next_steps"))] or
        ["To be decided by the founder from the gaps and stress tests above."])
    keys = sections or list(secs)
    for k in keys:
        if k not in secs:
            raise ValueError(f"unknown section '{k}'; choose from {', '.join(secs)}")
        L += secs[k] + [""]
    return "\n".join(L)


def analysis_md(rep: Dict) -> str:
    L = [f"## Business model analysis: {rep['company']}", "",
         f"Maturity: **{rep['maturity']['label']}**", "",
         f"Model: {', '.join(rep['classification']['labels']) or 'not set'} · revenue streams: {len(rep['revenue'])} · "
         f"costs: {len(rep['costs']['rows'])} · assumptions: {len(rep['assumptions'])} · alternatives: "
         f"{len(rep['alternatives']['alternatives'])}", ""]
    if rep["gaps"]:
        L += ["### Evidence gaps", ""] + [f"- {g}" for g in rep["gaps"]] + [""]
    if rep["unregistered"]:
        L += ["### Ledger assumptions not yet in the register", ""] + [
            f"- {u['id']} ({u['status']}): {u['claim']}" for u in rep["unregistered"]] + [""]
    if rep["issues"]:
        L += ["### Engine findings", ""] + [f"- **{i['level']}** ({i['area']}): {i['message']}" for i in rep["issues"]]
    return "\n".join(L) + "\n"


# ----------------------------------------------------------------------------- workbook
def workbook(rep: Dict, path: str) -> Dict:
    """Canvas, revenue, costs, assumptions, comparison and a live-formula stress sheet. No invented values."""
    import openpyxl
    from openpyxl.styles import Alignment, Font, PatternFill
    from openpyxl.utils import get_column_letter
    from .xlsx import BLUE
    head = PatternFill("solid", fgColor="F3F4F1")
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "README"
    lines = [(f"{rep['company']} business model workbook", Font(size=16, bold=True)),
             (f"Maturity: {rep['maturity']['label']}", None), ("", None),
             ("Blue cells on the Stress sheet are inputs copied from the spec; blank means unknown. Results are "
              "formulas and stay blank until their inputs exist.", None),
             ("Nothing in this workbook is a forecast. Assumptions and estimates keep their labels.",
              Font(bold=True, color="B4423A")),
             ("Generated by Startup Skills (startup-kit business-model).", Font(color="9AA3AD", size=9))]
    for i, (t, f) in enumerate(lines, 1):
        c = ws.cell(i, 1, t)
        if f:
            c.font = f
    ws.column_dimensions["A"].width = 110

    def sheet(name, header, rows, widths=None):
        sh = wb.create_sheet(name)
        for j, h in enumerate(header, 1):
            c = sh.cell(1, j, h)
            c.font = Font(bold=True)
            c.fill = head
            c.alignment = Alignment(wrap_text=True)
            sh.column_dimensions[get_column_letter(j)].width = (widths or {}).get(j, 22)
        for r in rows:
            sh.append(r)
        sh.freeze_panes = "B2"
        return sh

    sheet("Canvas", ["Block", "Item", "Basis", "Evidence", "Evidence status"],
          [[b["label"], i["text"], BASES.get(i["basis"], i["basis"]), ", ".join(i["evidence"]), i["status"]]
           for b in rep["canvas"].values() for i in b["items"]], {2: 60})
    sheet("Revenue", ["ID", "Stream", "Payer", "Pays for", "Mechanism", "Billing", "Price", "Price status",
                      "Take rate", "Stage", "Dependencies", "Evidence"],
          [[s["id"], s["name"], s["payer"], s["value"], s["mechanism"], s["billing"], s["price"], s["price_status"],
            s["take_rate"], s["stage"], ", ".join(s["dependencies"]), ", ".join(s["evidence"])]
           for s in rep["revenue"]], {4: 40})
    sheet("Costs", ["ID", "Cost", "Category", "Type", "Driver", "Amount", "Unit", "Status", "Basis"],
          [[r["id"], r["name"], r["category"], r["type"], r["driver"], r["value"], r["unit"], r["status"],
            r["basis"] or ", ".join(r["evidence"])] for r in rep["costs"]["rows"]])
    sheet("Assumptions", ["ID", "Assumption", "Category", "Why it matters", "Impact", "Evidence", "Strength",
                          "Contradicting", "Status", "Validation", "Hypothesis", "Critical"],
          [[a["id"], a["description"], a["category"], a["why"], a["impact"], ", ".join(a["evidence"]), a["strength"],
            ", ".join(a["contradicting"]), a["status"], a["validation"], a["hypothesis"],
            "yes" if a["critical"] else ""] for a in rep["assumptions"]], {2: 50, 4: 40, 10: 40})
    alts = rep["alternatives"]
    sheet("Comparison", ["Criterion"] + [f"{x['id']} {x['name']}" for x in alts["alternatives"]],
          [[c["label"]] + [f"{x['ratings'][k]['level']}: {x['ratings'][k]['why']}" for x in alts["alternatives"]]
           for k, c in alts["criteria"].items()] + [["Decision"] + [x["decision"] for x in alts["alternatives"]]],
          {j: 40 for j in range(2, 2 + len(alts["alternatives"]))})
    st = wb.create_sheet("Stress")
    st.column_dimensions["A"].width = 46
    st.column_dimensions["B"].width = 18
    st.column_dimensions["C"].width = 16
    st.cell(1, 1, "Input").font = Font(bold=True)
    st.cell(1, 2, "Value").font = Font(bold=True)
    st.cell(1, 3, "Status").font = Font(bold=True)
    names = ("price", "take_rate", "payment_fee_rate", "delivery_cost", "support_cost", "transactions_per_month",
             "fixed_costs_month", "cac", "purchases_per_customer")
    ref = {}
    for n, k in enumerate(names, 2):
        st.cell(n, 1, k)
        c = st.cell(n, 2, rep["stress"]["inputs"].get(k))
        c.font = Font(color=BLUE)
        st.cell(n, 3, rep["stress"]["input_status"].get(k, "unknown"))
        ref[k] = f"B{n}"
    fee_platform = rep["stress"]["bearer"] in ("platform", "")
    r0 = len(names) + 3
    st.cell(r0, 1, "Result (formula)").font = Font(bold=True)
    pf = f"{ref['price']}*{ref['payment_fee_rate']}" if fee_platform else "0"
    contrib = (f"{ref['price']}*{ref['take_rate']}-{pf}-{ref['delivery_cost']}-{ref['support_cost']}")
    need_c = [ref[k] for k in ("price", "take_rate", "payment_fee_rate", "delivery_cost", "support_cost")]

    def guard(cells, expr):
        return "=IF(AND(" + ",".join(f"ISNUMBER({c})" for c in cells) + f"),{expr},\"\")"
    formulas = [
        ("Contribution per transaction", guard(need_c, contrib)),
        ("Break-even transactions per month", guard(need_c + [ref["fixed_costs_month"]],
                                                    f"IF(({contrib})>0,{ref['fixed_costs_month']}/({contrib}),\"\")")),
        ("Monthly result before acquisition", guard(need_c + [ref["fixed_costs_month"], ref["transactions_per_month"]],
                                                    f"({contrib})*{ref['transactions_per_month']}-"
                                                    f"{ref['fixed_costs_month']}")),
        ("Highest affordable CAC", guard(need_c + [ref["purchases_per_customer"]],
                                         f"({contrib})*{ref['purchases_per_customer']}")),
    ]
    for n, (label, f) in enumerate(formulas, r0 + 1):
        st.cell(n, 1, label)
        st.cell(n, 2, f).number_format = "#,##0.00"
    wb.properties.title = f"{rep['company']} business model"
    wb.properties.creator = "Startup Skills"
    os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
    wb.save(path)
    return {"path": path, "sheets": wb.sheetnames, "formulas": len(formulas)}


# ----------------------------------------------------------------------------- document guard
GMV_REVENUE_RE = re.compile(r"\b(?:GMV|gross merchandise value)\b[^.\n]{0,40}\b(?:is|as|=|equals|counts as|"
                            r"becomes|of)\b[^.\n]{0,15}\b(?:our |the platform's |platform )?revenue\b|"
                            r"\brevenue\b[^.\n]{0,12}\b(?:is|was|of|=|equals)\b[^.\n]{0,25}\b(?:GMV|gross merchandise "
                            r"value)\b", re.I)
GMV_OK_RE = re.compile(r"\b(not|≠|isn't|is not|only|share|portion|fraction|take rate|commission|×|times|minus|"
                       r"never|does not|differs?|versus|vs\.?|unlike)\b", re.I)
REGISTERED_RE = re.compile(r"\b\d[\d,]*\s+(?:registered|signed[- ]up|sign-?ups?)\b[^.\n]{0,60}\b(?:active|"
                           r"liquid\w*|transacting|buying|selling|demand)\b", re.I)
LIQUIDITY_RE = re.compile(r"\b(liquid marketplace|liquidity (?:is |has been )?(?:achieved|reached|proven)|"
                          r"(?:achieved|reached|proven) liquidity|strong liquidity|network effects? (?:are|is) "
                          r"(?:kicking in|working|proven|in place))\b", re.I)
VIABILITY_RE = re.compile(r"\b(viable business model|proven business model|business model (?:is|has been) "
                          r"(?:proven|validated|viable)|(?:is|are) profitable|sustainable unit economics|"
                          r"(?:canvas|model) (?:proves|validates|demonstrates))\b", re.I)
PAY_AVAIL_RE = re.compile(r"\b(stripe|paypal|international card(?:s| acquiring)?|card acquiring)\b[^.\n]{0,60}\b("
                          r"accept\w*|available|integrat\w*|enabled?|support\w*|collect\w*|pay\w*)\b|\b(accept\w*|"
                          r"via|through|using|with)\s+(stripe|paypal)\b", re.I)
PAY_OK_RE = re.compile(r"\b(not|no|unavailable|unverified|unconfirmed|if|whether|verify|verif\w*|confirm\w*|question|depend\w*|cannot|"
                       r"can't|assum\w*|never|unless|until|ask|check)\b", re.I)
LEGAL_RE = re.compile(r"\b(fully compliant|legally (?:allowed|permitted|cleared|compliant)|no licen[cs]e (?:is )?"
                      r"(?:required|needed)|is (?:completely )?legal|complies with all|(?:is|are) tax[- ]free|"
                      r"no VAT (?:applies|is due))\b", re.I)
LEGAL_OK_RE = re.compile(r"\b(not|nothing|whether|if|confirm\w*|verif\w*|adviser|advisor|lawyer|counsel|question|unclear|"
                         r"uncertain|assum\w*)\b", re.I)
PROB_RE = re.compile(r"\b\d{1,3}\s?%\s+(?:chance|probability|likelihood|likely)\b|\bprobability of (?:success|"
                     r"failure|\w+ing)\b|\b(?:odds|chance) of success\b", re.I)
STATED_RE = re.compile(r"\b(would pay|willing to pay|said they(?:'d| would) pay|waitlist|wait-list|sign-?ups?)\b"
                       r"[^.\n]{0,60}\b(proves?|proven|validated|confirms?|guarantees?|is revenue|are paying|paying "
                       r"customers|revenue)\b", re.I)
STATED_OK_RE = re.compile(r"\b(not|no|never|isn't|is not|are not|don't|does not|cannot|until|unless)\b", re.I)


def check_document(text: str, ledger: Optional[Ledger] = None, rep: Optional[Dict] = None,
                   where: str = "document") -> List[Dict]:
    """Claim guard for business model documents (reuses the GTM guard, adds business-model checks)."""
    issues = gtm.check_claims(text, ledger, where)
    geos = [g.lower() for g in (rep or {}).get("geography", [])]
    nepal = any("nepal" in g for g in geos) or bool(re.search(r"\bNepal\b", text))
    body = text
    if body.startswith("---"):
        end = body.find("\n---", 3)
        if end != -1:
            body = "\n" * body[:end + 4].count("\n") + body[end + 4:]
    in_fence = False
    for n, line in enumerate(body.split("\n"), 1):
        s = line.strip()
        if s.startswith("```"):
            in_fence = not in_fence
            continue
        if in_fence or not s or s.startswith("#") or s.startswith("|"):
            continue
        for u in SENT_SPLIT_RE.split(s):
            cited = bool(CITE_RE.search(u))
            short = u[:100]

            def err(kind, msg):
                issues.append({"level": "error", "line": n, "kind": kind, "message": f"{where}:{n}: {msg}: '{short}'"})
            if GMV_REVENUE_RE.search(u) and not GMV_OK_RE.search(u):
                err("gmv", "GMV presented as revenue; platform revenue is only the share the platform keeps")
            if REGISTERED_RE.search(u) and not re.search(r"\bnot\b|≠|\bonly\b", u, re.I):
                err("registered", "registrations presented as active participants or demand")
            if LIQUIDITY_RE.search(u) and not cited and not gtm.NEGATION_RE.search(u):
                err("liquidity", "marketplace liquidity asserted without measured evidence")
            if VIABILITY_RE.search(u) and not cited and not gtm.NEGATION_RE.search(u):
                err("viability", "viability or profitability asserted without evidence; a canvas is not proof")
            if nepal and PAY_AVAIL_RE.search(u) and not PAY_OK_RE.search(u):
                err("payments", "payment provider availability asserted for a Nepal business; verify it with the "
                                "provider and register it as a dependency")
            if qr_confusion(u):
                err("payments", "in-person cross-border QR acceptance used as if it enabled international online "
                                "checkout or seller settlement")
            if LEGAL_RE.search(u) and not LEGAL_OK_RE.search(u):
                err("legal", "legal, tax or regulatory certainty claimed; this needs qualified confirmation")
            if PROB_RE.search(u) and not cited:
                err("probability", "probability stated without evidence; scenarios are what-ifs, not odds")
            if STATED_RE.search(u) and not STATED_OK_RE.search(u):
                err("stated-wtp", "stated interest or a waitlist presented as payment or validation")
    return issues
