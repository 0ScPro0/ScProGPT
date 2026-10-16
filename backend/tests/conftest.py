"""
Global fixtures for pytest.

This file contains fixtures available in all tests.
Fixtures are pre-configured objects that are reused
between tests (DB session, test data, mocks).
"""

import pytest
import pytest_asyncio
from typing import AsyncGenerator, List
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.pool import StaticPool

from database.models.base import Base  # type: ignore
from database.models.user import User  # type: ignore
from database.models.chat import Chat  # type: ignore
from database.models.message import Message  # type: ignore
from repositories import *  # type: ignore
from repositories import (  # type: ignore
    user_repository,
    chat_repository,
    message_repository,
    UserRepository,
    ChatRepository,
    MessageRepository,
)
from services.auth import AuthService  # type: ignore
from services.user import UserService  # type: ignore
from services.chat import ChatService  # type: ignore
from services.message import MessageService  # type: ignore
from core.config import settings  # type: ignore
from core.security import hash_password, create_access_token, create_refresh_token  # type: ignore
from schemas.auth import SignUpRequest, SignInRequest  # type: ignore
from schemas.chat import ChatCreate  # type: ignore
from schemas.message import MessageCreate  # type: ignore

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
# FIXTURES: Repositories
# ============================================================


# ============================================================
# FIXTURES: Test data (factories)
# ============================================================


# ============================================================
# FIXTURES: Services
# ============================================================


# ============================================================
# FIXTURES: Pre-populated users in DB
# ============================================================


# ============================================================
# FIXTURES: Test users, chats, messages
# ============================================================


async def create_user_in_db(
    session: AsyncSession,
    *,
    username: str = "testuser",
    email: str = "test@example.com",
    password: str = "password123",
    is_active: bool = True,
    is_superuser: bool = False,
) -> User:
    """Helper to create a user directly via repository."""
    hashed = hash_password(password)
    user = await user_repository.create_user(
        session=session,
        user_object={
            "username": username,
            "email": email,
            "password_hash": hashed,
            "is_active": is_active,
            "is_superuser": is_superuser,
        },
    )
    return user


@pytest_asyncio.fixture(scope="function")
async def user(test_session) -> User:
    """Fixture: created user."""
    return await create_user_in_db(test_session)


@pytest_asyncio.fixture(scope="function")
async def superuser(test_session) -> User:
    """Fixture: created superuser."""
    return await create_user_in_db(
        test_session,
        username="admin",
        email="admin@example.com",
        is_superuser=True,
    )


@pytest_asyncio.fixture(scope="function")
async def chat(test_session, user: User) -> Chat:
    """Fixture: chat owned by `user`."""
    created = await chat_repository.create_chat(
        session=test_session,
        chat_object=ChatCreate(user_id=user.id, title="Test chat"),
    )
    return created


@pytest_asyncio.fixture(scope="function")
async def msg(test_session, chat: Chat) -> Message:
    """Fixture: message in `chat`."""
    created = await message_repository.create_message(
        session=test_session,
        message_object=MessageCreate(role="user", content="Hello", chat_id=chat.id),
    )
    return created


# ============================================================
# FIXTURES: Services
# ============================================================


@pytest_asyncio.fixture(scope="function")
async def auth_service(test_session) -> AuthService:
    return AuthService(test_session, user_repository)


@pytest_asyncio.fixture(scope="function")
async def user_service(test_session) -> UserService:
    return UserService(test_session, user_repository)


@pytest_asyncio.fixture(scope="function")
async def chat_service(test_session) -> ChatService:
    return ChatService(test_session, chat_repository)


@pytest_asyncio.fixture(scope="function")
async def message_service(test_session) -> MessageService:
    return MessageService(test_session, message_repository)


# ============================================================
# FIXTURES: HTTP client against the real app (test DB)
# ============================================================


@pytest_asyncio.fixture(scope="function")
async def client(test_engine) -> AsyncGenerator[AsyncClient, None]:
    """
    FastAPI app client. The global `database.session_factory`
    is temporarily replaced with a factory bound to the in-memory
    test engine, so all dependency-injected sessions hit the test DB.
    """
    from database import database  # type: ignore
    from main import app  # type: ignore

    original_factory = database.session_factory
    database.session_factory = async_sessionmaker(
        bind=test_engine,
        autoflush=False,
        autocommit=False,
        expire_on_commit=False,
    )

    transport = ASGITransport(app=app)
    try:
        async with AsyncClient(transport=transport, base_url="http://test") as c:
            yield c
    finally:
        database.session_factory = original_factory
        app.dependency_overrides.clear()
