"""Tests for `core.config` and `core.exceptions`."""

import pytest
from pydantic import ValidationError
from fastapi import status

# ============================================================
# core.config
# ============================================================


class TestServerConfig:
    def test_defaults(self):
        from core.config import ServerConfig  # type: ignore

        cfg = ServerConfig()
        assert cfg.host == "0.0.0.0"
        assert cfg.port == 8000
        assert cfg.reload is False
        assert "http://localhost:3000" in cfg.cors_origins

    def test_custom_values(self):
        from core.config import ServerConfig  # type: ignore

        cfg = ServerConfig(host="127.0.0.1", port=5000, reload=True, cors_origins=["*"])
        assert cfg.host == "127.0.0.1"
        assert cfg.port == 5000
        assert cfg.cors_origins == ["*"]


class TestDatabaseConfig:
    def test_defaults(self):
        from core.config import DatabaseConfig  # type: ignore

        cfg = DatabaseConfig()
        assert cfg.url == ""
        assert cfg.echo is False
        assert cfg.pool_size == 5
        assert cfg.max_overflow == 10
        assert cfg.pool_pre_ping is True


class TestSecurityConfig:
    def test_requires_secret_key(self):
        from core.config import SecurityConfig  # type: ignore

        with pytest.raises(ValidationError):
            SecurityConfig()

    def test_defaults(self):
        from core.config import SecurityConfig  # type: ignore

        cfg = SecurityConfig(secret_key="test-secret")
        assert cfg.algorithm == "HS256"
        assert cfg.access_token_expire_minutes == 30
        assert cfg.refresh_token_expire_days == 30
        assert cfg.environment == "development"


class TestAIConfig:
    def test_defaults(self):
        from core.config import AIConfig  # type: ignore

        cfg = AIConfig()
        assert cfg.api_key == ""
        assert cfg.default_provider == "openai"
        assert cfg.default_model == cfg.openai.models["default"]
        assert "supported" in cfg.openai.models
        assert "default" in cfg.openrouter.models

    def test_openai_models_loaded(self):
        from core.config import AIConfig  # type: ignore

        cfg = AIConfig()
        assert isinstance(cfg.openai.models, dict)
        assert len(cfg.openai.models["supported"]) > 0


class TestDateConfig:
    def test_defaults(self):
        from core.config import DateConfig  # type: ignore

        cfg = DateConfig()
        assert cfg.datetime_format == "%Y-%m-%dT%H:%M:%S"
        assert cfg.date_format == "%Y-%m-%d"


class TestSettings:
    def test_settings_instance(self):
        from core.config import settings  # type: ignore

        assert settings.security.secret_key
        assert settings.server.port == 8000 or settings.server.port is not None
        assert settings.ai.default_provider


# ============================================================
# core.exceptions
# ============================================================


class TestExceptions:
    def _check(self, exc_cls, expected_status, detail="Some error", headers=None):
        exc = exc_cls(detail=detail, headers=headers)
        assert exc.status_code == expected_status
        assert exc.detail == detail
        if headers:
            assert exc.headers == headers

    def test_duplicated_error(self):
        from core.exceptions import DuplicatedError  # type: ignore

        self._check(DuplicatedError, status.HTTP_400_BAD_REQUEST)

    def test_auth_error(self):
        from core.exceptions import AuthError  # type: ignore

        self._check(AuthError, status.HTTP_403_FORBIDDEN)

    def test_permission_denied_error(self):
        from core.exceptions import PermissionDeniedError  # type: ignore

        self._check(PermissionDeniedError, status.HTTP_403_FORBIDDEN)

    def test_not_found_error(self):
        from core.exceptions import NotFoundError  # type: ignore

        self._check(NotFoundError, status.HTTP_404_NOT_FOUND)

    def test_http_not_implemented_error(self):
        from core.exceptions import HTTPNotImplementedError  # type: ignore

        self._check(HTTPNotImplementedError, status.HTTP_501_NOT_IMPLEMENTED)

    def test_validation_error(self):
        from core.exceptions import ValidationError  # type: ignore

        self._check(ValidationError, status.HTTP_422_UNPROCESSABLE_CONTENT)

    def test_invalid_token_type_error(self):
        from core.exceptions import InvalidTokenTypeError  # type: ignore

        exc = InvalidTokenTypeError()
        assert exc.status_code == status.HTTP_400_BAD_REQUEST
        assert exc.detail == "Invalid token type. Must be 'access' or 'refresh'"
        # custom detail
        self._check(InvalidTokenTypeError, status.HTTP_400_BAD_REQUEST, detail="boom")

    def test_provider_management_error(self):
        from core.exceptions import ProviderManagementError  # type: ignore

        self._check(ProviderManagementError, status.HTTP_422_UNPROCESSABLE_CONTENT)

    def test_ai_service_error(self):
        from core.exceptions import AIServiceError  # type: ignore

        self._check(AIServiceError, status.HTTP_502_BAD_GATEWAY)

    def test_ai_generation_error(self):
        from core.exceptions import AIGenerationError, AIStreamGenerationError  # type: ignore

        self._check(AIGenerationError, status.HTTP_502_BAD_GATEWAY)
        assert issubclass(AIStreamGenerationError, AIGenerationError)
