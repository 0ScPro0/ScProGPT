"""
Integration тесты для CRUD операций с пользователями.

Тестируем полный цикл: создание, чтение, обновление, удаление
с реальной тестовой БД (SQLite in-memory).
"""

import pytest
import pytest_asyncio

from database.models.user import User
from database.crud.user import CRUDUser, user_crud
from core.security import hash_password


# ============================================================
# ТЕСТЫ: Базовые CRUD операции
# ============================================================


class TestUserCRUDCreate:
    """Тесты создания пользователя"""

    @pytest.mark.asyncio
    async def test_create_user_success(self, test_session, user_data_factory):
        """Пользователь успешно создаётся"""
        data = user_data_factory()
        data["password_hash"] = hash_password(data["password"])
        del data["password"]  # Модель User не принимает 'password'

        user = await user_crud.create(test_session, object_in=data)

        assert user.id is not None
        assert user.username == data["username"]
        assert user.email == data["email"]
        assert user.is_active is True
        assert user.is_superuser is False

    @pytest.mark.asyncio
    async def test_create_user_with_dict(self, test_session, user_data_factory):
        """Пользователь создаётся из dict"""
        data = user_data_factory()
        data["password_hash"] = hash_password(data["password"])
        del data["password"]

        user = await user_crud.create_user(test_session, user_object=data)

        assert user.id is not None
        assert user.email == data["email"]

    @pytest.mark.asyncio
    async def test_create_user_auto_sets_timestamps(
        self, test_session, user_data_factory
    ):
        """При создании автоматически ставятся created_at и updated_at"""
        data = user_data_factory()
        data["password_hash"] = hash_password(data["password"])
        del data["password"]

        user = await user_crud.create(test_session, object_in=data)

        assert user.created_at is not None
        assert user.updated_at is not None


class TestUserCRUDRead:
    """Тесты чтения пользователей"""

    @pytest.mark.asyncio
    async def test_get_user_by_id(self, test_session, test_user_in_db):
        """Получение пользователя по ID"""
        user = await user_crud.get(test_session, test_user_in_db.id)

        assert user is not None
        assert user.id == test_user_in_db.id
        assert user.email == test_user_in_db.email

    @pytest.mark.asyncio
    async def test_get_nonexistent_user_returns_none(self, test_session):
        """Получение несуществующего пользователя возвращает None"""
        user = await user_crud.get(test_session, 99999)

        assert user is None

    @pytest.mark.asyncio
    async def test_get_by_email(self, test_session, test_user_in_db):
        """Получение пользователя по email"""
        user = await user_crud.get_by_email(test_session, test_user_in_db.email)

        assert user is not None
        assert user.id == test_user_in_db.id

    @pytest.mark.asyncio
    async def test_get_by_wrong_email_returns_none(self, test_session):
        """Получение по несуществующему email возвращает None"""
        user = await user_crud.get_by_email(test_session, "nonexistent@example.com")

        assert user is None

    @pytest.mark.asyncio
    async def test_get_by_username(self, test_session, test_user_in_db):
        """Получение пользователя по username"""
        user = await user_crud.get_by_username(test_session, test_user_in_db.username)

        assert user is not None
        assert user.id == test_user_in_db.id

    @pytest.mark.asyncio
    async def test_is_exists_returns_true(self, test_session, test_user_in_db):
        """Проверка существования пользователя"""
        exists = await user_crud.is_exists(test_session, id=test_user_in_db.id)

        assert exists is True

    @pytest.mark.asyncio
    async def test_is_exists_returns_false(self, test_session):
        """Проверка несуществующего пользователя"""
        exists = await user_crud.is_exists(test_session, id=99999)

        assert exists is False


