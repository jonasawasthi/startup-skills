"""Go-to-market engine: the deterministic half of the gtm-strategy-maker skill.

The skill decides *what* to recommend; this module checks that the
recommendation is internally consistent and honest:

* channel scoring with explicit weights, where the evidence criterion is
  computed from the ledger (never self-assessed) and scores need a rationale;
* business-model guards (e.g. paid ads before retention evidence, PLG without a
  self-serve product, outbound sales to low-price consumers);
* growth metrics that are computed only when every input exists; otherwise the
  formula and the missing inputs are returned instead of a number;
* pricing checks (researched vs hypothesis prices, unsourced competitor prices);
* marketplace side priority with visible arithmetic, and concentration guards;
* roadmap realism (effort vs team capacity, spend vs budget, dependencies);
* a claim guard for strategy documents (market size, customer, revenue and
  validation claims without evidence);
* a KPI tracker workbook with live formulas and no invented values.

Spec format: skills/gtm-strategy-maker/references/gtm-spec.md
"""
from __future__ import annotations

import os
import re
from typing import Any, Dict, List, Optional, Tuple

import yaml

from .evidence import CITE_RE, Ledger, _table_header, cited_ids

STATUS_ORDER = ["contradicted", "unverified", "assumption", "estimate", "reported", "verified"]
EVIDENCE_SCORE = {"verified": 5, "reported": 4, "estimate": 3, "assumption": 2, "unverified": 1, "contradicted": 1}
EARLY_STAGES = ("idea", "pre-seed")

CRITERIA = {  # key: (label, default weight)
    "customer_fit": ("Customer fit", 0.25),
    "economics": ("Economics", 0.20),
    "speed": ("Speed to signal", 0.15),
    "resources": ("Resource fit", 0.15),
    "scalability": ("Scalability", 0.10),
}
EVIDENCE_WEIGHT = 0.15
PLAYBOOK_FIELDS = ("why", "execution", "resources", "cost", "leading_indicators", "success_metrics", "risks",
                   "experiment")
EXPERIMENT_FIELDS = ("hypothesis", "metric", "threshold", "budget", "duration", "kill")

CHANNELS = {
    "founder-led-sales": "Founder-led sales",
    "outbound": "Direct sales and outbound",
    "content": "Content marketing",
    "seo": "SEO",
    "social": "Social media",
    "community": "Community-led growth",
    "referral": "Referral programme",
    "partnerships": "Partnerships",
    "influencer": "Influencer and creator marketing",
    "email": "Email marketing",
    "paid-ads": "Paid advertising",
    "affiliate": "Affiliate programme",
    "product-led": "Product-led growth",
    "developer-led": "Developer-led growth",
    "pr": "Public relations",
    "events": "Events and offline distribution",
}

MODELS = ("b2b-saas", "enterprise", "consumer-app", "marketplace", "creator-platform", "education", "devtool",
          "services", "ecommerce")
MARKETPLACE_MODELS = ("marketplace", "creator-platform")
CONSUMER_MODELS = ("consumer-app", "ecommerce", "education", "creator-platform", "marketplace")

# AARRR KPI sets per model: (stage, metric key) — metric keys refer to METRICS below
MODEL_KPIS = {
    "b2b-saas": ["visitor_signup", "activation_rate", "logo_churn", "arpu", "cac", "payback_months", "ltv_cac"],
    "enterprise": ["purchase_conversion", "arpu", "logo_churn", "cac", "payback_months", "ltv_cac"],
    "consumer-app": ["visitor_signup", "activation_rate", "logo_churn", "arpu", "cac", "ltv_cac", "referral_rate"],
    "marketplace": ["activation_rate", "liquidity", "supply_utilisation", "repeat_purchase_rate", "take_rate", "cac",
                    "aov"],
    "creator-platform": ["activation_rate", "liquidity", "supply_utilisation", "repeat_purchase_rate", "take_rate",
                         "cac", "aov"],
    "education": ["visitor_signup", "activation_rate", "purchase_conversion", "completion_rate",
                  "repeat_purchase_rate", "cac", "aov"],
    "devtool": ["visitor_signup", "activation_rate", "purchase_conversion", "logo_churn", "arpu", "cac"],
    "services": ["purchase_conversion", "repeat_purchase_rate", "aov", "cac"],
    "ecommerce": ["visitor_signup", "purchase_conversion", "repeat_purchase_rate", "aov", "cac", "ltv_cac"],
}

# metric key: (name, AARRR stage, formula text, inputs, function, kind)
METRICS: Dict[str, Tuple[str, str, str, Tuple[str, ...], Any, str]] = {
    "visitor_signup": ("Visitor → sign-up", "Acquisition", "signups ÷ visitors", ("signups", "visitors"),
                       lambda v: v["signups"] / v["visitors"], "pct"),
    "activation_rate": ("Activation rate", "Activation", "activated ÷ signups", ("activated", "signups"),
                        lambda v: v["activated"] / v["signups"], "pct"),
    "purchase_conversion": ("Purchase conversion", "Revenue", "new_customers ÷ activated",
                            ("new_customers", "activated"), lambda v: v["new_customers"] / v["activated"], "pct"),
    "completion_rate": ("Course completion", "Retention", "completions ÷ enrolments", ("completions", "enrolments"),
                        lambda v: v["completions"] / v["enrolments"], "pct"),
    "logo_churn": ("Churn (period)", "Retention", "customers_lost ÷ customers_start",
                   ("customers_lost", "customers_start"), lambda v: v["customers_lost"] / v["customers_start"], "pct"),
    "repeat_purchase_rate": ("Repeat purchase rate", "Retention", "repeat_customers ÷ customers",
                             ("repeat_customers", "customers"), lambda v: v["repeat_customers"] / v["customers"], "pct"),
    "referral_rate": ("Referral rate", "Referral", "referred_signups ÷ signups", ("referred_signups", "signups"),
                      lambda v: v["referred_signups"] / v["signups"], "pct"),
    "arpu": ("ARPU (period)", "Revenue", "revenue ÷ active_customers", ("revenue", "active_customers"),
             lambda v: v["revenue"] / v["active_customers"], "money"),
    "aov": ("Average order value", "Revenue", "gmv ÷ orders", ("gmv", "orders"), lambda v: v["gmv"] / v["orders"],
            "money"),
    "take_rate": ("Take rate", "Revenue", "net_revenue ÷ gmv", ("net_revenue", "gmv"),
                  lambda v: v["net_revenue"] / v["gmv"], "pct"),
    "liquidity": ("Listing sell-through (liquidity)", "Activation", "listings_with_sale ÷ listings_live",
                  ("listings_with_sale", "listings_live"), lambda v: v["listings_with_sale"] / v["listings_live"], "pct"),
    "supply_utilisation": ("Supply utilisation", "Activation", "suppliers_with_sale ÷ active_suppliers",
                           ("suppliers_with_sale", "active_suppliers"),
                           lambda v: v["suppliers_with_sale"] / v["active_suppliers"], "pct"),
    "cac": ("Blended CAC", "Acquisition", "acquisition_spend ÷ new_customers", ("acquisition_spend", "new_customers"),
            lambda v: v["acquisition_spend"] / v["new_customers"], "money"),
    "ltv_subscription": ("LTV (subscription)", "Revenue", "arpu × gross_margin ÷ churn",
                         ("arpu", "gross_margin", "churn"), lambda v: v["arpu"] * v["gross_margin"] / v["churn"],
                         "money"),
    "ltv_transactional": ("LTV (transactional)", "Revenue", "aov × contribution_margin × purchases_per_customer",
                          ("aov", "contribution_margin", "purchases_per_customer"),
                          lambda v: v["aov"] * v["contribution_margin"] * v["purchases_per_customer"], "money"),
    "ltv_cac": ("LTV : CAC", "Revenue", "ltv ÷ cac", ("ltv", "cac"), lambda v: v["ltv"] / v["cac"], "ratio"),
    "payback_months": ("CAC payback (months)", "Revenue", "cac ÷ (arpu × gross_margin)",
                       ("cac", "arpu", "gross_margin"), lambda v: v["cac"] / (v["arpu"] * v["gross_margin"]), "months"),
}
# derived values feed later metrics (metric key -> input name)
DERIVES = {"arpu": "arpu", "aov": "aov", "cac": "cac", "logo_churn": "churn", "ltv_subscription": "ltv",
           "ltv_transactional": "ltv"}
