"""Transparent calculators: bottom-up market sizing and unit economics.

Every input factor carries an evidence ID or an explicit status.  The output
shows the arithmetic, so a reader can challenge each step, and inherits the
weakest status of its inputs (a TAM built on one assumption is an estimate).
"""
from __future__ import annotations

from typing import Dict, List, Optional

import yaml

from .evidence import Ledger

_ORDER = ["contradicted", "unverified", "assumption", "estimate", "reported", "verified"]


def fmt_money(v: float, currency: str = "USD") -> str:
    sym = {"USD": "$", "EUR": "€", "GBP": "£", "INR": "₹"}.get(currency, "")
    a = abs(v)
    if a >= 1e9:
        s = f"{v / 1e9:.2f}B"
    elif a >= 1e6:
        s = f"{v / 1e6:.2f}M"
    elif a >= 1e3:
        s = f"{v / 1e3:.1f}K"
    else:
        s = f"{v:,.2f}" if a < 100 and v != int(v) else f"{v:,.0f}"
    return f"{sym}{s}" if sym else f"{s} {currency}"


def fmt_num(v: float) -> str:
    if isinstance(v, float) and 0 < abs(v) < 1:
        return f"{v * 100:.1f}%"
    if abs(v) >= 1e6:
        return f"{v / 1e6:.2f}M"
    return f"{v:,.0f}" if float(v).is_integer() else f"{v:,.2f}"


def _status(f: Dict, ledger: Optional[Ledger]) -> str:
    if f.get("evidence") and ledger is not None:
        ids = f["evidence"] if isinstance(f["evidence"], list) else [f["evidence"]]
        sts = [ledger.get(i).status for i in ids if ledger.get(i)]
        if not sts:
            return "unverified"
        return min(sts, key=lambda s: _ORDER.index(s) if s in _ORDER else 0)
    return f.get("status", "assumption")


def market_size(spec: Dict, ledger: Optional[Ledger] = None) -> Dict:
    """Compute TAM/SAM/SOM from multiplicative factors."""
    out = {"title": spec.get("title", "Market sizing"), "currency": spec.get("currency", "USD"),
           "geography": spec.get("geography", "unspecified"), "year": spec.get("year"), "layers": {}, "issues": []}
    for layer in ("tam", "sam", "som"):
        L = spec.get(layer)
        if not L:
            continue
        base_val = 1.0
        steps = []
        statuses = []
        if L.get("base"):
            prev = out["layers"].get(L["base"])
            if not prev:
                out["issues"].append(f"{layer}: base '{L['base']}' not computed")
                continue
            base_val = prev["value"]
            statuses.append(prev["status"])
            steps.append({"label": f"{L['base'].upper()}", "value": base_val, "status": prev["status"], "evidence": ""})
        val = base_val
        for f in L.get("factors", []):
            if "value" not in f:
                out["issues"].append(f"{layer}: factor '{f.get('label')}' has no value")
                continue
            st = _status(f, ledger)
            statuses.append(st)
            val *= float(f["value"])
            ev = f.get("evidence", "")
            steps.append({"label": f.get("label", ""), "value": f["value"], "unit": f.get("unit", ""), "status": st,
                          "evidence": ", ".join(ev) if isinstance(ev, list) else (ev or "")})
            if not f.get("evidence") and not f.get("status"):
                out["issues"].append(f"{layer}: factor '{f.get('label')}' has neither evidence nor status; "
                                     "treated as assumption")
        worst = min(statuses, key=lambda s: _ORDER.index(s) if s in _ORDER else 0) if statuses else "assumption"
        out["layers"][layer] = {"label": L.get("label", layer.upper()), "description": L.get("description", ""),
                                "value": val, "steps": steps, "status": worst}
    if "tam" in out["layers"] and "sam" in out["layers"] and out["layers"]["sam"]["value"] > out["layers"]["tam"]["value"]:
        out["issues"].append("SAM exceeds TAM; check factors")
    if "sam" in out["layers"] and "som" in out["layers"] and out["layers"]["som"]["value"] > out["layers"]["sam"]["value"]:
        out["issues"].append("SOM exceeds SAM; check factors")
    out["top_down"] = spec.get("top_down", [])
    return out


