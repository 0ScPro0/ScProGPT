"""
Глобальные фикстуры для pytest.

Этот файл содержит фикстуры, доступные во всех тестах.
Фикстуры — это предварительно настроенные объекты, которые
переиспользуются между тестами (сессия БД, тестовые данные, моки).
"""

import pytest
import pytest_asyncio
from typing import AsyncGenerator
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.pool import StaticPool

from database.models.base import Base
from database.models.user import User
from database.models.chat import Chat
from database.models.message import Message
from database.crud.user import CRUDUser, user_crud
from database.crud.chat import CRUDChat, chat_crud
from database.crud.message import CRUDMessage, message_crud
from services.auth import AuthService
from core.config import settings
from core.security import hash_password, create_access_token, create_refresh_token
from schemas.auth import SignUpRequest, SignInRequest


# ============================================================
# ТЕСТОВАЯ БАЗА ДАННЫХ (SQLite in-memory)
# ============================================================


@pytest.fixture(scope="session")
def anyio_backend():
    """Используем asyncio бэкенд для async тестов"""
    return "asyncio"


@pytest.fixture(scope="session")
def test_db_url():
    """
    URL для тестовой БД — SQLite в памяти.
    Не требует установки PostgreSQL.
    """
    return "sqlite+aiosqlite:///:memory:"


@pytest_asyncio.fixture(scope="function")
async def test_engine(test_db_url):
    """
    Создаёт движок тестовой БД.
    scope="function" — новая БД для каждого теста.
    """
    engine = create_async_engine(
        url=test_db_url,
        echo=False,
        poolclass=StaticPool,  # Один пул для всей сессии
    )

    # Создаём все таблицы
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    yield engine

    # Удаляем все таблицы после теста
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

    await engine.dispose()


@pytest_asyncio.fixture(scope="function")
async def test_session(test_engine) -> AsyncGenerator[AsyncSession, None]:
    """
    Возвращает сессию тестовой БД.
    Автоматически делает rollback после теста — данные не сохраняются.
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
# FIXTURES: CRUD-объекты
# ============================================================


@pytest.fixture
def user_crud_instance():
    """Экземпляр CRUDUser для использования в сервисах"""
    return CRUDUser(User)


@pytest.fixture
def chat_crud_instance():
    """Экземпляр CRUDChat для использования в сервисах"""
    return CRUDChat(Chat)


# ============================================================
# FIXTURES: Тестовые данные (фабрики)
# ============================================================


@pytest.fixture
def unique_email():
    """
    Генерирует уникальный email для каждого теста.
    Используется через pytest generate unique values.
    """
    import uuid

    return f"test_{uuid.uuid4().hex[:8]}@example.com"


@pytest.fixture
def user_data_factory():
    """
    Фабрика данных для создания пользователя.
    Каждый вызов генерирует УНИКАЛЬНЫЕ email и username.
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
    """Фабрика SignUpRequest для тестов авторизации"""

    def _make_signup_request(**overrides):
        data = user_data_factory(**overrides)
        return SignUpRequest(**data)

    return _make_signup_request


@pytest.fixture
def signin_request_factory(user_data_factory):
    """Фабрика SignInRequest для тестов авторизации"""

    def _make_signin_request(**overrides):
        email = overrides.get("email", user_data_factory()["email"])
        password = overrides.get("password", user_data_factory()["password"])
        return SignInRequest(email=email, password=password)

    return _make_signin_request


# ============================================================
# FIXTURES: Сервисы
# ============================================================


@pytest_asyncio.fixture
async def auth_service(test_session, user_crud_instance):
    """
    Экземпляр AuthService с тестовой сессией БД.
    Используется в integration тестах авторизации.
    """
    return AuthService(session=test_session, user_crud=user_crud_instance)


# ============================================================
# FIXTURES: Готовые пользователи в БД
# ============================================================


@pytest_asyncio.fixture
async def test_user_in_db(test_session, user_data_factory):
    """
    Создаёт пользователя в тестовой БД и возвращает его.
    Пароль хешируется.
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
    """Созёт суперпользователя в тестовой БД"""
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
# FIXTURES: Тестовые чаты
# ============================================================


@pytest_asyncio.fixture
async def test_chat_in_db(test_session, test_user_in_db):
    """Создаёт чат в БД, привязанный к test_user_in_db"""
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
