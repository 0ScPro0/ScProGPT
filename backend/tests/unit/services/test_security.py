"""
Unit tests for core/security.py module.

Tests cover:
- Password hashing
- Password verification
- JWT token creation (access/refresh)
- Token decoding
- Token expiration
"""

import pytest
from datetime import datetime, timedelta, timezone

from core.security import (  # type: ignore
    hash_password,
    verify_password,
    create_access_token,
    create_refresh_token,
    decode_token,
    create_token,
)
from core.exceptions import InvalidTokenTypeError  # type: ignore
from core.config import settings  # type: ignore


# ============================================================
# TESTS: Password hashing
# ============================================================


class TestPasswordHashing:
    """Password hashing and verification tests."""

    def test_password_is_hashed(self):
        """Hashed password is not equal to the original."""
        password = "MySecretPassword123!"
        hashed = hash_password(password)

        assert hashed != password

    def test_same_password_different_hashes(self):
        """Same password produces different hashes (bcrypt uses salt)."""
        password = "MySecretPassword123!"
        hash1 = hash_password(password)
        hash2 = hash_password(password)

        assert hash1 != hash2  # Salt is different each time

    def test_verify_correct_password(self):
        """Correct password passes verification."""
        password = "MySecretPassword123!"
        hashed = hash_password(password)

        assert verify_password(password, hashed) is True

    def test_verify_wrong_password(self):
        """Wrong password fails verification."""
        hashed = hash_password("CorrectPassword123!")

        assert verify_password("WrongPassword456!", hashed) is False

    def test_empty_password_fails(self):
        """Empty password fails verification."""
        hashed = hash_password("NotEmptyPassword123!")

        assert verify_password("", hashed) is False

    def test_hash_is_string(self):
        """Hash is a string."""
        hashed = hash_password("TestPassword123!")

        assert isinstance(hashed, str)

    def test_hash_starts_with_bcrypt_identifier(self):
        """bcrypt hash starts with $2b$."""
        hashed = hash_password("TestPassword123!")

        assert hashed.startswith("$2b$")


# ============================================================
# TESTS: JWT tokens
# ============================================================


class TestJWTTokenCreation:
    """JWT token creation tests."""

    def test_create_access_token_returns_string(self):
        """Access token is a string."""
        token = create_access_token({"sub": "1"})

        assert isinstance(token, str)

    def test_create_refresh_token_returns_string(self):
        """Refresh token is a string."""
        token = create_refresh_token({"sub": "1"})

        assert isinstance(token, str)

    def test_access_token_decodes_successfully(self):
        """Access token decodes successfully."""
        token = create_access_token({"sub": "42"})
        payload = decode_token(token)

        assert payload is not None
        assert payload["sub"] == "42"

    def test_refresh_token_decodes_successfully(self):
        """Refresh token decodes successfully."""
        token = create_refresh_token({"sub": "42"})
        payload = decode_token(token)

        assert payload is not None
        assert payload["sub"] == "42"

    def test_access_token_has_correct_type(self):
        """Access token has type='access'."""
        token = create_access_token({"sub": "1"})
        payload = decode_token(token)

        assert payload["type"] == "access"

    def test_refresh_token_has_correct_type(self):
        """Refresh token has type='refresh'."""
        token = create_refresh_token({"sub": "1"})
        payload = decode_token(token)

        assert payload["type"] == "refresh"

    def test_token_contains_expiration(self):
        """Token contains exp (expiration) field."""
        token = create_access_token({"sub": "1"})
        payload = decode_token(token)

        assert "exp" in payload  # type: ignore

    def test_token_contains_issued_at(self):
        """Token contains iat (issued at) field."""
        token = create_access_token({"sub": "1"})
        payload = decode_token(token)

        assert "iat" in payload  # type: ignore

    def test_token_expiration_is_in_future(self):
        """Token is not expired right after creation."""
        token = create_access_token({"sub": "1"})
        payload = decode_token(token)

        assert payload["exp"] > datetime.now(timezone.utc).timestamp()

    def test_custom_expires_delta(self):
        """Custom token lifetime can be set."""
        delta = timedelta(hours=1)
        token = create_access_token({"sub": "1"}, expires_delta=delta)
        payload = decode_token(token)

        expected_max = (datetime.now(timezone.utc) + delta).timestamp()
        # exp should be approximately 1 hour from now (with 5 second tolerance)
        assert payload["exp"] <= expected_max + 5


# ============================================================
# TESTS: Invalid token types
# ============================================================


class TestInvalidTokenType:
    """Invalid token type tests."""

    def test_invalid_token_type_raises_error(self):
        """create_token raises error for invalid token type."""
        with pytest.raises(InvalidTokenTypeError):
            create_token({"sub": "1"}, token_type="invalid")

    def test_decode_fake_token_returns_none(self):
        """Decoding a fake token returns None."""
        fake_token = "this.is.not.a.jwt"
        result = decode_token(fake_token)

        assert result is None

    def test_decode_empty_string_returns_none(self):
        """Decoding an empty string returns None."""
        result = decode_token("")

        assert result is None


# ============================================================
# TESTS: Token expiration
# ============================================================


class TestTokenExpiration:
    """Token expiration tests."""

    def test_expired_token_decodes_to_none(self):
        """Expired token returns None when decoded."""
        # Create a token with negative lifetime (already expired)
        delta = timedelta(seconds=-1)
        token = create_access_token({"sub": "1"}, expires_delta=delta)

        # Allow time for processing
        import time

        time.sleep(0.1)

        result = decode_token(token)
        assert result is None

    def test_access_token_default_expiration(self):
        """Access token has default lifetime from settings."""
        token = create_access_token({"sub": "1"})
        payload = decode_token(token)

        expected_expires = (
            datetime.now(timezone.utc)
            + timedelta(minutes=settings.security.access_token_expire_minutes)
        ).timestamp()

        # 5 second tolerance
        assert abs(payload["exp"] - expected_expires) < 5

    def test_refresh_token_default_expiration(self):
        """Refresh token has default lifetime from settings."""
        token = create_refresh_token({"sub": "1"})
        payload = decode_token(token)

        expected_expires = (
            datetime.now(timezone.utc)
            + timedelta(days=settings.security.refresh_token_expire_days)
        ).timestamp()

        # 5 second tolerance
        assert abs(payload["exp"] - expected_expires) < 5