RETENTION_INPUTS = ("churn", "customers_lost", "repeat_customers", "retention_d30", "retention_m1")


# ----------------------------------------------------------------------------- helpers
def _issue(level: str, area: str, message: str) -> Dict:
    return {"level": level, "area": area, "message": message}


def _ids(ev) -> List[str]:
    if not ev:
        return []
    return [str(x) for x in ev] if isinstance(ev, (list, tuple)) else [str(ev)]


def _worst(statuses: List[str]) -> str:
    return min(statuses, key=lambda s: STATUS_ORDER.index(s) if s in STATUS_ORDER else 0) if statuses else "assumption"


def _status_of(item: Any, ledger: Ledger) -> str:
    """Status of a {value, evidence|status} input: worst cited evidence, else the declared status."""
    if isinstance(item, dict):
        ids = _ids(item.get("evidence"))
        if ids:
            sts = [ledger.get(i).status for i in ids if ledger.get(i)]
            return _worst(sts) if sts else "unverified"
        return str(item.get("status", "assumption"))
    return "assumption"


def _val(item: Any):
    if isinstance(item, dict):
        return item.get("value")
    return item


def _text(x) -> str:
    if x is None:
        return ""
    if isinstance(x, (list, tuple)):
        return "; ".join(_text(i) for i in x)
    if isinstance(x, dict):
        return "; ".join(f"{k}: {_text(v)}" for k, v in x.items())
    return str(x).strip()


def _cell(x) -> str:
    return _text(x).replace("|", "/").replace("\n", " ")


def _cite(ids: List[str]) -> str:
    return f" [{', '.join(ids)}]" if ids else ""


def fmt_value(v: float, kind: str, currency: str = "") -> str:
    if kind == "pct":
        return f"{v * 100:.1f}%"
    if kind == "ratio":
        return f"{v:.1f}x"
    if kind == "months":
        return f"{v:.1f} months"
    if kind == "money":
        return f"{v:,.2f} {currency}".strip() if abs(v) < 100 else f"{v:,.0f} {currency}".strip()
    return f"{v:,.2f}"


# ----------------------------------------------------------------------------- loading
def load_spec(path: str) -> Dict:
    with open(path) as f:
        try:
            spec = yaml.safe_load(f) or {}
        except yaml.YAMLError as e:
            raise ValueError(f"{path} is not valid YAML ({str(e).splitlines()[0]}). Text containing commas, "
                             "colons or [E-001] citations inside [flow, lists] must be quoted.\n" + str(e)) from None
    if not isinstance(spec, dict):
        raise ValueError("GTM spec must be a YAML mapping")
    return spec


def resolve_context(spec: Dict, base: str) -> Tuple[Ledger, Dict, Optional[str]]:
    """Ledger, profile.yaml contents and profile dir for a spec (paths relative to the spec)."""
    from .profile import load_profile
    g = spec.get("gtm", {}) or {}
    prof_dir = g.get("profile")
    if prof_dir and not os.path.isabs(prof_dir):
        prof_dir = os.path.normpath(os.path.join(base, prof_dir))
    ev = g.get("evidence") or (os.path.join(prof_dir, "evidence.yaml") if prof_dir else None)
    if ev and not os.path.isabs(ev):
        ev = os.path.normpath(os.path.join(base, ev))
    ledger = Ledger.load(ev) if ev else Ledger([])
    profile = load_profile(prof_dir) if prof_dir else {}
    return ledger, profile, prof_dir


def model_types(spec: Dict) -> List[str]:
    bm = spec.get("business_model", {}) or {}
    types = [bm.get("type")] + list(bm.get("secondary_types") or [])
    return [t for t in types if t]


def check_evidence_ids(spec: Dict, ledger: Ledger) -> List[Dict]:
    """Every evidence ID anywhere in the spec must exist in the ledger."""
    issues, seen = [], set()

    def walk(o, path):
        if isinstance(o, dict):
            for k, v in o.items():
                if k == "evidence":
                    for i in _ids(v):
                        if i not in ledger and (i, path) not in seen:
                            seen.add((i, path))
                            issues.append(_issue("error", "evidence", f"{path or 'spec'} cites {i}, which is not in "
                                                                      "the ledger"))
                else:
                    walk(v, f"{path}.{k}" if path else str(k))
        elif isinstance(o, list):
            for n, v in enumerate(o):
                label = v.get("name") or v.get("key") or v.get("id") if isinstance(v, dict) else None
                walk(v, f"{path}[{label or n}]")
    walk(spec, "")
    return issues


# ----------------------------------------------------------------------------- channels
def evidence_score(ids: List[str], ledger: Ledger) -> int:
    """1..5 from the *strongest* cited entry. No evidence = 1. Computed, never self-assessed."""
    sts = [ledger.get(i).status for i in ids if ledger.get(i)]
    return max((EVIDENCE_SCORE.get(s, 1) for s in sts), default=1)


