"""
Integration tests for user CRUD operations.

Tests cover the full cycle: create, read, update, delete
with a real test database (SQLite in-memory).
"""

import pytest
import pytest_asyncio

from database.models.user import User  # type: ignore
from database.crud.user import CRUDUser, user_crud  # type: ignore
from core.security import hash_password  # type: ignore


# ============================================================
# TESTS: Basic CRUD operations
# ============================================================


class TestUserCRUDCreate:
    """User creation tests."""

    @pytest.mark.asyncio
    async def test_create_user_success(self, test_session, user_data_factory):
        """User is created successfully."""
        data = user_data_factory()
        data["password_hash"] = hash_password(data["password"])
        del data["password"]  # User model does not accept 'password'

        user = await user_crud.create(test_session, object_in=data)

        assert user.id is not None
        assert user.username == data["username"]
        assert user.email == data["email"]
        assert user.is_active is True
        assert user.is_superuser is False

    @pytest.mark.asyncio
    async def test_create_user_with_dict(self, test_session, user_data_factory):
        """User is created from dict."""
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
        """created_at and updated_at are automatically set on creation."""
        data = user_data_factory()
        data["password_hash"] = hash_password(data["password"])
        del data["password"]

        user = await user_crud.create(test_session, object_in=data)

        assert user.created_at is not None
        assert user.updated_at is not None


class TestUserCRUDRead:
    """User reading tests."""

    @pytest.mark.asyncio
    async def test_get_user_by_id(self, test_session, test_user_in_db):
        """Get user by ID."""
        user = await user_crud.get(test_session, test_user_in_db.id)

        assert user is not None
        assert user.id == test_user_in_db.id
        assert user.email == test_user_in_db.email

    @pytest.mark.asyncio
    async def test_get_nonexistent_user_returns_none(self, test_session):
        """Get non-existent user returns None."""
        user = await user_crud.get(test_session, 99999)

        assert user is None

    @pytest.mark.asyncio
    async def test_get_by_email(self, test_session, test_user_in_db):
        """Get user by email."""
        user = await user_crud.get_by_email(test_session, test_user_in_db.email)

        assert user is not None
        assert user.id == test_user_in_db.id

    @pytest.mark.asyncio
    async def test_get_by_wrong_email_returns_none(self, test_session):
        """Get by non-existent email returns None."""
        user = await user_crud.get_by_email(test_session, "nonexistent@example.com")

        assert user is None

    @pytest.mark.asyncio
    async def test_get_by_username(self, test_session, test_user_in_db):
        """Get user by username."""
        user = await user_crud.get_by_username(test_session, test_user_in_db.username)

        assert user is not None
        assert user.id == test_user_in_db.id

    @pytest.mark.asyncio
    async def test_is_exists_returns_true(self, test_session, test_user_in_db):
        """Check user exists."""
        exists = await user_crud.is_exists(test_session, id=test_user_in_db.id)

        assert exists is True

    @pytest.mark.asyncio
    async def test_is_exists_returns_false(self, test_session):
        """Check non-existent user."""
        exists = await user_crud.is_exists(test_session, id=99999)

        assert exists is False


class TestUserCRUDUpdate:
    """User update tests."""

    @pytest.mark.asyncio
    async def test_update_user_email(self, test_session, test_user_in_db, unique_email):
        """Update user email."""
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
        """Update user balance."""
        updated = await user_crud.update_field(
            test_session,
            object_id=test_user_in_db.id,
            field_name="balance",
            field_value=150.50,
        )

        assert updated is not None
        # balance is stored as Decimal, compare with tolerance
        assert float(updated.balance) == 150.50

    @pytest.mark.asyncio
    async def test_update_nonexistent_user_returns_none(self, test_session):
        """Update non-existent user returns None."""
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
        """Cannot update protected field id."""
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
        """Cannot update protected field created_at."""
        with pytest.raises(PermissionError):
            await user_crud.update_field(
                test_session,
                object_id=test_user_in_db.id,
                field_name="created_at",
                field_value="2000-01-01",
            )

    @pytest.mark.asyncio
    async def test_activate_user(self, test_session, test_user_in_db):
        """Activate user."""
        # First deactivate
        await user_crud.deactivate(test_session, user_id=test_user_in_db.id)

        # Activate
        updated = await user_crud.activate(test_session, user_id=test_user_in_db.id)

        assert updated is not None
        assert updated.is_active is True

    @pytest.mark.asyncio
    async def test_deactivate_user(self, test_session, test_user_in_db):
        """Deactivate user."""
        updated = await user_crud.deactivate(test_session, user_id=test_user_in_db.id)

        assert updated is not None
        assert updated.is_active is False

    @pytest.mark.asyncio
    async def test_is_active_returns_true(self, test_session, test_user_in_db):
        """Check user is active."""
        is_active = await user_crud.is_active(test_session, user_id=test_user_in_db.id)

        assert is_active is True

    @pytest.mark.asyncio
    async def test_is_active_returns_false_for_deactivated(
        self, test_session, test_user_in_db
    ):
        """Check deactivated user is inactive."""
        await user_crud.deactivate(test_session, user_id=test_user_in_db.id)

        is_active = await user_crud.is_active(test_session, user_id=test_user_in_db.id)

        assert is_active is False

    @pytest.mark.asyncio
    async def test_is_active_returns_false_for_nonexistent(self, test_session):
        """Check non-existent user."""
        is_active = await user_crud.is_active(test_session, user_id=99999)

        assert is_active is False

    @pytest.mark.asyncio
    async def test_update_refresh_token(self, test_session, test_user_in_db):
        """Update user refresh token."""
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
    """User deletion tests."""

    @pytest.mark.asyncio
    async def test_delete_user_success(self, test_session, test_user_in_db):
        """User is successfully deleted."""
        deleted = await user_crud.delete_user(test_session, user_id=test_user_in_db.id)

        assert deleted is not None
        assert deleted.id == test_user_in_db.id

        # Check that user no longer exists
        user = await user_crud.get(test_session, test_user_in_db.id)
        assert user is None

    @pytest.mark.asyncio
    async def test_delete_nonexistent_user_returns_none(self, test_session):
        """Delete non-existent user returns None."""
        deleted = await user_crud.delete_user(test_session, user_id=99999)

        assert deleted is None


class TestUserCRUDRecordsCount:
    """Record count tests."""

    @pytest.mark.asyncio
    async def test_records_count_zero(self, test_session):
        """Zero users in empty DB."""
        count = await user_crud.records_count(test_session)

        assert count == 0

    @pytest.mark.asyncio
    async def test_records_count_one(self, test_session, test_user_in_db):
        """One user after creation."""
        count = await user_crud.records_count(test_session)

        assert count == 1

    @pytest.mark.asyncio
    async def test_records_count_multiple(
        self, test_session, test_user_in_db, user_data_factory
    ):
        """Multiple users."""
        # Create 2 more users
        for _ in range(2):
            data = user_data_factory()
            data["password_hash"] = hash_password(data["password"])
            del data["password"]
            await user_crud.create(test_session, object_in=data)

        count = await user_crud.records_count(test_session)

        assert count == 3  # test_user_in_db + 2 new
