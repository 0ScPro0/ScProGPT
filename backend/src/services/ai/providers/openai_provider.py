from openai import AsyncOpenAI
from typing import Union, AsyncGenerator

from core.config import settings
from core.exceptions import AIGenerationError, AIStreamGenerationError
from utils.logger import log
from schemas.ai import (
    AssistantMessage,
    ProviderResponse,
    ProviderResponseStream,
    ProviderResponseChunk,
)
from .base_provider import BaseProvider


class OpenAIProvider(BaseProvider):
    def __init__(self) -> None:
        super().__init__()
        self.provider_name = "openai"
        self.prefix = "openai/v1"
        self.requires_v1_prefix = True
        self.base_url = settings.ai.base_url + self.prefix
        self.client = AsyncOpenAI(api_key=settings.ai.api_key, base_url=self.base_url)
        self._available_models = settings.ai.openai.models
        self.supports_models = settings.ai.openai.models["supports"]

    @log
    async def generate_text(
        self,
        *,
        messages: list,
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
        # Generate response
        try:
            response = await self.client.chat.completions.create(
                messages=messages,
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
        messages: list,
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
        # Generate response
        try:
            stream = await self.client.chat.completions.create(
                messages=messages,
                model=model,
                temperature=temperature,
                max_tokens=max_tokens,
                stream=True,
            )

            # Yield content
            content = ""
            async for chunk in stream:
                if chunk.choices[0].delta.content is not None:
                    # Add content
                    content += chunk.choices[0].delta.content

                    # Yield
                    yield ProviderResponseChunk(
                        provider=self.provider_name,
                        model=model,
                        content=chunk.choices[0].delta.content,
                    )
        except Exception as e:
            raise AIStreamGenerationError(f"Failed to generate response, detail: {e}")

        # Return full response
        response = ProviderResponseStream(
            provider=self.provider_name,
            model=model,
            message=AssistantMessage(content=content),
        )
        yield response
