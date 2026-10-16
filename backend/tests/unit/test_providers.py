"""Tests for AI providers: BaseProvider, OpenAIProvider, OpenRouterProvider."""

from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from openai import AsyncOpenAI

from core.exceptions import AIGenerationError  # type: ignore
from services.ai.providers.base_provider import BaseProvider  # type: ignore
from services.ai.providers.openai_provider import OpenAIProvider  # type: ignore
from services.ai.providers.openrouter_provider import OpenRouterProvider  # type: ignore
from schemas.ai import (  # type: ignore
    ProviderResponse,
    ProviderResponseStream,
    ProviderResponseChunk,
    UserMessage,
    AssistantMessage,
)


class ConcreteProvider(BaseProvider):
    """Concrete subclass used to instantiate BaseProvider in tests."""

    async def generate_text(self, messages, model, **kwargs):
        return ProviderResponse()

    async def generate_stream(self, messages, model, **kwargs):
        yield ProviderResponseChunk()
        return


class TestBaseProvider:
    @pytest.fixture
    def provider(self):
        p = ConcreteProvider()
        p.supported_models = ["gpt-4", "gpt-4o-mini"]
        p.default_model = "gpt-4o-mini"
        p.provider_name = "test"
        p.prefix = "test/v1"
        p.requires_v1_prefix = False
        p.v1_provider_pattern = rf"^{p.provider_name}/v1(?:/.*)?$"
        p.provider_pattern = rf"^{p.provider_name}(?:/.*)?$"
        return p

    async def test_init_defaults(self):
        p = ConcreteProvider()
        assert p.supported_models == []
        assert p.provider_name == "base"
        assert p.prefix == "openai/v1"
        assert p.default_model == "gpt-4o-mini"

    async def test_is_model_supports(self, provider):
        assert await provider.is_model_supports("gpt-4") is True
        assert await provider.is_model_supports("unknown") is False

    async def test_get_supported_models_returns_copy(self, provider):
        result = await provider.get_supported_models()
        assert result == ["gpt-4", "gpt-4o-mini"]
        result.append("extra")
        assert "extra" not in provider.supported_models

    async def test_add_supports_model(self, provider):
        assert await provider.add_supports_model("gpt-4") is True
        assert "gpt-4" in provider.supported_models
        assert await provider.add_supports_model("not-a-model") is False

    async def test_validate_model(self, provider):
        assert await provider.validate_model("gpt-4") == "gpt-4"
        # stripped of slashes
        assert await provider.validate_model("/gpt-4/") == "gpt-4"
        assert await provider.validate_model("unknown") is None

    async def test_set_prefix(self, provider):
        assert await provider.set_prefix("test/v2") == "test/v2"
        assert await provider.set_prefix("wrong/prefix") is None

    async def test_validate_prefix_current(self, provider):
        assert await provider.validate_prefix() == "test/v1"
        assert await provider.validate_prefix(None) == "test/v1"

    async def test_validate_prefix_invalid(self, provider):
        assert await provider.validate_prefix("nope/other") is None
        assert await provider.validate_prefix("") is None
        assert await provider.validate_prefix(123) is None

    async def test_validate_prefix_v1_pattern(self, provider):
        provider.requires_v1_prefix = True
        provider.prefix = "openaiv1"
        provider.provider_name = "openai"
        provider.v1_provider_pattern = rf"^{provider.provider_name}/v1(?:/.*)?$"
        provider.provider_pattern = rf"^{provider.provider_name}(?:/.*)?$"
        assert await provider.validate_prefix("openai/v1") == "openai/v1"
        assert await provider.validate_prefix("openai/v2") is None


class _FakeChoice:
    def __init__(self, content):
        self.message = SimpleNamespace(content=content)
        self.delta = SimpleNamespace(content=content)


class _FakeResponse:
    def __init__(self, content, usage):
        self.choices = [_FakeChoice(content)]
        self.usage = SimpleNamespace(
            prompt_tokens=usage[0], completion_tokens=usage[1], total_tokens=usage[2]
        )


