"""Agent 1 - Context Miner.

Reads every place colleagues wrote down (or argued about) what the data means -
the data catalogue, the process description, eight months of support tickets and
the Accounts Payable / Procurement mailboxes - and turns that scattered,
contradictory human knowledge into a structured list of *candidate rules*.

A claim is never trusted just because it was written down. Each one is captured
with the exact quote and source it came from, and a machine-checkable
prediction, so Agent 2 can hold it up against the database and see whether it
survives contact with the data.
"""

from __future__ import annotations

import json
import os
import re
from dataclasses import asdict, dataclass, field

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HERE)
CTX = os.path.join(REPO, "context")


@dataclass
class Claim:
    id: str
    kind: str            # status_meaning | gotcha | truth_source | block_semantics
    subject: str         # e.g. "STAT_KZ=34" or "PO net value"
    claim: str           # what the source asserts
    source: str          # file it came from
    quote: str           # verbatim supporting text
    prediction: str      # how Agent 2 can test it against the data
    trust_hint: str = "" # what the source itself says about its reliability

    def to_dict(self) -> dict:
        return asdict(self)


def _read(name: str) -> str:
    path = os.path.join(CTX, name)
    with open(path, encoding="utf-8") as fh:
        return fh.read()


def _find_line(text: str, needle: str) -> str:
    for line in text.splitlines():
        if needle.lower() in line.lower():
            return line.strip().lstrip("|").strip()
    return ""


def _catalogue_status_claims(glossary: str) -> list[Claim]:
    """Pull the STAT_KZ table out of catalogue section 6 verbatim."""
    claims: list[Claim] = []
    rows = re.findall(r"^\|\s*(\d{2})\s*\|\s*([^|]+?)\s*\|\s*$",
                      glossary, flags=re.MULTILINE)
    for code, meaning in rows:
        claims.append(Claim(
            id=f"cat.stat.{code}",
            kind="status_meaning",
            subject=f"STAT_KZ={code}",
            claim=f"Catalogue says STAT_KZ {code} means '{meaning.strip()}'",
            source="context/GLOSSARY.md (section 6)",
            quote=f"| {code} | {meaning.strip()} |",
            prediction=(
                "Documents currently at this code, and the transitions in "
                "ZTSTAT that lead into/out of it, should be consistent with "
                "this meaning."),
            trust_hint=(
                "Catalogue last fully revised 2018-11-04; note warns values "
                "were partly redefined in the 2019 harmonisation and never "
                "updated."),
        ))
    return claims


