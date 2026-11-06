# SOCX — System of Context for Purchase-to-Pay

A three-agent system that sits on top of the legacy ERP (the *system of
records*) and turns it into a *system of context*: it collects the meaning that
lives in people's heads and mailboxes, checks that meaning against the data, and
hands each person a clear, evidenced answer to act on.

Built for the people in the case: **Accounts Payable** (the retiring colleague
who knows what the codes mean), **Procurement/Controlling**, **Vendor Master
Data**, **IT Applications**, and **Internal Audit**.

## The three agents

| Agent | Role | What it does |
|---|---|---|
| **1 · Context Miner** | Collect | Reads the catalogue, process doc, 43 tickets and the AP/Procurement mailboxes. Extracts **candidate rules**, each with the exact quote and source, plus a machine-checkable prediction. |
| **2 · Analyst / Validator** | Diagnose | Turns each claim into a prediction and **tests it against the database**. Surviving claims become verified rules; failing ones become **findings** — real problems with evidence, sample document numbers, the SQL used, and a fix. |
| **3 · Anomaly Sentinel** | Detect | Learns what *normal* looks like from 20 years of history (valid transitions, the verification gate, the amount-vs-PO distribution), then checks each **incoming document** against it. Flags only anomalies it can defend with a historical **base rate**, each with an action. |
| **4 · Advisor / Presenter** | Act | Answers the north-star question, routes every fix and alert to the **person who owns it**, and shows the provenance behind every number. |

Agents 2 and 3 both feed the Advisor: Agent 2 finds problems in the *database's meaning*, Agent 3 finds problems in *individual incoming documents*.

The database decides every contradiction, never source seniority — exactly what
the case asks for.

## The audit assistant — live reasoning, plain language, voice

Ask a question and the **four agents run live, then and there** — nothing is
pre-answered and the tool never reads the calibration answers in `questions.md`.
You watch the agents work (an animated trace), then get a **plain-language**
verdict written for a non-technical reader:

- **The answer**, in one sentence, no jargon.
- **The problem** — *only if this question surfaces one*. Ask something with no
  issue behind it (e.g. "how many suppliers are in Germany?") and it simply
  answers; Agent 4 says "nothing looks wrong here." Problems are discovered per
  question, not pre-listed.
- **How to fix it**, in plain steps.
- **Who to contact** — the real person and department (with an email + a
  one-click "copy briefing"), e.g. stuck-invoice code confusion → *Anna Fischer,
  IT Applications* (owns the dictionary) and *Sandra Weber, Accounts Payable*.

The four steps are genuinely executed live ([socx/reasoner.py](socx/reasoner.py)):
Agent 1 reads the relevant emails/tickets/dictionary, Agent 2 runs the numbers
against the live database *now*, Agent 3 checks documents when the question calls
for it, Agent 4 writes the plain briefing. The SQL/proof is tucked behind a
"show the proof" toggle so the reader isn't shown any of it unless they want it.

## The audit assistant — LLM explanations + voice

SOCX behaves like an **internal audit & assurance specialist**. Numbers stay
deterministic (validated SQL); on top of them an LLM layer produces the
**descriptive** ("what is happening") and **diagnostic** ("why, and how to fix
it, and who should act") narration, grounded strictly in the facts SOCX already
proved — it is given the measure, its SQL, the mined rules and the findings, and
told to explain them, never to invent numbers.

- **Voice agent** — tap the mic, ask in your own words. The assistant answers
  **out loud** (browser speech synthesis) *and drives the screen*: it routes
  your question, switches to the right tab, and highlights the exact invoice,
  finding or document behind the answer. Speech recognition uses Chrome's Web
  Speech API; typing works in every browser as a fallback.
- **Graceful degradation** — with no API key it still explains, using a
  grounded template built from the findings and rules (the pill reads
  *narration: grounded*). Add the key and the same flow reads as a fluent LLM
  briefing (*narration: gpt-4o*). Nothing else changes.

Enable the LLM (optional):

```bash
cp .env.example .env      # then paste your key: OPENAI_API_KEY=sk-...
```

## Run it

The pipeline and every number are deterministic and run offline
(Python 3.10–3.14). The LLM narration is the only part that uses the key.

```bash
python run.py                 # build output/dashboard.html + report.json
python run.py --selfcheck     # verify all answers against questions.md
python run.py --ask "how much money is tied up in stuck invoices?"
PORT=8123 python serve.py     # live dashboard + voice + LLM at http://localhost:8123
```

Endpoints: `/` (dashboard), `/api/ask?q=...` (routed answer + explanation + which
tab to show), `/api/health` (is the LLM on?). Open `output/dashboard.html`
directly for the offline version (voice + grounded explanations still work; LLM
narration needs the server).

## What it proves (findings)

| # | Problem | Verdict from the data |
|---|---|---|
| F1 | Catalogue says status **34 = "verified and released"** | **FALSE** — the ZTSTAT log moves documents *into* 34 from "recorded" and *out* toward "released/paid". 34 = still in verification. 2,227 invoices affected. |
| F2 | Status codes **60, 70** used but undocumented | Recovered from the log: 60 = failed three-way match, 70 = released, not paid. |
| F3 | Shadow/staging/archive tables (`RBKP_SHADOW`, `ZRBKP_STG`, …) | Real siblings with different row counts — trust only the base tables. |
| F4 | PO value overstated ~200× | Must divide by price unit (PEINH) and exclude deleted lines (LOEKZ). |
| F5 | "Blocked" means three different things | 29 blocked vendors ≠ 3,737 payment-blocked invoices ≠ 1,510 verification blocks. |
| F6 | Totals mix currencies | Convert via TCURR at the rate valid on/before the posting date. |

## North star

> *"Which supplier invoices are currently stuck, how much money is tied up, and
> why?"*

**2,227 invoices · 294,814,064.51 EUR · avg 7.36 days in verification** — with
the vendor breakdown, the longest-waiting invoice, the rule applied, and the SQL
that produced each figure.

## Scaling to all 1,274 tables

SOCX never trusts the schema extract. The semantic layer works from three
primitives that scale: a **table allow-list** (base tables only, shadow/staging
copies rejected by suffix), **status semantics learned from the ZTSTAT log**
rather than the catalogue, and a **measure library** where each business
question is one validated, provenance-carrying query. Adding a table means
adding a measure, not re-reading 95k tokens of DDL per question.

## Layout

```
socx/
  db.py             read-only DB access, every query carries its SQL
  semantics.py      learns STAT_KZ meaning from the ZTSTAT change log
  agent1_miner.py   Agent 1 — mine claims from context sources
  agent2_analyst.py Agent 2 — validate claims, produce findings + fixes
  agent_anomaly.py  Agent 3 — Anomaly Sentinel (learns normal, flags incoming)
  agent3_advisor.py Agent 4 — north star + persona routing
  qa.py             validated measures + keyword question router
  personas.py       the people the system serves
  llm.py            audit-voice explanations (LLM, grounded fallback)
  assistant.py      the brain the voice agent calls (route → explain → drive UI)
run.py              orchestrator (agents 1→4) + self-check + ask
render.py           builds the self-contained dashboard.html
serve.py            live server (stdlib only) with /api/ask
output/             report.json + dashboard.html
```
