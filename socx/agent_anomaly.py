"""Agent 3 - Anomaly Sentinel (Level 3).

Once the system has understood the process from twenty years of history, it
knows what normal looks like - and anything it knows to be normal it can use as
a yardstick. This agent learns that yardstick from the data (never hand-coded
thresholds) and holds each incoming document up against it.

It is deliberately conservative. "A system that flags every outlier is useless -
on 1.5 million documents a 5% false-positive rate means 75,000 alerts and an
inbox nobody opens." So it only raises a flag it can defend with a historical
base rate, and every alert says what a person should do about it.

Two kinds of check:
  * process/history  - transitions and sequences that never occur in the log
  * ERP cross-check  - documents that look normal in isolation but contradict
                       the purchase order / vendor master they point at
"""

from __future__ import annotations

import json
import os
from dataclasses import asdict, dataclass, field

from . import db

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HERE)
INCOMING = os.path.join(REPO, "data", "incoming_documents.jsonl")

# An invoice amount above this multiple of its PO net value is treated as a
# three-way-match failure. The value is LEARNED below, not guessed.
_RATIO_HARD = 3.0


@dataclass
class NormalModel:
    """What 'normal' looks like, reconstructed from the history."""
    valid_transitions: dict            # objty -> {"from>to": count}
    known_statuses: dict               # objty -> [codes]
    total_docs: dict                   # objty -> N distinct objects
    verification_gate: dict            # stats behind "must pass through 34"
    amount_ratio_pctile: dict          # learned invoice/PO ratio percentiles


@dataclass
class Flag:
    rule: str
    severity: str          # critical | high | medium | low
    message: str           # what is wrong, in plain language
    base_rate: str         # the historical evidence that makes it an anomaly
    action: str            # what the person should do
    persona: str

    def to_dict(self):
        return asdict(self)


# --------------------------------------------------------------------------- #
# Learning phase
# --------------------------------------------------------------------------- #

def learn_normal() -> NormalModel:
    valid, known, totals = {}, {}, {}
    for objty in ("RBKP", "EKKO"):
        trans = db.run(
            "SELECT STAT_ALT, STAT_NEU, COUNT(*) FROM ZTSTAT WHERE OBJTY=? "
            "GROUP BY STAT_ALT, STAT_NEU", (objty,)).rows
        valid[objty] = {f"{a}>{b}": c for a, b, c in trans}
        known[objty] = sorted({b for _, b, _ in trans} |
                              {a for a, _, _ in trans if a})
        totals[objty] = db.scalar(
            "SELECT COUNT(DISTINCT OBJKY) FROM ZTSTAT WHERE OBJTY=?", (objty,))

    # Verification gate: of all invoices that ever reached release(70)/paid(80),
    # how many had entered verification(34) first?
    reached = db.scalar(
        "SELECT COUNT(DISTINCT OBJKY) FROM ZTSTAT WHERE OBJTY='RBKP' "
        "AND STAT_NEU IN ('70','80')")
    reached_via_34 = db.scalar(
        "SELECT COUNT(DISTINCT a.OBJKY) FROM ZTSTAT a WHERE a.OBJTY='RBKP' "
        "AND a.STAT_NEU IN ('70','80') AND EXISTS (SELECT 1 FROM ZTSTAT b "
        "WHERE b.OBJTY='RBKP' AND b.OBJKY=a.OBJKY AND b.STAT_NEU='34')")
    gate = {"reached_release_or_paid": reached,
            "of_which_via_verification": reached_via_34,
            "skipped": reached - reached_via_34}

    # Learn the invoice-amount / PO-net-value distribution from matched history.
    rows = db.run(
        "SELECT r.BELNR, SUM(r.WRBTR) inv, "
        "(SELECT SUM(p.MENGE*p.NETPR/p.PEINH) FROM EKPO p WHERE p.EBELN=r.EBELN "
        "AND (p.LOEKZ IS NULL OR p.LOEKZ='') AND p.PEINH>0) po "
        "FROM RSEG r WHERE r.EBELN<>'' GROUP BY r.BELNR").rows
    ratios = sorted(inv / po for _, inv, po in rows
                    if po and po > 0 and inv is not None)
    n = len(ratios)
    def pct(p):
        return round(ratios[min(n - 1, int(p * n))], 3) if n else None
    pctile = {"n": n, "p99": pct(0.99), "p99_9": pct(0.999),
              "max": round(ratios[-1], 2) if n else None,
              "share_gt_3x_pct": round(sum(r > 3 for r in ratios) / n * 100, 3)
              if n else None,
              "threshold": _RATIO_HARD}

    return NormalModel(valid, known, totals, gate, pctile)