def mine() -> dict:
    """Return the full mined knowledge base."""
    glossary = _read("GLOSSARY.md")
    process = _read("PROCESS.md")
    emails = _read("emails.md")
    tickets_raw = [json.loads(l) for l in _read("tickets.jsonl").splitlines()
                   if l.strip()]

    claims: list[Claim] = []
    claims += _catalogue_status_claims(glossary)

    # --- The single most important counter-claim: trust the log, not the doc.
    claims.append(Claim(
        id="truth.ztstat",
        kind="truth_source",
        subject="Where status meaning lives",
        claim=("The ZTSTAT logging table - not the catalogue - is the "
               "authoritative source for what a status value means today."),
        source="context/emails.md (Thread 5, T. Schmidt handover)",
        quote=("If you need to know what a status value actually means today, "
               "look at the logging table ... That sequence is the truth. The "
               "catalogue is what somebody wrote down seven years ago."),
        prediction=("Reconstructing the lifecycle from ZTSTAT should contradict "
                    "at least one catalogue meaning."),
        trust_hint="First-hand, from the application owner handing the system over.",
    ))

    # --- Support ticket that pins down what 34 really is.
    for t in tickets_raw:
        if t.get("ticket_id") == "INC0041207":
            claims.append(Claim(
                id="ticket.stat.34",
                kind="status_meaning",
                subject="STAT_KZ=34",
                claim=("Status 34 means the invoice is currently under "
                       "verification and payment is blocked - the catalogue "
                       "entry is outdated (pre-2019 range)."),
                source=f"context/tickets.jsonl ({t['ticket_id']})",
                quote=t["resolution"],
                prediction=("Invoices at 34 should NOT be paid and should sit "
                            "upstream of the release/paid states in ZTSTAT."),
                trust_hint="Closed as 'not a defect'; documentation fix raised "
                           "separately as CHG0008812.",
            ))

    # --- The three gotchas that make naive numbers wrong by orders of magnitude.
    claims.append(Claim(
        id="gotcha.peinh",
        kind="gotcha",
        subject="PO net value (EKPO.NETPR / PEINH)",
        claim=("Net price is per price unit (PEINH), not per piece. Value must "
               "be MENGE * NETPR / PEINH."),
        source="context/emails.md (Thread 2, K. Mueller)",
        quote=("The net price is not per piece, it is per price unit ... For a "
               "lot of our C-parts it is 100 or 1000. If you multiply quantity "
               "by price without dividing by the price unit you end up with "
               "numbers that are off by orders of magnitude."),
        prediction="Naive SUM(MENGE*NETPR) should be ~100-200x the correct value.",
    ))
    claims.append(Claim(
        id="gotcha.loekz",
        kind="gotcha",
        subject="Deleted PO items (EKPO.LOEKZ)",
        claim=("Cancelled line items are flagged (LOEKZ), not removed, and must "
               "be excluded from any volume/value figure."),
        source="context/emails.md (Thread 2) + context/PROCESS.md (pain points)",
        quote=("When a buyer cancels a single line, the line is not removed, it "
               "is only flagged. If you do not filter those out you are "
               "counting business that never happened."),
        prediction="Excluding LOEKZ<>'' should reduce PO counts/values measurably.",
    ))
    claims.append(Claim(
        id="gotcha.currency",
        kind="gotcha",
        subject="Currency conversion (TCURR)",
        claim=("Amounts are in document currency (USD/CNY/EUR). To total them, "
               "convert with the TCURR rate valid on or before the posting "
               "date - not today's rate."),
        source="context/emails.md (Thread 4, M. Keller)",
        quote=("There is a conversion rate table in the system with a valid-from "
               "date. The rate that applies is the last one valid before the "
               "document date, not today's rate."),
        prediction="Stuck invoices include non-EUR currencies; a raw SUM(RMWWR) "
                   "is meaningless.",
    ))

    # --- The block ambiguity: three different things, same word, same field name.
    claims.append(Claim(
        id="block.semantics",
        kind="block_semantics",
        subject="'Blocked' (vendor vs payment vs verification)",
        claim=("'Blocked' means three independent things: vendor block "
               "(LFA1.SPERR), payment block (RBKP.ZLSPR), and verification "
               "block (failed three-way match). They are stored separately."),
        source="context/PROCESS.md (section 3) + context/emails.md (Thread 3)",
        quote=("A vendor block and a payment block are two entirely different "
               "things, and they are stored in two entirely different places. "
               "To make it worse both fields carry the same name in the system."),
        prediction=("Count of blocked vendors (LFA1.SPERR) and count of "
                    "payment-blocked invoices (RBKP.ZLSPR) should differ by a "
                    "large margin."),
    ))

    return {
        "agent": "Agent 1 - Context Miner",
        "sources": {
            "GLOSSARY.md": "Data catalogue (last full revision 2018-11-04)",
            "PROCESS.md": "Business process description (2023, no table names)",
            "tickets.jsonl": f"{len(tickets_raw)} support tickets (2025)",
            "emails.md": "AP / Procurement mail threads (2025)",
        },
        "claims": [c.to_dict() for c in claims],
        "claim_count": len(claims),
    }


if __name__ == "__main__":
    print(json.dumps(mine(), indent=2, ensure_ascii=False))
