from pathlib import Path

from app import auth_store


def test_verify_repo_key_fails_when_no_key_issued(tmp_path: Path, monkeypatch):
    monkeypatch.setattr(auth_store, "DB_PATH", tmp_path / "api_keys.db")

    assert auth_store.verify_repo_key("owner/repo", "anything") is False


def test_issue_then_verify_roundtrip(tmp_path: Path, monkeypatch):
    monkeypatch.setattr(auth_store, "DB_PATH", tmp_path / "api_keys.db")

    api_key = auth_store.issue_repo_key("owner/repo")

    assert auth_store.verify_repo_key("owner/repo", api_key) is True


def test_verify_repo_key_rejects_wrong_key(tmp_path: Path, monkeypatch):
    monkeypatch.setattr(auth_store, "DB_PATH", tmp_path / "api_keys.db")
    auth_store.issue_repo_key("owner/repo")

    assert auth_store.verify_repo_key("owner/repo", "wrong-key") is False


def test_key_scoped_per_repo(tmp_path: Path, monkeypatch):
    monkeypatch.setattr(auth_store, "DB_PATH", tmp_path / "api_keys.db")
    key_a = auth_store.issue_repo_key("owner/repo-a")
    auth_store.issue_repo_key("owner/repo-b")

    assert auth_store.verify_repo_key("owner/repo-b", key_a) is False


def test_reissue_invalidates_previous_key(tmp_path: Path, monkeypatch):
    monkeypatch.setattr(auth_store, "DB_PATH", tmp_path / "api_keys.db")
    old_key = auth_store.issue_repo_key("owner/repo")
    new_key = auth_store.issue_repo_key("owner/repo")

    assert auth_store.verify_repo_key("owner/repo", old_key) is False
    assert auth_store.verify_repo_key("owner/repo", new_key) is True


def test_key_hash_not_stored_as_plaintext(tmp_path: Path, monkeypatch):
    monkeypatch.setattr(auth_store, "DB_PATH", tmp_path / "api_keys.db")
    api_key = auth_store.issue_repo_key("owner/repo")

    with auth_store._connect() as conn:
        row = conn.execute("SELECT key_hash FROM repo_keys WHERE repo = ?", ("owner/repo",)).fetchone()

    assert row[0] != api_key