class TestUserCRUDUpdate:
    """Тесты обновления пользователя"""

    @pytest.mark.asyncio
    async def test_update_user_email(self, test_session, test_user_in_db, unique_email):
        """Обновление email пользователя"""
        new_email = unique_email

        updated = await user_crud.update_field(
            test_session,
            object_id=test_user_in_db.id,
            field_name="email",
            field_value=new_email,
        )

        assert updated is not None
        assert updated.email == new_email

    @pytest.mark.asyncio
    async def test_update_user_balance(self, test_session, test_user_in_db):
        """Обновление баланса пользователя"""
        updated = await user_crud.update_field(
            test_session,
            object_id=test_user_in_db.id,
            field_name="balance",
            field_value=150.50,
        )

        assert updated is not None
        # balance хранится как Decimal, сравниваем с допуском
        assert float(updated.balance) == 150.50

    @pytest.mark.asyncio
    async def test_update_nonexistent_user_returns_none(self, test_session):
        """Обновление несуществующего пользователя возвращает None"""
        updated = await user_crud.update_field(
            test_session,
            object_id=99999,
            field_name="email",
            field_value="new@example.com",
        )

        assert updated is None

    @pytest.mark.asyncio
    async def test_cannot_update_protected_field_id(
        self, test_session, test_user_in_db
    ):
        """Нельзя обновить защищённое поле id"""
        with pytest.raises(PermissionError):
            await user_crud.update_field(
                test_session,
                object_id=test_user_in_db.id,
                field_name="id",
                field_value=999,
            )

    @pytest.mark.asyncio
    async def test_cannot_update_protected_field_created_at(
        self, test_session, test_user_in_db
    ):
        """Нельзя обновить защищённое поле created_at"""
        with pytest.raises(PermissionError):
            await user_crud.update_field(
                test_session,
                object_id=test_user_in_db.id,
                field_name="created_at",
                field_value="2000-01-01",
            )

    @pytest.mark.asyncio
    async def test_activate_user(self, test_session, test_user_in_db):
        """Активация пользователя"""
        # Сначала деактивируем
        await user_crud.deactivate(test_session, user_id=test_user_in_db.id)

        # Активируем
        updated = await user_crud.activate(test_session, user_id=test_user_in_db.id)

        assert updated is not None
        assert updated.is_active is True

    @pytest.mark.asyncio
    async def test_deactivate_user(self, test_session, test_user_in_db):
        """Деактивация пользователя"""
        updated = await user_crud.deactivate(test_session, user_id=test_user_in_db.id)

        assert updated is not None
        assert updated.is_active is False

    @pytest.mark.asyncio
    async def test_is_active_returns_true(self, test_session, test_user_in_db):
        """Проверка что пользователь активен"""
        is_active = await user_crud.is_active(test_session, user_id=test_user_in_db.id)

        assert is_active is True

    @pytest.mark.asyncio
    async def test_is_active_returns_false_for_deactivated(
        self, test_session, test_user_in_db
    ):
        """Проверка что деактивированный пользователь не активен"""
        await user_crud.deactivate(test_session, user_id=test_user_in_db.id)

        is_active = await user_crud.is_active(test_session, user_id=test_user_in_db.id)

        assert is_active is False

    @pytest.mark.asyncio
    async def test_is_active_returns_false_for_nonexistent(self, test_session):
        """Проверка несуществующего пользователя"""
        is_active = await user_crud.is_active(test_session, user_id=99999)

        assert is_active is False

    @pytest.mark.asyncio
    async def test_update_refresh_token(self, test_session, test_user_in_db):
        """Обновление refresh токена пользователя"""
        from datetime import datetime, timedelta, timezone

        token = "test_refresh_token_value"
        expires_at = datetime.now(timezone.utc) + timedelta(days=7)

        updated = await user_crud.update_refresh_token(
            test_session,
            user_id=test_user_in_db.id,
            refresh_token=token,
            expires_at=expires_at,
        )

        assert updated is not None
        assert updated.refresh_token == token


class TestUserCRUDDelete:
    """Тесты удаления пользователя"""

    @pytest.mark.asyncio
    async def test_delete_user_success(self, test_session, test_user_in_db):
        """Пользователь успешно удаляется"""
        deleted = await user_crud.delete_user(test_session, user_id=test_user_in_db.id)

        assert deleted is not None
        assert deleted.id == test_user_in_db.id

        # Проверяем что больше не существует
        user = await user_crud.get(test_session, test_user_in_db.id)
        assert user is None

    @pytest.mark.asyncio
    async def test_delete_nonexistent_user_returns_none(self, test_session):
        """Удаление несуществующего пользователя возвращает None"""
        deleted = await user_crud.delete_user(test_session, user_id=99999)

        assert deleted is None


class TestUserCRUDRecordsCount:
    """Тесты подсчёта записей"""

    @pytest.mark.asyncio
    async def test_records_count_zero(self, test_session):
        """Ноль пользователей в пустой БД"""
        count = await user_crud.records_count(test_session)

        assert count == 0

    @pytest.mark.asyncio
    async def test_records_count_one(self, test_session, test_user_in_db):
        """Один пользователь после создания"""
        count = await user_crud.records_count(test_session)

        assert count == 1

    @pytest.mark.asyncio
    async def test_records_count_multiple(
        self, test_session, test_user_in_db, user_data_factory
    ):
        """Несколько пользователей"""
        # Создаём ещё 2 пользователей
        for _ in range(2):
            data = user_data_factory()
            data["password_hash"] = hash_password(data["password"])
            del data["password"]
            await user_crud.create(test_session, object_in=data)

        count = await user_crud.records_count(test_session)

        assert count == 3  # test_user_in_db + 2 новых