class _FakeStreamChunk:
    def __init__(self, content=None, usage=None, has_choices=True):
        self.choices = (
            []
            if not has_choices
            else [SimpleNamespace(delta=SimpleNamespace(content=content))]
        )
        self.usage = (
            SimpleNamespace(
                prompt_tokens=usage[0],
                completion_tokens=usage[1],
                total_tokens=usage[2],
            )
            if usage
            else None
        )


def messages():
    return [
        UserMessage(content="hi"),
        AssistantMessage(content="hello there"),
    ]


class TestOpenAIProvider:
    @pytest.fixture
    def provider(self):
        p = OpenAIProvider()
        p.client = MagicMock()
        p.client.chat.completions.create = AsyncMock()
        return p

    async def test_generate_text(self, provider):
        provider.client.chat.completions.create.return_value = _FakeResponse(
            "Hello!", (10, 5, 15)
        )
        result = await provider.generate_text(messages=messages(), model="gpt-4")
        assert isinstance(result, ProviderResponse)
        assert result.message.content == "Hello!"
        assert result.usage["total_tokens"] == 15
        assert result.model == "gpt-4"
        assert result.provider == "openai"

    async def test_generate_text_error(self, provider):
        provider.client.chat.completions.create.side_effect = RuntimeError("api down")
        with pytest.raises(AIGenerationError):
            await provider.generate_text(messages=messages(), model="gpt-4")

    async def test_generate_stream_chunks(self, provider):
        stream_chunks = [
            _FakeStreamChunk(content="Hel"),
            _FakeStreamChunk(content="lo"),
            _FakeStreamChunk(has_choices=False),
            _FakeStreamChunk(content=None, usage=(5, 7, 12), has_choices=False),
            _FakeStreamChunk(content=" world"),
        ]

        async def fake_stream(*args, **kwargs):
            for c in stream_chunks:
                yield c

        provider.client.chat.completions.create.return_value = fake_stream()
        collected = [
            chunk
            async for chunk in provider.generate_stream(
                messages=messages(), model="gpt-4"
            )
        ]
        chunks = [c for c in collected if isinstance(c, ProviderResponseChunk)]
        assert len(chunks) == 3
        assert "".join(c.content for c in chunks) == "Hello world"
        final = collected[-1]
        assert isinstance(final, ProviderResponseStream)
        assert final.message.content == "Hello world"
        assert final.usage["total_tokens"] == 12

    async def test_generate_stream_error(self, provider):
        async def broken(*args, **kwargs):
            raise RuntimeError("stream broke")
            yield  # pragma: no cover

        provider.client.chat.completions.create.side_effect = broken
        collected = [
            chunk
            async for chunk in provider.generate_stream(
                messages=messages(), model="gpt-4"
            )
        ]
        # First chunk encodes the error
        assert "ERROR" in collected[0].content
        assert isinstance(collected[-1], ProviderResponseStream)


class TestOpenRouterProvider:
    @pytest.fixture
    def provider(self):
        p = OpenRouterProvider()
        p.client = MagicMock()
        p.client.chat.completions.create = AsyncMock()
        return p

    async def test_generate_text(self, provider):
        provider.client.chat.completions.create.return_value = _FakeResponse(
            "Hi", (1, 2, 3)
        )
        result = await provider.generate_text(messages=messages(), model="m1")
        assert isinstance(result, ProviderResponse)
        assert result.message.content == "Hi"
        assert result.provider == "openrouter"

    async def test_generate_text_error(self, provider):
        provider.client.chat.completions.create.side_effect = Exception("boom")
        with pytest.raises(AIGenerationError):
            await provider.generate_text(messages=messages(), model="m1")

    async def test_generate_stream(self, provider):
        stream_chunks = [
            _FakeStreamChunk(content="A"),
            _FakeStreamChunk(content="B"),
            _FakeStreamChunk(content="C", usage=(1, 2, 3)),
        ]

        async def fake_stream(*args, **kwargs):
            for c in stream_chunks:
                yield c

        provider.client.chat.completions.create.return_value = fake_stream()
        collected = [
            chunk
            async for chunk in provider.generate_stream(messages=messages(), model="m1")
        ]
        assert isinstance(collected[-1], ProviderResponseStream)
        assert collected[-1].message.content == "ABC"
