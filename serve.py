#!/usr/bin/env python3
"""Live SOCX server - stdlib only, no extra dependencies.

    python serve.py            # http://localhost:8000  (or PORT=8123 python serve.py)

The page loads with NO precomputed data. Every question hits /api/ask, which
reruns the whole 4-agent system live against the real database. Add your OpenAI
key to .env to enable full open-ended reasoning across all 1,274 tables.
"""

from __future__ import annotations

import json
import os
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import parse_qs, urlparse

from socx import llm, reasoner, db, charts
from render import build_dashboard

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "output")
PORT = int(os.environ.get("PORT", "8000"))


def _ensure_dashboard() -> str:
    os.makedirs(OUT, exist_ok=True)
    path = os.path.join(OUT, "dashboard.html")
    build_dashboard(path)
    return path


class Handler(BaseHTTPRequestHandler):
    def _send(self, code, body, ctype="application/json"):
        data = body.encode() if isinstance(body, str) else body
        self.send_response(code)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def do_GET(self):
        u = urlparse(self.path)
        if u.path in ("/", "/index.html", "/dashboard.html"):
            with open(os.path.join(OUT, "dashboard.html"), "rb") as fh:
                self._send(200, fh.read(), "text/html; charset=utf-8")
        elif u.path == "/api/ask":
            q = parse_qs(u.query).get("q", [""])[0]
            self._send(200, json.dumps(reasoner.reason(q), default=str))
        elif u.path == "/api/health":
            self._send(200, json.dumps({
                "llm": llm.available(), "model": llm.MODEL,
                "tables": len(db.list_tables())}))
        elif u.path == "/api/overview":
            self._send(200, json.dumps(charts.overview(), default=str))
        else:
            self._send(404, json.dumps({"error": "not found"}))

    def log_message(self, *a):
        pass


if __name__ == "__main__":
    _ensure_dashboard()
    print(f"SOCX live at http://localhost:{PORT}")
    print(f"  Reasoning: {'AI (OpenAI ' + llm.MODEL + ')' if llm.available() else 'schema engine - add OPENAI_API_KEY to .env for full LLM reasoning'}")
    print(f"  Tables reachable: {len(db.list_tables()):,}")
    ThreadingHTTPServer(("127.0.0.1", PORT), Handler).serve_forever()