def score_channels(spec: Dict, ledger: Ledger) -> Tuple[List[Dict], List[Dict]]:
    issues: List[Dict] = []
    weights = {k: w for k, (_, w) in CRITERIA.items()}
    weights.update({k: float(v) for k, v in (spec.get("channel_weights") or {}).items() if k in CRITERIA})
    max_primary = int(spec.get("max_primary_channels", 3))
    if max_primary > 4:
        issues.append(_issue("warning", "channels", f"max_primary_channels is {max_primary}; early teams rarely "
                                                    "run more than 3 channels well (product-channel fit is a power law)"))
    rows = []
    for ch in spec.get("channels", []) or []:
        key = str(ch.get("key", "")).strip()
        name = ch.get("name") or CHANNELS.get(key, key)
        if key not in CHANNELS:
            issues.append(_issue("info", "channels", f"'{key}' is not in the channel catalogue; scored as custom"))
        scores = ch.get("scores") or {}
        bad = False
        for c in CRITERIA:
            s = scores.get(c)
            if not isinstance(s, (int, float)) or not 1 <= s <= 5:
                issues.append(_issue("error", "channels", f"{name}: score '{c}' must be a number from 1 to 5"))
                bad = True
        if "evidence" in scores:
            issues.append(_issue("warning", "channels", f"{name}: the evidence score is computed from the ledger; "
                                                        "the declared value was ignored"))
        if not _text(ch.get("why")):
            issues.append(_issue("error", "channels", f"{name}: scores need a rationale ('why': why this fits the "
                                                      "target customer)"))
        ids = _ids(ch.get("evidence"))
        ev = evidence_score(ids, ledger)
        total = None
        if not bad:
            wsum = sum(weights.values()) + EVIDENCE_WEIGHT
            # round: weighted sums such as 3.0 otherwise land at 2.9999… and miss a threshold
            total = round((sum(weights[c] * float(scores[c]) for c in CRITERIA) + EVIDENCE_WEIGHT * ev) / wsum, 6)
        rows.append({"key": key, "name": name, "side": ch.get("side", "both"), "scores": scores, "evidence_score": ev,
                     "evidence": ids, "total": total, "spec": ch})
    ranked = sorted([r for r in rows if r["total"] is not None], key=lambda r: -r["total"])
    primary = 0
    later = 0
    for r in ranked:
        forced = r["spec"].get("decision")
        if forced in ("primary", "test-later", "not-now"):
            r["decision"] = forced
            r["forced"] = True
        elif r["total"] >= 3.0 and primary < max_primary:
            r["decision"] = "primary"
        elif r["total"] >= 2.5 and later < 3:
            r["decision"] = "test-later"
        else:
            r["decision"] = "not-now"
        primary += r["decision"] == "primary"
        later += r["decision"] == "test-later"
    for r in rows:
        r.setdefault("decision", "unscored")
    for i, r in enumerate(ranked, 1):
        r["rank"] = i
    if primary > max_primary:
        issues.append(_issue("error", "channels", f"{primary} primary channels exceed the limit of {max_primary}; "
                                                  "prioritise"))
    if rows and primary == 0:
        issues.append(_issue("warning", "channels", "no channel scored high enough to be primary (total ≥ 3.0); "
                                                    "the plan should start with customer discovery"))
    for r in ranked:
        if r["decision"] != "primary":
            continue
        ch = r["spec"]
        for f in PLAYBOOK_FIELDS:
            if not ch.get(f):
                issues.append(_issue("error", "channels", f"{r['name']}: primary channel needs '{f}'"))
        exp = ch.get("experiment") or {}
        if isinstance(exp, dict) and exp:
            miss = [f for f in EXPERIMENT_FIELDS if not exp.get(f)]
            if miss:
                issues.append(_issue("error", "channels", f"{r['name']}: experiment needs {', '.join(miss)}"))
    return ranked + [r for r in rows if r["total"] is None], issues


def model_guards(spec: Dict, channels: List[Dict], metric_values: Dict[str, Any], stage: str) -> List[Dict]:
    """Warnings where a primary channel conflicts with the business model, stage or evidence."""
    issues = []
    types = model_types(spec)
    bm = spec.get("business_model", {}) or {}
    if not types:
        issues.append(_issue("error", "model", "business_model.type is required (one of: " + ", ".join(MODELS) + ")"))
    for t in types:
        if t not in MODELS:
            issues.append(_issue("warning", "model", f"unknown business model '{t}'; known: {', '.join(MODELS)}"))
    has_retention = any(metric_values.get(k) is not None for k in RETENTION_INPUTS) or bool(spec.get("cohorts"))
    has_base = metric_values.get("active_customers") not in (None, 0) or metric_values.get("customers") not in (None, 0)
    for r in channels:
        if r.get("decision") != "primary":
            continue
        k, side, n = r["key"], r.get("side", "both"), r["name"]
        if k == "outbound" and side in ("demand", "both") and any(t in CONSUMER_MODELS for t in types):
            issues.append(_issue("warning", "model", f"{n}: outbound sales to consumer buyers rarely pays back at "
                                                     "consumer price points; restrict it to the supply side or justify"))
        if k in ("paid-ads", "affiliate") and not has_retention:
            issues.append(_issue("warning", "model", f"{n}: scaling channel chosen before any retention evidence; "
                                                     "keep it a capped experiment until a cohort is measured"))
        if k == "referral" and stage in EARLY_STAGES and not has_base:
            issues.append(_issue("warning", "model", f"{n}: referral programmes amplify an active, satisfied base; "
                                                     "there is no measured customer base yet"))
        if k in ("product-led", "developer-led") and not bm.get("self_serve"):
            issues.append(_issue("warning", "model", f"{n}: needs a self-serve product (business_model.self_serve "
                                                     "is not true)"))
        if k in ("seo", "content") and stage in EARLY_STAGES:
            issues.append(_issue("info", "model", f"{n}: slow to produce a signal (months); pair it with a fast "
                                                  "channel for the first 90 days"))
        if k in ("paid-ads", "affiliate") and "enterprise" in types:
            issues.append(_issue("warning", "model", f"{n}: enterprise buyers are rarely acquired through {k}"))
        if k == "outbound" and "devtool" in types and side != "supply":
            issues.append(_issue("warning", "model", f"{n}: developer tools usually need developer adoption before "
                                                     "outbound works"))
        if (k == "paid-ads" and side in ("demand", "both") and any(t in MARKETPLACE_MODELS for t in types)
                and metric_values.get("listings_with_sale") is None):
            issues.append(_issue("warning", "model", f"{n}: paying for demand before supply liquidity is measured "
                                                     "risks sending buyers to an empty marketplace"))
    return issues


# ----------------------------------------------------------------------------- metrics
RECURRING_PRICING = ("subscription", "freemium", "usage", "tiered", "enterprise", "saas", "seat")


def recurring(spec: Dict) -> bool:
    """Recurring revenue (subscription-style LTV) vs transactional (purchase-based LTV)."""
    model = str((spec.get("pricing") or {}).get("model", "")).lower()
    if model:
        return any(w in model for w in RECURRING_PRICING)
    return (model_types(spec) or ["b2b-saas"])[0] in ("b2b-saas", "enterprise", "consumer-app", "devtool")


