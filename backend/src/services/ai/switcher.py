from typing import List, AsyncGenerator, Union

from backend.src.schemas.ai import ProviderResponse
from core.config import settings
from services.ai.providers import OpenAIProvider  # TODO more providers


class NotImplementedProvider:
    def __init__(self, provider_name: str):
        self.provider_name = provider_name

    def __getattr__(self, name):
        """Intercepts all method calls"""
        raise NotImplementedError(
            f"Provider '{self.provider_name}' is not implemented. "
            f"Method '{name}' called but provider is still a stub."
        )

    def __call__(self, *args, **kwargs):
        """In case the object itself is called as a function"""
        raise NotImplementedError(f"Provider '{self.provider_name}' is not implemented")


class AISwitcher:
    def __init__(self):
        self.current_provider = settings.ai.default_provider
        self.current_model = settings.ai.default_model

        self._available_providers = {"openai", "openrouter", "google", "anthropic"}

        self.openai_provider = OpenAIProvider()
        self.google_provider = NotImplementedProvider("google")  # TODO
        self.anthropic_provider = NotImplementedProvider("anthropic")  # TODO
        self.openrouter_provider = NotImplementedProvider("openrouter")  # TODO
