"""Tests for `services.ai.service.AIService`."""

from unittest.mock import AsyncMock, MagicMock

import pytest

from core.exceptions import AIServiceError  # type: ignore
from services.ai.service import AIService  # type: ignore
from schemas.ai import (  # type: ignore
    ProviderResponse,
    ProviderResponseChunk,
    ProviderResponseStream,
    ProviderInfo,
    ProviderStatus,
    UserMessage,
    AssistantMessage,
    AIServiceStatusResponse,
    ProviderListResponse,
    ProviderDetailResponse,
    ModelListResponse,
)
from schemas.base import OperationResponse  # type: ignore


@pytest.fixture
def service():
    s = AIService.__new__(AIService)
    s.session = MagicMock()
    s.provider_manager = MagicMock()
    return s


def messages():
    return [UserMessage(content="hi")]


class FakeProvider:
    provider_name = "openai"

    async def generate_text(self, messages, model, temperature, max_tokens):
        return ProviderResponse(message=AssistantMessage(content="resp"), model=model)

    async def generate_stream(self, messages, model, temperature, max_tokens):
        yield ProviderResponseChunk(content="a")
        yield ProviderResponseStream(message=AssistantMessage(content="ab"))


class TestGenerateText:
    async def test_generate_text_ok(self, service):
        provider = FakeProvider()
        service._resolve_provider = AsyncMock(return_value=provider)
        service._resolve_model = AsyncMock(return_value="gpt-4")
        result = await service.generate_text(
            chat_id=1, messages=messages(), model="gpt-4"
        )
        assert isinstance(result, ProviderResponse)
        assert result.message.content == "resp"
        assert result.model == "gpt-4"


class TestGenerateStream:
    async def test_generate_stream_ok(self, service):
        provider = FakeProvider()
        service._resolve_provider = AsyncMock(return_value=provider)
        service._resolve_model = AsyncMock(return_value="gpt-4")
        collected = [
            chunk
            async for chunk in service.generate_stream(chat_id=1, messages=messages())
        ]
        assert len(collected) == 2
        assert isinstance(collected[-1], ProviderResponseStream)


def provider_mock(name="openai"):
    p = MagicMock()
    p.provider_name = name
    return p


class TestSetProvider:
    async def test_ok(self, service):
        old = provider_mock("openai")
        service.provider_manager.get_current_provider = AsyncMock(return_value=old)
        service.provider_manager.is_provider_available = AsyncMock(return_value=True)
        service.provider_manager.set_provider = AsyncMock()
        result = await service.set_provider(chat_id=1, provider_name="openrouter")
        assert isinstance(result, OperationResponse)
        assert result.success is True
        assert result.new_value == "openrouter"

    async def test_unavailable(self, service):
        service.provider_manager.get_current_provider = AsyncMock(
            return_value=provider_mock("openai")
        )
        service.provider_manager.is_provider_available = AsyncMock(return_value=False)
        with pytest.raises(AIServiceError):
            await service.set_provider(chat_id=1, provider_name="unknown")


class TestSetModel:
    async def test_ok(self, service):
        service.provider_manager.get_current_model = AsyncMock(return_value="old")
        service.provider_manager.is_model_available = AsyncMock(return_value=True)
        service.provider_manager.set_model = AsyncMock(return_value=True)
        result = await service.set_model(chat_id=1, model_name="new-model")
        assert result.success is True
        assert result.new_value == "new-model"

    async def test_unavailable(self, service):
        service.provider_manager.get_current_model = AsyncMock(return_value="m")
        service.provider_manager.is_model_available = AsyncMock(return_value=False)
        with pytest.raises(AIServiceError):
            await service.set_model(chat_id=1, model_name="no-model")


class TestSetProviderAndModel:
    async def test_switch_both(self, service):
        service.provider_manager.get_current_provider = AsyncMock(
            return_value=provider_mock("openai")
        )
        service.provider_manager.get_current_model = AsyncMock(return_value="m1")
        service.provider_manager.is_provider_available = AsyncMock(return_value=True)
        service.provider_manager.is_model_available = AsyncMock(return_value=True)
        service.provider_manager.set_provider = AsyncMock()
        service.provider_manager.set_model = AsyncMock()
        result = await service.set_provider_and_model(
            1, provider_name="openrouter", model_name="m2"
        )
        assert result.success is True

    async def test_no_changes(self, service):
        service.provider_manager.get_current_provider = AsyncMock(
            return_value=provider_mock("openai")
        )
        service.provider_manager.get_current_model = AsyncMock(return_value="m1")
        result = await service.set_provider_and_model(1)
        assert result.message == "No changes requested"

    async def test_bad_provider(self, service):
        service.provider_manager.get_current_provider = AsyncMock(
            return_value=provider_mock("openai")
        )
        service.provider_manager.get_current_model = AsyncMock(return_value="m1")
        service.provider_manager.is_provider_available = AsyncMock(return_value=False)
        with pytest.raises(AIServiceError):
            await service.set_provider_and_model(1, provider_name="bad")