def compute_metrics(spec: Dict, ledger: Ledger) -> Tuple[List[Dict], Dict[str, Any], List[Dict]]:
    """Compute every metric whose inputs exist; report formulas and missing inputs for the rest."""
    m = spec.get("metrics", {}) or {}
    raw = m.get("inputs", {}) or {}
    cur = m.get("currency") or (spec.get("gtm", {}) or {}).get("currency", "")
    values: Dict[str, Any] = {}
    statuses: Dict[str, str] = {}
    issues: List[Dict] = []
    for k, item in raw.items():
        v = _val(item)
        if v in (None, "", "unknown"):
            continue
        try:
            values[k] = float(v)
        except (TypeError, ValueError):
            issues.append(_issue("error", "metrics", f"input '{k}' is not a number: {v!r}"))
            continue
        statuses[k] = _status_of(item, ledger)
    wanted: List[str] = []
    for t in model_types(spec):
        for key in MODEL_KPIS.get(t, []):
            if key not in wanted:
                wanted.append(key)
    for key in m.get("kpis", []) or []:
        if key in METRICS and key not in wanted:
            wanted.append(key)
        elif key not in METRICS:
            issues.append(_issue("warning", "metrics", f"unknown KPI '{key}'; known: {', '.join(METRICS)}"))
    for key in METRICS:  # also compute anything whose inputs happen to be present
        if key not in wanted and all(i in values for i in METRICS[key][3]):
            wanted.append(key)
    # LTV variant follows the revenue model: recurring -> subscription formula, otherwise transactional
    ltv_key = "ltv_subscription" if recurring(spec) else "ltv_transactional"
    wanted = [k for k in wanted if not (k.startswith("ltv_") and k != "ltv_cac" and k != ltv_key
                                        and not all(i in values for i in METRICS[k][3]))]
    if "ltv_cac" in wanted and ltv_key not in wanted:
        wanted.append(ltv_key)
    if "ltv_cac" in wanted and "cac" not in wanted:
        wanted.append("cac")
    # dependencies first: derived inputs feed LTV, payback, LTV:CAC
    order = sorted(wanted, key=lambda k: (k in ("ltv_cac", "payback_months"), k.startswith("ltv")))
    out = []
    for key in order:
        name, stage, formula, inputs, fn, kind = METRICS[key]
        tgt = DERIVES.get(key)
        if tgt and tgt in raw and tgt in values and not all(i in values for i in inputs):
            # the founder supplied the metric itself (e.g. churn from a billing report): report it as given
            out.append({"key": key, "name": name, "stage": stage, "formula": f"supplied as '{tgt}'",
                        "inputs": [tgt], "missing": [], "value": values[tgt], "status": statuses[tgt],
                        "display": fmt_value(values[tgt], kind, cur)})
            continue
        missing = [i for i in inputs if i not in values]
        row = {"key": key, "name": name, "stage": stage, "formula": formula, "inputs": list(inputs),
               "missing": missing, "value": None, "display": "", "status": None}
        if not missing:
            try:
                v = fn(values)
                row["value"] = v
                row["status"] = _worst([statuses.get(i, "assumption") for i in inputs])
                row["display"] = fmt_value(v, kind, cur)
                tgt = DERIVES.get(key)
                if tgt and tgt not in values:
                    values[tgt] = v
                    statuses[tgt] = row["status"]
            except ZeroDivisionError:
                row["missing"] = [f"non-zero {i}" for i in inputs]
                row["display"] = "undefined (division by zero)"
        out.append(row)
    cohort_rows = []
    for c in spec.get("cohorts", []) or []:
        size = c.get("size")
        act = c.get("active") or []
        if not size:
            issues.append(_issue("error", "metrics", f"cohort {c.get('name', '?')}: size is required"))
            continue
        cohort_rows.append({"name": c.get("name", ""), "size": size,
                            "retention": [a / size for a in act], "evidence": _ids(c.get("evidence"))})
    if cohort_rows:
        out.append({"key": "cohorts", "name": "Cohort retention", "stage": "Retention", "formula":
                    "active in period n ÷ cohort size", "inputs": ["cohorts"], "missing": [], "value": cohort_rows,
                    "display": "see cohort table", "status": "reported"})
    return out, values, issues


# ----------------------------------------------------------------------------- pricing
def pricing_check(spec: Dict, ledger: Ledger) -> Tuple[Dict, List[Dict]]:
    p = spec.get("pricing")
    issues: List[Dict] = []
    if not p:
        return {}, [_issue("warning", "pricing", "no pricing section; record the model, value metric and price "
                                                 "hypotheses")]
    if not p.get("model"):
        issues.append(_issue("error", "pricing", "pricing.model is required (freemium, subscription, one-time, "
                                                 "commission, transaction, usage, tiered, enterprise, hybrid)"))
    if not p.get("value_metric"):
        issues.append(_issue("warning", "pricing", "no value metric: name the unit the customer pays for"))
    points = []
    for pp in p.get("price_points", []) or []:
        basis = pp.get("basis")
        ids = _ids(pp.get("evidence"))
        st = _status_of({"evidence": ids, "status": "assumption"}, ledger) if ids else "assumption"
        nm = pp.get("name", "price point")
        if basis not in ("researched", "hypothesis"):
            issues.append(_issue("error", "pricing", f"{nm}: basis must be 'researched' or 'hypothesis'"))
        if basis == "researched" and (not ids or st not in ("verified", "reported")):
            issues.append(_issue("error", "pricing", f"{nm}: marked researched but its evidence is "
                                                     f"'{st if ids else 'missing'}'; mark it a hypothesis or cite a "
                                                     "verified/reported source"))
        points.append({**pp, "status": st if ids else ("hypothesis" if basis == "hypothesis" else "unsourced")})
    for c in p.get("competitors", []) or []:
        if not _ids(c.get("evidence")):
            issues.append(_issue("error", "pricing", f"competitor price for {c.get('name', '?')} has no evidence "
                                                     "(cite the pricing page with an access date)"))
    hyps = [pp.get("name") for pp in points if pp.get("basis") == "hypothesis"]
    tested = set()
    for e in p.get("experiments", []) or []:
        for f in ("hypothesis", "metric", "threshold", "duration"):
            if not e.get(f):
                issues.append(_issue("error", "pricing", f"pricing experiment '{e.get('name', '?')}' needs '{f}'"))
        for t in _ids(e.get("tests")):
            tested.add(t)
    for h in hyps:
        if h not in tested:
            issues.append(_issue("warning", "pricing", f"price hypothesis '{h}' has no experiment (add one with "
                                                       f"tests: [{h}])"))
    model = str(p.get("model", ""))
    if any(w in model for w in ("commission", "transaction")):
        tr = _val(p.get("take_rate"))
        if tr is None:
            issues.append(_issue("error", "pricing", "commission/transaction model needs take_rate"))
        elif not 0 < float(tr) < 1:
            issues.append(_issue("error", "pricing", f"take_rate {tr} must be between 0 and 1"))
    return {"model": model, "value_metric": p.get("value_metric"), "points": points,
            "competitors": p.get("competitors", []) or [], "experiments": p.get("experiments", []) or [],
            "take_rate": p.get("take_rate")}, issues


