"""
Integration tests for chat CRUD operations.

Tests cover creation, reading, updating, and deletion of chats
with a real test database.
"""

import pytest
import pytest_asyncio

from database.models.chat import Chat  # type: ignore
from database.crud.chat import CRUDChat, chat_crud  # type: ignore
from core.security import hash_password  # type: ignore


# ============================================================
# TESTS: CRUD Chat — Create
# ============================================================


class TestChatCRUDCreate:
    """Chat creation tests."""

    @pytest.mark.asyncio
    async def test_create_chat_success(self, test_session, test_user_in_db):
        """Chat is created successfully."""
        chat_data = {
            "user_id": test_user_in_db.id,
            "title": "My Test Chat",
            "provider": "openai",
            "model": "gpt-4",
            "temperature": 0.8,
            "max_tokens": 3000,
        }

        chat = await chat_crud.create(test_session, object_in=chat_data)

        assert chat.id is not None
        assert chat.title == "My Test Chat"
        assert chat.provider == "openai"
        assert chat.model == "gpt-4"
        assert chat.temperature == 0.8
        assert chat.max_tokens == 3000
        assert chat.user_id == test_user_in_db.id
        assert chat.is_deleted is False
        assert chat.pinned is False

    @pytest.mark.asyncio
    async def test_create_chat_with_defaults(self, test_session, test_user_in_db):
        """Chat is created with default values."""
        chat_data = {
            "user_id": test_user_in_db.id,
            "provider": "openai",
            "model": "gpt-3.5-turbo",
        }

        chat = await chat_crud.create(test_session, object_in=chat_data)

        assert chat.title == "New Chat"
        assert chat.temperature == 0.7
        assert chat.max_tokens == 2000
        assert chat.pinned is False
        assert chat.is_deleted is False

    @pytest.mark.asyncio
    async def test_create_chat_auto_sets_position(self, test_session, test_user_in_db):
        """Chat automatically gets a position."""
        chat_data = {
            "user_id": test_user_in_db.id,
            "provider": "openai",
            "model": "gpt-3.5-turbo",
        }

        chat = await chat_crud.create(test_session, object_in=chat_data)

        assert chat.position is not None


# ============================================================
# TESTS: CRUD Chat — Read
# ============================================================


class TestChatCRUDRead:
    """Chat reading tests."""

    @pytest.mark.asyncio
    async def test_get_chat_by_id(self, test_session, test_chat_in_db):
        """Get chat by ID."""
        chat = await chat_crud.get_chat(test_session, chat_id=test_chat_in_db.id)

        assert chat is not None
        assert chat.id == test_chat_in_db.id
        assert chat.title == test_chat_in_db.title

    @pytest.mark.asyncio
    async def test_get_nonexistent_chat_returns_none(self, test_session):
        """Get non-existent chat returns None."""
        chat = await chat_crud.get_chat(test_session, chat_id=99999)

        assert chat is None

    @pytest.mark.asyncio
    async def test_get_user_chats(self, test_session, test_user_in_db):
        """Get all user's chats."""
        # Create more chats
        for i in range(3):
            await chat_crud.create(
                test_session,
                object_in={
                    "user_id": test_user_in_db.id,
                    "provider": "openai",
                    "model": "gpt-3.5-turbo",
                    "title": f"Chat {i}",
                },
            )

        chats = await chat_crud.get_user_chats(test_session, user_id=test_user_in_db.id)

        assert len(chats) == 4  # test_chat_in_db + 3 new

    @pytest.mark.asyncio
    async def test_get_user_chats_empty(self, test_session):
        """Get chats for non-existent user — empty list."""
        chats = await chat_crud.get_user_chats(test_session, user_id=99999)

        assert len(chats) == 0

    @pytest.mark.asyncio
    async def test_get_pinned_chats_only(self, test_session, test_user_in_db):
        """Get only pinned chats."""
        # Pin one chat
        await chat_crud.pin_chat(test_session, chat_id=test_chat_in_db.id)  # type: ignore

        # Create another unpinned chat
        await chat_crud.create(
            test_session,
            object_in={
                "user_id": test_user_in_db.id,
                "provider": "openai",
                "model": "gpt-3.5-turbo",
            },
        )

        pinned_chats = await chat_crud.get_user_chats(
            test_session, user_id=test_user_in_db.id, pinned_only=True
        )

        assert len(pinned_chats) == 1
        assert pinned_chats[0].pinned is True

    @pytest.mark.asyncio
    async def test_get_chat_provider(self, test_session, test_chat_in_db):
        """Get chat provider."""
        provider = await chat_crud.get_chat_provider(
            test_session, chat_id=test_chat_in_db.id
        )

        assert provider == "openai"

    @pytest.mark.asyncio
    async def test_get_chat_model(self, test_session, test_chat_in_db):
        """Get chat model."""
        model = await chat_crud.get_chat_model(test_session, chat_id=test_chat_in_db.id)

        assert model == "gpt-3.5-turbo"

    @pytest.mark.asyncio
    async def test_get_chat_by_user_and_id(
        self, test_session, test_user_in_db, test_chat_in_db
    ):
        """Get chat by user_id and chat_id."""
        chat = await chat_crud.get_chat_by_user_and_id(
            test_session, user_id=test_user_in_db.id, chat_id=test_chat_in_db.id
        )

        assert chat is not None
        assert chat.id == test_chat_in_db.id

    @pytest.mark.asyncio
    async def test_get_chat_by_wrong_user_and_id_returns_none(
        self, test_session, test_user_in_db, test_chat_in_db
    ):
        """Get chat with wrong user_id returns None."""
        chat = await chat_crud.get_chat_by_user_and_id(
            test_session, user_id=99999, chat_id=test_chat_in_db.id
        )

        assert chat is None


