"""A coordinated, LLM-driven multi-agent system for Purchase-to-Pay questions.

Four agents, each an LLM, work the question together against the live database.
They are not hard-coded to any question set and they do not read answers from a
schema-rendered lookup - every agent reasons from the real documents itself and
they COORDINATE: an agent that needs more information asks another agent for it,
that agent gathers it, and only then do they converge on a detailed answer.

  Agent 1  Context Miner  - reads DATABASE.md, the glossary, the process notes,
                            the emails and the tickets, and briefs the others on
                            what the question means and which rules/traps apply.
  Agent 2  Data Analyst   - writes SQL for the question and runs it live, in a
                            loop; explores, drills in, and may ask Agent 1 to
                            clarify a term before it trusts a number.
  Agent 3  Verifier       - stress-tests Agent 2's result: is it the right set,
                            does it fall into a known trap, is anything anomalous?
                            It can request further queries and have them run.
  Agent 4  Advisor        - synthesises everything into a detailed, plain-English
                            explanation: what the number means, how it was
                            derived step by step, why it matters, the fix, and
                            exactly who to contact.

All of this requires the OpenAI key (the one from the kickoff). Without it the
system falls back to a limited schema engine and says so.
"""

from __future__ import annotations

import json
import os
import re

from . import db, agent_anomaly, charts, llm

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HERE)

# Real people from the case correspondence (context/emails.md).
CONTACTS = {
    "ap":         {"person": "Sandra Weber", "dept": "Accounts Payable",
                   "source": "context/emails.md - Threads 1 & 6"},
    "proc_ctrl":  {"person": "Kai Mueller", "dept": "Procurement Controlling",
                   "source": "context/emails.md - Threads 1 & 2"},
    "controlling":{"person": "Markus Keller", "dept": "Financial Controlling",
                   "source": "context/emails.md - Thread 4"},
    "it":         {"person": "Anna Fischer", "dept": "IT Applications (MM/FI)",
                   "source": "context/emails.md - Thread 5"},
    "vmd":        {"person": "Vendor Master Data", "dept": "Vendor Master Data team",
                   "source": "context/emails.md - Thread 3"},
    "procurement":{"person": "Julia Hofmann", "dept": "Procurement",
                   "source": "context/emails.md - Threads 2 & 6"},
}
_ROSTER = "\n".join(f"- {k}: {v['person']}, {v['dept']} (source {v['source']})"
                    for k, v in CONTACTS.items())

_DOCS = None
_TABLES = None


def _read(path):
    try:
        with open(path, encoding="utf-8") as fh:
            return fh.read()
    except Exception:
        return ""


def _docs():
    """All the real material the agents reason over (cached, read once)."""
    global _DOCS
    if _DOCS is None:
        _DOCS = {
            "DATABASE.md": _read(os.path.join(REPO, "DATABASE.md")),
            "GLOSSARY.md": _read(os.path.join(REPO, "context", "GLOSSARY.md")),
            "PROCESS.md": _read(os.path.join(REPO, "context", "PROCESS.md")),
            "emails.md": _read(os.path.join(REPO, "context", "emails.md")),
            "tickets.jsonl": _read(os.path.join(REPO, "context", "tickets.jsonl")),
        }
    return _DOCS


def _tables():
    global _TABLES
    if _TABLES is None:
        _TABLES = db.list_tables()
    return _TABLES


# --------------------------------------------------------------------------- #
# LLM plumbing
# --------------------------------------------------------------------------- #

def _completion_kwargs(temperature):
    kwargs = {
        "model": llm.MODEL,
        "response_format": {"type": "json_object"},
    }
    # gpt-5-* reasoning models reject custom temperature.
    if not str(llm.MODEL).startswith("gpt-5"):
        kwargs["temperature"] = temperature
    return kwargs


