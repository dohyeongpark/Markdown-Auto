from __future__ import annotations

import hashlib
import hmac
import os
import secrets
import sqlite3
from datetime import UTC, datetime
from pathlib import Path

DB_PATH = Path(__file__).resolve().parent.parent / "api_keys.db"

_CREATE_TABLE = """
CREATE TABLE IF NOT EXISTS repo_keys (
    repo TEXT PRIMARY KEY,
    key_hash TEXT NOT NULL,
    created_at TEXT NOT NULL
)
"""


def _connect() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.execute(_CREATE_TABLE)
    os.chmod(DB_PATH, 0o600)
    return conn


def _hash_key(raw_key: str) -> str:
    return hashlib.sha256(raw_key.encode()).hexdigest()


def issue_repo_key(repo: str) -> str:
    """repo용 API 키를 새로 발급한다. 평문 키는 저장하지 않고 해시만 저장하므로,
    반환값을 호출자가 그 자리에서 전달하지 않으면 다시 조회할 방법이 없다(분실 시 재발급)."""
    raw_key = secrets.token_urlsafe(32)
    created_at = datetime.now(UTC).isoformat()
    with _connect() as conn:
        conn.execute(
            """
            INSERT INTO repo_keys (repo, key_hash, created_at)
            VALUES (?, ?, ?)
            ON CONFLICT(repo) DO UPDATE SET
                key_hash = excluded.key_hash,
                created_at = excluded.created_at
            """,
            (repo, _hash_key(raw_key), created_at),
        )
    return raw_key


def verify_repo_key(repo: str, raw_key: str) -> bool:
    with _connect() as conn:
        row = conn.execute(
            "SELECT key_hash FROM repo_keys WHERE repo = ?",
            (repo,),
        ).fetchone()
    if row is None:
        return False
    return hmac.compare_digest(row[0], _hash_key(raw_key))
