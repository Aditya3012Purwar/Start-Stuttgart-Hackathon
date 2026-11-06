"""Turn live SQL results into KPI cards and chart specs for the dashboard.

Numbers stay grounded: every visual is built from a query the agents (or the
overview snapshot) already ran. The browser only draws what this module emits.
"""

from __future__ import annotations

from collections import defaultdict

from . import db, semantics

_EUR_HINTS = ("eur", "value", "amount", "rmwwr", "tied", "money", "net")
_COUNT_HINTS = ("count", "n", "invoices", "vendors", "orders", "docs", "qty")


def _num(v):
    if v is None or isinstance(v, bool):
        return None
    if isinstance(v, (int, float)):
        return float(v)
    if isinstance(v, str):
        s = v.replace(",", "").replace("EUR", "").replace("€", "").strip()
        try:
            return float(s)
        except ValueError:
            return None
    return None


def _looks_id(values) -> bool:
    sample = [str(v) for v in values if v is not None][:8]
    if not sample:
        return False
    return all(s.isdigit() and len(s) >= 6 for s in sample)


def _pretty(name: str) -> str:
    return str(name or "").replace("_", " ").strip().title() or "Value"


def _fmt(n, label=""):
    if n is None:
        return "—"
    lab = (label or "").lower()
    if any(h in lab for h in _EUR_HINTS) and abs(n) >= 1000:
        if abs(n) >= 1_000_000:
            return f"{n / 1_000_000:,.1f}M EUR"
        return f"{n:,.0f} EUR"
    if abs(n - round(n)) < 1e-9 and abs(n) < 1e12:
        return f"{int(round(n)):,}"
    return f"{n:,.2f}"


def _kpi(label, value, hint=""):
    n = _num(value)
    return {
        "label": label,
        "display": _fmt(n, label) if n is not None else str(value),
        "value": n,
        "hint": hint,
    }


def _chart(cid, ctype, title, labels, data, series="Value", subtitle=""):
    return {
        "id": cid,
        "type": ctype,
        "title": title,
        "subtitle": subtitle or "Built from the live query behind this answer",
        "labels": [str(x)[:42] for x in labels],
        "datasets": [{"label": series, "data": [(_num(v) or 0) for v in data]}],
    }


def from_table(columns, rows, title="Result", cid="t"):
    """Infer 0–1 chart from a result grid."""
    if not columns or not rows or len(rows) < 2:
        return []
    ncols = len(columns)
    label_idx = 0
    for i in range(ncols):
        col_vals = [r[i] if i < len(r) else None for r in rows]
        if any(_num(v) is None and v is not None for v in col_vals):
            label_idx = i
            break
    num_idxs = [
        i for i in range(ncols)
        if i != label_idx and any(_num(r[i] if i < len(r) else None) is not None for r in rows)
    ]
    if not num_idxs:
        return []

    labels = [r[label_idx] if label_idx < len(r) else "" for r in rows]
    if _looks_id(labels) and len(rows) > 8:
        # Invoice-level lists chart badly. Roll up if a name-like column exists.
        name_idx = None
        for i, col in enumerate(columns):
            if i in (label_idx, *num_idxs):
                continue
            if "name" in col.lower() or "vendor" in col.lower() or "lifnr" in col.lower():
                name_idx = i
                break
        if name_idx is None:
            return []
        bucket = defaultdict(float)
        for r in rows:
            bucket[str(r[name_idx])] += _num(r[num_idxs[0]]) or 0
        top = sorted(bucket.items(), key=lambda kv: -kv[1])[:8]
        return [_chart(
            cid, "hbar", title + " · by vendor",
            [k for k, _ in top], [v for _, v in top],
            series=_pretty(columns[num_idxs[0]]))]

    # Prefer the most "interesting" numeric column (largest spread).
    def spread(i):
        vals = [_num(r[i] if i < len(r) else None) or 0 for r in rows]
        return max(vals) - min(vals) if vals else 0

    num_idx = max(num_idxs, key=spread)
    paired = [(str(r[label_idx]) if label_idx < len(r) else "",
               _num(r[num_idx] if num_idx < len(r) else None) or 0) for r in rows]
    paired.sort(key=lambda kv: -abs(kv[1]))
    paired = paired[:8]
    labels = [a for a, _ in paired]
    data = [b for _, b in paired]
    series = _pretty(columns[num_idx])
    long_labels = max((len(x) for x in labels), default=0) > 16
    ctype = "hbar" if long_labels or len(labels) > 5 else (
        "doughnut" if 2 <= len(labels) <= 6 else "bar")
    return [_chart(cid, ctype, title, labels, data, series=series)]


