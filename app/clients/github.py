from __future__ import annotations

import base64
from dataclasses import dataclass

import httpx

GITHUB_API_BASE = "https://api.github.com"


@dataclass(frozen=True)
class GitHubFile:
    path: str
    content: str


class GitHubClient:
    """GitHub Contents API read-only 래퍼. httpx.AsyncClient만 사용한다 (requests 금지).

    생성된 문서는 docs_store.py에 저장하고 GitHub에는 커밋하지 않으므로,
    이 클라이언트는 소스 파일 조회 기능만 제공한다 (쓰기 메서드 없음).
    """

    def __init__(self, token: str) -> None:
        self._token = token

    def _headers(self) -> dict[str, str]:
        return {
            "Authorization": f"Bearer {self._token}",
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
        }

    async def get_file(self, owner: str, repo: str, path: str, ref: str) -> GitHubFile | None:
        url = f"{GITHUB_API_BASE}/repos/{owner}/{repo}/contents/{path}"
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(url, params={"ref": ref}, headers=self._headers())

        if response.status_code == 404:
            return None
        response.raise_for_status()

        data = response.json()
        content = base64.b64decode(data["content"]).decode("utf-8")
        return GitHubFile(path=path, content=content)

    async def list_directory_files(self, owner: str, repo: str, directory: str, ref: str) -> dict[str, str]:
        """디렉토리 내 파일 경로 -> 내용 매핑을 반환한다 (하위 디렉토리는 재귀하지 않음)."""
        dir_path = "" if directory == "." else directory
        url = f"{GITHUB_API_BASE}/repos/{owner}/{repo}/contents/{dir_path}"
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(url, params={"ref": ref}, headers=self._headers())

        if response.status_code == 404:
            return {}
        response.raise_for_status()

        entries = response.json()
        files: dict[str, str] = {}
        for entry in entries:
            if entry["type"] != "file":
                continue
            file = await self.get_file(owner, repo, entry["path"], ref)
            if file is not None:
                files[file.path] = file.content
        return files
