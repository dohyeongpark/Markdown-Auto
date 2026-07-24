from __future__ import annotations

import sqlite3
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path

DB_PATH = Path(__file__).resolve().parent.parent / "docs.db"

_CREATE_TABLE = """
CREATE TABLE IF NOT EXISTS documents (
    repo TEXT NOT NULL,
    branch TEXT NOT NULL,
    directory TEXT NOT NULL,
    content TEXT NOT NULL,
    source_sha TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    PRIMARY KEY (repo, branch, directory)
)
"""


@dataclass(frozen=True)
class Document:
    repo: str
    branch: str
    directory: str
    content: str
    source_sha: str
    updated_at: str


def _connect() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.execute(_CREATE_TABLE)
    return conn


def get_document(repo: str, branch: str, directory: str) -> Document | None:
    with _connect() as conn:
        row = conn.execute(
            """
            SELECT repo, branch, directory, content, source_sha, updated_at
            FROM documents
            WHERE repo = ? AND branch = ? AND directory = ?
            """,
            (repo, branch, directory),
        ).fetchone()
    return Document(*row) if row else None


def list_documents(repo: str, branch: str) -> list[Document]:
    with _connect() as conn:
        rows = conn.execute(
            """
            SELECT repo, branch, directory, content, source_sha, updated_at
            FROM documents
            WHERE repo = ? AND branch = ?
            ORDER BY directory
            """,
            (repo, branch),
        ).fetchall()
    return [Document(*row) for row in rows]


def upsert_document(repo: str, branch: str, directory: str, content: str, source_sha: str) -> None:
    updated_at = datetime.now(UTC).isoformat()
    with _connect() as conn:
        conn.execute(
            """
            INSERT INTO documents (repo, branch, directory, content, source_sha, updated_at)
            VALUES (?, ?, ?, ?, ?, ?)
            ON CONFLICT(repo, branch, directory) DO UPDATE SET
                content = excluded.content,
                source_sha = excluded.source_sha,
                updated_at = excluded.updated_at
            """,
            (repo, branch, directory, content, source_sha, updated_at),
        )