def _chat(system, user, temperature=0.1):
    from openai import OpenAI
    client = OpenAI()
    resp = client.chat.completions.create(
        **_completion_kwargs(temperature),
        messages=[{"role": "system", "content": system},
                  {"role": "user", "content": user}])
    return json.loads(resp.choices[0].message.content)


def _chat_thread(system, messages, temperature=0):
    from openai import OpenAI
    client = OpenAI()
    resp = client.chat.completions.create(
        **_completion_kwargs(temperature),
        messages=[{"role": "system", "content": system}] + messages)
    return resp.choices[0].message.content


_WRITE = re.compile(r"\b(INSERT|UPDATE|DELETE|DROP|ALTER|CREATE|REPLACE|ATTACH|"
                    r"PRAGMA|VACUUM)\b", re.I)


def _safe_select(sql):
    s = (sql or "").strip().rstrip(";")
    return s.lower().startswith(("select", "with")) and not _WRITE.search(s)


def _run_sql(sql):
    if not _safe_select(sql):
        return {"error": "rejected: only read-only SELECT/WITH queries are allowed"}
    try:
        res = db.run(sql)
        return {"columns": res.columns, "rows": res.rows[:50],
                "row_count": len(res.rows)}
    except Exception as exc:
        return {"error": str(exc)}


# --------------------------------------------------------------------------- #
# Agent 1 - Context Miner
# --------------------------------------------------------------------------- #

_A1_SYS = (
    "You are Agent 1, the Context Miner in a four-agent finance analysis team. "
    "You read the company's real documents and brief your teammates. You never "
    "compute numbers - you explain meaning. Ground everything in the provided "
    "documents; cite which document a rule comes from. Be thorough: the analyst "
    "downstream depends on you to avoid the data traps. Respond as strict JSON: "
    '{"interpretation":"what the question is really asking, in business terms",'
    '"relevant_rules":[{"rule":"...","why_it_matters":"...","source":"file"}],'
    '"tables_to_use":["..."],"traps_to_avoid":["..."],'
    '"narration":"2-3 sentences describing what you found for the trace"}')


def agent1(question, extra=""):
    d = _docs()
    user = (f"QUESTION: {question}\n\n"
            f"=== DATABASE.md (authoritative data model) ===\n{d['DATABASE.md']}\n\n"
            f"=== GLOSSARY.md (data dictionary, partly outdated) ===\n{d['GLOSSARY.md']}\n\n"
            f"=== PROCESS.md ===\n{d['PROCESS.md']}\n\n"
            f"=== emails.md (staff correspondence) ===\n{d['emails.md']}\n\n"
            f"=== tickets.jsonl ===\n{d['tickets.jsonl'][:4000]}")
    if extra:
        user += f"\n\nA teammate asks you specifically: {extra}"
    return _chat(_A1_SYS, user, temperature=0.1)


# --------------------------------------------------------------------------- #
# Agent 2 - Data Analyst (agentic loop; can ask Agent 1 for help)
# --------------------------------------------------------------------------- #

_A2_SYS = (
    "You are Agent 2, the Data Analyst. You answer the question by writing and "
    "running read-only SQLite queries against the live database, using the data "
    "model in DATABASE.md and Agent 1's briefing. Work step by step: explore if "
    "you must, then compute the precise answer. Apply the traps Agent 1 named "
    "(price unit PEINH, deleted lines LOEKZ, currency conversion via TCURR, the "
    "true meaning of STAT_KZ from the change log, base tables only - no _SHADOW/"
    "_STG/_ARCH/_BAK/_OLD). Each turn respond as strict JSON with ONE action:\n"
    '{"action":"query","sql":"<one SELECT>","thought":"why you run this"}\n'
    '{"action":"ask_context","ask":"<a precise question for Agent 1>","thought":"..."}\n'
    '{"action":"final","key_numbers":{"label":value,...},'
    '"findings":"what the data shows, precisely","narration":"2-3 sentences for the trace"}\n'
    "Prefer few, well-aimed queries. Never write to the database.")


