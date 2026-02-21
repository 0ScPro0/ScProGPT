from openai import AsyncOpenAI
from typing import List, Dict, Any, Optional

from core.config import settings
from schemas.ai import AssistantMessage, ProviderResponse
from .base_provider import BaseProvider


class OpenAIProvider(BaseProvider):
    def __init__(self) -> None:
        super().__init__()
        self.provider_name = "openai"
        self.prefix: str = "openai/v1"
        self.base_url = settings.ai.base_url + self.prefix
        self.client = AsyncOpenAI(api_key=settings.ai.api_key, base_url=self.base_url)
        self._possibly_models = settings.ai.openai.models
        self.supports_models = settings.ai.openai.models["supports"]

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
        response = await self.client.chat.completions.create(
            messages=messages,
            model=model,
            temperature=temperature,
            max_tokens=max_tokens,
        )

        # Return
        return ProviderResponse(
            provider=self.provider_name,
            model=model,
            message=AssistantMessage(
                role=response.choices[0].message.role,
                content=response.choices[0].message.content,
            ),
        )
