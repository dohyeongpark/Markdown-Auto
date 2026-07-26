import os
from pathlib import Path

os.environ.setdefault("GITHUB_WEBHOOK_SECRET", "test-secret")
os.environ.setdefault("GITHUB_BOT_TOKEN", "test-token")
os.environ.setdefault("LLM_API_KEY", "test-key")
os.environ.setdefault("ADMIN_API_KEY", "test-admin-key")

from fastapi.testclient import TestClient

from app import auth_store, docs_store, prompt_store
from app.main import app

client = TestClient(app)


def _use_scratch_db(tmp_path: Path, monkeypatch):
    monkeypatch.setattr(docs_store, "DB_PATH", tmp_path / "docs.db")
    monkeypatch.setattr(prompt_store, "DB_PATH", tmp_path / "prompt_config.db")
    monkeypatch.setattr(auth_store, "DB_PATH", tmp_path / "api_keys.db")


def _auth_headers(repo: str) -> dict[str, str]:
    api_key = auth_store.issue_repo_key(repo)
    return {"X-Repo-Api-Key": api_key}


def test_list_docs_empty(tmp_path: Path, monkeypatch):
    _use_scratch_db(tmp_path, monkeypatch)

    response = client.get("/api/owner/repo/main/docs", headers=_auth_headers("owner/repo"))

    assert response.status_code == 200
    assert response.json() == []


def test_list_docs_without_api_key_returns_401(tmp_path: Path, monkeypatch):
    _use_scratch_db(tmp_path, monkeypatch)

    response = client.get("/api/owner/repo/main/docs")

    assert response.status_code == 401


def test_list_docs_with_wrong_api_key_returns_401(tmp_path: Path, monkeypatch):
    _use_scratch_db(tmp_path, monkeypatch)
    _auth_headers("owner/repo")  # 발급은 해두되 사용하지 않음

    response = client.get("/api/owner/repo/main/docs", headers={"X-Repo-Api-Key": "wrong-key"})

    assert response.status_code == 401


def test_list_docs_with_other_repos_key_returns_401(tmp_path: Path, monkeypatch):
    _use_scratch_db(tmp_path, monkeypatch)
    other_repo_headers = _auth_headers("owner/other-repo")

    response = client.get("/api/owner/repo/main/docs", headers=other_repo_headers)

    assert response.status_code == 401


def test_get_doc_for_subdirectory(tmp_path: Path, monkeypatch):
    _use_scratch_db(tmp_path, monkeypatch)
    docs_store.upsert_document("owner/repo", "main", "app", "# App", "sha1")

    response = client.get("/api/owner/repo/main/docs/app", headers=_auth_headers("owner/repo"))

    assert response.status_code == 200
    assert response.json()["content"] == "# App"


def test_get_doc_for_root_directory_uses_slug_not_dot(tmp_path: Path, monkeypatch):
    """루트 디렉토리(".")를 URL에 그대로 쓰면 dot-segment 정규화로
    /docs/. 가 /docs/ (목록 엔드포인트)로 접혀버리는 회귀를 막는 테스트.
    """
    _use_scratch_db(tmp_path, monkeypatch)
    docs_store.upsert_document("owner/repo", "main", ".", "# Root", "sha1")

    response = client.get("/api/owner/repo/main/docs/_root", headers=_auth_headers("owner/repo"))

    assert response.status_code == 200
    body = response.json()
    assert body["directory"] == "."
    assert body["content"] == "# Root"


def test_get_doc_missing_returns_404(tmp_path: Path, monkeypatch):
    _use_scratch_db(tmp_path, monkeypatch)

    response = client.get("/api/owner/repo/main/docs/missing", headers=_auth_headers("owner/repo"))

    assert response.status_code == 404


def test_list_prompt_presets_returns_registry_ids():
    response = client.get("/api/prompt-presets")

    assert response.status_code == 200
    ids = {preset["id"] for preset in response.json()}
    assert {"default", "educational", "concise"} <= ids


def test_get_prompt_config_defaults_to_null_fields_when_unset(tmp_path: Path, monkeypatch):
    _use_scratch_db(tmp_path, monkeypatch)

    response = client.get("/api/owner/repo/main/prompt-config", headers=_auth_headers("owner/repo"))

    assert response.status_code == 200
    body = response.json()
    assert body == {"preset_id": None, "custom_instructions": None, "updated_at": None}


def test_put_prompt_config_roundtrip(tmp_path: Path, monkeypatch):
    _use_scratch_db(tmp_path, monkeypatch)
    headers = _auth_headers("owner/repo")

    put_response = client.put(
        "/api/owner/repo/main/prompt-config",
        json={"preset_id": "educational", "custom_instructions": "짧게"},
        headers=headers,
    )
    assert put_response.status_code == 200

    get_response = client.get("/api/owner/repo/main/prompt-config", headers=headers)
    body = get_response.json()
    assert body["preset_id"] == "educational"
    assert body["custom_instructions"] == "짧게"
    assert body["updated_at"] is not None


def test_put_prompt_config_rejects_unknown_preset_id(tmp_path: Path, monkeypatch):
    _use_scratch_db(tmp_path, monkeypatch)

    response = client.put(
        "/api/owner/repo/main/prompt-config",
        json={"preset_id": "does-not-exist", "custom_instructions": None},
        headers=_auth_headers("owner/repo"),
    )

    assert response.status_code == 422


def test_put_prompt_config_without_api_key_returns_401(tmp_path: Path, monkeypatch):
    _use_scratch_db(tmp_path, monkeypatch)

    response = client.put(
        "/api/owner/repo/main/prompt-config",
        json={"preset_id": None, "custom_instructions": "인젝션 시도"},
    )

    assert response.status_code == 401


def test_issue_repo_api_key_requires_admin_key(tmp_path: Path, monkeypatch):
    _use_scratch_db(tmp_path, monkeypatch)

    response = client.post("/api/owner/repo/api-key")

    assert response.status_code == 401


def test_issue_repo_api_key_with_admin_key_returns_usable_key(tmp_path: Path, monkeypatch):
    _use_scratch_db(tmp_path, monkeypatch)

    issue_response = client.post("/api/owner/repo/api-key", headers={"X-Admin-Api-Key": "test-admin-key"})
    assert issue_response.status_code == 200
    api_key = issue_response.json()["api_key"]

    docs_response = client.get("/api/owner/repo/main/docs", headers={"X-Repo-Api-Key": api_key})
    assert docs_response.status_code == 200
