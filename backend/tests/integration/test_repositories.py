"""Integration tests for repositories (SQLite in-memory)."""

from datetime import datetime, timezone

import pytest

from repositories import (  # type: ignore
    UserRepository,
    ChatRepository,
    MessageRepository,
)
from repositories.user import user_repository  # type: ignore
from repositories.chat import chat_repository  # type: ignore
from repositories.message import message_repository  # type: ignore
from schemas.user import UserCreate, UserUpdate  # type: ignore
from schemas.chat import ChatCreate, ChatUpdate  # type: ignore
from schemas.message import MessageCreate, MessageUpdate  # type: ignore
from core.security import hash_password  # type: ignore
from tests.conftest import create_user_in_db

# ============================================================
# BaseRepository (via UserRepository/User)
# ============================================================


class TestBaseUserRepository:
    async def test_create_with_dict(self, test_session):
        user = await user_repository.create_user(
            session=test_session,
            user_object={
                "username": "bob",
                "email": "bob@example.com",
                "password_hash": hash_password("password123"),
            },
        )
        assert user.id is not None
        assert user.username == "bob"

    async def test_create_with_schema(self, test_session):
        schema = UserCreate(
            username="alice", email="alice@example.com", password="password123"
        )
        user = await user_repository.create(
            session=test_session,
            object_in={
                "username": schema.username,
                "email": schema.email,
                "password_hash": hash_password(schema.password),
            },
        )
        assert user.username == "alice"

    async def test_get(self, test_session, user):
        found = await user_repository.get(test_session, user.id)
        assert found.id == user.id
        assert await user_repository.get(test_session, 99999) is None

    async def test_get_many(self, test_session):
        for i in range(5):
            await create_user_in_db(
                test_session, username=f"user{i}", email=f"u{i}@example.com"
            )
        users = await user_repository.get_many(
            test_session, skip=0, limit=10, order_by=None
        )
        assert len(users) == 5
        # with relationships param
        users2 = await user_repository.get_many(
            test_session, skip=0, limit=10, order_by=None, relationships=["chats"]
        )
        assert len(users2) == 5

    async def test_get_by_field(self, test_session, user):
        found = await user_repository.get_by_field(
            session=test_session, field_name="email", field_value=user.email
        )
        assert found.id == user.id
        with pytest.raises(AttributeError):
            await user_repository.get_by_field(
                session=test_session, field_name="nope", field_value=1
            )

    async def test_get_by_field_many(self, test_session):
        await create_user_in_db(
            test_session, username="a1", email="a1@example.com", is_active=True
        )
        await create_user_in_db(
            test_session, username="a2", email="a2@example.com", is_active=True
        )
        result = await user_repository.get_by_field_many(
            session=test_session, field_name="is_active", field_value=True
        )
        assert len(result) == 2

    async def test_get_by_fields(self, test_session, user):
        found = await user_repository.get_by_fields(
            session=test_session,
            fields={"email": user.email, "username": "no-such-user"},
        )
        assert found.id == user.id
        # falsy field value is skipped -> returns None
        none = await user_repository.get_by_fields(
            session=test_session, fields={"email": None}
        )
        assert none is None

    async def test_get_by_fields_many(self, test_session):
        await create_user_in_db(
            test_session, username="x1", email="x1@example.com", is_superuser=True
        )
        await create_user_in_db(
            test_session, username="x2", email="x2@example.com", is_superuser=True
        )
        result = await user_repository.get_by_fields_many(
            session=test_session, fields={"is_superuser": True}
        )
        assert len(result) == 2
        # unknown field raises
        with pytest.raises(AttributeError):
            await user_repository.get_by_fields_many(
                session=test_session, fields={"does_not_exist": 1}
            )

    async def test_update_schema(self, test_session, user):
        updated = await user_repository.update(
            session=test_session,
            update_object_id=user.id,
            object_in=UserUpdate(username="renamed"),
        )
        assert updated.username == "renamed"
        assert (
            await user_repository.update(
                session=test_session, update_object_id=999, object_in=UserUpdate()
            )
            is None
        )

    async def test_update_dict(self, test_session, user):
        updated = await user_repository.update(
            session=test_session,
            update_object_id=user.id,
            object_in={"username": "from-dict"},
        )
        assert updated.username == "from-dict"

    async def test_update_by_field(self, test_session, user):
        updated = await user_repository.update_by_field(
            session=test_session,
            field_name="username",
            field_value=user.username,
            update_data={"is_superuser": True},
        )
        assert updated.is_superuser is True
        assert (
            await user_repository.update_by_field(
                session=test_session,
                field_name="username",
                field_value="ghost",
                update_data={"is_superuser": True},
            )
            is None
        )

    async def test_update_field(self, test_session, user):
        updated = await user_repository.update_field(
            session=test_session,
            object_id=user.id,
            field_name="username",
            field_value="field-updated",
        )
        assert updated.username == "field-updated"
        # missing object
        assert (
            await user_repository.update_field(
                session=test_session,
                object_id=999,
                field_name="username",
                field_value="x",
            )
            is None
        )
        # missing field
        with pytest.raises(AttributeError):
            await user_repository.update_field(
                session=test_session,
                object_id=user.id,
                field_name="nope",
                field_value="x",
            )
        # protected field
        with pytest.raises(PermissionError):
            await user_repository.update_field(
                session=test_session,
                object_id=user.id,
                field_name="id",
                field_value=100,
            )

    async def test_update_fields(self, test_session, user):
        updated = await user_repository.update_fields(
            session=test_session,
            object_id=user.id,
            fields={"username": "multi", "is_superuser": True},
        )
        assert updated.username == "multi"
        assert updated.is_superuser is True
        # missing
        assert (
            await user_repository.update_fields(
                session=test_session, object_id=999, fields={"username": "x"}
            )
            is None
        )
        # protected
        with pytest.raises(PermissionError):
            await user_repository.update_fields(
                session=test_session, object_id=user.id, fields={"created_at": 1}
            )
        # missing field
        with pytest.raises(AttributeError):
            await user_repository.update_fields(
                session=test_session, object_id=user.id, fields={"nope": 1}
            )

    async def test_delete(self, test_session, user):
        deleted = await user_repository.delete(session=test_session, id=user.id)
        assert deleted.id == user.id
        assert await user_repository.get(test_session, user.id) is None
        assert await user_repository.delete(session=test_session, id=user.id) is None

    async def test_is_exists_and_count(self, test_session):
        await create_user_in_db(test_session, username="c1", email="c1@example.com")
        await create_user_in_db(test_session, username="c2", email="c2@example.com")
        users = await user_repository.get_many(
            test_session, skip=0, limit=100, order_by=None
        )
        assert (
            await user_repository.is_exists(session=test_session, id=users[0].id)
            is True
        )
        assert await user_repository.is_exists(session=test_session, id=99999) is False
        assert await user_repository.records_count(test_session) == 2