def from_key_numbers(key_numbers: dict) -> list[dict]:
    kpis = []
    if not isinstance(key_numbers, dict):
        return kpis
    for k, v in key_numbers.items():
        if isinstance(v, dict):
            continue
        kpis.append(_kpi(_pretty(k), v, "From the analyst's key figures"))
    return kpis[:6]


def from_queries(trace_queries) -> tuple[list[dict], list[dict]]:
    kpis, charts = [], []
    for i, q in enumerate(trace_queries or []):
        res = q.get("result") or {}
        if "error" in res:
            continue
        cols, rows = res.get("columns") or [], res.get("rows") or []
        thought = (q.get("thought") or "Query result").strip()
        if res.get("row_count") == 1 and len(cols) == 1 and rows:
            kpis.append(_kpi(thought[:48] or _pretty(cols[0]), rows[0][0], thought))
        elif len(rows) >= 2:
            charts.extend(from_table(cols, rows, title=thought[:60] or "Breakdown", cid=f"q{i}"))
    return kpis[:6], charts[:3]


def from_anomalies(anomalies) -> list[dict]:
    if not anomalies:
        return []
    counts = defaultdict(int)
    for a in anomalies:
        counts[str(a.get("verdict") or "flagged")] += 1
    if len(counts) < 1:
        return []
    items = sorted(counts.items(), key=lambda kv: -kv[1])
    return [_chart("anom", "doughnut", "Flagged incoming documents",
                   [k for k, _ in items], [v for _, v in items],
                   series="Documents",
                   subtitle="Anomaly Sentinel · severity mix")]


def from_answer(table=None, key_numbers=None, queries=None, anomalies=None):
    kpis = from_key_numbers(key_numbers or {})
    q_kpis, q_charts = from_queries(queries)
    seen = {k["label"].lower() for k in kpis}
    for k in q_kpis:
        if k["label"].lower() not in seen:
            kpis.append(k)
            seen.add(k["label"].lower())
    charts = q_charts
    if table and not charts:
        charts.extend(from_table(table.get("columns"), table.get("rows"),
                                 title="Answer breakdown", cid="ans"))
    charts.extend(from_anomalies(anomalies))
    # Drop charts that are just a single slice.
    charts = [c for c in charts if len(c.get("labels") or []) >= 2][:3]
    return {"kpis": kpis[:5], "charts": charts}


def _to_eur(amount, waers, budat, rates):
    if amount is None:
        return 0.0
    if (waers or "EUR") == "EUR":
        return float(amount)
    best = None
    for r in rates:
        if r["FCURR"] == waers and r["TCURR"] == "EUR" and r["GDATU"] <= (budat or ""):
            if best is None or r["GDATU"] > best["GDATU"]:
                best = r
    return float(amount) * float(best["UKURS"]) if best else float(amount)


