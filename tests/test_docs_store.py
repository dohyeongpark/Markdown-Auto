from pathlib import Path

from app import docs_store


def test_get_document_returns_none_when_missing(tmp_path: Path, monkeypatch):
    monkeypatch.setattr(docs_store, "DB_PATH", tmp_path / "docs.db")

    assert docs_store.get_document("owner/repo", "main", "app") is None


def test_upsert_then_get_roundtrip(tmp_path: Path, monkeypatch):
    monkeypatch.setattr(docs_store, "DB_PATH", tmp_path / "docs.db")

    docs_store.upsert_document("owner/repo", "main", "app", "# App\ncontent", "sha1")
    document = docs_store.get_document("owner/repo", "main", "app")

    assert document is not None
    assert document.content == "# App\ncontent"
    assert document.source_sha == "sha1"


def test_upsert_overwrites_existing_document(tmp_path: Path, monkeypatch):
    monkeypatch.setattr(docs_store, "DB_PATH", tmp_path / "docs.db")

    docs_store.upsert_document("owner/repo", "main", "app", "old content", "sha1")
    docs_store.upsert_document("owner/repo", "main", "app", "new content", "sha2")

    document = docs_store.get_document("owner/repo", "main", "app")
    assert document is not None
    assert document.content == "new content"
    assert document.source_sha == "sha2"


def test_list_documents_scoped_to_repo_and_branch(tmp_path: Path, monkeypatch):
    monkeypatch.setattr(docs_store, "DB_PATH", tmp_path / "docs.db")

    docs_store.upsert_document("owner/repo", "main", "app", "content-a", "sha1")
    docs_store.upsert_document("owner/repo", "main", "prompts", "content-b", "sha1")
    docs_store.upsert_document("owner/repo", "dev", "app", "content-c", "sha2")
    docs_store.upsert_document("owner/other-repo", "main", "app", "content-d", "sha3")

    documents = docs_store.list_documents("owner/repo", "main")

    assert [doc.directory for doc in documents] == ["app", "prompts"]