# ============================================================
# UserRepository specific methods
# ============================================================


class TestUserRepositorySpecific:
    async def test_get_by_email_and_username(self, test_session, user):
        assert (
            await user_repository.get_by_email(test_session, user.email)
        ).id == user.id
        assert (
            await user_repository.get_by_username(test_session, user.username)
        ).id == user.id
        assert await user_repository.get_by_email(test_session, "x@y.z") is None

    async def test_update_api_key(self, test_session, user):
        updated = await user_repository.update_api_key(
            session=test_session, user_id=user.id, api_key="k" * 32
        )
        assert updated.api_key == "k" * 32

    async def test_update_password(self, test_session, user):
        updated = await user_repository.update_password(
            session=test_session, user_id=user.id, password_hash="newhash"
        )
        assert updated.password_hash == "newhash"

    async def test_update_settings(self, test_session, user):
        updated = await user_repository.update_settings(
            session=test_session, user_id=user.id, settings={"theme": "dark"}
        )
        assert updated.settings == {"theme": "dark"}

    async def test_update_and_clear_refresh_token(self, test_session, user):
        expires = datetime.now(timezone.utc)
        updated = await user_repository.update_refresh_token(
            session=test_session,
            user_id=user.id,
            refresh_token="rt-1",
            expires_at=expires,
        )
        assert updated.refresh_token == "rt-1"
        cleared = await user_repository.clear_refresh_token(
            session=test_session, user_id=user.id
        )
        assert cleared.refresh_token is None

    async def test_activate_deactivate(self, test_session, user):
        deactivated = await user_repository.deactivate(
            session=test_session, user_id=user.id
        )
        assert deactivated.is_active is False
        activated = await user_repository.activate(
            session=test_session, user_id=user.id
        )
        assert activated.is_active is True

    async def test_delete_user(self, test_session, user):
        deleted = await user_repository.delete_user(
            session=test_session, user_id=user.id
        )
        assert deleted.id == user.id

    async def test_is_active(self, test_session, user):
        assert (
            await user_repository.is_active(session=test_session, user_id=user.id)
            is True
        )
        await user_repository.deactivate(session=test_session, user_id=user.id)
        assert (
            await user_repository.is_active(session=test_session, user_id=user.id)
            is False
        )
        assert (
            await user_repository.is_active(session=test_session, user_id=99999)
            is False
        )


