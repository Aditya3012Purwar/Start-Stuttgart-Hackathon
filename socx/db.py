"""Read-only access to the legacy ERP database.

Every query runs through :func:`run` so that the SQL that produced a number is
always available alongside the number itself. In a finance department an answer
nobody can trace is worthless, so provenance is not optional here.
"""

from __future__ import annotations

import os
import sqlite3
from dataclasses import dataclass, field
from typing import Any

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HERE)
DB_PATH = os.path.join(REPO, "data", "erp_legacy.db")

# Tables a colleague hand-picked as relevant (data/schema.sql). Anything not in
# this set that looks like a copy of one of these is treated as untrusted.
TRUSTED_TABLES = {
    "LFA1", "MARA", "EKKO", "EKPO", "EKET", "MKPF", "MSEG", "RBKP",
    "RSEG", "BKPF", "ZTFRG", "ZTSTAT", "T161", "TCURR",
}

# Suffixes that mark a table as a stale copy, staging area or archive. These
# "look entirely plausible" but must never feed a report.
UNTRUSTED_SUFFIXES = ("_BAK", "_SHADOW", "_STG", "_ARCH", "_OLD")


@dataclass
class QueryResult:
    """A query, its rows, and enough metadata to reproduce it."""

    sql: str
    columns: list[str]
    rows: list[tuple]
    params: tuple = field(default_factory=tuple)

    @property
    def scalar(self) -> Any:
        if self.rows and self.rows[0]:
            return self.rows[0][0]
        return None

    def dicts(self) -> list[dict]:
        return [dict(zip(self.columns, r)) for r in self.rows]

    def to_provenance(self) -> dict:
        return {"sql": self.sql.strip(), "params": list(self.params)}


def _connect() -> sqlite3.Connection:
    # uri=True + mode=ro enforces the "treat it as a production replica" rule at
    # the driver level: writes fail rather than silently corrupting the case.
    con = sqlite3.connect(f"file:{DB_PATH}?mode=ro", uri=True)
    return con


def run(sql: str, params: tuple = ()) -> QueryResult:
    con = _connect()
    try:
        cur = con.execute(sql, params)
        rows = cur.fetchall()
        cols = [d[0] for d in cur.description] if cur.description else []
        return QueryResult(sql=sql, columns=cols, rows=rows, params=params)
    finally:
        con.close()


def scalar(sql: str, params: tuple = ()) -> Any:
    return run(sql, params).scalar


def list_tables() -> list[str]:
    return [r[0] for r in run(
        "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name").rows]


def table_count(table: str) -> int:
    return int(scalar(f"SELECT COUNT(*) FROM {table}"))


def is_untrusted(table: str) -> bool:
    up = table.upper()
    return any(up.endswith(sfx) for sfx in UNTRUSTED_SUFFIXES)
