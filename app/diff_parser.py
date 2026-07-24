from __future__ import annotations

import posixpath


def get_changed_directories(payload: dict) -> set[str]:
    """push 페이로드의 head_commit(최신 커밋) 기준으로 변경된 디렉토리 목록을 반환한다.

    루트에 있는 파일은 "." 로 표시한다.
    """
    head_commit = payload.get("head_commit")
    if head_commit is None:
        return set()

    paths = [
        *head_commit.get("added", []),
        *head_commit.get("removed", []),
        *head_commit.get("modified", []),
    ]

    directories: set[str] = set()
    for path in paths:
        directory = posixpath.dirname(path)
        directories.add(directory if directory else ".")
    return directories