# ----------------------------------------------------------------------------- marketplace
def marketplace_analysis(spec: Dict, ledger: Ledger) -> Tuple[Dict, List[Dict]]:
    mk = spec.get("marketplace")
    types = model_types(spec)
    issues: List[Dict] = []
    if not mk:
        if any(t in MARKETPLACE_MODELS for t in types):
            issues.append(_issue("error", "marketplace", "marketplace or creator-platform model needs a "
                                                         "'marketplace' section (sides, launch focus, atomic network)"))
        return {}, issues
    sides = []
    for s in mk.get("sides", []) or []:
        d = s.get("difficulty")
        if not isinstance(d, (int, float)) or not 1 <= d <= 5:
            issues.append(_issue("error", "marketplace", f"side {s.get('name', '?')}: difficulty must be 1–5"))
            continue
        score = float(d) + (2 if s.get("brings_other_side") else 0) + (1 if s.get("standalone_value") else 0)
        parts = [f"difficulty {d}"] + (["+2 brings the other side"] if s.get("brings_other_side") else []) + (
            ["+1 standalone value"] if s.get("standalone_value") else [])
        if not _text(s.get("why")):
            issues.append(_issue("warning", "marketplace", f"side {s.get('name')}: explain the difficulty rating "
                                                           "('why')"))
        sides.append({**s, "score": score, "working": " ".join(parts)})
    if len(sides) < 2 and mk.get("sides"):
        issues.append(_issue("warning", "marketplace", "a marketplace needs at least two sides"))
    sides.sort(key=lambda s: -s["score"])
    first = sides[0] if sides else None
    tie = len(sides) > 1 and sides[0]["score"] == sides[1]["score"]
    if tie:
        issues.append(_issue("warning", "marketplace", "sides tie on priority; decide explicitly with a reason"))
    launch = mk.get("launch", {}) or {}
    geos = launch.get("geographies") or []
    cats = launch.get("categories") or []
    if not geos or not cats:
        issues.append(_issue("warning", "marketplace", "launch focus needs at least one geography and one category"))
    if (len(geos) > 1 or len(cats) > 1) and not _text(launch.get("justification")):
        issues.append(_issue("warning", "marketplace", f"launching in {len(geos)} geographies and {len(cats)} "
                                                       "categories at once dilutes density; concentrate or give a "
                                                       "justification"))
    for f, msg in (("atomic_network", "define the atomic network (smallest self-sustaining unit)"),
                   ("liquidity_target", "set a liquidity target (e.g. share of listings with a sale in 30 days)"),
                   ("trust_safety", "list trust and safety mechanisms before scaling"),):
        if not mk.get(f):
            issues.append(_issue("warning", "marketplace", msg))
    p = spec.get("pricing") or {}
    if (p.get("take_rate") is not None or mk.get("take_rate") is not None) and not mk.get("disintermediation_defence"):
        issues.append(_issue("warning", "marketplace", "take rate without a disintermediation defence (why "
                                                       "transactions stay on-platform)"))
    return {"sides": sides, "first": first, "tie": tie, "launch": launch, "spec": mk}, issues


# ----------------------------------------------------------------------------- roadmap
STANDARD_ENDS = (30, 60, 90, 180, 365)


def roadmap_check(spec: Dict) -> Tuple[List[Dict], List[Dict]]:
    rm = spec.get("roadmap", {}) or {}
    phases = rm.get("phases", []) or []
    issues: List[Dict] = []
    if not phases:
        return [], [_issue("warning", "roadmap", "no roadmap phases")]
    team = spec.get("team", {}) or {}
    people = float(team.get("people", 0) or 0)
    hours = float(team.get("hours_per_week", 40) or 0)
    roles = {str(r).lower() for r in team.get("roles", []) or []}
    if not people:
        issues.append(_issue("error", "roadmap", "team.people is required to check roadmap capacity"))
    budget = spec.get("budget", {}) or {}
    available = _val(budget.get("available")) if isinstance(budget.get("available"), dict) else budget.get("available")
    task_ids = {str(t.get("id")) for ph in phases for t in ph.get("tasks", []) or [] if t.get("id")}
    out, end, spend_total = [], 0, 0.0
    for ph in phases:
        days = int(ph.get("days", 0) or 0)
        name = ph.get("name", f"phase ending day {end + days}")
        if not days:
            issues.append(_issue("error", "roadmap", f"{name}: 'days' (phase length) is required"))
        end += days
        capacity = people * hours / 8.0 * days / 7.0  # person-days available
        tasks = ph.get("tasks", []) or []
        effort = sum(float(t.get("effort_days", 0) or 0) for t in tasks)
        spend = sum(float(t.get("cost", 0) or 0) for t in tasks) + float(ph.get("budget", 0) or 0)
        spend_total += spend
        for f in ("objectives", "tasks", "kpis", "success_criteria"):
            if not ph.get(f):
                issues.append(_issue("warning", "roadmap", f"{name}: missing '{f}'"))
        for t in tasks:
            tn = t.get("task", t.get("id", "task"))
            if not t.get("owner"):
                issues.append(_issue("warning", "roadmap", f"{name}: task '{tn}' has no owner"))
            elif roles and str(t["owner"]).lower() not in roles:
                issues.append(_issue("warning", "roadmap", f"{name}: owner '{t['owner']}' of '{tn}' is not in "
                                                           "team.roles (a hire or partner the plan depends on?)"))
            if t.get("effort_days") is None:
                issues.append(_issue("warning", "roadmap", f"{name}: task '{tn}' has no effort_days estimate"))
            for dep in _ids(t.get("depends_on")):
                if dep not in task_ids:
                    issues.append(_issue("error", "roadmap", f"{name}: '{tn}' depends on unknown task '{dep}'"))
        load = effort / capacity if capacity else None
        if capacity and effort > capacity:
            issues.append(_issue("error", "roadmap", f"{name}: {effort:.0f} person-days of work vs "
                                                     f"{capacity:.0f} available ({people:g} people × {hours:g} h/week);"
                                                     " unrealistic: cut scope or extend the phase"))
        elif capacity and effort > 0.85 * capacity:
            issues.append(_issue("warning", "roadmap", f"{name}: {load:.0%} of capacity planned; no slack for "
                                                       "support, product work or surprises"))
        out.append({"name": name, "days": days, "end": end, "effort": effort, "capacity": capacity, "load": load,
                    "spend": spend, "spec": ph})
    if available not in (None, "") and spend_total > float(available):
        issues.append(_issue("error", "roadmap", f"planned spend {spend_total:,.0f} exceeds available budget "
                                                 f"{float(available):,.0f}"))
    ends = {p["end"] for p in out}
    missing = [e for e in STANDARD_ENDS if e not in ends]
    if missing:
        issues.append(_issue("info", "roadmap", "no phase ends on day " + ", ".join(map(str, missing)) +
                             " (standard horizons: 30/60/90 days, 6 and 12 months)"))
    return out, issues


def cross_product_check(spec: Dict, phases: List[Dict]) -> Tuple[List[Dict], List[Dict]]:
    """Cross-product opportunities must respect product status and the phase they land in."""
    status = {str(p.get("name")): p.get("status", "unknown") for p in spec.get("products", []) or []}
    ends = {p["name"]: p["end"] for p in phases}
    issues, rows = [], []
    for c in spec.get("cross_product", []) or []:
        prod = str(c.get("product"))
        st = c.get("status") or status.get(prod, "unknown")
        if c.get("status") and prod in status and c["status"] != status[prod]:
            issues.append(_issue("error", "products", f"{prod}: status '{c['status']}' conflicts with products list "
                                                      f"('{status[prod]}')"))
        end = ends.get(c.get("phase"))
        if c.get("phase") and end is None:
            issues.append(_issue("warning", "products", f"{prod}: phase '{c.get('phase')}' is not a roadmap phase"))
        if end is not None and end <= 90:
            if st in ("planned", "proposed", "unknown"):
                issues.append(_issue("error", "products", f"{prod} is {st} but its opportunity is scheduled in the "
                                                          "first 90 days"))
            elif st == "in-development":
                issues.append(_issue("warning", "products", f"{prod} is in development; the first-90-day plan "
                                                            "depends on shipping it"))
            elif st == "built":
                issues.append(_issue("info", "products", f"{prod} is built, not live: private beta or pilot only "
                                                         "until it launches"))
        rows.append({**c, "status": st, "end": end})
    return rows, issues


