"""
Unit tests for Meta WhatsApp Webhook Security and HMAC-SHA256 signature verification.
"""

from app.modules.messaging.security import compute_meta_signature, verify_meta_signature


def test_compute_meta_signature_format() -> None:
    """Verify compute_meta_signature returns proper 'sha256=<hex>' structure."""
    secret = "test-secret-123"
    body = b'{"object": "whatsapp_business_account"}'
    signature = compute_meta_signature(body, secret)

    assert signature.startswith("sha256=")
    # SHA-256 hex digest is 64 characters long + 7 chars for 'sha256=' = 71
    assert len(signature) == 71


def test_verify_valid_signature() -> None:
    """Verify that a legitimate signature is validated as True."""
    secret = "secret-key-xyz"
    body = b'{"entry": [{"id": "12345"}]}'
    valid_signature = compute_meta_signature(body, secret)

    assert verify_meta_signature(body, valid_signature, secret) is True


def test_verify_signature_with_whitespace() -> None:
    """Verify that signatures with leading/trailing spaces are stripped and validated."""
    secret = "secret-key-xyz"
    body = b'{"entry": [{"id": "12345"}]}'
    signature = "  " + compute_meta_signature(body, secret) + "  "

    assert verify_meta_signature(body, signature, secret) is True


def test_verify_missing_signature_header() -> None:
    """Verify that missing or empty signature headers return False."""
    secret = "secret-key-xyz"
    body = b'{"entry": [{"id": "12345"}]}'

    assert verify_meta_signature(body, None, secret) is False
    assert verify_meta_signature(body, "", secret) is False
    assert verify_meta_signature(body, "   ", secret) is False


def test_verify_missing_app_secret() -> None:
    """Verify that empty app secrets return False."""
    body = b'{"entry": [{"id": "12345"}]}'
    sig = compute_meta_signature(body, "temp-secret")

    assert verify_meta_signature(body, sig, "") is False


def test_verify_malformed_prefix() -> None:
    """Verify that signatures without 'sha256=' prefix are rejected."""
    secret = "secret-key-xyz"
    body = b'{"entry": [{"id": "12345"}]}'
    raw_hash = compute_meta_signature(body, secret).replace("sha256=", "")

    # Missing prefix completely
    assert verify_meta_signature(body, raw_hash, secret) is False
    # Wrong prefix (e.g., sha1=)
    assert verify_meta_signature(body, f"sha1={raw_hash}", secret) is False


def test_verify_body_tampering() -> None:
    """Verify that altering even a single byte in the body fails verification."""
    secret = "secret-key-xyz"
    original_body = b'{"message": "Hello"}'
    tampered_body = b'{"message": "Hello!"}'

    signature = compute_meta_signature(original_body, secret)

    # Verification must fail with tampered body
    assert verify_meta_signature(tampered_body, signature, secret) is False


def test_verify_wrong_secret() -> None:
    """Verify that verifying with a different secret returns False."""
    body = b'{"message": "Hello"}'
    sig_with_secret_1 = compute_meta_signature(body, "secret-one")

    assert verify_meta_signature(body, sig_with_secret_1, "secret-two") is False

