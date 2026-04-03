"""
Integration тесты для AuthService.

Тестируем полный цикл авторизации:
- Регистрация (signup)
- Вход (signin)
- Обновление токена (refresh_token)
- Выход (logout)
- Ошибки авторизации
"""

import pytest
import pytest_asyncio

from core.exceptions import AuthError
from core.security import decode_token, hash_password, verify_password
from schemas.auth import SignUpRequest, SignInRequest


# ============================================================
# ТЕСТЫ: Регистрация (Signup)
# ============================================================

class TestAuthSignup:
    """Тесты регистрации пользователя"""

    @pytest.mark.asyncio
    async def test_signup_success(self, auth_service, signup_request_factory):
        """Успешная регистрация нового пользователя"""
        request = signup_request_factory()

        response = await auth_service.signup(request)

        # Проверяем ответ
        assert response.access_token is not None
        assert response.refresh_token is not None
        assert response.user.email == request.email
        assert response.user.username == request.username
        assert response.access_token_expires_in is not None
        assert response.refresh_token_expires_in is not None

    @pytest.mark.asyncio
    async def test_signup_creates_user_in_db(
        self, auth_service, signup_request_factory, test_session, user_crud
    ):
        """Регистрация создаёт пользователя в БД"""
        request = signup_request_factory()

        await auth_service.signup(request)

        user = await user_crud.get_by_email(test_session, request.email)
        assert user is not None
        assert user.email == request.email

    @pytest.mark.asyncio
    async def test_signup_password_is_hashed(
        self, auth_service, signup_request_factory, test_session, user_crud
    ):
        """Пароль сохраняется в хешированном виде"""
        request = signup_request_factory()

        await auth_service.signup(request)

        user = await user_crud.get_by_email(test_session, request.email)
        assert user.password_hash != request.password
        assert verify_password(request.password, user.password_hash)

    @pytest.mark.asyncio
    async def test_signup_user_is_active_by_default(
        self, auth_service, signup_request_factory, test_session, user_crud
    ):
        """Зарегистрированный пользователь активен"""
        request = signup_request_factory()

        await auth_service.signup(request)

        user = await user_crud.get_by_email(test_session, request.email)
        assert user.is_active is True

    @pytest.mark.asyncio
    async def test_signup_user_is_not_superuser(
        self, auth_service, signup_request_factory, test_session, user_crud
    ):
        """Зарегистрированный пользователь не суперюзер"""
        request = signup_request_factory()

        await auth_service.signup(request)

        user = await user_crud.get_by_email(test_session, request.email)
        assert user.is_superuser is False

    @pytest.mark.asyncio
    async def test_signup_duplicate_email_raises_error(
        self, auth_service, signup_request_factory, test_user_in_db
    ):
        """Регистрация с уже существующим email вызывает ошибку"""
        request = signup_request_factory(email=test_user_in_db.email)

        with pytest.raises(AuthError) as exc_info:
            await auth_service.signup(request)

        assert "already exists" in str(exc_info.value.detail)

    @pytest.mark.asyncio
    async def test_signup_returns_jwt_tokens_with_correct_user_id(
        self, auth_service, signup_request_factory
    ):
        """Токены содержат правильный user_id"""
        request = signup_request_factory()

        response = await auth_service.signup(request)

        access_payload = decode_token(response.access_token)
        refresh_payload = decode_token(response.refresh_token)

        assert access_payload["sub"] == response.user.id
        assert refresh_payload["sub"] == response.user.id

    @pytest.mark.asyncio
    async def test_signup_stores_refresh_token_in_db(
        self, auth_service, signup_request_factory, test_session, user_crud
    ):
        """Refresh токен сохраняется в БД"""
        request = signup_request_factory()

        response = await auth_service.signup(request)

        user = await user_crud.get_by_email(test_session, request.email)
        assert user.refresh_token == response.refresh_token
        assert user.refresh_token_expires_at is not None


# ============================================================
# ТЕСТЫ: Вход (Signin)
# ============================================================

