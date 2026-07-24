from __future__ import annotations

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.docs_store import get_document, list_documents

router = APIRouter(prefix="/api")

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


@router.get("/{owner}/{repo}/{branch}/docs", response_model=list[DocumentSummary])
async def list_repo_docs(owner: str, repo: str, branch: str) -> list[DocumentSummary]:
    documents = list_documents(repo=f"{owner}/{repo}", branch=branch)
    return [
        DocumentSummary(directory=doc.directory, source_sha=doc.source_sha, updated_at=doc.updated_at)
        for doc in documents
    ]


@router.get("/{owner}/{repo}/{branch}/docs/{directory:path}", response_model=DocumentDetail)
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
