"""Audit trail used by the demo handlers. DO NOT MODIFY.

Uses its own table (`_audit`) in the same SQLite file and its own short-lived
connections, so it is independent of however you implement the queue.
"""

import os
import sqlite3
import time
import uuid

_SCHEMA = """
CREATE TABLE IF NOT EXISTS _audit (
    run_id TEXT NOT NULL,
    n      INTEGER NOT NULL,
    event  TEXT NOT NULL,      -- start | ok | error
    pid    INTEGER NOT NULL,
    at     REAL NOT NULL
)
"""


def _connect(db: str) -> sqlite3.Connection:
    conn = sqlite3.connect(db, timeout=30, isolation_level=None)
    conn.execute(_SCHEMA)
    return conn


def record(db: str, n: int, event: str, run_id: str | None = None) -> str:
    run_id = run_id or uuid.uuid4().hex
    conn = _connect(db)
    try:
        conn.execute(
            "INSERT INTO _audit (run_id, n, event, pid, at) VALUES (?, ?, ?, ?, ?)",
            (run_id, n, event, os.getpid(), time.time()),
        )
    finally:
        conn.close()
    return run_id


def starts(db: str, n: int) -> int:
    """How many times a handler has started for job n so far."""
    conn = _connect(db)
    try:
        return conn.execute("SELECT COUNT(*) FROM _audit WHERE n = ? AND event = 'start'", (n,)).fetchone()[0]
    finally:
        conn.close()


def runs(db: str) -> list[tuple[int, str, float, float | None, str | None]]:
    """(n, run_id, started, finished, outcome) per run; finished is None if the run never ended."""
    conn = _connect(db)
    try:
        rows = conn.execute(
            """
            SELECT s.n, s.run_id, s.at, e.at, e.event
            FROM _audit s
            LEFT JOIN _audit e ON e.run_id = s.run_id AND e.event != 'start'
            WHERE s.event = 'start'
            ORDER BY s.n, s.at
            """
        ).fetchall()
    finally:
        conn.close()
    return rows