# ============================================================
# ChatRepository
# ============================================================


class TestChatRepository:
    async def test_create_and_get(self, test_session, user):
        chat = await chat_repository.create_chat(
            session=test_session,
            chat_object=ChatCreate(user_id=user.id, title="New"),
        )
        assert chat.id is not None
        found = await chat_repository.get_chat(session=test_session, chat_id=chat.id)
        assert found.id == chat.id
        assert await chat_repository.get(session=test_session, id=chat.id) is not None

    async def test_get_user_chats(self, test_session, user):
        for i in range(3):
            await chat_repository.create_chat(
                session=test_session,
                chat_object=ChatCreate(user_id=user.id, title=f"c{i}"),
            )
        chats = await chat_repository.get_user_chats(
            session=test_session, user_id=user.id
        )
        assert len(chats) == 3
        pinned = await chat_repository.get_user_chats(
            session=test_session, user_id=user.id, pinned_only=True
        )
        assert len(pinned) == 0

    async def test_get_chat_by_user_and_id(self, test_session, user, chat):
        found = await chat_repository.get_chat_by_user_and_id(
            session=test_session, user_id=user.id, chat_id=chat.id
        )
        assert found.id == chat.id
        none = await chat_repository.get_chat_by_user_and_id(
            session=test_session, user_id=999, chat_id=chat.id
        )
        assert none is None

    async def test_get_chat_with_messages(self, test_session, user, chat, msg):
        found = await chat_repository.get_chat_with_messages(
            session=test_session, chat_id=chat.id
        )
        assert found.id == chat.id
        limited = await chat_repository.get_chat_with_messages(
            session=test_session, chat_id=chat.id, user_id=user.id
        )
        assert limited is not None
        miss = await chat_repository.get_chat_with_messages(
            session=test_session, chat_id=chat.id, user_id=999
        )
        assert miss is None

    async def test_get_provider_and_model(self, test_session, chat):
        assert (
            await chat_repository.get_chat_provider(
                session=test_session, chat_id=chat.id
            )
            == "openai"
        )
        assert (
            await chat_repository.get_chat_model(session=test_session, chat_id=chat.id)
            == chat.model
        )

    async def test_pin_unpin(self, test_session, chat):
        pinned = await chat_repository.pin_chat(session=test_session, chat_id=chat.id)
        assert pinned.pinned is True
        unpinned = await chat_repository.unpin_chat(
            session=test_session, chat_id=chat.id, user_id=0
        )
        assert unpinned.pinned is False
        # missing chat
        assert await chat_repository.pin_chat(session=test_session, chat_id=999) is None
        assert (
            await chat_repository.unpin_chat(
                session=test_session, chat_id=999, user_id=0
            )
            is None
        )

    async def test_update_chat_position(self, test_session, chat):
        updated = await chat_repository.update_chat_position(
            session=test_session, chat_id=chat.id, position=5
        )
        assert updated.position == 5
        assert (
            await chat_repository.update_chat_position(
                session=test_session, chat_id=999, position=5
            )
            is None
        )

    async def test_update_chat_model(self, test_session, chat):
        updated = await chat_repository.update_chat_model(
            session=test_session, chat_id=chat.id, model="gpt-4"
        )
        assert updated.model == "gpt-4"
        assert (
            await chat_repository.update_chat_model(
                session=test_session, chat_id=999, model="gpt-4"
            )
            is None
        )

    async def test_update_provider_and_model(self, test_session, chat):
        updated = await chat_repository.update_chat_provider_and_model(
            session=test_session, chat_id=chat.id, provider="openrouter", model="m2"
        )
        assert updated.provider == "openrouter"
        assert updated.model == "m2"
        assert (
            await chat_repository.update_chat_provider_and_model(
                session=test_session, chat_id=999, provider="x", model="y"
            )
            is None
        )

    async def test_update_system_prompt(self, test_session, chat):
        updated = await chat_repository.update_system_prompt(
            session=test_session, chat_id=chat.id, user_id=0, prompt="be nice"
        )
        assert updated.system_prompt == "be nice"
        assert (
            await chat_repository.update_system_prompt(
                session=test_session, chat_id=999, user_id=0, prompt="x"
            )
            is None
        )

    async def test_delete_chat(self, test_session, chat, msg):
        # chat owns one message — it must be cascaded on chat deletion
        remaining = await message_repository.get_chat_messages(
            session=test_session, chat_id=chat.id
        )
        assert len(remaining) == 1

        deleted = await chat_repository.delete_chat(
            session=test_session, chat_id=chat.id
        )
        assert deleted.id == chat.id
        assert (
            await chat_repository.delete_chat(session=test_session, chat_id=chat.id)
            is None
        )

        # no orphan messages stay behind
        orphan = await message_repository.get_chat_messages(
            session=test_session, chat_id=chat.id
        )
        assert orphan == []


