import uuid
from datetime import timedelta

import jwt
import pytest

from app.core.security import (
    create_access_token,
    decode_access_token,
    hash_password,
    verify_password,
)


def test_hash_password_generates_valid_bcrypt_hash() -> None:
    """Verify that hash_password returns a standard bcrypt hash string."""
    plain_password = "SuperSecretPassword123!"
    hashed = hash_password(plain_password)

    assert hashed != plain_password
    assert hashed.startswith("$2b$") or hashed.startswith("$2a$")


def test_verify_password_matches() -> None:
    """Verify verify_password returns True for correct password and False for incorrect."""
    password = "CorrectHorseBatteryStaple!"
    hashed = hash_password(password)

    assert verify_password(password, hashed) is True
    assert verify_password("WrongPassword!", hashed) is False
    assert verify_password("", hashed) is False


def test_create_and_decode_access_token() -> None:
    """Verify encoding and decoding a JWT token preserves claims."""
    user_id = str(uuid.uuid4())
    org_id = str(uuid.uuid4())
    role = "OWNER"

    data = {
        "sub": user_id,
        "org_id": org_id,
        "role": role,
    }

    token = create_access_token(data=data, expires_delta=timedelta(minutes=15))
    assert isinstance(token, str)

    payload = decode_access_token(token)
    assert payload["sub"] == user_id
    assert payload["org_id"] == org_id
    assert payload["role"] == role
    assert payload["type"] == "access"
    assert "exp" in payload
    assert "iat" in payload


def test_expired_token_raises_expired_signature_error() -> None:
    """Verify decode_access_token raises ExpiredSignatureError when expired."""
    data = {"sub": "user_123"}
    # Create token that expired 10 minutes ago
    expired_token = create_access_token(
        data=data,
        expires_delta=timedelta(minutes=-10),
    )

    with pytest.raises(jwt.ExpiredSignatureError):
        decode_access_token(expired_token)


def test_invalid_token_raises_invalid_token_error() -> None:
    """Verify decoding a malformed token raises InvalidTokenError."""
    with pytest.raises(jwt.InvalidTokenError):
        decode_access_token("not.a.valid.jwt.token")
