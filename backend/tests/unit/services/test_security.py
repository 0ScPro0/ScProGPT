"""
Unit тесты для модуля core/security.py.

Тестируем:
- Хеширование паролей
- Верификацию паролей
- Создание JWT токенов (access/refresh)
- Декодирование токенов
- Истечение срока токенов
"""

import pytest
from datetime import datetime, timedelta, timezone

from core.security import (
    hash_password,
    verify_password,
    create_access_token,
    create_refresh_token,
    decode_token,
    create_token,
)
from core.exceptions import InvalidTokenTypeError
from core.config import settings


# ============================================================
# ТЕСТЫ: Хеширование паролей
# ============================================================

class TestPasswordHashing:
    """Тесты хеширования и верификации паролей"""

    def test_password_is_hashed(self):
        """Пароль после хеширования не равен оригиналу"""
        password = "MySecretPassword123!"
        hashed = hash_password(password)

        assert hashed != password

    def test_same_password_different_hashes(self):
        """Один и тот же пароль даёт разные хеши (bcrypt использует соль)"""
        password = "MySecretPassword123!"
        hash1 = hash_password(password)
        hash2 = hash_password(password)

        assert hash1 != hash2  # Соль каждый раз разная

    def test_verify_correct_password(self):
        """Верный пароль проходит верификацию"""
        password = "MySecretPassword123!"
        hashed = hash_password(password)

        assert verify_password(password, hashed) is True

    def test_verify_wrong_password(self):
        """Неверный пароль не проходит верификацию"""
        hashed = hash_password("CorrectPassword123!")

        assert verify_password("WrongPassword456!", hashed) is False

    def test_empty_password_fails(self):
        """Пустой пароль не проходит верификацию"""
        hashed = hash_password("NotEmptyPassword123!")

        assert verify_password("", hashed) is False

    def test_hash_is_string(self):
        """Хеш — это строка"""
        hashed = hash_password("TestPassword123!")

        assert isinstance(hashed, str)

    def test_hash_starts_with_bcrypt_identifier(self):
        """bcrypt хеш начинается с $2b$"""
        hashed = hash_password("TestPassword123!")

        assert hashed.startswith("$2b$")


# ============================================================
# ТЕСТЫ: JWT токены
# ============================================================

class TestJWTTokenCreation:
    """Тесты создания JWT токенов"""

    def test_create_access_token_returns_string(self):
        """Access token — это строка"""
        token = create_access_token({"sub": "1"})

        assert isinstance(token, str)

    def test_create_refresh_token_returns_string(self):
        """Refresh token — это строка"""
        token = create_refresh_token({"sub": "1"})

        assert isinstance(token, str)

    def test_access_token_decodes_successfully(self):
        """Access token успешно декодируется"""
        token = create_access_token({"sub": "42"})
        payload = decode_token(token)

        assert payload is not None
        assert payload["sub"] == "42"

    def test_refresh_token_decodes_successfully(self):
        """Refresh token успешно декодируется"""
        token = create_refresh_token({"sub": "42"})
        payload = decode_token(token)

        assert payload is not None
        assert payload["sub"] == "42"

    def test_access_token_has_correct_type(self):
        """Access token имеет type='access'"""
        token = create_access_token({"sub": "1"})
        payload = decode_token(token)

        assert payload["type"] == "access"

    def test_refresh_token_has_correct_type(self):
        """Refresh token имеет type='refresh'"""
        token = create_refresh_token({"sub": "1"})
        payload = decode_token(token)

        assert payload["type"] == "refresh"

    def test_token_contains_expiration(self):
        """Токен содержит поле exp (expiration)"""
        token = create_access_token({"sub": "1"})
        payload = decode_token(token)

        assert "exp" in payload

    def test_token_contains_issued_at(self):
        """Токен содержит поле iat (issued at)"""
        token = create_access_token({"sub": "1"})
        payload = decode_token(token)

        assert "iat" in payload

    def test_token_expiration_is_in_future(self):
        """Токен не просрочен сразу после создания"""
        token = create_access_token({"sub": "1"})
        payload = decode_token(token)

        assert payload["exp"] > datetime.now(timezone.utc).timestamp()

    def test_custom_expires_delta(self):
        """Можно задать кастомное время жизни токена"""
        delta = timedelta(hours=1)
        token = create_access_token({"sub": "1"}, expires_delta=delta)
        payload = decode_token(token)

        expected_max = (datetime.now(timezone.utc) + delta).timestamp()
        # exp должен быть примерно через 1 час (с допуском 5 секунд)
        assert payload["exp"] <= expected_max + 5


# ============================================================
# ТЕСТЫ: Невалидные токены
# ============================================================

class TestInvalidTokenType:
    """Тесты невалидных типов токенов"""

    def test_invalid_token_type_raises_error(self):
        """create_token с неверным типом выбрасывает ошибку"""
        with pytest.raises(InvalidTokenTypeError):
            create_token({"sub": "1"}, token_type="invalid")

    def test_decode_fake_token_returns_none(self):
        """Декодирование поддельного токена возвращает None"""
        fake_token = "this.is.not.a.jwt"
        result = decode_token(fake_token)

        assert result is None

    def test_decode_empty_string_returns_none(self):
        """Декодирование пустой строки возвращает None"""
        result = decode_token("")

        assert result is None


# ============================================================
# ТЕСТЫ: Истечение срока токена
# ============================================================

class TestTokenExpiration:
    """Тесты истечения срока токенов"""

    def test_expired_token_decodes_to_none(self):
        """Просроченный токен при декодировании возвращает None"""
        # Создаём токен с отрицательным временем (уже просрочен)
        delta = timedelta(seconds=-1)
        token = create_access_token({"sub": "1"}, expires_delta=delta)

        # Даём время на обработку
        import time
        time.sleep(0.1)

        result = decode_token(token)
        assert result is None

    def test_access_token_default_expiration(self):
        """Access token имеет дефолтное время жизни из настроек"""
        token = create_access_token({"sub": "1"})
        payload = decode_token(token)

        expected_expires = (
            datetime.now(timezone.utc)
            + timedelta(minutes=settings.security.access_token_expire_minutes)
        ).timestamp()

        # Допуск 5 секунд
        assert abs(payload["exp"] - expected_expires) < 5

    def test_refresh_token_default_expiration(self):
        """Refresh token имеет дефолтное время жизни из настроек"""
        token = create_refresh_token({"sub": "1"})
        payload = decode_token(token)

        expected_expires = (
            datetime.now(timezone.utc)
            + timedelta(days=settings.security.refresh_token_expire_days)
        ).timestamp()

        # Допуск 5 секунд
        assert abs(payload["exp"] - expected_expires) < 5
