"""Driver-based financial model → XLSX with live formulas.

Conventions (standard in finance practice):
  * blue font = input (assumption), black = formula, green = link to another sheet;
  * every input row carries status + evidence ID;
  * nothing is hard-coded in formula sheets.

``simulate`` mirrors the spreadsheet formulas in Python so other skills can
chart projections, and tests can cross-check the workbook after recalculation.
"""
from __future__ import annotations

import datetime as _dt
from typing import Dict, List, Optional, Tuple

import openpyxl
from openpyxl.styles import Alignment, Border, Font, PatternFill, Side
from openpyxl.utils import get_column_letter
from openpyxl.workbook.defined_name import DefinedName

from .evidence import Ledger

BLUE = "1F4FBF"
GREEN = "2E7D32"


def _v(x, default=0.0):
    if isinstance(x, dict):
        x = x.get("value", default)
    return default if x is None else x


def _month_dates(start: str, n: int) -> List[_dt.date]:
    y, m = [int(p) for p in str(start).split("-")[:2]]
    out = []
    for i in range(n):
        yy, mm = y + (m - 1 + i) // 12, (m - 1 + i) % 12 + 1
        out.append(_dt.date(yy, mm, 1))
    return out


def simulate(model: Dict) -> Dict:
    M = model.get("model", {})
    n = int(M.get("months", 36))
    streams = model.get("revenue_streams", [])
    res = {"months": n, "streams": {}, "revenue": [0.0] * n, "cogs": [0.0] * n}
    for s in streams:
        name = s["name"]
        start = int(_v(s.get("start_month"), 1))
        if s.get("type", "subscription") == "subscription":
            new0, g, churn, price = _v(s["new_customers_month1"]), _v(s.get("new_customers_growth")), _v(s.get("churn")), _v(s["price"])
            active, prev, rev = [], 0.0, []
            for i in range(n):
                mi = i + 1
                new = new0 * (1 + g) ** (mi - start) if mi >= start else 0.0
                cur = prev * (1 - churn) + new
                active.append(cur)
                rev.append(cur * price)
                prev = cur
            res["streams"][name] = {"active": active, "revenue": rev}
        else:
            gmv0, g, take = _v(s["gmv_month1"]), _v(s.get("gmv_growth")), _v(s["take_rate"])
            gmv = [gmv0 * (1 + g) ** (i + 1 - start) if i + 1 >= start else 0.0 for i in range(n)]
            rev = [x * take for x in gmv]
            res["streams"][name] = {"gmv": gmv, "revenue": rev}
        cp = _v(s.get("cogs_pct"))
        for i in range(n):
            res["revenue"][i] += rev[i]
            res["cogs"][i] += rev[i] * cp
    res["gross_profit"] = [r - c for r, c in zip(res["revenue"], res["cogs"])]
    people = [0.0] * n
    for h in model.get("headcount", []):
        st, cnt, cost = int(_v(h.get("start_month"), 1)), _v(h.get("count"), 1), _v(h["monthly_cost"])
        for i in range(n):
            if i + 1 >= st:
                people[i] += cnt * cost
    other = [0.0] * n
    for o in model.get("opex", []):
        base, g = _v(o["monthly"]), _v(o.get("growth"))
        for i in range(n):
            other[i] += base * (1 + g) ** i
    res["opex"] = [p + o for p, o in zip(people, other)]
    res["ebitda"] = [g - o for g, o in zip(res["gross_profit"], res["opex"])]
    funding = [0.0] * n
    for f in model.get("funding", []):
        amt = _v(f.get("amount"))
        mi = int(_v(f.get("month"), 1))
        if 1 <= mi <= n:
            funding[mi - 1] += amt
    cash, bal = [], _v(M.get("starting_cash"))
    for i in range(n):
        bal = bal + res["ebitda"][i] + funding[i]
        cash.append(bal)
    res["funding"], res["cash"] = funding, cash
    neg = [i + 1 for i, c in enumerate(cash) if c < 0]
    res["cash_out_month"] = neg[0] if neg else None
    res["annual"] = []
    for y in range(0, n, 12):
        sl = slice(y, min(y + 12, n))
        res["annual"].append({"year": y // 12 + 1, "revenue": sum(res["revenue"][sl]),
                              "gross_profit": sum(res["gross_profit"][sl]), "opex": sum(res["opex"][sl]),
                              "ebitda": sum(res["ebitda"][sl]), "ending_cash": cash[sl][-1]})
    return res


