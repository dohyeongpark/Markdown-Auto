from app.diff_parser import get_changed_directories


def test_extracts_directories_from_head_commit():
    payload = {
        "head_commit": {
            "added": ["app/webhook.py"],
            "removed": ["old/legacy.py"],
            "modified": ["README.md", "app/diff_parser.py"],
        }
    }

    assert get_changed_directories(payload) == {"app", "old", "."}


def test_returns_empty_set_when_no_head_commit():
    assert get_changed_directories({}) == set()


def test_ignores_other_commits_in_push_only_uses_head_commit():
    payload = {
        "commits": [
            {"added": ["ignored/file.py"], "removed": [], "modified": []},
        ],
        "head_commit": {"added": ["app/main.py"], "removed": [], "modified": []},
    }

    assert get_changed_directories(payload) == {"app"}