# ============================================================
# MessageRepository
# ============================================================


class TestMessageRepository:
    async def test_create_and_get(self, test_session, chat):
        msg = await message_repository.create_message(
            session=test_session,
            message_object=MessageCreate(role="user", content="hi", chat_id=chat.id),
        )
        assert msg.id is not None
        found = await message_repository.get_message(
            session=test_session, message_id=msg.id
        )
        assert found.id == msg.id

    async def test_get_chat_messages(self, test_session, chat):
        for i in range(2):
            await message_repository.create_message(
                session=test_session,
                message_object=MessageCreate(
                    role="user", content=f"m{i}", chat_id=chat.id
                ),
            )
        messages = await message_repository.get_chat_messages(
            session=test_session, chat_id=chat.id
        )
        assert len(messages) == 2

    async def test_get_message_with_chat(self, test_session, chat, msg):
        found = await message_repository.get_message_with_chat(
            session=test_session, message_id=msg.id
        )
        assert found.id == msg.id
        assert found.chat.id == chat.id

    async def test_update_message_tokens(self, test_session, chat, msg):
        updated = await message_repository.update_message_tokens(
            session=test_session,
            message_id=msg.id,
            prompt_tokens=10,
            completion_tokens=20,
            total_tokens=30,
            cost=0.5,
        )
        assert updated.prompt_tokens == 10
        assert updated.total_tokens == 30
        assert (
            await message_repository.update_message_tokens(
                session=test_session,
                message_id=999,
                prompt_tokens=1,
                completion_tokens=1,
                total_tokens=2,
                cost=0.1,
            )
            is None
        )

    async def test_delete_message(self, test_session, chat, msg):
        deleted = await message_repository.delete_message(
            session=test_session, message_id=msg.id
        )
        assert deleted.id == msg.id
        assert (
            await message_repository.delete_message(
                session=test_session, message_id=msg.id
            )
            is None
        )
