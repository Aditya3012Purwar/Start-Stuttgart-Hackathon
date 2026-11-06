"""Learn what STAT_KZ values actually mean, from the data itself.

The data catalogue describes the status codes, but it was last revised in 2018
and "the status values were partly redefined during the 2019 harmonisation."
The handover note is explicit about where the truth lives:

    "If you need to know what a status value actually means today, look at the
     logging table. It records every status change with a timestamp, so you can
     see the actual sequence documents go through. That sequence is the truth."

So instead of trusting the catalogue we reconstruct the lifecycle from ZTSTAT
(OBJTY='RBKP') and derive each code's meaning from its position in the flow and
from the terminal states documents rest in.
"""

from __future__ import annotations

from dataclasses import dataclass

from . import db

# Human-readable meanings we can defend *from the data*: they are the ordered
# stages the log actually walks documents through, corroborated by the tickets.
LEARNED_INVOICE_MEANINGS = {
    "50": "Invoice recorded (entered, not yet in verification)",
    "34": "In invoice verification - recorded, NOT yet released for payment, NOT paid",
    "60": "Failed three-way match - blocked, needs a clerk (exception branch)",
    "70": "Approved / released for payment, not yet paid",
    "80": "Paid / process complete",
    "90": "Cancelled",
}


@dataclass
class StatusProfile:
    code: str
    entered: int          # how many times a document moved *into* this code
    left: int             # how many times a document moved *out of* this code
    is_terminal: bool     # documents that reach it and never leave
    typical_predecessors: list[str]
    typical_successors: list[str]
    learned_meaning: str


def learn_invoice_lifecycle() -> dict[str, StatusProfile]:
    """Reconstruct the RBKP status lifecycle from the ZTSTAT change log."""
    entered = {r[0]: r[1] for r in db.run(
        "SELECT STAT_NEU, COUNT(*) FROM ZTSTAT WHERE OBJTY='RBKP' "
        "GROUP BY STAT_NEU").rows}
    left = {r[0]: r[1] for r in db.run(
        "SELECT STAT_ALT, COUNT(*) FROM ZTSTAT WHERE OBJTY='RBKP' "
        "AND STAT_ALT<>'' GROUP BY STAT_ALT").rows}

    succ = db.run(
        "SELECT STAT_ALT, STAT_NEU, COUNT(*) c FROM ZTSTAT "
        "WHERE OBJTY='RBKP' AND STAT_ALT<>'' GROUP BY STAT_ALT, STAT_NEU").rows

    successors: dict[str, list[tuple[str, int]]] = {}
    predecessors: dict[str, list[tuple[str, int]]] = {}
    for a, b, c in succ:
        successors.setdefault(a, []).append((b, c))
        predecessors.setdefault(b, []).append((a, c))

    profiles: dict[str, StatusProfile] = {}
    for code in sorted(set(entered) | set(left)):
        e = entered.get(code, 0)
        l = left.get(code, 0)
        top_succ = [x for x, _ in sorted(
            successors.get(code, []), key=lambda t: -t[1])[:3]]
        top_pred = [x for x, _ in sorted(
            predecessors.get(code, []), key=lambda t: -t[1])[:3]]
        profiles[code] = StatusProfile(
            code=code,
            entered=e,
            left=l,
            is_terminal=(e > 0 and l == 0) or (e - l) > e * 0.5,
            typical_predecessors=top_pred,
            typical_successors=top_succ,
            learned_meaning=LEARNED_INVOICE_MEANINGS.get(code, "(undocumented)"),
        )
    return profiles