def market_size_md(res: Dict) -> str:
    cur = res["currency"]
    L = [f"## {res['title']}", "",
         f"Geography: **{res['geography']}**" + (f" · Year: **{res['year']}**" if res.get("year") else "") +
         f" · Currency: **{cur}**", ""]
    for key, layer in res["layers"].items():
        L += [f"### {key.upper()}: {fmt_money(layer['value'], cur)}  ·  status: {layer['status']}", ""]
        if layer["description"]:
            L += [layer["description"], ""]
        L += ["| Step | Factor | Value | Status | Evidence |", "|---|---|---|---|---|"]
        for i, s in enumerate(layer["steps"], 1):
            v = s["value"]
            vs = fmt_money(v, cur) if s["label"] in ("TAM", "SAM") else (
                f"{fmt_num(v)}{(' ' + s['unit']) if s.get('unit') else ''}")
            L.append(f"| {i} | {s['label']} | {vs} | {s['status']} | {s['evidence'] or '—'} |")
        L.append(f"| = | **{key.upper()}** | **{fmt_money(layer['value'], cur)}** | {layer['status']} | |")
        L.append("")
    if res.get("top_down"):
        L += ["### Top-down cross-checks", "", "| Figure | Value | Source | Note |", "|---|---|---|---|"]
        for t in res["top_down"]:
            L.append(f"| {t.get('label', '')} | {t.get('value', '')} | {t.get('evidence', t.get('source', '—'))} | {t.get('note', '')} |")
        L.append("")
    if res["issues"]:
        L += ["### Issues", ""] + [f"- {i}" for i in res["issues"]] + [""]
    L += ["_Each layer inherits the weakest status of its inputs. A figure labelled 'assumption' or 'estimate' "
          "must be presented that way in every document._", ""]
    return "\n".join(L)


def unit_economics(arpu_month: float, gross_margin: float, monthly_churn: float, cac: float) -> Dict:
    if monthly_churn <= 0:
        raise ValueError("monthly_churn must be > 0 (use a conservative value; zero churn implies infinite LTV)")
    gm_month = arpu_month * gross_margin
    lifetime = 1 / monthly_churn
    ltv = gm_month * lifetime
    payback = cac / gm_month if gm_month > 0 else float("inf")
    return {"arpu_month": arpu_month, "gross_margin": gross_margin, "monthly_churn": monthly_churn, "cac": cac,
            "gross_profit_per_month": gm_month, "expected_lifetime_months": lifetime, "ltv": ltv,
            "ltv_to_cac": ltv / cac if cac else float("inf"), "payback_months": payback}


def unit_economics_md(arpu_month, gross_margin, monthly_churn, cac, currency="USD") -> str:
    r = unit_economics(arpu_month, gross_margin, monthly_churn, cac)
    L = ["| Metric | Value | Formula |", "|---|---|---|",
         f"| ARPU / month | {fmt_money(arpu_month, currency)} | input |",
         f"| Gross margin | {gross_margin:.0%} | input |",
         f"| Monthly churn | {monthly_churn:.1%} | input |",
         f"| CAC | {fmt_money(cac, currency)} | input |",
         f"| Expected lifetime | {r['expected_lifetime_months']:.1f} months | 1 / churn |",
         f"| LTV (gross-margin) | {fmt_money(r['ltv'], currency)} | ARPU × GM / churn |",
         f"| LTV : CAC | {r['ltv_to_cac']:.1f}x | LTV / CAC |",
         f"| CAC payback | {r['payback_months']:.1f} months | CAC / (ARPU × GM) |", "",
         "Sensitivity of LTV:CAC to churn (rows) and CAC (columns):", ""]
    churns = [monthly_churn * m for m in (0.5, 1, 1.5, 2)]
    cacs = [cac * m for m in (0.5, 1, 1.5, 2)]
    L.append("| churn \\ CAC | " + " | ".join(fmt_money(c, currency) for c in cacs) + " |")
    L.append("|---|" + "---|" * len(cacs))
    for ch in churns:
        L.append(f"| {ch:.1%} | " + " | ".join(f"{unit_economics(arpu_month, gross_margin, ch, c)['ltv_to_cac']:.1f}x"
                                               for c in cacs) + " |")
    L += ["", "_Benchmarks such as LTV:CAC ≥ 3 and payback ≤ 12–18 months are heuristics from SaaS practice, not laws; "
          "they vary by segment and capital cost._", ""]
    return "\n".join(L)


def load_yaml(path: str) -> Dict:
    with open(path) as f:
        return yaml.safe_load(f) or {}
