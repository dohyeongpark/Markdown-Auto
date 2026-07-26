from __future__ import annotations

import hashlib
import hmac
import json
import logging

from fastapi import APIRouter, BackgroundTasks, Header, HTTPException, Request, Response

from app.clients.github import GitHubClient
from app.config import get_settings
from app.diff_parser import get_changed_directories
from app.doc_writer import generate_and_store_docs
from app.llm_client import get_llm_client
from app.state import set_last_processed_sha

logger = logging.getLogger(__name__)

router = APIRouter()


def verify_signature(payload_body: bytes, signature_header: str | None, secret: str) -> bool:
    """GitHub의 X-Hub-Signature-256 헤더를 검증한다."""
    if not signature_header or not signature_header.startswith("sha256="):
        return False

    expected = hmac.new(secret.encode(), payload_body, hashlib.sha256).hexdigest()
    received = signature_header.removeprefix("sha256=")
    return hmac.compare_digest(expected, received)


@router.post("/webhook/github", status_code=202)
async def receive_github_push(
    request: Request,
    background_tasks: BackgroundTasks,
    x_hub_signature_256: str | None = Header(default=None),
    x_github_event: str | None = Header(default=None),
) -> Response:
    """push 이벤트를 받아 즉시 202를 반환하고, 실제 처리는 BackgroundTask로 위임한다.

    LLM 호출을 절대 여기서 동기적으로 기다리지 않는다. 생성된 문서는 GitHub에
    다시 커밋하지 않고 docs_store에만 저장하므로, 봇 스스로 push를 유발할 일이
    없어 [skip-docs] 같은 자기 트리거 방지 로직이 필요 없다.

    GitHub는 웹훅 등록 시 ping 이벤트를 먼저 보내고, 설정에 따라 push 외의
    이벤트도 보낼 수 있다. push가 아닌 이벤트는 페이로드 구조가 달라 그대로
    파싱하면 에러가 나므로, 서명 검증 후 이벤트 타입을 확인해 push만 처리한다.
    """
    body = await request.body()
    settings = get_settings()

    if not verify_signature(body, x_hub_signature_256, settings.github_webhook_secret):
        raise HTTPException(status_code=401, detail="invalid signature")

    if x_github_event != "push":
        logger.info("push가 아닌 이벤트 무시: %s", x_github_event)
        return Response(status_code=202)

    payload = json.loads(body)
    background_tasks.add_task(process_push_event, payload)
    return Response(status_code=202)


async def process_push_event(payload: dict) -> None:
    repository = payload["repository"]
    owner = repository["owner"]["login"]
    repo = repository["name"]
    branch = payload["ref"].removeprefix("refs/heads/")
    head_sha = payload["after"]

    changed_directories = get_changed_directories(payload)
    if not changed_directories:
        return

    settings = get_settings()
    github_client = GitHubClient(token=settings.github_bot_token)
    llm_client = get_llm_client()

    for directory in changed_directories:
        await generate_and_store_docs(
            github_client=github_client,
            llm_client=llm_client,
            owner=owner,
            repo=repo,
            branch=branch,
            directory=directory,
            commit_sha=head_sha,
        )

    set_last_processed_sha(repo=f"{owner}/{repo}", branch=branch, sha=head_sha)
