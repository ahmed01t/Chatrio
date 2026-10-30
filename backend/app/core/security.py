"""
Cryptography and Security Utilities.

This module provides:
1. `hash_password`: Hashes plain text passwords using bcrypt.
2. `verify_password`: Securely verifies a plain password against its bcrypt hash.
3. `create_access_token`: Generates signed JWT access tokens with expiration claims.
4. `decode_access_token`: Verifies and decodes a signed JWT access token.
"""

from datetime import UTC, datetime, timedelta
from typing import Any

import jwt
from pwdlib import PasswordHash
from pwdlib.hashers.bcrypt import BcryptHasher

from app.core.config import get_settings

# Initialize PasswordHash configured with BcryptHasher
password_hasher: PasswordHash = PasswordHash((BcryptHasher(),))


def hash_password(password: str) -> str:
    """
    Hashes a plain text password using bcrypt.

    Bcrypt automatically generates a cryptographic salt and hashes the password.
    Plain passwords should NEVER be persisted to the database.
    """
    return password_hasher.hash(password)


def verify_password(plain: str, hashed: str) -> bool:
    """
    Verifies a plain text password against a stored bcrypt hash.

    Returns True if the password matches the hash, False otherwise.
    Uses constant-time comparison to prevent timing attacks.
    """
    return password_hasher.verify(plain, hashed)


def create_access_token(
    data: dict[str, Any],
    expires_delta: timedelta | None = None,
) -> str:
    """
    Generates a signed JSON Web Token (JWT) access token.

    Args:
        data: Payload claims to encode into the token (e.g. sub, org_id, role).
        expires_delta: Optional custom duration. Defaults to settings.ACCESS_TOKEN_EXPIRE_MINUTES.

    Returns:
        Encoded JWT token string signed with HMAC-SHA256.
    """
    settings = get_settings()
    to_encode = data.copy()

    now = datetime.now(UTC)
    if expires_delta is not None:
        expire = now + expires_delta
    else:
        expire = now + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)

    to_encode.update(
        {
            "exp": expire,
            "iat": now,
            "type": "access",
        }
    )

    encoded_jwt: str = jwt.encode(
        to_encode,
        settings.JWT_SECRET,
        algorithm=settings.JWT_ALGORITHM,
    )
    return encoded_jwt


def decode_access_token(token: str) -> dict[str, Any]:
    """
    Decodes and verifies a JWT access token.

    Args:
        token: The raw JWT string provided by the client (e.g. Bearer token).

    Returns:
        The decoded claims payload dictionary.

    Raises:
        jwt.ExpiredSignatureError: If the token expiration time (exp) has passed.
        jwt.InvalidTokenError: If the signature is invalid or token is malformed.
    """
    settings = get_settings()
    decoded: dict[str, Any] = jwt.decode(
        token,
        settings.JWT_SECRET,
        algorithms=[settings.JWT_ALGORITHM],
    )
    return decoded
