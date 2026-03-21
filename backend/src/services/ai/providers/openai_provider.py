from openai import AsyncOpenAI
from typing import Union, AsyncGenerator, List

from core.config import settings
from core.exceptions import AIGenerationError, AIStreamGenerationError
from utils.logger import log
from schemas.ai import (
    AssistantMessage,
    UserMessage,
    ProviderResponse,
    ProviderResponseStream,
    ProviderResponseChunk,
)
from .base_provider import BaseProvider


Message = Union[AssistantMessage, UserMessage]


class OpenAIProvider(BaseProvider):
    def __init__(self) -> None:
        super().__init__()
        self.provider_name = "openai"
        self.prefix = "openai/v1"
        self.requires_v1_prefix = True
        self.base_url = settings.ai.base_url + self.prefix
        self.client = AsyncOpenAI(api_key=settings.ai.api_key, base_url=self.base_url)
        self._available_models = settings.ai.openai.models
        self.supported_models = settings.ai.openai.models["supports"]

    @log
    async def generate_text(
        self,
        *,
        messages: List[Message],
        model: str,
        temperature: float = 1,
        max_tokens: int = 4096,
    ) -> ProviderResponse:
        """
        Generate and return full response immediately

        Args:
            messages: chat context, list of dicts of messages and roles
            model: AI model
            temperature: the degree of randomness and creativity of the generated text
            max_tokens: max tokens for response

        Returns:
            provider response as ProviderResponse object
        """
        # Dump messages to dict
        dump_messages: list = [m.model_dump() for m in messages]

        # Generate response
        try:
            response = await self.client.chat.completions.create(
                messages=dump_messages,
                model=model,
                temperature=temperature,
                max_tokens=max_tokens,
            )
        except Exception as e:
            raise AIGenerationError(f"Failed to generate response, detail: {e}")

        # Return
        return ProviderResponse(
            provider=self.provider_name,
            model=model,
            message=AssistantMessage(
                content=response.choices[0].message.content,
            ),
        )

    @log
    async def generate_stream(
        self,
        *,
        messages: List[Message],
        model: str,
        temperature: float = 1,
        max_tokens: int = 4096,
    ) -> AsyncGenerator[Union[ProviderResponseChunk, ProviderResponseStream], None]:
        """
        Generate and return response stream

        Args:
            messages: chat context, list of dicts of messages and roles
            model: AI model
            temperature: the degree of randomness and creativity of the generated text
            max_tokens: max tokens for response

        Returns:
            provider response stream
        """
        # Dump messages
        # Specified list type hint cause create method returns exceptions for any other type
        dump_messages: list = [m.model_dump() for m in messages]

        # Generate response
        content = ""
        try:
            stream = await self.client.chat.completions.create(
                messages=dump_messages,
                model=model,
                temperature=temperature,
                max_tokens=max_tokens,
                stream=True,
            )

            # Yield content
            async for chunk in stream:
                if not chunk.choices:
                    continue

                delta = chunk.choices[0].delta
                if delta and delta.content:
                    # Add content
                    content += delta.content

                    # Yield
                    yield ProviderResponseChunk(
                        provider=self.provider_name,
                        model=model,
                        content=delta.content,
                    )
        except Exception as e:
            yield ProviderResponseChunk(
                provider=self.provider_name,
                model=model,
                content=f"\n\n[ERROR: {str(e)}]",
            )

        # Return full response
        response = ProviderResponseStream(
            provider=self.provider_name,
            model=model,
            message=AssistantMessage(content=content),
        )
        yield response
