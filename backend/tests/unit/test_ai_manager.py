"""Tests for `services.ai.manager.ProviderManager`."""

from unittest.mock import AsyncMock, MagicMock

import pytest

from core.exceptions import (  # type: ignore
    NotFoundError,
    ProviderManagementError,
    HTTPNotImplementedError,
)
from services.ai.manager import ProviderManager, NotImplementedProvider  # type: ignore
from services.ai.providers import OpenAIProvider  # type: ignore
from schemas.ai import ProviderInfo, ProviderStatus  # type: ignore


@pytest.fixture
def manager(monkeypatch):
    m = ProviderManager(session=MagicMock())
    fake = MagicMock()
    fake.get_chat_provider = AsyncMock(return_value="openai")
    fake.get_chat_model = AsyncMock(return_value="gpt-4o-mini")
    m.chat_repository = fake
    # ProviderManager.get_provider reads the module-level `chat_repository`
    monkeypatch.setattr("services.ai.manager.chat_repository", fake)
    return m


class TestNotImplementedProvider:
    def test_attribute_access_raises(self):
        p = NotImplementedProvider("google")
        with pytest.raises(HTTPNotImplementedError):
            p.some_method()

    def test_call_raises(self):
        p = NotImplementedProvider("google")
        with pytest.raises(HTTPNotImplementedError):
            p()


class TestProviderManagerInit:
    def test_available_providers(self):
        m = ProviderManager(session=MagicMock())
        assert m._available_providers == {"openai", "openrouter", "google", "anthropic"}
        assert set(m.providers.keys()) == {
            "openai",
            "openrouter",
            "google",
            "anthropic",
        }
        assert isinstance(m.providers["openai"], OpenAIProvider)


class TestGetProvider:
    async def test_get_existing(self, manager):
        manager.chat_repository.get_chat_provider = AsyncMock(return_value="openai")
        provider = await manager.get_provider(chat_id=1)
        assert isinstance(provider, OpenAIProvider)

    async def test_get_unavailable(self, manager):
        manager.chat_repository.get_chat_provider = AsyncMock(return_value="unknown")
        with pytest.raises(NotFoundError):
            await manager.get_provider(chat_id=1)

    async def test_get_current_provider(self, manager):
        manager.chat_repository.get_chat_provider = AsyncMock(return_value="openai")
        provider = await manager.get_current_provider(1)
        assert provider.provider_name == "openai"


class TestSetProvider:
    async def test_set_provider_ok(self, manager):
        manager.is_provider_available = AsyncMock(return_value=True)
        manager.get_current_model = AsyncMock(return_value="gpt-4o-mini")
        manager.is_model_available = AsyncMock(return_value=True)
        manager.chat_repository.update_chat_provider_and_model = AsyncMock()
        result = await manager.set_provider(1, "openai")
        assert result is True
        manager.chat_repository.update_chat_provider_and_model.assert_awaited_once()

    async def test_set_provider_unavailable(self, manager):
        manager.is_provider_available = AsyncMock(return_value=False)
        with pytest.raises(NotFoundError):
            await manager.set_provider(1, "unknown")

    async def test_set_provider_error(self, manager):
        manager.is_provider_available = AsyncMock(return_value=True)
        manager.get_current_model = AsyncMock(return_value="gpt-4o-mini")
        manager.is_model_available = AsyncMock(return_value=True)
        manager.chat_repository.update_chat_provider_and_model = AsyncMock(
            side_effect=Exception("db")
        )
        with pytest.raises(ProviderManagementError):
            await manager.set_provider(1, "openai")


class TestAvailability:
    async def test_is_provider_available(self, manager):
        assert await manager.is_provider_available("openai") is True
        assert await manager.is_provider_available("unknown") is False

    async def test_get_available_providers(self, manager):
        result = await manager.get_available_providers()
        assert result == {"openai", "openrouter", "google", "anthropic"}
        # copy semantics
        result.add("x")
        assert "x" not in manager._available_providers

    async def test_get_registered_providers(self, manager):
        result = await manager.get_registered_providers()
        assert set(result) == {"openai", "openrouter", "google", "anthropic"}


