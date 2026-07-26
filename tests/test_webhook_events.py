import hashlib
import hmac
import json
import os

os.environ.setdefault("GITHUB_WEBHOOK_SECRET", "test-secret")
os.environ.setdefault("GITHUB_BOT_TOKEN", "test-token")
os.environ.setdefault("LLM_API_KEY", "test-key")

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)
SECRET = "test-secret"


def _signed_headers(body: bytes, event: str) -> dict[str, str]:
    digest = hmac.new(SECRET.encode(), body, hashlib.sha256).hexdigest()
    return {
        "X-Hub-Signature-256": f"sha256={digest}",
        "X-GitHub-Event": event,
        "Content-Type": "application/json",
    }


def test_ping_event_is_accepted_without_processing():
    """GitHub는 웹훅 등록 시 push와 페이로드 구조가 다른 ping을 먼저 보낸다.
    이걸 push로 파싱하려 하면 KeyError가 나던 회귀를 막는 테스트.
    """
    body = json.dumps({"zen": "Keep it logically awesome.", "hook_id": 1}).encode()

    response = client.post("/webhook/github", content=body, headers=_signed_headers(body, "ping"))

    assert response.status_code == 202


def test_non_push_event_is_ignored():
    body = json.dumps({"action": "opened"}).encode()

    response = client.post("/webhook/github", content=body, headers=_signed_headers(body, "issues"))

    assert response.status_code == 202


def test_push_event_without_valid_signature_is_rejected():
    body = json.dumps({"ref": "refs/heads/main"}).encode()

    response = client.post(
        "/webhook/github",
        content=body,
        headers={"X-Hub-Signature-256": "sha256=bad", "X-GitHub-Event": "push"},
    )

    assert response.status_code == 401
