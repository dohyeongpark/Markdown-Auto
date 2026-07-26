from __future__ import annotations

import logging

from app.clients.github import GitHubClient
from app.docs_store import get_document, upsert_document
from app.llm_client import LLMClient
from app.prompts import render_prompt

logger = logging.getLogger(__name__)


async def generate_and_store_docs(
    *,
    github_client: GitHubClient,
    llm_client: LLMClient,
    owner: str,
    repo: str,
    branch: str,
    directory: str,
    commit_sha: str,
    style_instructions: str | None = None,
) -> None:
    """디렉토리 하나에 대해 문서를 생성하고 docs_store(SQLite)에 저장한다.

    GitHub에는 쓰지 않는다 — 봇이 자기 push를 다시 트리거할 일이 없으므로
    무한 루프 방지 로직([skip-docs] 등)이 필요 없다.
    실패 시 예외를 삼키지 않고 로깅 후 재발생시킨다.
    """
    repo_full_name = f"{owner}/{repo}"

    try:
        existing = get_document(repo_full_name, branch, directory)
        source_files = await github_client.list_directory_files(owner, repo, directory, ref=branch)

        if not source_files:
            # 이미지/락파일 등 문서화에 의미 없는 파일만 있는 디렉토리 — LLM 호출 없이 건너뛴다.
            logger.info("문서화할 소스 파일이 없어 건너뜀: %s/%s (%s)", repo_full_name, branch, directory)
            return

        prompt = render_prompt(
            directory=directory,
            existing_readme=existing.content if existing else None,
            source_files=source_files,
            style_instructions=style_instructions,
        )
        generated_markdown = await llm_client.generate_docs(prompt)

        upsert_document(
            repo=repo_full_name,
            branch=branch,
            directory=directory,
            content=generated_markdown,
            source_sha=commit_sha,
        )
    except Exception:
        logger.exception("문서 생성/저장 실패: %s/%s (%s)", repo_full_name, branch, directory)
        raise
