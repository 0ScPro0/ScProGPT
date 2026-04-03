"""
Integration тесты для CRUD операций с чатами.

Тестируем создание, чтение, обновление, удаление чатов
с реальной тестовой БД.
"""

import pytest
import pytest_asyncio

from database.models.chat import Chat
from database.crud.chat import CRUDChat, chat_crud
from core.security import hash_password


# ============================================================
# ТЕСТЫ: CRUD Chat — Создание
# ============================================================

class TestChatCRUDCreate:
    """Тесты создания чата"""

    @pytest.mark.asyncio
    async def test_create_chat_success(self, test_session, test_user_in_db):
        """Чат успешно создаётся"""
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
        """Чат создаётся с дефолтными значениями"""
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
        """Чат автоматически получает position"""
        chat_data = {
            "user_id": test_user_in_db.id,
            "provider": "openai",
            "model": "gpt-3.5-turbo",
        }

        chat = await chat_crud.create(test_session, object_in=chat_data)

        assert chat.position is not None


# ============================================================
# ТЕСТЫ: CRUD Chat — Чтение
# ============================================================

class TestChatCRUDRead:
    """Тесты чтения чатов"""

    @pytest.mark.asyncio
    async def test_get_chat_by_id(self, test_session, test_chat_in_db):
        """Получение чата по ID"""
        chat = await chat_crud.get_chat(test_session, chat_id=test_chat_in_db.id)

        assert chat is not None
        assert chat.id == test_chat_in_db.id
        assert chat.title == test_chat_in_db.title

    @pytest.mark.asyncio
    async def test_get_nonexistent_chat_returns_none(self, test_session):
        """Получение несуществующего чата возвращает None"""
        chat = await chat_crud.get_chat(test_session, chat_id=99999)

        assert chat is None

    @pytest.mark.asyncio
    async def test_get_user_chats(self, test_session, test_user_in_db):
        """Получение всех чатов пользователя"""
        # Создаём ещё чаты
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

        assert len(chats) == 4  # test_chat_in_db + 3 новых

    @pytest.mark.asyncio
    async def test_get_user_chats_empty(self, test_session):
        """Получение чатов несуществующего пользователя — пустой список"""
        chats = await chat_crud.get_user_chats(test_session, user_id=99999)

        assert len(chats) == 0

    @pytest.mark.asyncio
    async def test_get_pinned_chats_only(self, test_session, test_user_in_db):
        """Получение только закреплённых чатов"""
        # Закрепляем один чат
        await chat_crud.pin_chat(test_session, chat_id=test_chat_in_db.id)

        # Создаём ещё один незакреплённый
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
        """Получение провайдера чата"""
        provider = await chat_crud.get_chat_provider(
            test_session, chat_id=test_chat_in_db.id
        )

        assert provider == "openai"

    @pytest.mark.asyncio
    async def test_get_chat_model(self, test_session, test_chat_in_db):
        """Получение модели чата"""
        model = await chat_crud.get_chat_model(test_session, chat_id=test_chat_in_db.id)

        assert model == "gpt-3.5-turbo"

    @pytest.mark.asyncio
    async def test_get_chat_by_user_and_id(self, test_session, test_user_in_db, test_chat_in_db):
        """Получение чата по user_id и chat_id"""
        chat = await chat_crud.get_chat_by_user_and_id(
            test_session, user_id=test_user_in_db.id, chat_id=test_chat_in_db.id
        )

        assert chat is not None
        assert chat.id == test_chat_in_db.id

    @pytest.mark.asyncio
    async def test_get_chat_by_wrong_user_and_id_returns_none(
        self, test_session, test_user_in_db, test_chat_in_db
    ):
        """Получение чата чужим user_id возвращает None"""
        chat = await chat_crud.get_chat_by_user_and_id(
            test_session, user_id=99999, chat_id=test_chat_in_db.id
        )

        assert chat is None


# ============================================================
# ТЕСТЫ: CRUD Chat — Обновление
# ============================================================