def validate_model(model: Dict) -> List[str]:
    errs = []
    if not model.get("revenue_streams"):
        errs.append("model needs at least one revenue stream")
    for s in model.get("revenue_streams", []):
        t = s.get("type", "subscription")
        need = ["new_customers_month1", "price"] if t == "subscription" else ["gmv_month1", "take_rate"]
        for k in need:
            if k not in s:
                errs.append(f"stream '{s.get('name')}': missing {k}")
        ch = _v(s.get("churn"))
        if t == "subscription" and not (0 <= ch < 1):
            errs.append(f"stream '{s.get('name')}': churn must be in [0,1)")
    for f in model.get("funding", []):
        if f.get("amount") in (None, "", "TBD"):
            errs.append(f"funding '{f.get('label', '')}' has no amount; modelled as 0 until the founder sets it")
    return errs


class _Inputs:
    """Collects every assumption as a row on the Assumptions sheet and returns its absolute reference."""

    def __init__(self, ws, ledger: Optional[Ledger]):
        self.ws, self.ledger, self.row = ws, ledger, 5
        self.used_ids: List[str] = []

    def add(self, label: str, spec, unit: str = "", fmt: str = "#,##0.00") -> str:
        val = _v(spec)
        ev = spec.get("evidence") if isinstance(spec, dict) else None
        ids = ev if isinstance(ev, list) else ([ev] if ev else [])
        status = (spec.get("status") if isinstance(spec, dict) else None) or (
            self.ledger.get(ids[0]).status if (ids and self.ledger is not None and self.ledger.get(ids[0])) else
            "assumption")
        r = self.row
        ws = self.ws
        ws.cell(r, 1, label)
        c = ws.cell(r, 2, val)
        c.font = Font(color=BLUE, bold=True)
        c.number_format = fmt
        ws.cell(r, 3, unit)
        ws.cell(r, 4, status)
        ws.cell(r, 5, ", ".join(ids))
        ws.cell(r, 6, (spec.get("note") if isinstance(spec, dict) else "") or "")
        for i in ids:
            if i not in self.used_ids:
                self.used_ids.append(i)
        if status in ("assumption", "estimate", "unverified"):
            ws.cell(r, 4).font = Font(color="B7791F", bold=True)
        self.row += 1
        return f"Assumptions!$B${r}"

    def section(self, title: str):
        self.row += 1
        c = self.ws.cell(self.row, 1, title)
        c.font = Font(bold=True, size=11)
        self.row += 1


