from __future__ import annotations

import os
import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).resolve().parent.parent / "state.db"

_CREATE_TABLE = """
CREATE TABLE IF NOT EXISTS branch_state (
    repo TEXT NOT NULL,
    branch TEXT NOT NULL,
    last_sha TEXT NOT NULL,
    PRIMARY KEY (repo, branch)
)
"""


def _connect() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.execute(_CREATE_TABLE)
    os.chmod(DB_PATH, 0o600)
    return conn


def get_last_processed_sha(repo: str, branch: str) -> str | None:
    with _connect() as conn:
        row = conn.execute(
            "SELECT last_sha FROM branch_state WHERE repo = ? AND branch = ?",
            (repo, branch),
        ).fetchone()
    return row[0] if row else None


def set_last_processed_sha(repo: str, branch: str, sha: str) -> None:
    with _connect() as conn:
        conn.execute(
            """
            INSERT INTO branch_state (repo, branch, last_sha)
            VALUES (?, ?, ?)
            ON CONFLICT(repo, branch) DO UPDATE SET last_sha = excluded.last_sha
            """,
            (repo, branch, sha),
        )