# ----------------------------------------------------------------------------- analysis
def analyze(spec_path: str) -> Dict:
    spec = load_spec(spec_path)
    base = os.path.dirname(os.path.abspath(spec_path))
    ledger, profile, prof_dir = resolve_context(spec, base)
    g = spec.get("gtm", {}) or {}
    stage = g.get("stage") or profile.get("stage") or "unknown"
    issues: List[Dict] = []
    if not (g.get("profile") or g.get("evidence")):
        issues.append(_issue("warning", "evidence", "no profile or ledger configured; evidence cannot be checked"))
    issues += check_evidence_ids(spec, ledger)
    metrics, values, mi = compute_metrics(spec, ledger)
    channels, ci = score_channels(spec, ledger)
    issues += mi + ci + model_guards(spec, channels, values, stage)
    pricing, pi = pricing_check(spec, ledger)
    market, mki = marketplace_analysis(spec, ledger)
    phases, ri = roadmap_check(spec)
    cross, xi = cross_product_check(spec, phases)
    issues += pi + mki + ri + xi
    missing_profile = []
    if prof_dir:
        from .profile import missing_information
        missing_profile = [m for m in missing_information(prof_dir)
                           if m.split(":")[0] in ("customers.md", "market.md", "competitors.md", "business-model.md",
                                                  "traction.md", "profile.yaml")]
    return {"spec": os.path.abspath(spec_path), "company": g.get("company") or profile.get("name", ""),
            "stage": stage, "types": model_types(spec), "currency": g.get("currency", ""),
            "channels": channels, "metrics": metrics, "pricing": pricing, "marketplace": market,
            "roadmap": phases, "cross_product": cross, "issues": issues, "missing_profile": missing_profile,
            "ledger_summary": ledger.summary() if len(ledger) else {},
            "errors": sum(1 for i in issues if i["level"] == "error"),
            "warnings": sum(1 for i in issues if i["level"] == "warning"), "_spec": spec}


def analysis_md(rep: Dict) -> str:
    """Markdown+ tables the strategy document embeds (or the founder reads directly)."""
    L = [f"## GTM analysis: {rep['company']}", "",
         f"Stage: **{rep['stage']}** · Business model: **{', '.join(rep['types']) or 'unspecified'}**", ""]
    if rep["ledger_summary"]:
        L += ["Evidence base: " + ", ".join(f"{v} {k}" for k, v in rep["ledger_summary"].items() if v) + ".", ""]
    # channels
    L += ["### Channel matrix", "",
          "Scores are 1–5. *Evidence* is computed from the strongest cited ledger entry (verified 5, reported 4, "
          "estimate 3, assumption 2, none 1). Totals are weighted. Status of each score: founder judgement unless "
          "evidence is cited.", "",
          "| Rank | Channel | Side | Fit | Econ. | Speed | Resources | Scale | Evidence | Total | Decision |",
          "|---:|---|---|---:|---:|---:|---:|---:|---:|---:|---|"]
    for r in rep["channels"]:
        s = r["scores"]
        L.append(f"| {r.get('rank', '—')} | {_cell(r['name'])}{_cite(r['evidence'])} | {r['side']} | "
                 + " | ".join(str(s.get(c, '—')) for c in CRITERIA)
                 + f" | {r['evidence_score']} | {'%.2f' % r['total'] if r['total'] is not None else '—'} | "
                   f"{r['decision']}{' (founder override)' if r.get('forced') else ''} |")
    L.append("")
    for r in rep["channels"]:
        if r["decision"] != "primary":
            continue
        ch = r["spec"]
        L += [f"#### {r['name']}", ""]
        for f, label in (("why", "Why it fits"), ("execution", "How to execute"), ("resources", "Resources"),
                         ("cost", "Cost considerations"), ("leading_indicators", "Leading indicators"),
                         ("success_metrics", "Success metrics"), ("risks", "Risks and limitations")):
            if ch.get(f):
                L.append(f"- **{label}:** {_text(ch[f])}")
        e = ch.get("experiment") or {}
        if e:
            L.append(f"- **Validation experiment (hypothesis):** {_text(e.get('hypothesis'))} Metric: "
                     f"{_text(e.get('metric'))}; threshold: {_text(e.get('threshold'))}; budget: "
                     f"{_text(e.get('budget'))}; duration: {_text(e.get('duration'))}; kill if: {_text(e.get('kill'))}.")
        L.append("")
    deprior = [r for r in rep["channels"] if r["decision"] in ("not-now", "test-later")]
    if deprior:
        L += ["**Not prioritised now:** " + "; ".join(
            f"{r['name']} ({r['decision']}{': ' + _text(r['spec'].get('reason')) if r['spec'].get('reason') else ''})"
            for r in deprior) + ".", ""]
    # marketplace
    mk = rep["marketplace"]
    if mk:
        L += ["### Marketplace: which side first", "",
              "| Side | Role | Difficulty | Brings other side | Standalone value | Priority | Working |",
              "|---|---|---:|---|---|---:|---|"]
        for s in mk["sides"]:
            L.append(f"| {_cell(s.get('name'))}{_cite(_ids(s.get('evidence')))} | {s.get('role', '')} | "
                     f"{s.get('difficulty')} | {'yes' if s.get('brings_other_side') else 'no'} | "
                     f"{'yes' if s.get('standalone_value') else 'no'} | {s['score']:g} | {s['working']} |")
        L.append("")
        if mk["first"]:
            L += [f"Prioritise **{mk['first'].get('name')}** first"
                  + (" (tie: founder decision required)" if mk["tie"] else "") + f". {_text(mk['first'].get('why'))}",
                  ""]
        lf = mk["launch"]
        L += [f"- **Launch focus:** {_text(lf.get('geographies')) or 'unspecified'} · "
              f"{_text(lf.get('categories')) or 'unspecified'}"
              + (f" ({_text(lf.get('justification'))})" if lf.get("justification") else ""),
              f"- **Atomic network:** {_text(mk['spec'].get('atomic_network')) or 'not defined'}",
              f"- **Liquidity target (hypothesis):** {_text(mk['spec'].get('liquidity_target')) or 'not set'}",
              f"- **Trust and safety:** {_text(mk['spec'].get('trust_safety')) or 'not defined'}",
              f"- **Disintermediation defence:** {_text(mk['spec'].get('disintermediation_defence')) or 'not defined'}",
              ""]
    # pricing
    p = rep["pricing"]
    if p:
        L += ["### Pricing", "", f"Model: **{p['model']}** · Value metric: **{_text(p['value_metric']) or 'not set'}**",
              ""]
        if p["points"]:
            L += ["| Price point | Price | Basis | Evidence status |", "|---|---:|---|---|"]
            for pp in p["points"]:
                L.append(f"| {_cell(pp.get('name'))}{_cite(_ids(pp.get('evidence')))} | {_cell(pp.get('price'))} "
                         f"{_cell(pp.get('currency', ''))} | {pp.get('basis')} | {pp['status']} |")
            L.append("")
        if p["competitors"]:
            L += ["| Competitor / alternative | Price | Evidence status |", "|---|---|---|"]
            for c in p["competitors"]:
                L.append(f"| {_cell(c.get('name'))}{_cite(_ids(c.get('evidence')))} | {_cell(c.get('price'))} | "
                         f"{'cited' if _ids(c.get('evidence')) else 'UNSOURCED'} |")
            L.append("")
        if p["experiments"]:
            L += ["| Monetisation experiment | Hypothesis | Metric | Threshold | Duration |", "|---|---|---|---|---|"]
            for e in p["experiments"]:
                L.append(f"| {_cell(e.get('name'))} | {_cell(e.get('hypothesis'))} | {_cell(e.get('metric'))} | "
                         f"{_cell(e.get('threshold'))} | {_cell(e.get('duration'))} |")
            L.append("")
    # metrics
    known = [m for m in rep["metrics"] if m["value"] is not None and m["key"] != "cohorts"]
    unknown = [m for m in rep["metrics"] if m["value"] is None]
    L += ["### Growth metrics", ""]
    if known:
        L += ["| Metric | AARRR stage | Value | Status | Formula |", "|---|---|---:|---|---|"]
        for m in known:
            L.append(f"| {m['name']} | {m['stage']} | {m['display']} | {m['status']} | {m['formula']} |")
        L.append("")
    else:
        L += ["No metric can be computed yet: no measured inputs were supplied.", ""]
    if unknown:
        L += ["Not computed (inputs missing; nothing has been estimated in their place):", "",
              "| Metric | AARRR stage | Formula | Missing inputs |", "|---|---|---|---|"]
        for m in unknown:
            L.append(f"| {m['name']} | {m['stage']} | {m['formula']} | {', '.join(m['missing'])} |")
        L.append("")
    for m in rep["metrics"]:
        if m["key"] == "cohorts":
            n = max(len(c["retention"]) for c in m["value"])
            L += ["| Cohort | Size | " + " | ".join(f"P{i}" for i in range(n)) + " |",
                  "|---|---:|" + "---:|" * n]
            for c in m["value"]:
                cells = [f"{x:.0%}" for x in c["retention"]] + ["—"] * (n - len(c["retention"]))
                L.append(f"| {_cell(c['name'])}{_cite(c['evidence'])} | {c['size']} | " + " | ".join(cells) + " |")
            L.append("")
    # roadmap
    if rep["roadmap"]:
        L += ["### Roadmap capacity check", "",
              "| Phase | Days | Ends day | Planned effort (person-days) | Capacity | Load | Planned spend |",
              "|---|---:|---:|---:|---:|---:|---:|"]
        for ph in rep["roadmap"]:
            L.append(f"| {_cell(ph['name'])} | {ph['days']} | {ph['end']} | {ph['effort']:.0f} | "
                     f"{ph['capacity']:.0f} | {'%.0f%%' % (ph['load'] * 100) if ph['load'] is not None else '—'} | "
                     f"{ph['spend']:,.0f} |")
        L += ["", "_Effort, cost and capacity are planning assumptions supplied in the spec._", ""]
    if rep["cross_product"]:
        L += ["### Cross-product opportunities", "", "| Product | Status | Opportunity | Phase |", "|---|---|---|---|"]
        for c in rep["cross_product"]:
            L.append(f"| {_cell(c.get('product'))} | {c['status']} | {_cell(c.get('opportunity'))} | "
                     f"{_cell(c.get('phase'))} |")
        L.append("")
    if rep["missing_profile"]:
        L += ["### Missing profile information", ""] + [f"- [ ] {m}" for m in rep["missing_profile"]] + [""]
    if rep["issues"]:
        L += ["### Engine findings", ""] + [f"- **{i['level']}** ({i['area']}): {i['message']}" for i in rep["issues"]]
        L.append("")
    return "\n".join(L)


