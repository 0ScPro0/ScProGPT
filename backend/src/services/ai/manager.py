from typing import Set, Dict, Union, Optional, TypeVar

from core.config import settings
from core.exceptions import (
    NotFoundError,
    ProviderManagementError,
    HTTPNotImplementedError,
)
from services.ai.providers import BaseProvider, OpenAIProvider  # TODO more providers
from schemas.ai import ProviderInfo, ProviderStatus
from utils.logger import log


class NotImplementedProvider:
    def __init__(self, provider_name: str):
        self.provider_name = provider_name

    def __getattr__(self, name):
        """Intercepts all method calls"""
        raise HTTPNotImplementedError(
            f"Provider '{self.provider_name}' is not implemented. "
            f"Method '{name}' called but provider is still a stub."
        )

    def __call__(self, *args, **kwargs):
        """In case the object itself is called as a function"""
        raise HTTPNotImplementedError(
            f"Provider '{self.provider_name}' is not implemented"
        )


ProviderType = Union[OpenAIProvider, NotImplementedProvider]


class ProviderManager:
    """Manager for working with providers and theirs models"""

    def __init__(self):
        # Resolve provider name to instance
        self._available_providers: Set[str] = {
            "openai",
            "openrouter",
            "google",
            "anthropic",
        }
        self.providers: Dict[str, ProviderType] = {
            "openai": OpenAIProvider(),
            "google": NotImplementedProvider("google"),
            "anthropic": NotImplementedProvider("anthropic"),
            "openrouter": NotImplementedProvider("openrouter"),
        }
        self._default_provider_name: str = settings.ai.default_provider
        self.current_provider: ProviderType = self.providers.get(
            self._default_provider_name,
            NotImplementedProvider(self._default_provider_name),
        )
        self.current_model: str = settings.ai.default_model

    async def get_provider(self, provider_name: str = None) -> Optional[ProviderType]:
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
        provider = self.providers.get(name)
        if not provider:
            raise NotFoundError(f"Provider not found or can not be assign: {name}")

        return provider

    async def get_current_provider(self) -> Optional[ProviderType]:
        """
        Get current provider.

        Returns:
            Current provider object.
        """
        return await self.get_provider(self.current_provider.provider_name)

    @log
    async def set_provider(self, provider_name: str) -> bool:
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
            new_provider = await self._find_provider(provider_name)
            if new_provider:
                self.current_provider = new_provider
            return True
        except Exception as e:
            raise ProviderManagementError(f"Can not set new current provider: {e}")

    async def is_provider_available(self, provider_name: str) -> bool:
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

    async def _find_provider(self, provider_name: str) -> Optional[ProviderType]:
        """
        Find provider by name.

        Args:
            provider_name: Name of the provider to find.

        Returns:
            Provider object if found, else None.
        """
        return self.providers.get(provider_name)

    async def _validate_provider(
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
            provider = await self._find_provider(provider) or self.current_provider
        return provider

    async def get_model(
        self, model_name: str, provider: Optional[Union[ProviderType, str]] = None
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
        provider = await self._validate_provider(provider)

        # Validate model using provider's validate_model method
        validated_model = await provider.validate_model(model_name)
        return validated_model

    @log
    async def set_model(self, model_name: str) -> bool:
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
            if await self.is_model_available(model_name=model_name):
                self.current_model = model_name
                return True
            return False
        except Exception as e:
            raise ProviderManagementError(f"Can not set new current model {e}")

    async def is_model_available(
        self,
        model_name: str,
        provider: Optional[Union[ProviderType, str]] = None,
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
        provider = await self._validate_provider(provider)
        if not provider:
            return False

        # Check if model exists in provider's available models
        validated_model = await provider.validate_model(model_name)
        if not validated_model:
            return False

        # Check if model is currently supported
        return await provider.is_model_supports(validated_model)

    async def get_available_providers(self) -> Set[str]:
        """
        Get set of all available provider names.

        Returns:
            Set of available provider names.
        """
        return self._available_providers.copy()

    async def get_registered_providers(self) -> list[str]:
        """
        Get list of registered (initialized) provider names.

        Returns:
            List of registered provider names.
        """
        return list(self.providers.keys())

    async def get_provider_info(self, provider_name: str) -> Optional[ProviderInfo]:
        """
        Get information about a specific provider.

        Args:
            provider_name: Name of the provider to get info for.

        Returns:
            Dictionary with provider info (name, prefix, supported models) or None if not found.
        """
        provider = await self._find_provider(provider_name)
        if not provider or isinstance(provider, NotImplementedProvider):
            return None

        return ProviderInfo(
            name=provider.provider_name,
            prefix=provider.prefix,
            supported_models=provider.get_supports_models(),
            current_model=self.current_model,
        )

    async def get_current_model(self) -> str:
        """
        Get current model name.

        Returns:
            Current model name.
        """
        return self.current_model

    @log
    async def reset_to_defaults(self) -> bool:
        """
        Reset current provider and model to default values.

        Returns:
            True if reset was successful.
        """
        try:
            self.current_provider = self.providers.get(
                settings.ai.default_provider,
                NotImplementedProvider(settings.ai.default_provider),
            )
            self.current_model = settings.ai.default_model
            return True
        except Exception as e:
            raise ProviderManagementError(f"Can not reset to defaults: {e}")

    async def get_status(self) -> ProviderStatus:
        """
        Get current status of the provider manager.

        Returns:
            Dictionary with current status including:
            - current_provider: name of current provider
            - current_model: name of current model
            - available_providers: set of available provider names
            - registered_providers: list of registered provider names
        """
        return ProviderStatus(
            current_provider=self.current_provider.provider_name,
            current_model=self.current_model,
            available_providers=await self.get_available_providers(),
            registered_providers=await self.get_registered_providers(),
        )
