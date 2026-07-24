import hashlib
import hmac

from app.webhook import verify_signature


def _sign(secret: str, body: bytes) -> str:
    digest = hmac.new(secret.encode(), body, hashlib.sha256).hexdigest()
    return f"sha256={digest}"


def test_valid_signature_passes():
    body = b'{"ok": true}'
    secret = "test-secret"
    assert verify_signature(body, _sign(secret, body), secret) is True


def test_invalid_signature_fails():
    body = b'{"ok": true}'
    assert verify_signature(body, "sha256=deadbeef", "test-secret") is False


def test_missing_signature_fails():
    assert verify_signature(b"{}", None, "test-secret") is False


def test_signature_without_sha256_prefix_fails():
    assert verify_signature(b"{}", "deadbeef", "test-secret") is False
