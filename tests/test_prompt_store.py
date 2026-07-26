from pathlib import Path

from app import prompt_store


def test_get_prompt_config_returns_none_when_missing(tmp_path: Path, monkeypatch):
    monkeypatch.setattr(prompt_store, "DB_PATH", tmp_path / "prompt_config.db")

    assert prompt_store.get_prompt_config("owner/repo", "main") is None


def test_upsert_then_get_roundtrip(tmp_path: Path, monkeypatch):
    monkeypatch.setattr(prompt_store, "DB_PATH", tmp_path / "prompt_config.db")

    prompt_store.upsert_prompt_config(
        "owner/repo", "main", preset_id="educational", custom_instructions="짧게 써줘"
    )
    config = prompt_store.get_prompt_config("owner/repo", "main")

    assert config is not None
    assert config.preset_id == "educational"
    assert config.custom_instructions == "짧게 써줘"


def test_upsert_overwrites_existing_config(tmp_path: Path, monkeypatch):
    monkeypatch.setattr(prompt_store, "DB_PATH", tmp_path / "prompt_config.db")

    prompt_store.upsert_prompt_config("owner/repo", "main", preset_id="educational", custom_instructions="a")
    prompt_store.upsert_prompt_config("owner/repo", "main", preset_id="concise", custom_instructions="b")

    config = prompt_store.get_prompt_config("owner/repo", "main")
    assert config is not None
    assert config.preset_id == "concise"
    assert config.custom_instructions == "b"


def test_upsert_with_null_fields_roundtrips(tmp_path: Path, monkeypatch):
    monkeypatch.setattr(prompt_store, "DB_PATH", tmp_path / "prompt_config.db")

    prompt_store.upsert_prompt_config("owner/repo", "main", preset_id=None, custom_instructions=None)
    config = prompt_store.get_prompt_config("owner/repo", "main")

    assert config is not None
    assert config.preset_id is None
    assert config.custom_instructions is None


def test_config_scoped_per_repo_and_branch(tmp_path: Path, monkeypatch):
    monkeypatch.setattr(prompt_store, "DB_PATH", tmp_path / "prompt_config.db")

    prompt_store.upsert_prompt_config("owner/repo", "main", preset_id="educational", custom_instructions=None)
    prompt_store.upsert_prompt_config("owner/repo", "dev", preset_id="concise", custom_instructions=None)
    prompt_store.upsert_prompt_config("owner/other-repo", "main", preset_id=None, custom_instructions="x")

    assert prompt_store.get_prompt_config("owner/repo", "main").preset_id == "educational"
    assert prompt_store.get_prompt_config("owner/repo", "dev").preset_id == "concise"
    assert prompt_store.get_prompt_config("owner/other-repo", "main").custom_instructions == "x"
