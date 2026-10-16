"""Tests for `core.security`."""

from datetime import timedelta, datetime, timezone

import pytest
from unittest.mock import AsyncMock, MagicMock

from core.exceptions import AuthError, InvalidTokenTypeError  # type: ignore
from core.security import (  # type: ignore
    verify_password,
    hash_password,
    create_token,
    create_access_token,
    create_refresh_token,
    encode_token,
    decode_token,
    get_current_user,
)


def make_credentials(token: str):
    cred = MagicMock()
    cred.credentials = token
    return cred


class TestPassword:
    def test_hash_and_verify(self):
        hashed = hash_password("password123")
        assert hashed != "password123"
        assert verify_password("password123", hashed) is True
        assert verify_password("wrong", hashed) is False


class TestCreateToken:
    def test_create_access(self):
        token = create_token({"sub": "1"}, "access")
        payload = decode_token(token)
        assert payload["sub"] == "1"
        assert payload["type"] == "access"

    def test_create_refresh(self):
        token = create_token({"sub": "1"}, "refresh")
        payload = decode_token(token)
        assert payload["type"] == "refresh"

    def test_invalid_type_raises(self):
        with pytest.raises(InvalidTokenTypeError):
            create_token({"sub": "1"}, "invalid")

    def test_custom_expires(self):
        token = create_token({"sub": "1"}, "access", expires_delta=timedelta(minutes=5))
        payload = decode_token(token)
        assert payload is not None
        assert payload["sub"] == "1"

    def test_access_helpers(self):
        access = create_access_token({"sub": "2"})
        refresh = create_refresh_token({"sub": "2"})
        assert decode_token(access)["type"] == "access"
        assert decode_token(refresh)["type"] == "refresh"


class TestEncodeDecode:
    def test_encode_decode_roundtrip(self):
        payload = {"sub": "42", "type": "access"}
        token = encode_token(payload)
        assert token is not None
        decoded = decode_token(token)
        assert decoded["sub"] == "42"

    def test_decode_invalid(self):
        assert decode_token("garbage.token.value") is None

    def test_decode_expired(self):
        token = create_access_token({"sub": "1"}, expires_delta=timedelta(seconds=-10))
        assert decode_token(token) is None

    def test_encode_bad_key(self, monkeypatch):
        from core.security import jwt, settings  # type: ignore

        def fake_encode(payload, key, algorithm):
            from jwt import InvalidKeyError

            raise InvalidKeyError("bad key")

        monkeypatch.setattr(jwt, "encode", fake_encode)
        assert encode_token({"sub": "1"}) is None


class TestGetCurrentUser:
    async def test_valid_user(self, test_session, user):
        token = create_access_token({"sub": str(user.id)})
        result = await get_current_user(
            credentials=make_credentials(token), session=test_session
        )
        assert result.id == user.id

    async def test_invalid_token(self, test_session):
        with pytest.raises(AuthError):
            await get_current_user(
                credentials=make_credentials("bad.token"), session=test_session
            )

    async def test_refresh_token_rejected(self, test_session, user):
        token = create_refresh_token({"sub": str(user.id)})
        with pytest.raises(AuthError):
            await get_current_user(
                credentials=make_credentials(token), session=test_session
            )

    async def test_user_not_found(self, test_session):
        token = create_access_token({"sub": "999999"})
        with pytest.raises(AuthError):
            await get_current_user(
                credentials=make_credentials(token), session=test_session
            )

    async def test_inactive_user(self, test_session):
        from tests.conftest import create_user_in_db

        inactive = await create_user_in_db(
            test_session,
            username="inactive",
            email="inactive@example.com",
            is_active=False,
        )
        token = create_access_token({"sub": str(inactive.id)})
        with pytest.raises(AuthError):
            await get_current_user(
                credentials=make_credentials(token), session=test_session
            )
