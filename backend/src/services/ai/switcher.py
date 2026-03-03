from typing import Set, Dict, Union, Optional, TypeVar

from core.config import settings
from core.exceptions import NotFoundError, ProviderManagmentError
from services.ai.providers import BaseProvider, OpenAIProvider  # TODO more providers


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


ProviderType = Union[OpenAIProvider, NotImplementedProvider]


class AISwitcher:
    def __init__(self):
        self.current_provider: ProviderType = settings.ai.default_provider
        self.current_model: str = settings.ai.default_model

        self._available_providers: Set[str] = {
            "openai",
            "openrouter",
            "google",
            "anthropic",
        }

        self._providers: Dict[str, ProviderType] = {
            "openai": OpenAIProvider(),
            "google": NotImplementedProvider("google"),
            "anthropic": NotImplementedProvider("anthropic"),
            "openrouter": NotImplementedProvider("openrouter"),
        }

    def get_provider(self, provider_name: str = None) -> Optional[ProviderType]:
        """
        Get provider by name, or current if not specified

        Returns:
            Provider object
        """

        # Check provider is available
        name = provider_name or self.current_provider.provider_name
        if not self.is_provider_available(name):
            raise NotFoundError(f"Unavailabe provider: {name}")

        # Trying to find provider
        provider = self._providers.get(name)
        if not provider:
            raise NotFoundError(f"Provider not found or can not be assign: {name}")

        return provider

    def get_current_provider(self) -> Optional[ProviderType]:
        """
        Get current provider

        Returns:
            Current provider
        """
        return self.get_provider(self.current_provider.provider_name)

    def set_provider(self, provider_name: str) -> bool:
        """
        Set new current provider by name

        Returns:
            True if new provider successfuly set
        """

        # Check provider is available
        if not self.is_provider_available(provider_name):
            raise NotFoundError(f"Unavailabe provider: {provider_name}")

        try:
            new_provider = self._find_provider(provider_name)
            if new_provider:
                self.current_provider = new_provider
            return True
        except Exception as e:
            raise ProviderManagmentError(f"Can not set new current provider: {e}")

    def is_provider_available(self, provider_name: str) -> bool:
        """
        Check provider by available

        Returns:
            True if provider is available
        """
        if provider_name not in self._available_providers:
            return False
        return True

    def _find_provider(self, provider_name: str) -> Optional[ProviderType]:
        """
        Find provider by provider_name

        Returns:
            Provider object if found else None
        """
        return self._providers.get(provider_name)
