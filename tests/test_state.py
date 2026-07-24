from pathlib import Path

from app import state


def test_roundtrip_last_processed_sha(tmp_path: Path, monkeypatch):
    monkeypatch.setattr(state, "DB_PATH", tmp_path / "state.db")

    assert state.get_last_processed_sha("owner/repo", "main") is None

    state.set_last_processed_sha("owner/repo", "main", "abc123")
    assert state.get_last_processed_sha("owner/repo", "main") == "abc123"

    state.set_last_processed_sha("owner/repo", "main", "def456")
    assert state.get_last_processed_sha("owner/repo", "main") == "def456"


def test_state_is_scoped_per_branch(tmp_path: Path, monkeypatch):
    monkeypatch.setattr(state, "DB_PATH", tmp_path / "state.db")

    state.set_last_processed_sha("owner/repo", "main", "main-sha")
    state.set_last_processed_sha("owner/repo", "dev", "dev-sha")

    assert state.get_last_processed_sha("owner/repo", "main") == "main-sha"
    assert state.get_last_processed_sha("owner/repo", "dev") == "dev-sha"