def agent2(question, brief, coord, trace_queries):
    d = _docs()
    messages = [{"role": "user", "content":
                 f"QUESTION: {question}\n\nAGENT 1 BRIEFING:\n{json.dumps(brief)}\n\n"
                 f"DATA MODEL (DATABASE.md):\n{d['DATABASE.md']}\n\n"
                 f"There are {len(_tables())} tables; the core ones are in the data "
                 f"model above. Begin."}]
    result = {"findings": "", "key_numbers": {}, "narration": ""}
    for _ in range(6):
        raw = _chat_thread(_A2_SYS, messages)
        messages.append({"role": "assistant", "content": raw})
        try:
            out = json.loads(raw)
        except Exception:
            break
        act = out.get("action")
        if act == "query":
            sql = out.get("sql", "")
            res = _run_sql(sql)
            trace_queries.append({"sql": sql, "result": res,
                                  "thought": out.get("thought", "")})
            messages.append({"role": "user",
                             "content": f"RESULT: {json.dumps(res)[:3000]}"})
        elif act == "ask_context":
            ask = out.get("ask", "")
            ans = agent1(question, extra=ask)
            coord.append({"from": "Agent 2", "to": "Agent 1", "ask": ask,
                          "got": ans.get("narration", "")})
            messages.append({"role": "user", "content":
                             f"AGENT 1 REPLIES: {json.dumps(ans)[:2000]}"})
        elif act == "final":
            result = {"findings": out.get("findings", ""),
                      "key_numbers": out.get("key_numbers", {}),
                      "narration": out.get("narration", "")}
            break
        else:
            break
    return result


# --------------------------------------------------------------------------- #
# Agent 3 - Verifier (can request follow-up queries)
# --------------------------------------------------------------------------- #

_A3_SYS = (
    "You are Agent 3, the Verifier and Anomaly Sentinel. You stress-test Agent "
    "2's result before it is trusted: is it the correct set (not a look-alike), "
    "did it fall into a trap Agent 1 warned about, and - for document questions "
    "- is anything genuinely anomalous versus history? You may request extra "
    "queries to check. Respond as strict JSON:\n"
    '{"action":"verify","sql":["<check query>",...],"thought":"what you want to confirm"}\n'
    '{"action":"final","holds":true/false,"is_problem":true/false,'
    '"problem":"plain, or null","confidence":"high/medium/low",'
    '"narration":"2-3 sentences for the trace"}')


def agent3(question, brief, analyst, trace_queries, coord, anomalies=None):
    ctx = (f"QUESTION: {question}\nAGENT 1 TRAPS: {brief.get('traps_to_avoid')}\n"
           f"AGENT 2 FINDINGS: {analyst.get('findings')}\n"
           f"AGENT 2 NUMBERS: {analyst.get('key_numbers')}\n"
           f"QUERIES RUN: {json.dumps([q['sql'] for q in trace_queries])[:1500]}")
    if anomalies:
        ctx += f"\nANOMALY SCAN (historical base rates): {json.dumps(anomalies)[:2500]}"
    messages = [{"role": "user", "content": ctx}]
    for _ in range(3):
        raw = _chat_thread(_A3_SYS, messages)
        messages.append({"role": "assistant", "content": raw})
        try:
            out = json.loads(raw)
        except Exception:
            break
        if out.get("action") == "verify":
            results = []
            for sql in out.get("sql", [])[:4]:
                res = _run_sql(sql)
                trace_queries.append({"sql": sql, "result": res,
                                      "thought": "Agent 3 verification"})
                results.append({"sql": sql, "result": res})
            coord.append({"from": "Agent 3", "to": "Agent 2",
                          "ask": "run verification queries",
                          "got": f"{len(results)} check(s) executed"})
            messages.append({"role": "user",
                             "content": f"CHECK RESULTS: {json.dumps(results)[:3000]}"})
        else:
            return out
    return {"holds": True, "is_problem": False, "problem": None,
            "confidence": "low", "narration": "Verification inconclusive."}


