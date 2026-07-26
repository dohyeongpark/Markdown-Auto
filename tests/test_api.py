import os
from pathlib import Path

os.environ.setdefault("GITHUB_WEBHOOK_SECRET", "test-secret")
os.environ.setdefault("GITHUB_BOT_TOKEN", "test-token")
os.environ.setdefault("LLM_API_KEY", "test-key")

from fastapi.testclient import TestClient

from app import docs_store, prompt_store
from app.main import app

client = TestClient(app)


def _use_scratch_db(tmp_path: Path, monkeypatch):
    monkeypatch.setattr(docs_store, "DB_PATH", tmp_path / "docs.db")
    monkeypatch.setattr(prompt_store, "DB_PATH", tmp_path / "prompt_config.db")


def test_list_docs_empty(tmp_path: Path, monkeypatch):
    _use_scratch_db(tmp_path, monkeypatch)

    response = client.get("/api/owner/repo/main/docs")

    assert response.status_code == 200
    assert response.json() == []


def test_get_doc_for_subdirectory(tmp_path: Path, monkeypatch):
    _use_scratch_db(tmp_path, monkeypatch)
    docs_store.upsert_document("owner/repo", "main", "app", "# App", "sha1")

    response = client.get("/api/owner/repo/main/docs/app")

    assert response.status_code == 200
    assert response.json()["content"] == "# App"


def test_get_doc_for_root_directory_uses_slug_not_dot(tmp_path: Path, monkeypatch):
    """루트 디렉토리(".")를 URL에 그대로 쓰면 dot-segment 정규화로
    /docs/. 가 /docs/ (목록 엔드포인트)로 접혀버리는 회귀를 막는 테스트.
    """
    _use_scratch_db(tmp_path, monkeypatch)
    docs_store.upsert_document("owner/repo", "main", ".", "# Root", "sha1")

    response = client.get("/api/owner/repo/main/docs/_root")

    assert response.status_code == 200
    body = response.json()
    assert body["directory"] == "."
    assert body["content"] == "# Root"


def test_get_doc_missing_returns_404(tmp_path: Path, monkeypatch):
    _use_scratch_db(tmp_path, monkeypatch)

    response = client.get("/api/owner/repo/main/docs/missing")

    assert response.status_code == 404


def test_list_prompt_presets_returns_registry_ids():
    response = client.get("/api/prompt-presets")

    assert response.status_code == 200
    ids = {preset["id"] for preset in response.json()}
    assert {"default", "educational", "concise"} <= ids


def test_get_prompt_config_defaults_to_null_fields_when_unset(tmp_path: Path, monkeypatch):
    _use_scratch_db(tmp_path, monkeypatch)

    response = client.get("/api/owner/repo/main/prompt-config")

    assert response.status_code == 200
    body = response.json()
    assert body == {"preset_id": None, "custom_instructions": None, "updated_at": None}


def test_put_prompt_config_roundtrip(tmp_path: Path, monkeypatch):
    _use_scratch_db(tmp_path, monkeypatch)

    put_response = client.put(
        "/api/owner/repo/main/prompt-config",
        json={"preset_id": "educational", "custom_instructions": "짧게"},
    )
    assert put_response.status_code == 200

    get_response = client.get("/api/owner/repo/main/prompt-config")
    body = get_response.json()
    assert body["preset_id"] == "educational"
    assert body["custom_instructions"] == "짧게"
    assert body["updated_at"] is not None


def test_put_prompt_config_rejects_unknown_preset_id(tmp_path: Path, monkeypatch):
    _use_scratch_db(tmp_path, monkeypatch)

    response = client.put(
        "/api/owner/repo/main/prompt-config",
        json={"preset_id": "does-not-exist", "custom_instructions": None},
    )

    assert response.status_code == 422
