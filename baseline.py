#!/usr/bin/env python3
"""
NAIVE BASELINE  --  this is the state of the art without context.

It does exactly what everybody tries first: throw the raw DDL at an LLM,
ask for SQL, run it, print the result. No glossary, no process knowledge,
no tickets, no verification.

It works for trivial questions and fails badly on anything that requires
knowing what the data actually means. That failure is the point of this
case. Your job is to beat it.

Usage:
    python baseline.py
    python baseline.py "how many invoices are stuck in verification?"
"""

import os
import re
import sqlite3
import sys

try:
    from openai import OpenAI
except ImportError:
    sys.exit("Missing dependency. Run:  python -m pip install -r requirements.txt")

HERE = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(HERE, "data", "erp_legacy.db")
SCHEMA_PATH = os.path.join(HERE, "data", "schema.sql")
MODEL = "gpt-5-nano"

DEFAULT_QUESTION = "How many supplier invoices are currently stuck in verification?"

PROMPT = """You are a SQL assistant for a legacy ERP database (SQLite).

Schema:
{schema}

Answer the user's question by writing a single SQLite query.
Return only the SQL, no explanation, no markdown fences.

Question: {question}
"""


def load_env():
    """Minimal .env loader so nobody has to install python-dotenv."""
    path = os.path.join(HERE, ".env")
    if not os.path.exists(path):
        return
    with open(path, encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, val = line.split("=", 1)
            os.environ.setdefault(key.strip(), val.strip().strip('"').strip("'"))


load_env()
MODEL = os.environ.get("OPENAI_MODEL", "gpt-5-nano")


def ask_for_sql(client, schema, question):
    kwargs = {
        "model": MODEL,
        "messages": [{"role": "user",
                      "content": PROMPT.format(schema=schema, question=question)}],
    }
    if not str(MODEL).startswith("gpt-5"):
        kwargs["temperature"] = 0
    resp = client.chat.completions.create(**kwargs)
    sql = resp.choices[0].message.content.strip()
    sql = re.sub(r"^```(?:sql)?|```$", "", sql, flags=re.MULTILINE).strip()
    return sql


def main():
    load_env()
    if not os.environ.get("OPENAI_API_KEY"):
        sys.exit(
            "OPENAI_API_KEY is not set.\n"
            "Copy .env.example to .env and paste the key you were given."
        )

    question = " ".join(sys.argv[1:]) or DEFAULT_QUESTION

    with open(SCHEMA_PATH, encoding="utf-8") as fh:
        schema = fh.read()

    client = OpenAI()

    print("=" * 70)
    print("QUESTION :", question)
    print("=" * 70)

    sql = ask_for_sql(client, schema, question)
    print("\nGENERATED SQL\n-------------")
    print(sql)

    con = sqlite3.connect(DB_PATH)
    try:
        rows = con.execute(sql).fetchall()
    except Exception as exc:
        print("\nQUERY FAILED:", exc)
        return
    finally:
        con.close()

    print("\nRESULT\n------")
    for row in rows[:20]:
        print("   ", row)
    if len(rows) > 20:
        print(f"    ... and {len(rows) - 20} more rows")

    print("""
----------------------------------------------------------------------
Now go and check that answer against questions.md.

If it happens to be right, ask yourself whether it was right for the
right reason, or whether the model guessed and got lucky. Then try:

    python baseline.py "what is the total net value of all valid purchase order items?"
    python baseline.py "which vendors are blocked?"

Both of those have an obvious-looking answer that is wrong by a wide
margin. The information needed to get them right exists - it is in
context/, not in the schema.
----------------------------------------------------------------------""")


if __name__ == "__main__":
    main()
