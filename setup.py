#!/usr/bin/env python3
"""
Health check. Run this once after cloning:

    python setup.py

Verifies that the database is intact, that dependencies are installed and
that your API key is in place. Tells you what is missing if anything is.
"""

import gzip
import os
import shutil
import sqlite3
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
GZ = os.path.join(HERE, "data", "erp_legacy.db.gz")
DB = os.path.join(HERE, "data", "erp_legacy.db")

CORE = ["LFA1", "MARA", "EKKO", "EKPO", "EKET", "MKPF", "MSEG", "RBKP",
        "RSEG", "BKPF", "ZTFRG", "ZTSTAT", "T161", "TCURR"]


def check_env():
    """Report whether .env exists and actually carries a key."""
    path = os.path.join(HERE, ".env")
    if not os.path.exists(path):
        print(".env                MISSING -> copy .env.example to .env "
              "and paste your key")
        return
    key = ""
    with open(path, encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if line.startswith("OPENAI_API_KEY") and "=" in line:
                key = line.split("=", 1)[1].strip().strip('"').strip("'")
    if not key:
        print(".env                found, but OPENAI_API_KEY is empty")
    elif key.startswith("sk-paste") or "paste-the-key" in key:
        print(".env                found, but still contains the placeholder "
              "-> paste the key you were given")
    elif not key.startswith("sk-"):
        print(".env                found, but the key does not look like an "
              "OpenAI key (expected it to start with 'sk-')")
    else:
        print(".env                found, key looks plausible")


def main():
    if sys.version_info < (3, 10):
        sys.exit(f"Python {sys.version_info.major}.{sys.version_info.minor} "
                 "is too old. This case is tested on 3.10 - 3.14.")

    if not os.path.exists(DB):
        if not os.path.exists(GZ):
            sys.exit("data/erp_legacy.db is missing. Re-clone the repo.")
        print("Unpacking database ...")
        with gzip.open(GZ, "rb") as src, open(DB, "wb") as dst:
            shutil.copyfileobj(src, dst, 1024 * 1024)
    size = os.path.getsize(DB) / 1024 / 1024
    print(f"data/erp_legacy.db  {size:.1f} MB")

    con = sqlite3.connect(DB)
    cur = con.cursor()
    tables = [r[0] for r in cur.execute(
        "SELECT name FROM sqlite_master WHERE type='table'")]
    missing = [t for t in CORE if t not in tables]
    if missing:
        sys.exit(f"Database looks damaged, missing: {missing}")

    rows = sum(cur.execute(f"SELECT COUNT(*) FROM {t}").fetchone()[0]
               for t in CORE)
    print(f"tables              {len(tables)}")
    print(f"rows in the 14 core tables  {rows:,}")

    n_stuck = cur.execute(
        "SELECT COUNT(*) FROM RBKP WHERE STAT_KZ='34'").fetchone()[0]
    con.close()

    ok = n_stuck == 2227
    print(f"integrity check     {'ok' if ok else 'MISMATCH'}")
    if not ok:
        sys.exit("Database content is not what it should be. Re-clone.")

    try:
        import openai  # noqa: F401
        print("openai package      installed")
    except ImportError:
        print("openai package      MISSING -> run "
              "python -m pip install -r requirements.txt")

    check_env()

    print("\nReady. Next:  python baseline.py")


if __name__ == "__main__":
    main()
