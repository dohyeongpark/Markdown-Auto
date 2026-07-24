import os
from pathlib import Path

os.environ.setdefault("GITHUB_WEBHOOK_SECRET", "test-secret")
os.environ.setdefault("GITHUB_BOT_TOKEN", "test-token")
os.environ.setdefault("LLM_API_KEY", "test-key")

from fastapi.testclient import TestClient

from app import docs_store
from app.main import app

client = TestClient(app)


def _use_scratch_db(tmp_path: Path, monkeypatch):
    monkeypatch.setattr(docs_store, "DB_PATH", tmp_path / "docs.db")


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
