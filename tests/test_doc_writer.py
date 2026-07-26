import os
from pathlib import Path

os.environ.setdefault("GITHUB_WEBHOOK_SECRET", "test-secret")
os.environ.setdefault("GITHUB_BOT_TOKEN", "test-token")
os.environ.setdefault("LLM_API_KEY", "test-key")

import app.doc_writer as doc_writer_module
import app.webhook as webhook_module
from app import docs_store, prompt_store
from app.doc_writer import generate_and_store_docs


class _FakeGitHubClient:
    async def list_directory_files(self, owner, repo, directory, ref):
        return {}


class _FakeLLMClient:
    async def generate_docs(self, prompt):
        return "# generated"


async def test_generate_and_store_docs_forwards_style_instructions(tmp_path: Path, monkeypatch):
    monkeypatch.setattr(docs_store, "DB_PATH", tmp_path / "docs.db")

    captured = {}

    def _fake_render_prompt(*, directory, existing_readme, source_files, style_instructions=None):
        captured["style_instructions"] = style_instructions
        return "prompt"

    monkeypatch.setattr(doc_writer_module, "render_prompt", _fake_render_prompt)

    await generate_and_store_docs(
        github_client=_FakeGitHubClient(),
        llm_client=_FakeLLMClient(),
        owner="owner",
        repo="repo",
        branch="main",
        directory="app",
        commit_sha="sha1",
        style_instructions="간결하게",
    )

    assert captured["style_instructions"] == "간결하게"


async def test_process_push_event_looks_up_prompt_config_once_per_push(tmp_path: Path, monkeypatch):
    monkeypatch.setattr(prompt_store, "DB_PATH", tmp_path / "prompt_config.db")

    call_count = 0
    original_get_prompt_config = webhook_module.get_prompt_config

    def _counting_get_prompt_config(*args, **kwargs):
        nonlocal call_count
        call_count += 1
        return original_get_prompt_config(*args, **kwargs)

    monkeypatch.setattr(webhook_module, "get_prompt_config", _counting_get_prompt_config)

    generated_for: list[str] = []

    async def _fake_generate_and_store_docs(*, directory, style_instructions, **kwargs):
        generated_for.append(directory)

    monkeypatch.setattr(webhook_module, "generate_and_store_docs", _fake_generate_and_store_docs)
    monkeypatch.setattr(webhook_module, "set_last_processed_sha", lambda **kwargs: None)

    payload = {
        "ref": "refs/heads/main",
        "after": "sha1",
        "repository": {"name": "repo", "owner": {"login": "owner"}},
        "head_commit": {"added": ["app/a.py", "docs/b.py"], "removed": [], "modified": []},
    }

    await webhook_module.process_push_event(payload)

    assert call_count == 1
    assert sorted(generated_for) == ["app", "docs"]
