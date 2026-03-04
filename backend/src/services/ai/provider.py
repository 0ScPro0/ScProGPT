from typing import Set, Dict, Union, Optional, TypeVar

from core.config import settings
from core.exceptions import NotFoundError, ProviderManagementError
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


class ProviderManager:
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
        Get provider by name, or current if not specified.

        Args:
            provider_name: Name of the provider to retrieve. If None, uses current provider.

        Returns:
            Provider object.

        Raises:
            NotFoundError: If provider is not available or not found.
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
        Get current provider.

        Returns:
            Current provider object.
        """
        return self.get_provider(self.current_provider.provider_name)

    def set_provider(self, provider_name: str) -> bool:
        """
        Set new current provider by name.

        Args:
            provider_name: Name of the provider to set as current.

        Returns:
            True if new provider successfully set.

        Raises:
            NotFoundError: If provider is not available.
            ProviderManagmentError: If provider cannot be set.
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
            raise ProviderManagementError(f"Can not set new current provider: {e}")

    def is_provider_available(self, provider_name: str) -> bool:
        """
        Check if provider is available.

        Args:
            provider_name: Name of the provider to check.

        Returns:
            True if provider is available.
        """
        if provider_name not in self._available_providers:
            return False
        return True

    def _find_provider(self, provider_name: str) -> Optional[ProviderType]:
        """
        Find provider by name.

        Args:
            provider_name: Name of the provider to find.

        Returns:
            Provider object if found, else None.
        """
        return self._providers.get(provider_name)

    def _validate_provider(
        self, provider: Optional[Union[ProviderType, str]]
    ) -> ProviderType:
        """
        Validate and resolve provider to a concrete ProviderType instance.

        Args:
            provider: Provider to validate. Can be a ProviderType instance,
                a provider name as string, or None (uses current_provider).

        Returns:
            Resolved ProviderType instance.
        """
        provider = provider or self.current_provider
        if isinstance(provider, str):
            provider = self._find_provider(provider) or self.current_provider
        return provider

    def get_model(
        self, *, provider: Optional[Union[ProviderType, str]] = None, model_name: str
    ) -> Optional[str]:
        """
        Get model by name for the specified provider.

        Args:
            provider: Provider to get model from. Can be a ProviderType instance,
                a provider name as string, or None (uses current_provider).
            model_name: Name of the model to retrieve.

        Returns:
            Model name if validated and available, else None.
        """
        provider = self._validate_provider(provider)

        # Validate model using provider's validate_model method
        validated_model = provider.validate_model(model_name)
        return validated_model

    def set_model(self, model_name: str) -> bool:
        """
        Set new current model by name.

        Args:
            model_name: Name of the model to set as current.

        Returns:
            True if new model successfully set.

        Raises:
            ProviderManagementError: If model cannot be set.
        """
        try:
            if self.is_model_available(model_name=model_name):
                self.current_model = model_name
                return True
            return False
        except Exception as e:
            raise ProviderManagementError(f"Can not set new current model {e}")

    def is_model_available(
        self, *, provider: Optional[Union[ProviderType, str]] = None, model_name: str
    ) -> bool:
        """
        Check if model is available for the given provider.

        Args:
            provider: Provider to check model availability. Can be a ProviderType instance,
                a provider name as string, or None (uses current_provider).
            model_name: Name of the model to check.

        Returns:
            True if model is available for the provider.
        """
        provider = self._validate_provider(provider)
        if not provider:
            return False

        # Check if model exists in provider's available models
        validated_model = provider.validate_model(model_name)
        if not validated_model:
            return False

        # Check if model is currently supported
        return provider.is_model_supports(validated_model)
