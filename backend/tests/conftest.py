"""
Global fixtures for pytest.

This file contains fixtures available in all tests.
Fixtures are pre-configured objects that are reused
between tests (DB session, test data, mocks).
"""

import pytest
import pytest_asyncio
from typing import AsyncGenerator
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.pool import StaticPool

from database.models.base import Base  # type: ignore
from database.models.user import User  # type: ignore
from database.models.chat import Chat  # type: ignore
from database.models.message import Message  # type: ignore
from database.crud.user import CRUDUser, user_crud  # type: ignore
from database.crud.chat import CRUDChat, chat_crud  # type: ignore
from database.crud.message import CRUDMessage, message_crud  # type: ignore
from services.auth import AuthService  # type: ignore
from core.config import settings  # type: ignore
from core.security import hash_password, create_access_token, create_refresh_token  # type: ignore
from schemas.auth import SignUpRequest, SignInRequest  # type: ignore


# ============================================================
# TEST DB (SQLite in-memory)
# ============================================================


@pytest.fixture(scope="session")
def anyio_backend():
    """Use asyncio backend for async tests."""
    return "asyncio"


@pytest.fixture(scope="session")
def test_db_url():
    """
    URL for test DB — SQLite in memory.
    Do not required to install PostgreSQL.
    """
    return "sqlite+aiosqlite:///:memory:"


@pytest_asyncio.fixture(scope="function")
async def test_engine(test_db_url):
    """
    Create test DB engine.
    scope="function" — new DB for every test.
    """
    engine = create_async_engine(
        url=test_db_url,
        echo=False,
        poolclass=StaticPool,  # One connection for all sessions
    )

    # Create all tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    yield engine

    # Drop tables after test
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

    await engine.dispose()


@pytest_asyncio.fixture(scope="function")
async def test_session(test_engine) -> AsyncGenerator[AsyncSession, None]:
    """
    Return test DB session.
    Automatically rolls back after each test — data is not persisted.
    """
    session_factory = async_sessionmaker(
        bind=test_engine,
        autoflush=False,
        autocommit=False,
        expire_on_commit=False,
    )

    async with session_factory() as session:
        yield session
        await session.rollback()


# ============================================================
# FIXTURES: CRUD objects
# ============================================================


@pytest.fixture
def user_crud_instance():
    """CRUDUser instance for use in services."""
    return CRUDUser(User)


@pytest.fixture
def chat_crud_instance():
    """CRUDChat instance for use in services."""
    return CRUDChat(Chat)


# ============================================================
# FIXTURES: Test data (factories)
# ============================================================


@pytest.fixture
def unique_email():
    """
    Generate a unique email for each test.
    Uses pytest to generate unique values.
    """
    import uuid

    return f"test_{uuid.uuid4().hex[:8]}@example.com"


@pytest.fixture
def user_data_factory():
    """
    Factory for creating user data.
    Each call generates UNIQUE email and username.
    """
    import uuid

    def _make_user_data(**overrides):
        unique_id = uuid.uuid4().hex[:8]
        data = {
            "username": f"testuser_{unique_id}",
            "email": f"test_{unique_id}@example.com",
            "password": "TestPassword123!",
        }
        data.update(overrides)
        return data

    return _make_user_data


@pytest.fixture
def signup_request_factory(user_data_factory):
    """SignUpRequest factory for auth tests."""

    def _make_signup_request(**overrides):
        data = user_data_factory(**overrides)
        return SignUpRequest(**data)

    return _make_signup_request


@pytest.fixture
def signin_request_factory(user_data_factory):
    """SignInRequest factory for auth tests."""

    def _make_signin_request(**overrides):
        email = overrides.get("email", user_data_factory()["email"])
        password = overrides.get("password", user_data_factory()["password"])
        return SignInRequest(email=email, password=password)

    return _make_signin_request


# ============================================================
# FIXTURES: Services
# ============================================================


@pytest_asyncio.fixture
async def auth_service(test_session, user_crud_instance):
    """
    AuthService instance with test DB session.
    Used in auth integration tests.
    """
    return AuthService(session=test_session, user_crud=user_crud_instance)


# ============================================================
# FIXTURES: Pre-populated users in DB
# ============================================================


@pytest_asyncio.fixture
async def test_user_in_db(test_session, user_data_factory):
    """
    Create a user in test DB and return it.
    Password is hashed.
    """
    data = user_data_factory()
    hashed_pw = hash_password(data["password"])

    user = User(
        username=data["username"],
        email=data["email"],
        password_hash=hashed_pw,
        is_active=True,
        is_superuser=False,
        balance=0.0,
    )

    test_session.add(user)
    await test_session.commit()
    await test_session.refresh(user)

    return user


@pytest_asyncio.fixture
async def admin_user_in_db(test_session, user_data_factory):
    """Create a superuser in test DB."""
    data = user_data_factory(username="admin_test")
    hashed_pw = hash_password(data["password"])

    user = User(
        username=data["username"],
        email=data["email"],
        password_hash=hashed_pw,
        is_active=True,
        is_superuser=True,
        balance=0.0,
    )

    test_session.add(user)
    await test_session.commit()
    await test_session.refresh(user)

    return user


# ============================================================
# FIXTURES: Test chats
# ============================================================


@pytest_asyncio.fixture
async def test_chat_in_db(test_session, test_user_in_db):
    """Create a chat in DB linked to test_user_in_db."""
    chat = Chat(
        user_id=test_user_in_db.id,
        title="Test Chat",
        provider="openai",
        model="gpt-3.5-turbo",
        temperature=0.7,
        max_tokens=2000,
    )

    test_session.add(chat)
    await test_session.commit()
    await test_session.refresh(chat)

    return chat
