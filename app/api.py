from __future__ import annotations

import hmac

from fastapi import APIRouter, Depends, Header, HTTPException
from pydantic import BaseModel

from app.auth_store import issue_repo_key, verify_repo_key
from app.config import get_settings
from app.docs_store import delete_document, get_document, list_documents
from app.prompt_store import get_prompt_config, upsert_prompt_config
from app.prompts import PRESETS, get_preset

router = APIRouter(prefix="/api")


def require_repo_key(owner: str, repo: str, x_repo_api_key: str | None = Header(default=None)) -> None:
    if not x_repo_api_key or not verify_repo_key(f"{owner}/{repo}", x_repo_api_key):
        raise HTTPException(status_code=401, detail="invalid or missing repo API key")


def require_admin_key(x_admin_api_key: str | None = Header(default=None)) -> None:
    settings = get_settings()
    if not x_admin_api_key or not hmac.compare_digest(x_admin_api_key, settings.admin_api_key):
        raise HTTPException(status_code=401, detail="invalid or missing admin API key")


# 저장소 루트 디렉토리는 내부적으로 "."로 표현하지만, URL 경로 세그먼트로 그대로 쓰면
# HTTP 클라이언트(브라우저 fetch, httpx 등)가 RFC 3986 dot-segment 정규화로
# "/docs/." -> "/docs/" 로 접어버려 목록 엔드포인트와 충돌한다. URL 경계에서만
# 별도 슬러그로 주고받는다.
ROOT_DIRECTORY_SLUG = "_root"


def _directory_from_url(url_directory: str) -> str:
    return "." if url_directory == ROOT_DIRECTORY_SLUG else url_directory


class DocumentSummary(BaseModel):
    directory: str
    source_sha: str
    updated_at: str


class DocumentDetail(DocumentSummary):
    content: str


class PromptPresetSummary(BaseModel):
    id: str
    label: str
    description: str


class PromptConfigResponse(BaseModel):
    preset_id: str | None
    custom_instructions: str | None
    updated_at: str | None


class PromptConfigUpdate(BaseModel):
    preset_id: str | None = None
    custom_instructions: str | None = None


class RepoApiKeyResponse(BaseModel):
    api_key: str


@router.post(
    "/{owner}/{repo}/api-key",
    response_model=RepoApiKeyResponse,
    dependencies=[Depends(require_admin_key)],
)
async def issue_repo_api_key(owner: str, repo: str) -> RepoApiKeyResponse:
    """관리자 시크릿(ADMIN_API_KEY)으로만 호출 가능. 발급된 평문 키는 이 응답에서만 확인할 수 있고
    저장소에는 해시만 남으므로, 분실 시 재호출로 재발급(기존 키는 즉시 무효화)해야 한다."""
    api_key = issue_repo_key(repo=f"{owner}/{repo}")
    return RepoApiKeyResponse(api_key=api_key)


@router.get(
    "/{owner}/{repo}/{branch}/docs",
    response_model=list[DocumentSummary],
    dependencies=[Depends(require_repo_key)],
)
async def list_repo_docs(owner: str, repo: str, branch: str) -> list[DocumentSummary]:
    documents = list_documents(repo=f"{owner}/{repo}", branch=branch)
    return [
        DocumentSummary(directory=doc.directory, source_sha=doc.source_sha, updated_at=doc.updated_at)
        for doc in documents
    ]


@router.get(
    "/{owner}/{repo}/{branch}/docs/{directory:path}",
    response_model=DocumentDetail,
    dependencies=[Depends(require_repo_key)],
)
async def get_repo_doc(owner: str, repo: str, branch: str, directory: str) -> DocumentDetail:
    document = get_document(repo=f"{owner}/{repo}", branch=branch, directory=_directory_from_url(directory))
    if document is None:
        raise HTTPException(status_code=404, detail="document not found")

    return DocumentDetail(
        directory=document.directory,
        source_sha=document.source_sha,
        updated_at=document.updated_at,
        content=document.content,
    )


@router.delete(
    "/{owner}/{repo}/{branch}/docs/{directory:path}",
    status_code=204,
    dependencies=[Depends(require_repo_key)],
)
async def delete_repo_doc(owner: str, repo: str, branch: str, directory: str) -> None:
    deleted = delete_document(repo=f"{owner}/{repo}", branch=branch, directory=_directory_from_url(directory))
    if not deleted:
        raise HTTPException(status_code=404, detail="document not found")


@router.get("/prompt-presets", response_model=list[PromptPresetSummary])
async def list_prompt_presets() -> list[PromptPresetSummary]:
    return [
        PromptPresetSummary(id=preset.id, label=preset.label, description=preset.description)
        for preset in PRESETS
    ]


@router.get(
    "/{owner}/{repo}/{branch}/prompt-config",
    response_model=PromptConfigResponse,
    dependencies=[Depends(require_repo_key)],
)
async def get_repo_prompt_config(owner: str, repo: str, branch: str) -> PromptConfigResponse:
    config = get_prompt_config(repo=f"{owner}/{repo}", branch=branch)
    if config is None:
        return PromptConfigResponse(preset_id=None, custom_instructions=None, updated_at=None)

    return PromptConfigResponse(
        preset_id=config.preset_id,
        custom_instructions=config.custom_instructions,
        updated_at=config.updated_at,
    )


@router.put(
    "/{owner}/{repo}/{branch}/prompt-config",
    response_model=PromptConfigResponse,
    dependencies=[Depends(require_repo_key)],
)
async def put_repo_prompt_config(
    owner: str, repo: str, branch: str, body: PromptConfigUpdate
) -> PromptConfigResponse:
    if body.preset_id is not None and get_preset(body.preset_id) is None:
        raise HTTPException(status_code=422, detail=f"unknown preset_id: {body.preset_id}")

    upsert_prompt_config(
        repo=f"{owner}/{repo}",
        branch=branch,
        preset_id=body.preset_id,
        custom_instructions=body.custom_instructions,
    )

    config = get_prompt_config(repo=f"{owner}/{repo}", branch=branch)
    assert config is not None
    return PromptConfigResponse(
        preset_id=config.preset_id,
        custom_instructions=config.custom_instructions,
        updated_at=config.updated_at,
    )