# --------------------------------------------------------------------------- #
# Agent 4 - Advisor (detailed synthesis)
# --------------------------------------------------------------------------- #

_A4_SYS = (
    "You are Agent 4, the Advisor - an internal audit & assurance specialist "
    "briefing a NON-TECHNICAL colleague. Synthesise the team's work into a clear, "
    "DETAILED explanation. Do not be terse: explain what the number means, HOW it "
    "was derived step by step, WHY it matters, and the reasoning behind any "
    "problem and its fix. Use ONLY the provided facts; never invent numbers. "
    "Choose the right contact(s) from the roster and say why. Respond as strict "
    "JSON:\n"
    '{"headline":"one-sentence answer with the key number",'
    '"explanation":"3-6 sentences, plain language, explaining how it was worked '
    'out and the reasoning - use \\n\\n between paragraphs",'
    '"status":"problem" or "info",'
    '"problem":"detailed plain explanation, or null",'
    '"fix":"detailed plain steps, or null",'
    '"contacts":[{"key":"<roster key>","why":"why them, specifically"}],'
    '"spoken":"a natural 2-4 sentence spoken summary"}')


def agent4(question, brief, analyst, verify):
    user = (f"QUESTION: {question}\n\nAGENT 1 (context): {json.dumps(brief)[:2500]}\n\n"
            f"AGENT 2 (analysis): findings={analyst.get('findings')} "
            f"numbers={analyst.get('key_numbers')}\n\n"
            f"AGENT 3 (verification): {json.dumps(verify)[:1500]}\n\n"
            f"CONTACT ROSTER (choose from these real people):\n{_ROSTER}")
    return _chat(_A4_SYS, user, temperature=0.2)


# --------------------------------------------------------------------------- #
# Orchestration
# --------------------------------------------------------------------------- #

_DOC_HINTS = ("document", "documents", "look wrong", "anomal", "suspicious",
              "incoming", "recent doc", "fraud", "unusual", "flagged")


def reason(question: str) -> dict:
    question = (question or "").strip()
    if not question:
        return {"matched": False, "headline": "Ask me a question."}
    if not llm.available():
        return _fallback(question)

    coord = []            # inter-agent messages
    trace_queries = []    # every SQL any agent ran, with results

    # Agent 1 briefs the team.
    brief = agent1(question)

    # Agent 3 pre-computes the historical anomaly picture only when relevant.
    anomalies = None
    if any(h in question.lower() for h in _DOC_HINTS):
        A = agent_anomaly.detect()
        anomalies = {"flagged": A["flagged_count"], "total": A["total_documents"],
                     "clean": A["clean_count"], "normal_model": A["normal_model"],
                     "examples": [{"doc": r["doc_id"], "vendor": r["vendor"],
                                   "flags": r["flags"]} for r in A["results"]
                                  if r["flags"]][:8]}

    # Agent 2 investigates (and may consult Agent 1).
    analyst = agent2(question, brief, coord, trace_queries)
    # Agent 3 verifies (and may request more queries).
    verify = agent3(question, brief, analyst, trace_queries, coord, anomalies)
    # Agent 4 synthesises a detailed answer.
    advice = agent4(question, brief, analyst, verify)

    contacts = []
    for c in advice.get("contacts", []):
        key = c.get("key")
        if key in CONTACTS:
            contacts.append(dict(CONTACTS[key], why=c.get("why", "")))

    status = advice.get("status") or ("problem" if verify.get("is_problem") else "info")
    evidence = [{"label": q.get("thought") or "query", "sql": q["sql"],
                 "note": _note(q["result"])} for q in trace_queries]

    # Build a detailed trace showing the coordination.
    trace = [
        {"agent": "Agent 1 · Context Miner", "action": "Read the documents & briefed the team",
         "detail": brief.get("narration", "") + _rules_line(brief)},
        {"agent": "Agent 2 · Data Analyst",
         "action": f"Wrote & ran {len(trace_queries)} live quer"
                   f"{'y' if len(trace_queries)==1 else 'ies'}",
         "detail": analyst.get("narration", "") + _coord_line(coord, "Agent 2")},
        {"agent": "Agent 3 · Verifier",
         "action": "Stress-tested the result",
         "detail": verify.get("narration", "") +
                   f" (confidence: {verify.get('confidence','?')})"},
        {"agent": "Agent 4 · Advisor", "action": "Wrote the detailed briefing",
         "detail": "Synthesised the team's work into the explanation below."},
    ]

    last_table = _last_multirow(trace_queries)
    result = {
        "matched": True, "question": question, "mode": "llm",
        "status": status, "headline": advice.get("headline", ""),
        "explanation": advice.get("explanation", ""),
        "problem": advice.get("problem"), "fix": advice.get("fix"),
        "contacts": contacts, "spoken": advice.get("spoken", ""),
        "evidence": evidence, "trace": trace,
        "coordination": coord, "table": last_table,
        "ui": {"tab": "ask", "focus": None},
    }
    if anomalies:
        result["anomalies"] = [{"doc_id": e["doc"], "vendor": e["vendor"],
                                "verdict": e["flags"][0]["severity"],
                                "flags": e["flags"]}
                               for e in anomalies["examples"]]
    result["visuals"] = charts.from_answer(
        table=last_table,
        key_numbers=analyst.get("key_numbers") or {},
        queries=trace_queries,
        anomalies=result.get("anomalies"),
    )
    return result


