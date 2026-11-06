#!/usr/bin/env python3
"""SOCX command line.

    python run.py                     # build the (data-less) dashboard.html
    python run.py --ask "..."         # run the 4 agents live on one question
    python serve.py                   # live server + voice + /api/ask

Nothing here reads a fixed answer set. Every question reruns the agents against
the live database. Add your OpenAI key to .env for full open-ended reasoning.
"""

from __future__ import annotations

import argparse
import json
import os

from render import build_dashboard
from socx import reasoner, llm, db

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "output")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--ask")
    args = ap.parse_args()

    if args.ask:
        print(json.dumps(reasoner.reason(args.ask), indent=2,
                         ensure_ascii=False, default=str))
        return

    os.makedirs(OUT, exist_ok=True)
    path = os.path.join(OUT, "dashboard.html")
    build_dashboard(path)
    print("SOCX dashboard built (data-less - it fills in live per question).")
    print(f"  reasoning : {'AI / ' + llm.MODEL if llm.available() else 'schema engine (add OPENAI_API_KEY to .env)'}")
    print(f"  tables    : {len(db.list_tables()):,} reachable")
    print(f"  -> {os.path.relpath(path, HERE)}   (serve with: PORT=8123 python serve.py)")


if __name__ == "__main__":
    main()
