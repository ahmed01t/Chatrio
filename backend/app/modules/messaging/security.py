"""
Meta WhatsApp Webhook Security & HMAC Verification.

Provides cryptographic verification for inbound Meta webhooks:
1. Validates that the request payload was genuinely signed by Meta using `META_APP_SECRET`.
2. Employs `hmac.compare_digest` to prevent timing-based side-channel attacks.
3. Rejects missing headers, invalid prefixes, and tampered payload bytes.
"""

import hashlib
import hmac


def compute_meta_signature(raw_body: bytes, app_secret: str) -> str:
    """
    Computes an HMAC-SHA256 signature for a raw payload using the Meta app secret.

    Format: 'sha256=<hex_digest>'
    """
    digest = hmac.new(
        key=app_secret.encode("utf-8"),
        msg=raw_body,
        digestmod=hashlib.sha256,
    ).hexdigest()
    return f"sha256={digest}"


def verify_meta_signature(
    raw_body: bytes,
    signature_header: str | None,
    app_secret: str,
) -> bool:
    """
    Verifies that an incoming webhook payload matches the Meta X-Hub-Signature-256 header.

    Args:
        raw_body: Exact raw bytes of the request body (do NOT parse JSON beforehand).
        signature_header: Value of the 'X-Hub-Signature-256' HTTP header.
        app_secret: The Meta App Secret configured for your Meta Developer App.

    Returns:
        True if the signature is valid and authentic, False otherwise.
    """
    if not signature_header or not app_secret:
        return False

    clean_header = signature_header.strip()
    prefix = "sha256="
    if not clean_header.startswith(prefix):
        return False

    received_hash = clean_header[len(prefix) :].strip()
    expected_hash = hmac.new(
        key=app_secret.encode("utf-8"),
        msg=raw_body,
        digestmod=hashlib.sha256,
    ).hexdigest()

    # Timing-attack-safe comparison
    return hmac.compare_digest(received_hash, expected_hash)