def _note(res):
    if "error" in res:
        return "ERROR: " + res["error"]
    if res.get("row_count") == 1 and len(res.get("columns", [])) == 1:
        return str(res["rows"][0][0])
    return f"{res.get('row_count', 0)} row(s)"


def _rules_line(brief):
    r = brief.get("relevant_rules", [])
    return (" Applied " + str(len(r)) + " rule(s) from the documents.") if r else ""


def _coord_line(coord, who):
    asks = [c for c in coord if c["from"] == who]
    return (f" It asked Agent 1 to clarify {len(asks)} point(s).") if asks else ""


def _last_multirow(qs):
    for q in reversed(qs):
        r = q["result"]
        if "error" not in r and r.get("row_count", 0) > 1 and len(r.get("columns", [])) >= 1:
            return {"columns": r["columns"], "rows": r["rows"]}
    return None


# --------------------------------------------------------------------------- #
# Fallback (no key) - honest and limited. The real system is the LLM team above.
# --------------------------------------------------------------------------- #

def _fallback(question):
    trace = [
        {"agent": "Agent 1 · Context Miner", "action": "Ready",
         "detail": "Can read DATABASE.md, the glossary, the emails and tickets."},
        {"agent": "Agent 2 · Data Analyst", "action": "Waiting for the reasoning key",
         "detail": "The analyst writes and runs live SQL with the LLM."},
        {"agent": "Agent 3 · Verifier", "action": "Waiting", "detail": "Verifies the analyst's result."},
        {"agent": "Agent 4 · Advisor", "action": "Waiting", "detail": "Writes the detailed briefing."},
    ]
    return {
        "matched": False, "question": question, "status": "ok", "mode": "grounded",
        "headline": "Add your OpenAI key to switch the agent team on.",
        "explanation": ("This build runs four coordinating LLM agents that read "
                        "DATABASE.md and the correspondence, write and run SQL "
                        "live, verify each other's work, and explain the result "
                        "in detail. That reasoning needs the OpenAI key from the "
                        "kickoff.\n\nPaste it into the .env file as "
                        "OPENAI_API_KEY=sk-... and restart the server - nothing "
                        "else changes, and the agents come to life."),
        "problem": None, "fix": None, "contacts": [], "evidence": [],
        "spoken": ("To run the full agent team, add your OpenAI key to the env "
                   "file and restart. Then I can reason over any question live."),
        "trace": trace, "ui": {"tab": "ask", "focus": None},
    }