# ----------------------------------------------------------------------------- claim guard
MARKET_RE = re.compile(r"\b(TAM|SAM|SOM|market size|market is worth|market worth|addressable market)\b", re.I)
NUMBER_RE = re.compile(r"\d")
TRACTION_RE = re.compile(
    r"(?:\b(?:we|it|the platform|the product|the company|company)\s+(?:has|have|had|now has|serves?|reached|grew|grows)\b"
    r"[^.\n]{0,40}\d)|(?:\d[\d,.]*\s*(?:k|K|m|M)?\s*(?:paying |active |monthly )?(?:customers|users|creators|learners|"
    r"students|subscribers|signups|sign-ups|members|teachers|downloads)\b)|(?:\b(?:revenue|MRR|ARR|GMV|sales)\b[^.\n]{0,25}"
    r"(?:of|is|was|reached|at|=)\s*(?:NPR|Rs\.?|INR|USD|EUR|GBP|[$€£₹])?\s*[^\s]*\d)|(?:\b(?:CAC|LTV|churn|conversion(?: rate)?|retention|payback)\b"
    r"[^.\n]{0,25}(?:of|is|was|at|=|:)\s*(?:NPR|Rs\.?|INR|USD|EUR|GBP|[$€£₹])?\s*[^\s]*\d)", re.I)
VALIDATION_RE = re.compile(r"\b(proven demand|proven|validated demand|validated|customers love|users love|"
                           r"product[- ]market fit|strong traction|strong demand|huge demand|high demand)\b", re.I)
NEGATION_RE = re.compile(r"\b(no|not|never|without|before|until|yet|unvalidated|unproven|hypothes\w*|test\w*|validate\b|"
                         r"validation|whether|if|evidence (?:needed|required)|to be|would|could|aim|goal|target|"
                         r"measure\w*)\b", re.I)
QUALIFIER_RE = re.compile(r"\b(target|goal|aim|hypothes\w*|assum\w*|estimat\w*|threshold|kill|benchmark|illustrative|"
                          r"example|formula|unknown|missing|measure\w*|plan\w*|budget|if|would|could|may|might|"
                          r"expected|forecast|scenario|projection|at least|up to|cap|limit|maximum|minimum|pilot|"
                          r"experiment|test|list|contact|recruit|onboard|invite|interview|visit|survey|call|ask)\b"
                          r"|≥|≤|>=|<=", re.I)
SENTENCE_RE = re.compile(r"(?<=[.!?])\s+(?=[A-Z0-9*\[(\"“])|;\s+")
RANGE_RE = re.compile(r"\d[\d,.]*\s*(?:[–-]|to)\s*\d[\d,.]*")
LIST_MARKER_RE = re.compile(r"^(?:[-*+]|\d+[.)])\s+")


