from __future__ import annotations

import base64
from dataclasses import dataclass

import httpx

GITHUB_API_BASE = "https://api.github.com"

# 문서화에 의미가 없는 파일들(이미지/폰트/압축/컴파일 산출물, 락파일 등)은
# LLM 프롬프트에 넣지 않는다. 확장자로 걸러지지 않는 바이너리는 get_file()에서
# UTF-8 디코딩 실패 시 한 번 더 걸러진다 (방어적 처리).
_EXCLUDED_EXTENSIONS = {
    # 이미지
    ".png",
    ".jpg",
    ".jpeg",
    ".gif",
    ".ico",
    ".webp",
    ".bmp",
    ".svg",
    ".avif",
    ".tiff",
    # 폰트
    ".woff",
    ".woff2",
    ".ttf",
    ".eot",
    ".otf",
    # 압축/아카이브
    ".zip",
    ".tar",
    ".gz",
    ".7z",
    ".rar",
    # 오디오/비디오
    ".mp4",
    ".mp3",
    ".wav",
    ".mov",
    ".avi",
    ".webm",
    # 기타 바이너리 산출물
    ".pdf",
    ".db",
    ".sqlite",
    ".sqlite3",
    ".pyc",
    ".class",
    ".o",
    ".so",
    ".dll",
    ".exe",
    ".jar",
    ".wasm",
}

_EXCLUDED_FILENAMES = {
    "package-lock.json",
    "yarn.lock",
    "pnpm-lock.yaml",
    "poetry.lock",
    "pipfile.lock",
    "composer.lock",
    "gemfile.lock",
    "cargo.lock",
    "go.sum",
}


def _is_excluded_file(path: str) -> bool:
    name = path.rsplit("/", 1)[-1].lower()
    if name in _EXCLUDED_FILENAMES:
        return True
    suffix = name[name.rfind(".") :] if "." in name else ""
    return suffix in _EXCLUDED_EXTENSIONS


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
        raw_content = base64.b64decode(data["content"])
        try:
            content = raw_content.decode("utf-8")
        except UnicodeDecodeError:
            # 확장자로 걸러지지 않은 바이너리 파일 (방어적 처리) — 문서화 대상에서 제외.
            return None
        return GitHubFile(path=path, content=content)

    async def list_directory_files(self, owner: str, repo: str, directory: str, ref: str) -> dict[str, str]:
        """디렉토리 내 파일 경로 -> 내용 매핑을 반환한다 (하위 디렉토리는 재귀하지 않음).

        이미지/폰트/락파일 등 문서화에 의미 없는 파일은 애초에 fetch하지 않는다.
        """
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
            if _is_excluded_file(entry["path"]):
                continue
            file = await self.get_file(owner, repo, entry["path"], ref)
            if file is not None:
                files[file.path] = file.content
        return files