class TestChatCRUDUpdate:
    """Тесты обновления чата"""

    @pytest.mark.asyncio
    async def test_pin_chat(self, test_session, test_chat_in_db):
        """Закрепление чата"""
        updated = await chat_crud.pin_chat(test_session, chat_id=test_chat_in_db.id)

        assert updated is not None
        assert updated.pinned is True

    @pytest.mark.asyncio
    async def test_unpin_chat(self, test_session, test_chat_in_db):
        """Открепление чата"""
        # Сначала закрепляем
        await chat_crud.pin_chat(test_session, chat_id=test_chat_in_db.id)

        updated = await chat_crud.unpin_chat(
            test_session, chat_id=test_chat_in_db.id, user_id=test_chat_in_db.user_id
        )

        assert updated is not None
        assert updated.pinned is False

    @pytest.mark.asyncio
    async def test_pin_nonexistent_chat_returns_none(self, test_session):
        """Закрепление несуществующего чата возвращает None"""
        updated = await chat_crud.pin_chat(test_session, chat_id=99999)

        assert updated is None

    @pytest.mark.asyncio
    async def test_update_chat_model(self, test_session, test_chat_in_db):
        """Обновление модели чата"""
        updated = await chat_crud.update_chat_model(
            test_session, chat_id=test_chat_in_db.id, model="gpt-4o"
        )

        assert updated is not None
        assert updated.model == "gpt-4o"

    @pytest.mark.asyncio
    async def test_update_chat_provider_and_model(self, test_session, test_chat_in_db):
        """Обновление провайдера и модели чата"""
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
        """Обновление позиции чата"""
        updated = await chat_crud.update_chat_position(
            test_session, chat_id=test_chat_in_db.id, position=5
        )

        assert updated is not None
        assert updated.position == 5

    @pytest.mark.asyncio
    async def test_update_nonexistent_chat_returns_none(self, test_session):
        """Обновление несуществующего чата возвращает None"""
        updated = await chat_crud.update_chat_model(
            test_session, chat_id=99999, model="gpt-4"
        )

        assert updated is None


# ============================================================
# ТЕСТЫ: CRUD Chat — Удаление
# ============================================================

class TestChatCRUDDelete:
    """Тесты удаления чата"""

    @pytest.mark.asyncio
    async def test_delete_chat_success(self, test_session, test_chat_in_db):
        """Чат успешно удаляется"""
        deleted = await chat_crud.delete_chat(test_session, chat_id=test_chat_in_db.id)

        # delete возвращает True/False, не объект
        assert deleted is True

        # Проверяем что чат удалён
        chat = await chat_crud.get_chat(test_session, chat_id=test_chat_in_db.id)
        assert chat is None

    @pytest.mark.asyncio
    async def test_delete_nonexistent_chat_returns_false(self, test_session):
        """Удаление несуществующего чата возвращает False"""
        result = await chat_crud.delete_chat(test_session, chat_id=99999)

        assert result is False


# ============================================================
# ТЕСТЫ: CRUD Chat — Связь User-Chat
# ============================================================

class TestChatUserRelationship:
    """Тесты связи между пользователем и чатами"""

    @pytest.mark.asyncio
    async def test_chats_deleted_when_user_deleted(
        self, test_session, test_user_in_db, test_chat_in_db
    ):
        """При удалении пользователя его чаты тоже удаляются (cascade)"""
        user_id = test_user_in_db.id
        chat_id = test_chat_in_db.id

        # Удаляем пользователя
        await user_crud.delete_user(test_session, user_id=user_id)

        # Чат должен удалиться из-за cascade
        chat = await chat_crud.get_chat(test_session, chat_id=chat_id)
        assert chat is None

    @pytest.mark.asyncio
    async def test_user_has_chats_relationship(self, test_session, test_user_in_db):
        """У пользователя есть связь с чатами"""
        # Создаём чаты
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

        # Получаем пользователя с чатами
        from sqlalchemy.orm import selectinload
        from sqlalchemy import select

        result = await test_session.execute(
            select(type(test_user_in_db))
            .where(type(test_user_in_db).id == test_user_in_db.id)
            .options(selectinload(type(test_user_in_db).chats))
        )
        user = result.scalar_one()

        assert len(user.chats) == 3  # test_chat_in_db + 2 новых