class TestAuthSignin:
    """Тесты входа пользователя"""

    @pytest.mark.asyncio
    async def test_signin_success(self, auth_service, test_user_in_db):
        """Успешный вход с правильными данными"""
        request = SignInRequest(
            email=test_user_in_db.email,
            password="TestPassword123!",  # пароль из фикстуры
        )

        response = await auth_service.signin(request)

        assert response.access_token is not None
        assert response.refresh_token is not None
        assert response.user.id == test_user_in_db.id
        assert response.user.email == test_user_in_db.email

    @pytest.mark.asyncio
    async def test_signin_wrong_password_raises_error(
        self, auth_service, test_user_in_db
    ):
        """Вход с неправильным паролем вызывает ошибку"""
        request = SignInRequest(
            email=test_user_in_db.email,
            password="WrongPassword456!",
        )

        with pytest.raises(AuthError) as exc_info:
            await auth_service.signin(request)

        assert "Invalid credentials" in str(exc_info.value.detail)

    @pytest.mark.asyncio
    async def test_signin_nonexistent_email_raises_error(self, auth_service):
        """Вход с несуществующим email вызывает ошибку"""
        request = SignInRequest(
            email="nonexistent@example.com",
            password="SomePassword123!",
        )

        with pytest.raises(AuthError) as exc_info:
            await auth_service.signin(request)

        assert "Invalid credentials" in str(exc_info.value.detail)

    @pytest.mark.asyncio
    async def test_signin_deactivated_user_raises_error(
        self, auth_service, test_user_in_db, user_crud, test_session
    ):
        """Вход деактивированного пользователя вызывает ошибку"""
        # Деактивируем пользователя
        await user_crud.deactivate(test_session, user_id=test_user_in_db.id)

        request = SignInRequest(
            email=test_user_in_db.email,
            password="TestPassword123!",
        )

        with pytest.raises(AuthError) as exc_info:
            await auth_service.signin(request)

        assert "deactivated" in str(exc_info.value.detail).lower()

    @pytest.mark.asyncio
    async def test_signin_updates_refresh_token_in_db(
        self, auth_service, test_user_in_db, test_session, user_crud
    ):
        """Вход обновляет refresh токен в БД"""
        old_token = "old_refresh_token"
        await user_crud.update_refresh_token(
            test_session, user_id=test_user_in_db.id, refresh_token=old_token,
            expires_at=None,
        )

        request = SignInRequest(
            email=test_user_in_db.email,
            password="TestPassword123!",
        )

        response = await auth_service.signin(request)

        user = await user_crud.get(test_session, test_user_in_db.id)
        assert user.refresh_token == response.refresh_token
        assert user.refresh_token != old_token

    @pytest.mark.asyncio
    async def test_signin_returns_tokens_with_correct_type(
        self, auth_service, test_user_in_db
    ):
        """Токены имеют правильный тип (access/refresh)"""
        request = SignInRequest(
            email=test_user_in_db.email,
            password="TestPassword123!",
        )

        response = await auth_service.signin(request)

        access_payload = decode_token(response.access_token)
        refresh_payload = decode_token(response.refresh_token)

        assert access_payload["type"] == "access"
        assert refresh_payload["type"] == "refresh"


# ============================================================
# ТЕСТЫ: Обновление токена (Refresh)
# ============================================================