class TestResetToDefaults:
    async def test_ok(self, service):
        service.provider_manager.get_current_provider = AsyncMock(
            return_value=provider_mock("old")
        )
        service.provider_manager.get_current_model = AsyncMock(
            side_effect=["old", "new"]
        )
        service.provider_manager.reset_to_defaults = AsyncMock()
        result = await service.reset_to_defaults(1)
        assert result.success is True


class TestInformation:
    async def test_get_status_configured(self, service):
        service.provider_manager.get_status = AsyncMock(
            return_value=ProviderStatus(
                current_provider="openai",
                current_model="gpt-4",
                available_providers=["openai"],
                registered_providers=["openai", "google"],
            )
        )
        result = await service.get_status(1)
        assert isinstance(result, AIServiceStatusResponse)
        assert result.is_configured is True

    async def test_get_status_not_configured(self, service):
        service.provider_manager.get_status = AsyncMock(
            return_value=ProviderStatus(
                current_provider="openai",
                current_model="gpt-4",
                available_providers=["openai"],
                registered_providers=[],
            )
        )
        result = await service.get_status(1)
        assert result.is_configured is False

    async def test_get_providers(self, service):
        service.provider_manager.get_available_providers = AsyncMock(
            return_value={"openai", "google"}
        )
        service.provider_manager.get_current_provider = AsyncMock(
            return_value=provider_mock("openai")
        )
        result = await service.get_providers(1)
        assert isinstance(result, ProviderListResponse)
        assert result.providers == ["google", "openai"]
        assert result.current_provider == "openai"

    async def test_get_provider_info_ok(self, service):
        info = ProviderInfo(
            name="openai",
            prefix="openai/v1",
            supported_models=["gpt-4"],
            current_model="gpt-4",
        )
        service.provider_manager.get_provider_info = AsyncMock(return_value=info)
        service.provider_manager.get_current_provider = AsyncMock(
            return_value=provider_mock("openai")
        )
        result = await service.get_provider_info(1)
        assert isinstance(result, ProviderDetailResponse)
        assert result.is_current is True

    async def test_get_provider_info_missing(self, service):
        service.provider_manager.get_provider_info = AsyncMock(return_value=None)
        service.get_current_provider_name = AsyncMock(return_value="openai")
        with pytest.raises(AIServiceError):
            await service.get_provider_info(1)

    class FakeProviderWithModels(FakeProvider):
        async def get_supported_models(self):
            return ["gpt-4", "gpt-4o-mini"]

    async def test_get_models(self, service):
        provider = self.FakeProviderWithModels()
        service.get_current_provider_name = AsyncMock(return_value="openai")
        service._resolve_provider = AsyncMock(return_value=provider)
        service.provider_manager.get_current_model = AsyncMock(return_value="gpt-4")
        result = await service.get_models(1)
        assert isinstance(result, ModelListResponse)
        assert result.provider == "openai"
        assert result.models == ["gpt-4", "gpt-4o-mini"]

    async def test_get_current_provider_name(self, service):
        service.provider_manager.get_current_provider = AsyncMock(
            return_value=provider_mock("openai")
        )
        assert await service.get_current_provider_name(1) == "openai"

    async def test_get_current_model_name(self, service):
        service.provider_manager.get_current_model = AsyncMock(return_value="gpt-4")
        assert await service.get_current_model_name(1) == "gpt-4"


class TestHelpers:
    async def test_resolve_provider_named(self, service):
        service.provider_manager.is_provider_available = AsyncMock(return_value=True)
        service.provider_manager.get_provider = AsyncMock(
            return_value=provider_mock("x")
        )
        result = await service._resolve_provider(chat_id=1, provider_name="x")
        assert result.provider_name == "x"

    async def test_resolve_provider_unavailable(self, service):
        service.provider_manager.is_provider_available = AsyncMock(return_value=False)
        with pytest.raises(AIServiceError):
            await service._resolve_provider(chat_id=1, provider_name="bad")

    async def test_resolve_provider_current_missing(self, service):
        service.provider_manager.get_current_provider = AsyncMock(return_value=None)
        with pytest.raises(AIServiceError):
            await service._resolve_provider(chat_id=1)

    async def test_resolve_model_named_valid(self, service):
        provider = FakeProvider()
        provider.validate_model = AsyncMock(return_value="gpt-4")  # type: ignore
        result = await service._resolve_model(
            chat_id=1, model_name="gpt-4", provider=provider
        )
        assert result == "gpt-4"

    async def test_resolve_model_named_invalid(self, service):
        provider = FakeProvider()
        provider.validate_model = AsyncMock(return_value=None)  # type: ignore
        with pytest.raises(AIServiceError):
            await service._resolve_model(chat_id=1, model_name="bad", provider=provider)

    async def test_resolve_model_current(self, service):
        service.provider_manager.get_current_provider = AsyncMock(
            return_value=FakeProvider()
        )
        service.provider_manager.get_current_model = AsyncMock(return_value="cur")
        result = await service._resolve_model(chat_id=1, model_name=None)
        assert result == "cur"

    async def test_resolve_model_without_provider(self, service):
        provider = FakeProvider()
        service.provider_manager.get_current_provider = AsyncMock(return_value=provider)
        provider.validate_model = AsyncMock(return_value="gpt-4")  # type: ignore
        result = await service._resolve_model(chat_id=1, model_name="gpt-4")
        assert result == "gpt-4"
