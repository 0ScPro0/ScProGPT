"""Integration tests for services (with in-memory SQLite)."""

from datetime import datetime, timezone, timedelta

import pytest

from schemas.user import UserCreate, UserUpdate  # type: ignore
from schemas.chat import ChatCreate  # type: ignore
from schemas.message import MessageCreate  # type: ignore
from schemas.auth import SignUpRequest, SignInRequest, TokenRefreshRequest  # type: ignore
from core.exceptions import AuthError  # type: ignore
from core.security import (  # type: ignore
    create_refresh_token,
    create_access_token,
    hash_password,
)
from tests.conftest import create_user_in_db

# ============================================================
# BaseService
# ============================================================


class TestBaseService:
    async def test_get(self, user_service, user):
        found = await user_service.get(user.id)
        assert found.id == user.id
        assert await user_service.get(99999) is None

    async def test_get_many(self, user_service, test_session):
        for i in range(3):
            await create_user_in_db(
                test_session, username=f"s{i}", email=f"s{i}@example.com"
            )
        users = await user_service.get_many(skip=0, limit=100, order_by=None)
        assert len(users) == 3

    async def test_create_and_update_and_delete(self, user_service, test_session):
        created = await user_service.create(
            {
                "username": "svc",
                "email": "svc@example.com",
                "password_hash": hash_password("password123"),
            }
        )
        assert created.id is not None
        updated = await user_service.update(
            created.id, UserUpdate(username="svc-updated")
        )
        assert updated.username == "svc-updated"
        deleted = await user_service.delete(created.id)
        assert deleted.id == created.id
        assert await user_service.get(created.id) is None


# ============================================================
# UserService
# ============================================================


class TestUserService:
    async def test_get_all_users(self, user_service, test_session):
        await create_user_in_db(test_session)
        result = await user_service.get_all_users()
        assert len(result) == 1
        assert result[0].username == "testuser"

    async def test_get_user(self, user_service, user):
        result = await user_service.get_user(user.id)
        assert result.id == user.id

    async def test_update_user(self, user_service, user):
        result = await user_service.update_user(user.id, UserUpdate(username="renamed"))
        assert result.username == "renamed"

    async def test_delete_user(self, user_service, user):
        result = await user_service.delete_user(user.id)
        assert result.id == user.id


# ============================================================
# ChatService
# ============================================================


class TestChatService:
    async def test_create_chat(self, chat_service, user):
        result = await chat_service.create_chat(ChatCreate(user_id=user.id))
        assert result.id is not None
        assert result.user_id == user.id

    async def test_get_chat(self, chat_service, chat):
        result = await chat_service.get_chat(chat.id)
        assert result.id == chat.id

    async def test_get_user_chats(self, chat_service, user, test_session):
        from repositories.chat import chat_repository  # type: ignore

        await chat_repository.create_chat(
            session=test_session,
            chat_object=ChatCreate(user_id=user.id, title="a"),
        )
        await chat_repository.create_chat(
            session=test_session,
            chat_object=ChatCreate(user_id=user.id, title="b"),
        )
        result = await chat_service.get_user_chats(user.id)
        assert len(result) == 2

    async def test_get_user_pinned_chats(self, chat_service, user, test_session):
        from repositories.chat import chat_repository  # type: ignore

        await chat_repository.create_chat(
            session=test_session,
            chat_object=ChatCreate(user_id=user.id, title="a"),
        )
        await chat_repository.pin_chat(
            session=test_session,
            chat_id=(await chat_service.get_user_chats(user.id))[0].id,
        )
        result = await chat_service.get_user_pinned_chats(user.id)
        assert len(result) == 1

    async def test_delete_chat(self, chat_service, chat):
        result = await chat_service.delete_chat(chat.id)
        assert result.id == chat.id

    async def test_set_title(self, chat_service, chat):
        result = await chat_service.set_title(chat.id, "Updated title")
        assert result.success is True
        assert result.new_value == "Updated title"

    async def test_is_user_has_chat(self, chat_service, user, chat):
        assert await chat_service.is_user_has_chat(user.id, chat.id) is True
        assert await chat_service.is_user_has_chat(user.id, 99999) is False


# ============================================================
# MessageService
# ============================================================


class TestMessageService:
    async def test_create_and_get_message(self, message_service, chat):
        result = await message_service.create_message(
            MessageCreate(role="user", content="hello", chat_id=chat.id)
        )
        assert result.id is not None
        found = await message_service.get_message(result.id)
        assert found.id == result.id

    async def test_get_chat_messages(self, message_service, chat):
        await message_service.create_message(
            MessageCreate(role="user", content="hi", chat_id=chat.id)
        )
        await message_service.create_message(
            MessageCreate(role="assistant", content="yo", chat_id=chat.id)
        )
        result = await message_service.get_chat_messages(chat.id)
        assert len(result) == 2
        assert result[0].role == "user"
        assert result[1].role == "assistant"

    async def test_get_chat_response_messages(self, message_service, chat):
        await message_service.create_message(
            MessageCreate(role="user", content="hi", chat_id=chat.id)
        )
        result = await message_service.get_chat_response_messages(chat.id)
        assert len(result) == 1
        assert result[0].chat_id == chat.id