class TestAuthRefresh:
    """Тесты обновления токена"""

    @pytest.mark.asyncio
    async def test_refresh_token_success(
        self, auth_service, test_user_in_db, test_session, user_crud
    ):
        """Успешное обновление access токена"""
        from datetime import datetime, timedelta, timezone
        from core.security import create_refresh_token
        from schemas.auth import TokenRefreshRequest

        # Создаём refresh токен
        refresh_token = create_refresh_token({"sub": str(test_user_in_db.id)})
        expires_at = datetime.now(timezone.utc) + timedelta(days=7)

        # Сохраняем в БД
        await user_crud.update_refresh_token(
            test_session,
            user_id=test_user_in_db.id,
            refresh_token=refresh_token,
            expires_at=expires_at,
        )

        request = TokenRefreshRequest(refresh_token=refresh_token)
        response = await auth_service.refresh_token(request)

        assert "access_token" in response
        assert "access_token_expires_in" in response

    @pytest.mark.asyncio
    async def test_refresh_with_fake_token_raises_error(self, auth_service):
        """Обновление с поддельным токеном вызывает ошибку"""
        from schemas.auth import TokenRefreshRequest

        request = TokenRefreshRequest(refresh_token="fake.token.here")

        with pytest.raises(AuthError) as exc_info:
            await auth_service.refresh_token(request)

        assert "Invalid refresh token" in str(exc_info.value.detail)

    @pytest.mark.asyncio
    async def test_refresh_with_wrong_stored_token_raises_error(
        self, auth_service, test_user_in_db, test_session, user_crud
    ):
        """Обновление с токеном, не совпадающим с БД, вызывает ошибку"""
        from datetime import datetime, timedelta, timezone
        from core.security import create_refresh_token
        from schemas.auth import TokenRefreshRequest

        # Создаём один токен
        refresh_token = create_refresh_token({"sub": str(test_user_in_db.id)})
        expires_at = datetime.now(timezone.utc) + timedelta(days=7)

        # Но сохраняем другой
        await user_crud.update_refresh_token(
            test_session,
            user_id=test_user_in_db.id,
            refresh_token="different_stored_token",
            expires_at=expires_at,
        )

        request = TokenRefreshRequest(refresh_token=refresh_token)

        with pytest.raises(AuthError) as exc_info:
            await auth_service.refresh_token(request)

        assert "Invalid refresh token" in str(exc_info.value.detail)


# ============================================================
# ТЕСТЫ: Выход (Logout)
# ============================================================

class TestAuthLogout:
    """Тесты выхода пользователя"""

    @pytest.mark.asyncio
    async def test_logout_clears_refresh_token(
        self, auth_service, test_user_in_db, test_session, user_crud
    ):
        """Logout очищает refresh токен в БД"""
        from datetime import datetime, timedelta, timezone
        from core.security import create_refresh_token

        # Устанавливаем refresh токен
        refresh_token = create_refresh_token({"sub": str(test_user_in_db.id)})
        expires_at = datetime.now(timezone.utc) + timedelta(days=7)
        await user_crud.update_refresh_token(
            test_session,
            user_id=test_user_in_db.id,
            refresh_token=refresh_token,
            expires_at=expires_at,
        )

        # Выходим
        result = await auth_service.logout(test_user_in_db.id)

        assert result is True

        # Проверяем что токен очищен
        user = await user_crud.get(test_session, test_user_in_db.id)
        assert user.refresh_token is None
        assert user.refresh_token_expires_at is None

    @pytest.mark.asyncio
    async def test_logout_nonexistent_user(self, auth_service):
        """Logout несуществующего пользователя не вызывает ошибку"""
        result = await auth_service.logout(99999)

        assert result is True


# ============================================================
# ТЕСТЫ: Edge cases
# ============================================================

class TestAuthEdgeCases:
    """Граничные случаи и дополнительные проверки"""

    @pytest.mark.asyncio
    async def test_signup_and_signin_flow(
        self, auth_service, signup_request_factory, test_session, user_crud
    ):
        """Полный цикл: регистрация → вход"""
        # Регистрируемся
        signup_request = signup_request_factory()
        signup_response = await auth_service.signup(signup_request)

        assert signup_response.user.email == signup_request.email

        # Выходим и входим снова
        signin_request = SignInRequest(
            email=signup_request.email,
            password=signup_request.password,
        )
        signin_response = await auth_service.signin(signin_request)

        assert signin_response.user.id == signup_response.user.id

    @pytest.mark.asyncio
    async def test_multiple_signups_with_different_emails(
        self, auth_service, signup_request_factory
    ):
        """Можно зарегистрировать несколько пользователей"""
        user1 = await auth_service.signup(signup_request_factory())
        user2 = await auth_service.signup(signup_request_factory())

        assert user1.user.id != user2.user.id
        assert user1.user.email != user2.user.email

    @pytest.mark.asyncio
    async def test_signin_returns_same_user_id_as_signup(
        self, auth_service, signup_request_factory
    ):
        """ID пользователя при signup и signin совпадает"""
        signup_response = await auth_service.signup(signup_request_factory())

        signin_request = SignInRequest(
            email=signup_response.user.email,
            password="TestPassword123!",
        )
        signin_response = await auth_service.signin(signin_request)

        assert signup_response.user.id == signin_response.user.id
