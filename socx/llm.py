"""LLM explanation layer - the voice of the audit & assurance specialist.

SOCX is deterministic where it counts: every number comes from validated SQL.
This module adds the *explanation* on top - descriptive ("what is happening")
and diagnostic ("why, and how to resolve it") - phrased the way an internal
auditor would brief the department that owns the problem.

It is grounded on purpose. The LLM is only ever given facts SOCX already proved
(the measure result, its SQL, the mined rules, the validated findings) and is
instructed to explain them, never to invent numbers. If no API key is present
the same structure is produced deterministically, so the product works offline
and simply reads richer when a key is added.
"""

from __future__ import annotations

import os

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HERE)


def _load_env() -> None:
    path = os.path.join(REPO, ".env")
    if not os.path.exists(path):
        return
    with open(path, encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            k, v = line.split("=", 1)
            os.environ.setdefault(k.strip(), v.strip().strip('"').strip("'"))


_load_env()
MODEL = os.environ.get("OPENAI_MODEL", "gpt-5-nano")


def available() -> bool:
    _load_env()
    key = os.environ.get("OPENAI_API_KEY", "")
    return bool(key) and key.startswith("sk-") and "paste" not in key


SYSTEM = (
    "You are SOCX, an internal audit & assurance specialist for a legacy "
    "Purchase-to-Pay ERP. You brief business departments (Accounts Payable, "
    "Procurement, Controlling, Vendor Master Data, IT). Your job is descriptive "
    "AND diagnostic analytics: say plainly what the data shows, then explain the "
    "likely root cause and the concrete remediation. Rules: use ONLY the facts "
    "provided - never invent numbers, vendors or codes; always ground the 'why' "
    "in the rule/source given; be concise and spoken-friendly (this may be read "
    "aloud). Structure: 1-2 sentences describing the finding, 1-2 on the root "
    "cause, 1-2 on how to resolve it and who should act. No markdown headers."
)


def _facts_block(question, answer, findings, claims) -> str:
    lines = [f"QUESTION: {question}"]
    if answer:
        if answer.get("value") is not None:
            lines.append(f"ANSWER: {answer.get('value_display', answer['value'])}")
        elif answer.get("rows"):
            lines.append("ANSWER (rows): " +
                         "; ".join(str(r) for r in answer["rows"][:5]))
        lines.append(f"WHAT IT MEASURES: {answer.get('explain','')}")
        if answer.get("provenance"):
            lines.append(f"SQL: {answer['provenance'].get('sql','')}")
    for c in claims:
        lines.append(f"RULE [{c['id']}] {c['claim']} (source: {c['source']})")
    for f in findings:
        lines.append(
            f"RELATED FINDING [{f['id']}] {f['title']}: {f.get('problem','')} "
            f"| verdict: {f.get('verdict','')} | fix: {f.get('solution','')}")
    return "\n".join(lines)


def _fallback(question, answer, findings, claims) -> str:
    """Deterministic descriptive+diagnostic explanation (no key needed)."""
    parts = []
    if answer and answer.get("value") is not None:
        parts.append(f"{answer.get('value_display', answer['value'])}. "
                     f"{answer.get('explain','')}")
    elif answer:
        parts.append(answer.get("explain", ""))
    if findings:
        f = findings[0]
        parts.append(f"Why this happens: {f.get('problem','')} "
                     f"The data verdict is: {f.get('verdict','')}")
        parts.append(f"How to resolve it: {f.get('solution','')}")
    elif claims:
        parts.append("This is grounded in the rule: " + claims[0]["claim"] +
                     f" (source: {claims[0]['source']}).")
    if not parts:
        parts.append("No validated basis was found for that question, so SOCX "
                     "will not guess. Ask about stuck invoices, blocked vendors, "
                     "purchase-order value, or the incoming-document anomalies.")
    return " ".join(p.strip() for p in parts if p.strip())


def explain(question, answer=None, findings=None, claims=None) -> dict:
    """Return {'mode': 'llm'|'grounded', 'text': ...}."""
    findings = findings or []
    claims = claims or []
    if not available():
        return {"mode": "grounded",
                "text": _fallback(question, answer, findings, claims)}
    try:
        from openai import OpenAI
        client = OpenAI()
        kwargs = {
            "model": MODEL,
            "messages": [
                {"role": "system", "content": SYSTEM},
                {"role": "user", "content": _facts_block(
                    question, answer, findings, claims)},
            ],
        }
        # gpt-5-* reasoning models reject custom temperature.
        if not str(MODEL).startswith("gpt-5"):
            kwargs["temperature"] = 0.2
        resp = client.chat.completions.create(**kwargs)
        return {"mode": "llm", "text": resp.choices[0].message.content.strip()}
    except Exception as exc:  # never let the narration break the answer
        return {"mode": "grounded",
                "text": _fallback(question, answer, findings, claims),
                "error": str(exc)}