def build_workbook(model: Dict, path: str, ledger: Optional[Ledger] = None) -> Dict:
    M = model.get("model", {})
    n = int(M.get("months", 36))
    cur = M.get("currency", "USD")
    money = f'#,##0;[Red]-#,##0'
    dates = _month_dates(M.get("start", "2027-01"), n)
    wb = openpyxl.Workbook()
    thin = Side(style="thin", color="D9DDE1")
    head_fill = PatternFill("solid", fgColor="F3F4F1")

    # ---------------- README
    ws0 = wb.active
    ws0.title = "README"
    lines = [
        (f"{M.get('company', '')} financial model", Font(size=16, bold=True)),
        (f"Scenario: {M.get('scenario', 'base')} · Currency: {cur} · Start: {M.get('start', '')} · Months: {n}", None),
        ("", None),
        ("How to read this workbook", Font(bold=True)),
        ("Blue values on the Assumptions sheet are inputs. Everything else is a formula; change inputs, not formulas.", None),
        ("Each input shows its status (verified / reported / estimate / assumption) and evidence ID.", None),
        ("Projections are scenarios built on assumptions, not forecasts of what will happen.", Font(bold=True, color="B4423A")),
        ("", None),
        ("Sheets: Assumptions → Monthly (36-month build) → Annual (summary) → Unit economics → Sources", None),
        ("Generated by Startup Skills (startup-kit).", Font(color="9AA3AD", size=9)),
    ]
    for i, (txt, font) in enumerate(lines, 1):
        c = ws0.cell(i, 1, txt)
        if font:
            c.font = font
    ws0.column_dimensions["A"].width = 110

    # ---------------- Assumptions
    wa = wb.create_sheet("Assumptions")
    for col, h in enumerate(["Input", "Value", "Unit", "Status", "Evidence", "Note"], 1):
        c = wa.cell(4, col, h)
        c.font = Font(bold=True)
        c.fill = head_fill
    wa.cell(1, 1, "Assumptions").font = Font(size=14, bold=True)
    wa.cell(2, 1, "Blue = input. Status comes from the evidence ledger; 'assumption' rows must be validated.").font = Font(
        color="5B6470", italic=True)
    for col, w in zip("ABCDEF", (46, 16, 14, 14, 16, 50)):
        wa.column_dimensions[col].width = w
    I = _Inputs(wa, ledger)
    I.section("Company")
    ref_cash = I.add("Starting cash", M.get("starting_cash", {"value": 0, "status": "assumption"}), cur, money)
    ref_funding = []
    for f in model.get("funding", []):
        ref_funding.append((int(_v(f.get("month"), 1)), I.add(f"Funding: {f.get('label', 'round')}", f.get("amount_spec", {
            "value": _v(f.get("amount")), "status": f.get("status", "assumption"), "evidence": f.get("evidence"),
            "note": "Amount not set by founder" if f.get("amount") in (None, "", "TBD") else ""}), cur, money)))
    stream_refs = []
    for s in model.get("revenue_streams", []):
        I.section(f"Revenue: {s['name']}")
        r = {"name": s["name"], "type": s.get("type", "subscription"),
             "start": I.add(f"{s['name']}: start month", s.get("start_month", {"value": 1, "status": "assumption"}), "month", "0")}
        if r["type"] == "subscription":
            r["new0"] = I.add(f"{s['name']}: new customers in first month", s["new_customers_month1"], "customers", "#,##0.0")
            r["g"] = I.add(f"{s['name']}: monthly growth of new customers", s.get("new_customers_growth", 0), "%/month", "0.0%")
            r["churn"] = I.add(f"{s['name']}: monthly churn", s.get("churn", 0), "%/month", "0.0%")
            r["price"] = I.add(f"{s['name']}: price per customer per month", s["price"], cur, "#,##0.00")
        else:
            r["gmv0"] = I.add(f"{s['name']}: transaction volume in first month", s["gmv_month1"], cur, money)
            r["g"] = I.add(f"{s['name']}: monthly volume growth", s.get("gmv_growth", 0), "%/month", "0.0%")
            r["take"] = I.add(f"{s['name']}: take rate", s["take_rate"], "%", "0.0%")
        r["cogs"] = I.add(f"{s['name']}: direct cost as % of revenue", s.get("cogs_pct", 0), "%", "0.0%")
        stream_refs.append(r)
    I.section("Team (monthly fully-loaded cost)")
    head_refs = []
    for h in model.get("headcount", []):
        head_refs.append((h["role"], I.add(f"{h['role']}: start month", h.get("start_month", {"value": 1}), "month", "0"),
                          I.add(f"{h['role']}: count", h.get("count", {"value": 1}), "people", "0"),
                          I.add(f"{h['role']}: monthly cost each", h["monthly_cost"], cur, money)))
    I.section("Operating expenses")
    opex_refs = []
    for o in model.get("opex", []):
        opex_refs.append((o["name"], I.add(f"{o['name']}: monthly (month 1)", o["monthly"], cur, money),
                          I.add(f"{o['name']}: monthly growth", o.get("growth", 0), "%/month", "0.0%")))
    ue = model.get("unit_economics")
    ue_refs = {}
    if ue:
        I.section("Unit economics inputs")
        ue_refs["cac"] = I.add("Blended CAC", ue["cac"], cur, money)

    # ---------------- Monthly
    wm = wb.create_sheet("Monthly")
    wm.column_dimensions["A"].width = 38
    wm.freeze_panes = "B3"
    wm.cell(1, 1, "Month").font = Font(bold=True)
    wm.cell(2, 1, "Date").font = Font(bold=True)
    for i in range(n):
        col = i + 2
        wm.cell(1, col, i + 1).font = Font(bold=True)
        c = wm.cell(2, col, dates[i])
        c.number_format = "mmm yy"
        c.font = Font(bold=True)
        c.fill = head_fill
        wm.column_dimensions[get_column_letter(col)].width = 11
    row = 4
    rows = {}

    def put(label, formula_fn, fmt=money, bold=False, top=False):
        nonlocal row
        wm.cell(row, 1, label).font = Font(bold=bold)
        for i in range(n):
            col = get_column_letter(i + 2)
            prev = get_column_letter(i + 1)
            c = wm.cell(row, i + 2, formula_fn(i, col, prev))
            c.number_format = fmt
            if bold:
                c.font = Font(bold=True)
            if top:
                c.border = Border(top=Side(style="thin", color="14171A"))
        rows[label] = row
        row += 1
        return row - 1

    rev_rows, cogs_terms = [], []
    for r in stream_refs:
        wm.cell(row, 1, r["name"]).font = Font(bold=True, color="1F5C4A")
        row += 1
        if r["type"] == "subscription":
            rn = put(f"  {r['name']}: new customers",
                     lambda i, c, p, r=r: f"=IF({c}$1>={r['start']},{r['new0']}*(1+{r['g']})^({c}$1-{r['start']}),0)", "#,##0.0")
            ra = row
            put(f"  {r['name']}: active customers",
                lambda i, c, p, r=r, rn=rn, ra=ra: (f"={c}{rn}" if i == 0 else f"={p}{ra}*(1-{r['churn']})+{c}{rn}"), "#,##0.0")
            rr = put(f"  {r['name']}: revenue", lambda i, c, p, r=r, ra=ra: f"={c}{ra}*{r['price']}")
        else:
            rg = put(f"  {r['name']}: transaction volume",
                     lambda i, c, p, r=r: f"=IF({c}$1>={r['start']},{r['gmv0']}*(1+{r['g']})^({c}$1-{r['start']}),0)")
            rr = put(f"  {r['name']}: revenue", lambda i, c, p, r=r, rg=rg: f"={c}{rg}*{r['take']}")
        rev_rows.append(rr)
        cogs_terms.append((rr, r["cogs"]))
    row += 1
    tr = put("Total revenue", lambda i, c, p: "=" + "+".join(f"{c}{x}" for x in rev_rows), bold=True, top=True)
    tc = put("Direct costs (COGS)", lambda i, c, p: "=" + "+".join(f"{c}{x}*{ref}" for x, ref in cogs_terms))
    gp = put("Gross profit", lambda i, c, p: f"={c}{tr}-{c}{tc}", bold=True)
    put("Gross margin", lambda i, c, p: f"=IF({c}{tr}=0,0,{c}{gp}/{c}{tr})", "0.0%")
    row += 1
    team_rows = []
    for role, st, cnt, cost in head_refs:
        team_rows.append(put(f"  Team: {role}", lambda i, c, p, st=st, cnt=cnt, cost=cost: f"=IF({c}$1>={st},{cnt}*{cost},0)"))
    ox_rows = []
    for name, base, g in opex_refs:
        ox_rows.append(put(f"  Opex: {name}", lambda i, c, p, base=base, g=g: f"={base}*(1+{g})^({c}$1-1)"))
    all_ox = team_rows + ox_rows
    to = put("Total operating expenses", lambda i, c, p: ("=" + "+".join(f"{c}{x}" for x in all_ox)) if all_ox else "=0",
             bold=True, top=True)
    eb = put("EBITDA (approx. operating cash flow)", lambda i, c, p: f"={c}{gp}-{c}{to}", bold=True)
    row += 1
    fu = put("Funding received", lambda i, c, p: "=" + ("+".join(f"IF({c}$1={m},{ref},0)" for m, ref in ref_funding) or "0"))
    cb_row = row
    put("Cash balance (end of month)", lambda i, c, p: (f"={ref_cash}+{c}{eb}+{c}{fu}" if i == 0 else
                                                        f"={p}{cb_row}+{c}{eb}+{c}{fu}"), bold=True, top=True)
    last = get_column_letter(n + 1)
    wm.cell(row + 1, 1, "First month with negative cash (0 = none)").font = Font(bold=True)
    wm.cell(row + 1, 2, f'=IFERROR(MATCH(TRUE,INDEX(B{cb_row}:{last}{cb_row}<0,0),0),0)')

    # ---------------- Annual
    wy = wb.create_sheet("Annual")
    wy.column_dimensions["A"].width = 34
    years = (n + 11) // 12
    wy.cell(1, 1, "Annual summary (sums of Monthly)").font = Font(size=14, bold=True)
    for y in range(years):
        c = wy.cell(3, y + 2, f"Year {y + 1}")
        c.font = Font(bold=True)
        c.fill = head_fill
        wy.column_dimensions[get_column_letter(y + 2)].width = 16
    for k, (label, src, agg) in enumerate([("Revenue", tr, "SUM"), ("Gross profit", gp, "SUM"),
                                           ("Operating expenses", to, "SUM"), ("EBITDA", eb, "SUM"),
                                           ("Ending cash", cb_row, "LAST")]):
        r = 4 + k
        wy.cell(r, 1, label).font = Font(bold=label in ("Revenue", "EBITDA", "Ending cash"))
        for y in range(years):
            a = get_column_letter(2 + 12 * y)
            b = get_column_letter(min(1 + 12 * (y + 1), n + 1))
            f = f"=SUM(Monthly!{a}{src}:{b}{src})" if agg == "SUM" else f"=Monthly!{b}{src}"
            c = wy.cell(r, y + 2, f)
            c.number_format = money
            c.font = Font(color=GREEN)

    # ---------------- Unit economics
    wu = wb.create_sheet("Unit economics")
    wu.column_dimensions["A"].width = 44
    wu.column_dimensions["B"].width = 18
    wu.column_dimensions["C"].width = 40
    wu.cell(1, 1, "Unit economics (first subscription stream)").font = Font(size=14, bold=True)
    sub = next((r for r in stream_refs if r["type"] == "subscription"), None)
    if sub:
        rows_ue = [("ARPU per month", f"={sub['price']}", "#,##0.00", "price input"),
                   ("Gross margin", f"=1-{sub['cogs']}", "0.0%", "1 − direct cost %"),
                   ("Monthly churn", f"={sub['churn']}", "0.0%", "input"),
                   ("Expected lifetime (months)", "=IF(B5=0,0,1/B5)", "0.0", "1 / churn"),
                   ("Gross-margin LTV", "=IF(B5=0,0,B3*B4/B5)", money, "ARPU × GM / churn")]
        if ue_refs.get("cac"):
            rows_ue += [("CAC", f"={ue_refs['cac']}", money, "input"),
                        ("LTV : CAC", "=IF(B8=0,0,B7/B8)", "0.0x", "LTV / CAC"),
                        ("CAC payback (months)", "=IF(B3*B4=0,0,B8/(B3*B4))", "0.0", "CAC / (ARPU × GM)")]
        for k, (label, f, fmt, note) in enumerate(rows_ue):
            wu.cell(3 + k, 1, label)
            c = wu.cell(3 + k, 2, f)
            c.number_format = fmt
            c.font = Font(color=GREEN)
            wu.cell(3 + k, 3, note).font = Font(color="5B6470", italic=True)
    else:
        wu.cell(3, 1, "No subscription stream: unit economics depend on transaction frequency; model separately.")

    # ---------------- Sources
    ws = wb.create_sheet("Sources")
    ws.column_dimensions["A"].width = 10
    ws.column_dimensions["B"].width = 60
    ws.column_dimensions["C"].width = 14
    ws.column_dimensions["D"].width = 70
    for col, h in enumerate(["ID", "Claim", "Status", "Source"], 1):
        c = ws.cell(1, col, h)
        c.font = Font(bold=True)
        c.fill = head_fill
    for k, eid in enumerate(I.used_ids, 2):
        e = ledger.get(eid) if ledger is not None else None
        ws.cell(k, 1, eid)
        ws.cell(k, 2, e.claim if e else "NOT IN LEDGER")
        ws.cell(k, 3, e.status if e else "missing")
        ws.cell(k, 4, e.citation() if e else "")
    wb.properties.title = f"{M.get('company', '')} financial model ({M.get('scenario', 'base')})"
    wb.properties.creator = "Startup Skills (startup-kit)"
    wb.save(path)
    missing = [i for i in I.used_ids if ledger is not None and i not in ledger]
    return {"path": path, "evidence_used": I.used_ids, "missing_evidence": missing,
            "rows": {"revenue": tr, "gross_profit": gp, "opex": to, "ebitda": eb, "cash": cb_row}}