# ============================================================
# TESTS: CRUD Chat — Update
# ============================================================


class TestChatCRUDUpdate:
    """Chat update tests."""

    @pytest.mark.asyncio
    async def test_pin_chat(self, test_session, test_chat_in_db):
        """Pin a chat."""
        updated = await chat_crud.pin_chat(test_session, chat_id=test_chat_in_db.id)

        assert updated is not None
        assert updated.pinned is True

    @pytest.mark.asyncio
    async def test_unpin_chat(self, test_session, test_chat_in_db):
        """Unpin a chat."""
        # First pin it
        await chat_crud.pin_chat(test_session, chat_id=test_chat_in_db.id)

        updated = await chat_crud.unpin_chat(
            test_session, chat_id=test_chat_in_db.id, user_id=test_chat_in_db.user_id
        )

        assert updated is not None
        assert updated.pinned is False

    @pytest.mark.asyncio
    async def test_pin_nonexistent_chat_returns_none(self, test_session):
        """Pin non-existent chat returns None."""
        updated = await chat_crud.pin_chat(test_session, chat_id=99999)

        assert updated is None

    @pytest.mark.asyncio
    async def test_update_chat_model(self, test_session, test_chat_in_db):
        """Update chat model."""
        updated = await chat_crud.update_chat_model(
            test_session, chat_id=test_chat_in_db.id, model="gpt-4o"
        )

        assert updated is not None
        assert updated.model == "gpt-4o"

    @pytest.mark.asyncio
    async def test_update_chat_provider_and_model(self, test_session, test_chat_in_db):
        """Update chat provider and model."""
        updated = await chat_crud.update_chat_provider_and_model(
            test_session,
            chat_id=test_chat_in_db.id,
            provider="openrouter",
            model="meta-llama/llama-3",
        )

        assert updated is not None
        assert updated.provider == "openrouter"
        assert updated.model == "meta-llama/llama-3"

    @pytest.mark.asyncio
    async def test_update_chat_position(self, test_session, test_chat_in_db):
        """Update chat position."""
        updated = await chat_crud.update_chat_position(
            test_session, chat_id=test_chat_in_db.id, position=5
        )

        assert updated is not None
        assert updated.position == 5

    @pytest.mark.asyncio
    async def test_update_nonexistent_chat_returns_none(self, test_session):
        """Update non-existent chat returns None."""
        updated = await chat_crud.update_chat_model(
            test_session, chat_id=99999, model="gpt-4"
        )

        assert updated is None


# ============================================================
# TESTS: CRUD Chat — Delete
# ============================================================


class TestChatCRUDDelete:
    """Chat deletion tests."""

    @pytest.mark.asyncio
    async def test_delete_chat_success(self, test_session, test_chat_in_db):
        """Chat is successfully deleted."""
        deleted = await chat_crud.delete_chat(test_session, chat_id=test_chat_in_db.id)

        # delete returns True/False, not an object
        assert deleted is True

        # Check that chat is deleted
        chat = await chat_crud.get_chat(test_session, chat_id=test_chat_in_db.id)
        assert chat is None

    @pytest.mark.asyncio
    async def test_delete_nonexistent_chat_returns_false(self, test_session):
        """Delete non-existent chat returns False."""
        result = await chat_crud.delete_chat(test_session, chat_id=99999)

        assert result is False


# ============================================================
# TESTS: CRUD Chat — User-Chat Relationship
# ============================================================


class TestChatUserRelationship:
    """User-Chat relationship tests."""

    @pytest.mark.asyncio
    async def test_chats_deleted_when_user_deleted(
        self, test_session, test_user_in_db, test_chat_in_db
    ):
        """When user is deleted, their chats are also deleted (cascade)."""
        user_id = test_user_in_db.id
        chat_id = test_chat_in_db.id

        # Delete user
        await user_crud.delete_user(test_session, user_id=user_id)  # type: ignore

        # Chat should be deleted due to cascade
        chat = await chat_crud.get_chat(test_session, chat_id=chat_id)
        assert chat is None

    @pytest.mark.asyncio
    async def test_user_has_chats_relationship(self, test_session, test_user_in_db):
        """User has chats relationship."""
        # Create chats
        for i in range(2):
            await chat_crud.create(
                test_session,
                object_in={
                    "user_id": test_user_in_db.id,
                    "provider": "openai",
                    "model": "gpt-3.5-turbo",
                    "title": f"Chat {i}",
                },
            )

        # Get user with chats
        from sqlalchemy.orm import selectinload
        from sqlalchemy import select

        result = await test_session.execute(
            select(type(test_user_in_db))
            .where(type(test_user_in_db).id == test_user_in_db.id)
            .options(selectinload(type(test_user_in_db).chats))
        )
        user = result.scalar_one()

        assert len(user.chats) == 3  # test_chat_in_db + 2 new