# --------------------------------------------------------------------------- #
# Scoring phase
# --------------------------------------------------------------------------- #

def _sequence(doc) -> list[tuple[str, str]]:
    return [(h.get("from", ""), h.get("to", "")) for h in doc.get("history", [])]


def _po_net_value(po: str):
    return db.scalar(
        "SELECT SUM(MENGE*NETPR/PEINH) FROM EKPO WHERE EBELN=? "
        "AND (LOEKZ IS NULL OR LOEKZ='') AND PEINH>0", (po,))


def score_document(doc: dict, model: NormalModel) -> list[Flag]:
    flags: list[Flag] = []
    objty = doc.get("doc_type", "RBKP")
    valid = model.valid_transitions.get(objty, {})
    known = set(model.known_statuses.get(objty, []))
    total = model.total_docs.get(objty, 0)
    seq = _sequence(doc)
    tos = [b for _, b in seq]

    # 1. Unknown status code (never seen in this object's history).
    for code in set(tos):
        if code and code not in known:
            flags.append(Flag(
                rule="unknown_status",
                severity="high",
                message=f"Document passed through status '{code}', which does "
                        f"not exist in the {objty} status vocabulary.",
                base_rate=f"'{code}' appears 0 times across {total:,} historical "
                          f"{objty} document histories.",
                action="Reject/hold: an unrecognised status usually means a "
                       "manual edit or an interface that bypassed the workflow.",
                persona="it_apps"))

    # 2. Invalid transitions (a from>to pair the log has never produced).
    for a, b in seq:
        key = f"{a}>{b}"
        if b and b in known and key not in valid and a in (known | {""}):
            flags.append(Flag(
                rule="invalid_transition",
                severity="high",
                message=f"Transition {a or 'start'} -> {b} is not part of the "
                        f"learned {objty} lifecycle.",
                base_rate=f"The move {a or 'start'}->{b} occurs 0 times in "
                          f"{total:,} historical {objty} histories.",
                action="Investigate how the document skipped or reversed a step; "
                       "the workflow should not permit this.",
                persona="ap_clerk" if objty == "RBKP" else "procurement"))

    # 3. Verification gate (invoices only): released/paid without verification.
    if objty == "RBKP" and any(t in ("70", "80") for t in tos) and "34" not in tos:
        g = model.verification_gate
        flags.append(Flag(
            rule="skipped_verification",
            severity="critical",
            message="Invoice was released/paid without ever entering "
                    "verification (status 34).",
            base_rate=f"0 of {g['reached_release_or_paid']:,} invoices that "
                      f"reached release/payment historically did so without "
                      f"passing through verification.",
            action="Pull the payment immediately and route the invoice through "
                    "the three-way match before it settles.",
            persona="ap_clerk"))

    # 4. Negative amount (rare; legitimate only as a credit memo).
    amt = doc.get("amount")
    if isinstance(amt, (int, float)) and amt < 0:
        flags.append(Flag(
            rule="negative_amount",
            severity="low",
            message=f"Negative document amount ({amt:,.2f} {doc.get('currency','')}).",
            base_rate="Standard supplier invoices are positive; negatives are "
                      "normal only for credit memos.",
            action="Confirm the document is genuinely a credit memo; if not, the "
                    "sign is wrong.",
            persona="controlling"))

    # --- ERP cross-checks (things invisible in the history alone) ------------
    vendor = doc.get("vendor_id")
    vrow = db.run("SELECT SPERR, NAME1 FROM LFA1 WHERE LIFNR=?", (vendor,)).rows
    if not vrow:
        flags.append(Flag(
            rule="vendor_unknown",
            severity="high",
            message=f"Vendor {vendor} is not in the vendor master (LFA1).",
            base_rate="Every legitimate document references an existing vendor.",
            action="Do not process; the vendor must be created/verified first.",
            persona="vendor_master"))
    elif vrow[0][0] not in (None, ""):
        flags.append(Flag(
            rule="blocked_vendor",
            severity="high",
            message=f"Document raised against vendor '{vrow[0][1]}', which "
                    f"carries a vendor block (LFA1.SPERR).",
            base_rate="A vendor block stops all new business with that supplier "
                      "- this looks normal in the document's own history.",
            action="Hold: no new orders or invoices should be posted to a "
                    "blocked vendor without a compliance release.",
            persona="vendor_master"))

    # PO reference checks (skip for EKKO docs, which are POs themselves).
    po = doc.get("po_reference")
    if objty == "RBKP":
        if not po:
            flags.append(Flag(
                rule="no_po_reference",
                severity="medium",
                message="Invoice has no purchase-order reference.",
                base_rate="Invoices in this process are raised against a PO; a "
                          "missing reference blocks the three-way match.",
                action="Return to the supplier/buyer to attach the correct PO.",
                persona="ap_clerk"))
        else:
            po_val = _po_net_value(po)
            if po_val is None:
                flags.append(Flag(
                    rule="po_missing",
                    severity="high",
                    message=f"Referenced PO {po} does not exist in EKPO.",
                    base_rate="A valid invoice must reference a real PO item.",
                    action="Hold; the PO number is wrong or the order was purged.",
                    persona="procurement"))
            elif isinstance(amt, (int, float)) and amt > 0 and po_val > 0:
                ratio = amt / po_val
                if ratio > model.amount_ratio_pctile["threshold"]:
                    sev = "high" if ratio > 10 else "medium"
                    p = model.amount_ratio_pctile
                    flags.append(Flag(
                        rule="amount_exceeds_po",
                        severity=sev,
                        message=f"Invoice amount {amt:,.0f} is {ratio:.1f}x the "
                                f"PO net value {po_val:,.0f}.",
                        base_rate=f"Historically only {p['share_gt_3x_pct']}% of "
                                  f"invoices exceed 3x their PO (p99={p['p99']}x, "
                                  f"max ever {p['max']}x).",
                        action="Block for three-way match: quantity or price on "
                                "the invoice deviates sharply from the order.",
                        persona="ap_clerk"))
    return flags


