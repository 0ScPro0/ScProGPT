from openai import AsyncOpenAI
from typing import List, Dict, Any, Optional

from core.config import settings
from .base import BaseProvider


class OpenAIProvider(BaseProvider):
    def __init__(self) -> None:
        super().__init__()
        self.provider_name = "openai"
        self.prefix: str = "openai/v1"
        self.base_url = settings.ai.base_url + self.prefix
        self.client = AsyncOpenAI(api_key=settings.ai.api_key, base_url=self.base_url)
        self._possibly_models = settings.ai.openai.all_possible_models
        self.supports_models = settings.ai.openai.supported_models
