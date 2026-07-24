from __future__ import annotations

import logging

from app.clients.github import GitHubClient
from app.llm_client import LLMClient
from app.prompts import render_prompt

logger = logging.getLogger(__name__)

SKIP_MARKER = "[skip-docs]"


def resolve_doc_path(directory: str) -> str:
    return "README.md" if directory == "." else f"{directory}/README.md"


async def commit_directory_docs(
    *,
    github_client: GitHubClient,
    llm_client: LLMClient,
    owner: str,
    repo: str,
    branch: str,
    directory: str,
) -> None:
    """디렉토리 하나에 대해 문서를 생성/수정하고 봇 계정으로 커밋한다.

    실패 시 예외를 삼키지 않고 로깅 후 재발생시킨다 (상위에서 해당 push의
    state 갱신을 막아 다음 이벤트에서 재시도되도록 한다).
    """
    doc_path = resolve_doc_path(directory)

    try:
        existing = await github_client.get_file(owner, repo, doc_path, ref=branch)
        source_files = await github_client.list_directory_files(owner, repo, directory, ref=branch)

        prompt = render_prompt(
            directory=directory,
            existing_readme=existing.content if existing else None,
            source_files=source_files,
        )
        generated_markdown = await llm_client.generate_docs(prompt)

        await github_client.create_or_update_file(
            owner=owner,
            repo=repo,
            path=doc_path,
            content=generated_markdown,
            message=f"docs({directory}): update README {SKIP_MARKER}",
            branch=branch,
            sha=existing.sha if existing else None,
        )
    except Exception:
        logger.exception("문서 생성/커밋 실패: %s/%s (%s)", repo, directory, doc_path)
        raise