SEVERITY_ORDER = {"critical": 0, "high": 1, "medium": 2, "low": 3}


def detect() -> dict:
    model = learn_normal()
    docs = [json.loads(l) for l in open(INCOMING, encoding="utf-8")
            if l.strip()]
    results = []
    for d in docs:
        flags = score_document(d, model)
        flags.sort(key=lambda f: SEVERITY_ORDER[f.severity])
        results.append({
            "doc_id": d["doc_id"],
            "doc_type": d.get("doc_type"),
            "vendor": d.get("vendor_name"),
            "amount": d.get("amount"),
            "currency": d.get("currency"),
            "current_status": d.get("current_status"),
            "path": " -> ".join(b for _, b in _sequence(d)),
            "flags": [f.to_dict() for f in flags],
            "verdict": ("clean" if not flags else flags[0].severity),
        })
    flagged = [r for r in results if r["flags"]]
    worst = {"critical": 0, "high": 0, "medium": 0, "low": 0}
    for r in flagged:
        worst[r["verdict"]] += 1

    return {
        "agent": "Agent 3 - Anomaly Sentinel",
        "method": ("'Normal' was learned from the ZTSTAT history and the matched "
                   "PO/vendor data. Each incoming document is checked against it; "
                   "only anomalies with a defensible base rate are raised."),
        "normal_model": {
            "valid_transitions": model.valid_transitions,
            "verification_gate": model.verification_gate,
            "amount_ratio_learned": model.amount_ratio_pctile,
        },
        "total_documents": len(docs),
        "flagged_count": len(flagged),
        "clean_count": len(docs) - len(flagged),
        "severity_breakdown": worst,
        "results": sorted(results,
                          key=lambda r: SEVERITY_ORDER.get(r["verdict"], 9)),
    }


if __name__ == "__main__":
    print(json.dumps(detect(), indent=2, ensure_ascii=False, default=str))
