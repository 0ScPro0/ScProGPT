from typing import AsyncGenerator, Union
from services.base import BaseService
from services.ai.providers import OpenAIProvider

from schemas.ai import ProviderResponse, ProviderResponseStream, ProviderResponseChunk
from utils.logger import log


class AIService:
    def __init__(self) -> None:
        self.provider = OpenAIProvider()

    @log
    async def generate_text(self, prompt: str) -> ProviderResponse:
        message = [{"role": "user", "content": prompt}]
        response = await self.provider.generate_text(
            messages=message, model="gpt-4o-mini"
        )
        return response

    @log
    async def generate_stream(
        self, prompt: str
    ) -> AsyncGenerator[Union[ProviderResponseStream, ProviderResponseChunk], None]:
        message = [{"role": "user", "content": prompt}]
        stream = self.provider.generate_stream(messages=message, model="gpt-4o-mini")
        async for chunk in stream:
            yield chunk
