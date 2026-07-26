from __future__ import annotations

import os
import sqlite3
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path

DB_PATH = Path(__file__).resolve().parent.parent / "prompt_config.db"

_CREATE_TABLE = """
CREATE TABLE IF NOT EXISTS prompt_configs (
    repo TEXT NOT NULL,
    branch TEXT NOT NULL,
    preset_id TEXT,
    custom_instructions TEXT,
    updated_at TEXT NOT NULL,
    PRIMARY KEY (repo, branch)
)
"""


@dataclass(frozen=True)
class PromptConfig:
    repo: str
    branch: str
    preset_id: str | None
    custom_instructions: str | None
    updated_at: str


def _connect() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.execute(_CREATE_TABLE)
    os.chmod(DB_PATH, 0o600)
    return conn


def get_prompt_config(repo: str, branch: str) -> PromptConfig | None:
    with _connect() as conn:
        row = conn.execute(
            """
            SELECT repo, branch, preset_id, custom_instructions, updated_at
            FROM prompt_configs
            WHERE repo = ? AND branch = ?
            """,
            (repo, branch),
        ).fetchone()
    return PromptConfig(*row) if row else None


def upsert_prompt_config(
    repo: str, branch: str, *, preset_id: str | None, custom_instructions: str | None
) -> None:
    updated_at = datetime.now(UTC).isoformat()
    with _connect() as conn:
        conn.execute(
            """
            INSERT INTO prompt_configs (repo, branch, preset_id, custom_instructions, updated_at)
            VALUES (?, ?, ?, ?, ?)
            ON CONFLICT(repo, branch) DO UPDATE SET
                preset_id = excluded.preset_id,
                custom_instructions = excluded.custom_instructions,
                updated_at = excluded.updated_at
            """,
            (repo, branch, preset_id, custom_instructions, updated_at),
        )