class TestProviderInfo:
    async def test_get_provider_info_openai(self, manager):
        manager.get_current_model = AsyncMock(return_value="gpt-4o-mini")
        info = await manager.get_provider_info(1, "openai")
        assert isinstance(info, ProviderInfo)
        assert info.name == "openai"
        assert info.current_model == "gpt-4o-mini"

    async def test_get_provider_info_not_implemented(self, manager):
        info = await manager.get_provider_info(1, "google")
        assert info is None

    async def test_get_provider_info_unknown(self, manager):
        info = await manager.get_provider_info(1, "nope")
        assert info is None


class TestHelpers:
    async def test_find_provider(self, manager):
        provider = await manager._find_provider("openai")
        assert provider.provider_name == "openai"
        assert await manager._find_provider("unknown") is None

    async def test_validate_provider_name_str(self, manager):
        manager.get_current_provider = AsyncMock(
            return_value=manager.providers["openai"]
        )
        provider = await manager._validate_provider(1, "openrouter")
        assert provider.provider_name == "openrouter"

    async def test_validate_provider_instance(self, manager):
        manager.get_current_provider = AsyncMock(
            return_value=manager.providers["openai"]
        )
        provider = await manager._validate_provider(1, manager.providers["openrouter"])
        assert provider.provider_name == "openrouter"

    async def test_validate_provider_none(self, manager):
        manager.get_current_provider = AsyncMock(
            return_value=manager.providers["openai"]
        )
        provider = await manager._validate_provider(1, None)
        assert provider.provider_name == "openai"


class TestModelsManagement:
    async def test_set_model_ok(self, manager):
        manager.is_model_available = AsyncMock(return_value=True)
        manager.chat_repository.update_chat_model = AsyncMock()
        assert await manager.set_model(1, "gpt-4o-mini") is True
        manager.chat_repository.update_chat_model.assert_awaited_once()

    async def test_set_model_not_available(self, manager):
        manager.is_model_available = AsyncMock(return_value=False)
        assert await manager.set_model(1, "bad") is False

    async def test_set_model_error(self, manager):
        manager.is_model_available = AsyncMock(side_effect=Exception("boom"))
        with pytest.raises(ProviderManagementError):
            await manager.set_model(1, "gpt-4")

    async def test_get_current_model(self, manager):
        manager.chat_repository.get_chat_model = AsyncMock(return_value="gpt-4")
        assert await manager.get_current_model(1) == "gpt-4"

    async def test_get_model(self, manager):
        provider = manager.providers["openai"]
        manager._validate_provider = AsyncMock(return_value=provider)
        validated = await manager.get_model(1, "gpt-4o-mini")
        assert validated == "gpt-4o-mini"

    async def test_is_model_available_true(self, manager):
        provider = manager.providers["openai"]
        manager._validate_provider = AsyncMock(return_value=provider)
        result = await manager.is_model_available(1, provider.default_model)
        assert isinstance(result, bool)

    async def test_is_model_available_false_for_unknown(self, manager):
        provider = manager.providers["openai"]
        manager._validate_provider = AsyncMock(return_value=provider)
        assert await manager.is_model_available(1, "totally-not-a-model") is False


class TestResetAndStatus:
    async def test_reset_to_defaults(self, manager):
        manager.set_provider = AsyncMock()
        manager.set_model = AsyncMock()
        assert await manager.reset_to_defaults(1) is True
        manager.set_provider.assert_awaited_once()
        manager.set_model.assert_awaited_once()

    async def test_reset_to_defaults_error(self, manager):
        manager.set_provider = AsyncMock(side_effect=Exception("boom"))
        with pytest.raises(ProviderManagementError):
            await manager.reset_to_defaults(1)

    async def test_get_status(self, manager):
        provider = manager.providers["openai"]
        manager.get_current_provider = AsyncMock(return_value=provider)
        manager.get_current_model = AsyncMock(return_value="gpt-4o-mini")
        status = await manager.get_status(1)
        assert isinstance(status, ProviderStatus)
        assert status.current_provider == "openai"
        assert status.current_model == "gpt-4o-mini"
        assert "openai" in status.available_providers