def overview() -> dict:
    """Live P2P snapshot for business users. Pure SQL — no LLM."""
    meanings = semantics.LEARNED_INVOICE_MEANINGS
    rates = db.run("SELECT FCURR, TCURR, GDATU, UKURS FROM TCURR").dicts()
    stuck_rows = db.run(
        "SELECT r.WAERS, r.RMWWR, r.BUDAT, l.NAME1 "
        "FROM RBKP r JOIN LFA1 l ON l.LIFNR = r.LIFNR "
        "WHERE r.STAT_KZ = '34'").dicts()
    stuck_n = len(stuck_rows)
    stuck_eur = sum(_to_eur(r["RMWWR"], r["WAERS"], r["BUDAT"], rates) for r in stuck_rows)

    by_vendor = defaultdict(lambda: {"n": 0, "eur": 0.0})
    for r in stuck_rows:
        by_vendor[r["NAME1"]]["n"] += 1
        by_vendor[r["NAME1"]]["eur"] += _to_eur(r["RMWWR"], r["WAERS"], r["BUDAT"], rates)
    top = sorted(by_vendor.items(), key=lambda kv: -kv[1]["eur"])[:5]

    status = db.run(
        "SELECT STAT_KZ, COUNT(*) n FROM RBKP GROUP BY STAT_KZ ORDER BY n DESC").rows
    lands = db.run(
        "SELECT LAND1, COUNT(*) n FROM LFA1 GROUP BY LAND1 ORDER BY n DESC").rows
    po_types = db.run(
        "SELECT COALESCE(t.BATXT, k.BSART), COUNT(*) "
        "FROM EKKO k LEFT JOIN T161 t ON t.BSART = k.BSART "
        "GROUP BY k.BSART ORDER BY 2 DESC").rows
    waiting = db.scalar("SELECT COUNT(*) FROM EKKO WHERE STAT_KZ = '10'")
    failed = db.scalar("SELECT COUNT(*) FROM RBKP WHERE STAT_KZ = '60'")
    unpaid = db.scalar("SELECT COUNT(*) FROM RBKP WHERE STAT_KZ = '70'")
    blocked_vendors = db.scalar("SELECT COUNT(*) FROM LFA1 WHERE SPERR = 'X'")
    pay_block = db.scalar(
        "SELECT COUNT(*) FROM RBKP WHERE ZLSPR IS NOT NULL AND ZLSPR <> ''")

    status_labels = [f"{c} · {meanings.get(c, 'other')}" for c, _ in status]
    return {
        "kpis": [
            _kpi("Stuck invoices", stuck_n, "RBKP.STAT_KZ = 34 · in verification"),
            _kpi("Cash tied up", stuck_eur, "Stuck invoices converted to EUR via TCURR"),
            _kpi("Failed three-way match", failed, "STAT_KZ = 60 · needs a clerk"),
            _kpi("Released, not paid", unpaid, "STAT_KZ = 70"),
            _kpi("POs waiting approval", waiting, "EKKO.STAT_KZ = 10"),
        ],
        "charts": [
            _chart("ov-status", "doughnut", "Invoice book by stage",
                   status_labels, [n for _, n in status], series="Invoices",
                   subtitle="Current RBKP.STAT_KZ · meanings learned from ZTSTAT"),
            _chart("ov-vendors", "hbar", "Cash tied up — top 5 vendors",
                   [name for name, _ in top],
                   [round(d["eur"], 2) for _, d in top], series="EUR",
                   subtitle="Stuck invoices (34) · TCURR rate on/before posting date"),
            _chart("ov-blocks", "hbar", "Three different kinds of “blocked”",
                   [f"Vendors ({blocked_vendors})",
                    f"Payment-blocked invoices ({pay_block:,})",
                    f"Failed 3-way match ({failed:,})"],
                   [blocked_vendors, pay_block, failed], series="Count",
                   subtitle="LFA1.SPERR vs RBKP.ZLSPR vs STAT_KZ 60 — not the same thing"),
            _chart("ov-po", "doughnut", "Purchase orders by type",
                   [lab for lab, _ in po_types], [n for _, n in po_types],
                   series="Orders", subtitle="EKKO × T161"),
            _chart("ov-land", "bar", "Vendors by country",
                   [c for c, _ in lands], [n for _, n in lands],
                   series="Vendors", subtitle="LFA1.LAND1"),
        ],
        "note": ("Snapshot computed live from data/erp_legacy.db. Status 34 is "
                 "in verification — the 2018 catalogue saying it is “released” "
                 "is wrong. Currency totals use TCURR as-of the posting date."),
    }
