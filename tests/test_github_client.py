import base64

import httpx

from app.clients.github import GitHubClient, _is_excluded_file


def test_is_excluded_file_by_extension():
    assert _is_excluded_file("img/logo.png") is True
    assert _is_excluded_file("fonts/roboto.woff2") is True
    assert _is_excluded_file("dist/bundle.min.js") is False
    assert _is_excluded_file("app/main.py") is False


def test_is_excluded_file_by_known_lockfile_name():
    assert _is_excluded_file("frontend/package-lock.json") is True
    assert _is_excluded_file("backend/poetry.lock") is True
    assert _is_excluded_file("go.sum") is True


def test_is_excluded_file_case_insensitive():
    assert _is_excluded_file("img/Logo.PNG") is True


class _FakeResponse:
    def __init__(self, status_code, json_data):
        self.status_code = status_code
        self._json_data = json_data

    def json(self):
        return self._json_data

    def raise_for_status(self):
        pass


async def test_list_directory_files_skips_excluded_entries_without_fetching(monkeypatch):
    requested_urls = []

    async def fake_get(self, url, params=None, headers=None):
        requested_urls.append(url)
        if url.endswith("/contents/somedir"):
            return _FakeResponse(
                200,
                [
                    {"type": "file", "path": "somedir/a.py"},
                    {"type": "file", "path": "somedir/logo.png"},
                    {"type": "file", "path": "somedir/package-lock.json"},
                    {"type": "dir", "path": "somedir/nested"},
                ],
            )
        if url.endswith("/contents/somedir/a.py"):
            content = base64.b64encode(b"print(1)").decode()
            return _FakeResponse(200, {"content": content})
        raise AssertionError(f"unexpected url fetched: {url}")

    monkeypatch.setattr(httpx.AsyncClient, "get", fake_get)

    client = GitHubClient(token="test-token")
    files = await client.list_directory_files("owner", "repo", "somedir", ref="main")

    assert files == {"somedir/a.py": "print(1)"}
    # 디렉토리 목록 조회 1회 + a.py 내용 조회 1회만 발생 (png/lock/디렉토리는 fetch 자체를 안 함)
    assert len(requested_urls) == 2


async def test_get_file_returns_none_for_undecodable_binary_content(monkeypatch):
    async def fake_get(self, url, params=None, headers=None):
        content = base64.b64encode(b"\x89PNG\r\n\x1a\n").decode()
        return _FakeResponse(200, {"content": content})

    monkeypatch.setattr(httpx.AsyncClient, "get", fake_get)

    client = GitHubClient(token="test-token")
    result = await client.get_file("owner", "repo", "img/photo.jpg.bak", ref="main")

    assert result is None