def check_claims(text: str, ledger: Optional[Ledger] = None, where: str = "document") -> List[Dict]:
    """Flag unsupported market-size, customer/revenue/traction and validation claims in strategy prose.

    A line passes if it cites evidence ([E-001]) or is explicitly framed as a target, hypothesis or formula.
    Market-size and traction claims without either are errors; validation language without evidence is an error.
    """
    issues: List[Dict] = []
    body = text
    if body.startswith("---"):
        end = body.find("\n---", 3)
        if end != -1:
            body = "\n" * body[:end + 4].count("\n") + body[end + 4:]
    in_fence = False
    lines = body.split("\n")
    pos = 0
    for n, line in enumerate(lines, 1):
        start = pos
        pos += len(line) + 1
        s = line.strip()
        if s.startswith("```") or s.startswith("~~~"):
            in_fence = not in_fence
            continue
        if in_fence or not s or s.startswith("#") or set(s) <= set("|-: "):
            continue
        s = LIST_MARKER_RE.sub("", s)          # "1. teachers publish…" is a list item, not a count
        if s.startswith("|"):
            units = [(s, s + " " + _table_header(body, start))]     # a table row is judged with its header
        else:
            # sentence level: a citation elsewhere on the line must not vouch for an uncited sentence
            units = [(u, u) for u in SENTENCE_RE.split(s) if u.strip()]
        for u, ctx in units:
            if not MARKET_RE.search(u):
                # "cooperatives of 200–600 members" describes a segment; a range is not a traction claim
                u = RANGE_RE.sub("a range of", u)
            cited = bool(CITE_RE.search(u))
            qualified = bool(QUALIFIER_RE.search(ctx))
            short = u.strip()[:100]
            if MARKET_RE.search(u) and NUMBER_RE.search(u) and not cited and not qualified:
                issues.append({"level": "error", "line": n, "kind": "market-size",
                               "message": f"{where}:{n}: market-size figure without evidence or calculation: "
                                          f"'{short}'"})
            elif TRACTION_RE.search(u) and not cited and not qualified:
                issues.append({"level": "error", "line": n, "kind": "traction",
                               "message": f"{where}:{n}: customer/revenue/metric claim without evidence: '{short}'"})
            m = VALIDATION_RE.search(u)
            if m and not cited and not NEGATION_RE.search(u):
                issues.append({"level": "error", "line": n, "kind": "validation",
                               "message": f"{where}:{n}: '{m.group(0)}' asserted without evidence: '{short}'"})
    if ledger is not None:
        for i in ledger.check_text(text, where):
            issues.append({"level": i.level, "line": None, "kind": "citation", "message": str(i)})
    return issues


# ----------------------------------------------------------------------------- KPI workbook
def kpi_workbook(rep: Dict, path: str, weeks: int = 26) -> Dict:
    """KPI tracker: definitions, a weekly input grid (blank, blue) with formula columns, and experiments."""
    import openpyxl
    from openpyxl.styles import Alignment, Font, PatternFill
    from openpyxl.utils import get_column_letter
    from .xlsx import BLUE
    head = PatternFill("solid", fgColor="F3F4F1")
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "README"
    rows = [(f"{rep['company']} KPI dashboard specification", Font(size=16, bold=True)),
            (f"Stage: {rep['stage']} · Business model: {', '.join(rep['types'])}", None), ("", None),
            ("Weekly sheet: enter measured counts in the blue columns. Rate columns are formulas; they stay blank "
             "until both inputs exist.", None),
            ("No values are pre-filled. Targets on the KPIs sheet are hypotheses until validated.",
             Font(bold=True, color="B4423A")),
            ("Sheets: KPIs (definitions) → Weekly (tracker) → Experiments (channel and pricing tests)", None),
            ("Generated by Startup Skills (startup-kit gtm kpi).", Font(color="9AA3AD", size=9))]
    for i, (t, f) in enumerate(rows, 1):
        c = ws.cell(i, 1, t)
        if f:
            c.font = f
    ws.column_dimensions["A"].width = 110
    # definitions
    wk = wb.create_sheet("KPIs")
    hdr = ["AARRR stage", "Metric", "Formula", "Inputs", "Current value", "Status", "Target (hypothesis)", "Owner"]
    for j, h in enumerate(hdr, 1):
        c = wk.cell(1, j, h)
        c.font = Font(bold=True)
        c.fill = head
    targets = (rep["_spec"].get("metrics", {}) or {}).get("targets", {}) or {}
    owner = (rep["_spec"].get("metrics", {}) or {}).get("owner", "")
    r = 2
    for m in rep["metrics"]:
        if m["key"] == "cohorts":
            continue
        wk.append([m["stage"], m["name"], m["formula"], ", ".join(m["inputs"]),
                   m["display"] if m["value"] is not None else "not measured", m["status"] or "missing input",
                   _text(targets.get(m["key"], "")), owner])
        r += 1
    for col, w in zip("ABCDEFGH", (14, 30, 44, 40, 16, 16, 26, 14)):
        wk.column_dimensions[col].width = w
    # weekly tracker
    ww = wb.create_sheet("Weekly")
    ratio = [m for m in rep["metrics"] if m["key"] in METRICS and len(METRICS[m["key"]][3]) == 2
             and METRICS[m["key"]][5] in ("pct", "money")]
    inputs: List[str] = []
    for m in ratio:
        for i in METRICS[m["key"]][3]:
            if i not in inputs:
                inputs.append(i)
    cols = ["Week starting"] + inputs + [METRICS[m["key"]][0] for m in ratio]
    for j, h in enumerate(cols, 1):
        c = ww.cell(1, j, h)
        c.font = Font(bold=True)
        c.fill = head
        c.alignment = Alignment(wrap_text=True)
        ww.column_dimensions[get_column_letter(j)].width = 16
    col_of = {name: get_column_letter(2 + k) for k, name in enumerate(inputs)}
    nform = 0
    for w in range(weeks):
        row = w + 2
        ww.cell(row, 1, f"Week {w + 1}")
        for k in range(len(inputs)):
            ww.cell(row, 2 + k).font = Font(color=BLUE)
        for k, m in enumerate(ratio):
            num, den = METRICS[m["key"]][3]
            a, b = col_of[num], col_of[den]
            c = ww.cell(row, 2 + len(inputs) + k,
                        f'=IF(AND(ISNUMBER({a}{row}),ISNUMBER({b}{row}),{b}{row}<>0),{a}{row}/{b}{row},"")')
            c.number_format = "0.0%" if METRICS[m["key"]][5] == "pct" else "#,##0.00"
            nform += 1
    ww.freeze_panes = "B2"
    # experiments
    we = wb.create_sheet("Experiments")
    eh = ["Type", "Name", "Hypothesis", "Metric", "Threshold", "Budget", "Duration", "Kill criterion", "Result",
          "Decision"]
    for j, h in enumerate(eh, 1):
        c = we.cell(1, j, h)
        c.font = Font(bold=True)
        c.fill = head
        we.column_dimensions[get_column_letter(j)].width = 22
    for ch in rep["channels"]:
        e = ch["spec"].get("experiment") or {}
        if e and ch["decision"] in ("primary", "test-later"):
            we.append(["Channel", ch["name"], _text(e.get("hypothesis")), _text(e.get("metric")),
                       _text(e.get("threshold")), _text(e.get("budget")), _text(e.get("duration")),
                       _text(e.get("kill")), "", ""])
    for e in (rep["pricing"] or {}).get("experiments", []):
        we.append(["Pricing", _text(e.get("name")), _text(e.get("hypothesis")), _text(e.get("metric")),
                   _text(e.get("threshold")), _text(e.get("budget")), _text(e.get("duration")),
                   _text(e.get("kill")), "", ""])
    wb.properties.title = f"{rep['company']} KPI dashboard"
    wb.properties.creator = "Startup Skills"
    os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
    wb.save(path)
    return {"path": path, "inputs": inputs, "formulas": nform, "kpis": r - 2}