# ============================================================
# AuthService
# ============================================================


class TestAuthService:
    async def test_signup_success(self, auth_service):
        result = await auth_service.signup(
            SignUpRequest(
                username="newuser", email="new@example.com", password="password123"
            )
        )
        assert result.access_token
        assert result.refresh_token
        assert result.user.username == "newuser"

    async def test_signup_duplicate_email(self, auth_service, user):
        with pytest.raises(AuthError):
            await auth_service.signup(
                SignUpRequest(
                    username="other", email=user.email, password="password123"
                )
            )

    async def test_signin_success(self, auth_service, user):
        result = await auth_service.signin(
            SignInRequest(email=user.email, password="password123")
        )
        assert result.access_token
        assert result.user.id == user.id

    async def test_signin_wrong_password(self, auth_service, user):
        with pytest.raises(AuthError):
            await auth_service.signin(
                SignInRequest(email=user.email, password="wrongpass1")
            )

    async def test_signin_unknown_email(self, auth_service):
        with pytest.raises(AuthError):
            await auth_service.signin(
                SignInRequest(email="nobody@example.com", password="password123")
            )

    async def test_signin_inactive(self, auth_service, test_session):
        inactive = await create_user_in_db(
            test_session,
            username="off",
            email="off@example.com",
            is_active=False,
        )
        with pytest.raises(AuthError):
            await auth_service.signin(
                SignInRequest(email=inactive.email, password="password123")
            )

    async def test_get_current_user_valid_token(self, auth_service):
        token = create_access_token({"sub": "1", "type": "access"})
        # Method validates payload; valid access token returns None
        assert await auth_service.get_current_user(token) is None

    async def test_get_current_user_invalid_token(self, auth_service):
        with pytest.raises(AuthError):
            await auth_service.get_current_user("bad.token")

    async def test_get_current_user_wrong_type(self, auth_service):
        token = create_refresh_token({"sub": "1"})
        with pytest.raises(AuthError):
            await auth_service.get_current_user(token)

    async def test_refresh_token_success(self, auth_service, test_session):
        user = await create_user_in_db(test_session)
        refresh = create_refresh_token({"sub": str(user.id)})
        expires = datetime.now(timezone.utc) + timedelta(days=1)
        from repositories.user import user_repository  # type: ignore

        await user_repository.update_refresh_token(
            session=test_session,
            user_id=user.id,
            refresh_token=refresh,
            expires_at=expires,
        )
        result = await auth_service.refresh_token(
            TokenRefreshRequest(refresh_token=refresh)
        )
        assert result["access_token"]

    async def test_refresh_token_invalid(self, auth_service):
        with pytest.raises(AuthError):
            await auth_service.refresh_token(TokenRefreshRequest(refresh_token="bad"))

    async def test_refresh_token_wrong_type(self, auth_service):
        token = create_access_token({"sub": "1"})
        with pytest.raises(AuthError):
            await auth_service.refresh_token(TokenRefreshRequest(refresh_token=token))

    async def test_refresh_token_expired(self, auth_service):
        token = create_refresh_token({"sub": "1"}, timedelta(seconds=-10))
        with pytest.raises(AuthError):
            await auth_service.refresh_token(TokenRefreshRequest(refresh_token=token))

    async def test_refresh_token_user_not_found(self, auth_service):
        token = create_refresh_token({"sub": "99999"})
        with pytest.raises(AuthError):
            await auth_service.refresh_token(TokenRefreshRequest(refresh_token=token))

    async def test_refresh_token_not_matching(self, auth_service, test_session):
        user = await create_user_in_db(test_session)
        other = create_refresh_token({"sub": str(user.id)})
        expires = datetime.now(timezone.utc) + timedelta(days=1)
        from repositories.user import user_repository  # type: ignore

        await user_repository.update_refresh_token(
            session=test_session,
            user_id=user.id,
            refresh_token="stored-value",
            expires_at=expires,
        )
        with pytest.raises(AuthError):
            await auth_service.refresh_token(TokenRefreshRequest(refresh_token=other))

    async def test_refresh_token_stored_expired(self, auth_service, test_session):
        user = await create_user_in_db(test_session)
        token = create_refresh_token({"sub": str(user.id)})
        expires = datetime.now(timezone.utc) - timedelta(days=1)
        from repositories.user import user_repository  # type: ignore

        await user_repository.update_refresh_token(
            session=test_session,
            user_id=user.id,
            refresh_token=token,
            expires_at=expires,
        )
        with pytest.raises(AuthError):
            await auth_service.refresh_token(TokenRefreshRequest(refresh_token=token))

    async def test_logout(self, auth_service, user):
        assert await auth_service.logout(user.id) is True
