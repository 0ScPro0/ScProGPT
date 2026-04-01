from typing import Set, Dict, Union, Optional, TypeVar
from sqlalchemy.ext.asyncio import AsyncSession

from core.config import settings
from core.exceptions import (
    NotFoundError,
    ProviderManagementError,
    HTTPNotImplementedError,
)
from services.ai.providers import (
    BaseProvider,
    OpenAIProvider,
    OpenRouterProvider,
)  # TODO more providers
from database.crud.chat import chat_crud
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


ProviderType = Union[OpenAIProvider, OpenRouterProvider, NotImplementedProvider]


class ProviderManager:
    """Manager for working with providers and theirs models"""

    def __init__(self, session: AsyncSession):
        # Resolve provider name to instance
        self.session = session
        self.chat_crud = chat_crud
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
            "openrouter": OpenRouterProvider(),
        }
        self._default_provider_name: str = settings.ai.default_provider
        self._default_model: str = settings.ai.default_model

    # =========================================PROVIDER MANAGEMENT====================================================

    async def get_provider(
        self, *, chat_id: int, provider_name: str = None
    ) -> ProviderType:
        """
        Get provider object by name, or current if not specified.

        Args:
            chat_id: Current chat id
            provider_name: Name of the provider to retrieve. If None, uses current provider.

        Returns:
            Provider object.

        Raises:
            NotFoundError: If provider is not available or not found.
        """
        # Check provider is available
        provider_name = await chat_crud.get_chat_provider(
            session=self.session, chat_id=chat_id
        )
        if not await self.is_provider_available(provider_name):
            raise NotFoundError(f"Unavailabe provider: {provider_name}")

        # Trying to find provider
        provider = self.providers.get(provider_name)
        if not provider:
            raise NotFoundError(
                f"Provider not found or can not be assign: {provider_name}"
            )

        return provider

    async def get_current_provider(self, chat_id: int) -> ProviderType:
        """
        Get current provider object.

        Args:
            chat_id: Current chat id

        Returns:
            Current provider object.
        """
        provider_name = await self.chat_crud.get_chat_provider(
            session=self.session, chat_id=chat_id
        )
        return await self.get_provider(chat_id=chat_id, provider_name=provider_name)

    @log
    async def set_provider(self, chat_id: int, provider_name: str) -> bool:
        """
        Set new current provider by name.

        Args:
            chat_id: Current chat id
            provider_name: Name of the provider to set as current.

        Returns:
            True if new provider successfully set.

        Raises:
            NotFoundError: If provider is not available.
            ProviderManagmentError: If provider cannot be set.
        """
        # Check provider is available
        if not await self.is_provider_available(provider_name):
            raise NotFoundError(f"Unavailabe provider: {provider_name}")

        # Update provider in database
        try:
            new_provider = await self._find_provider(provider_name)
            if new_provider:
                # Getting current model
                current_model = await self.get_current_model(chat_id=chat_id)

                # If current model is not available for new provider, switch it to default provider model
                if not await self.is_model_available(
                    chat_id=chat_id, model_name=current_model, provider=new_provider
                ):
                    current_model = new_provider.default_model

                # Set new provider
                await self.chat_crud.update_chat_provider_and_model(
                    session=self.session,
                    chat_id=chat_id,
                    provider=new_provider.provider_name,
                    model=current_model,
                )
            return True
        except Exception as e:
            raise ProviderManagementError(f"Can not set new current provider: {e}")

    async def is_provider_available(self, provider_name: str) -> bool:  # OK
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

    async def get_provider_info(
        self, chat_id: int, provider_name: str
    ) -> Optional[ProviderInfo]:
        """
        Get information about a specific provider.

        Args:
            chat_id: Current chat id
            provider_name: Name of the provider to get info for.

        Returns:
            Dictionary with provider info (name, prefix, supported models) or None if not found.
        """
        provider = await self._find_provider(provider_name)
        if not provider or isinstance(provider, NotImplementedProvider):
            return None

        model = await self.get_current_model(chat_id=chat_id)

        return ProviderInfo(
            name=provider.provider_name,
            prefix=provider.prefix,
            supported_models=provider.get_supported_models(),
            current_model=model,
        )

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
        self, chat_id: int, provider: Optional[Union[ProviderType, str]]
    ) -> ProviderType:
        """
        Validate and resolve provider to a concrete ProviderType instance.

        Args:
            chat_id: Current chat id
            provider: Provider to validate. Can be a ProviderType instance,
                a provider name as string, or None (uses current_provider).

        Returns:
            Resolved ProviderType instance.
        """
        current_provider = await self.get_current_provider(chat_id=chat_id)

        provider = provider or current_provider
        if isinstance(provider, str):
            provider = await self._find_provider(provider) or current_provider
        return provider

    # =========================================MODELS MANAGEMENT====================================================

    @log
    async def set_model(self, chat_id: int, model_name: str) -> bool:
        """
        Set new current model by name to database.

        Args:
            chat_id: Current chat id
            model_name: Name of the model to set as current.

        Returns:
            True if new model successfully set.

        Raises:
            ProviderManagementError: If model cannot be set.
        """
        try:
            if await self.is_model_available(chat_id=chat_id, model_name=model_name):
                # Update chat model in database
                await self.chat_crud.update_chat_model(
                    session=self.session, chat_id=chat_id, model=model_name
                )
                return True
            return False
        except Exception as e:
            raise ProviderManagementError(f"Can not set new current model {e}")

    async def get_current_model(self, chat_id: int) -> Optional[str]:
        """
        Get current model name (str) from database.

        Args:
            chat_id: Current chat id

        Returns:
            Current model name, or None if not set.
        """
        model = await self.chat_crud.get_chat_model(
            session=self.session, chat_id=chat_id
        )
        return model

    async def get_model(
        self,
        chat_id: int,
        model_name: str,
        provider: Optional[Union[ProviderType, str]] = None,
    ) -> Optional[str]:
        """
        Get model by name for the specified provider.
        This function can not be called for get current model.

        Args:
            chat_id: Current chat id
            provider: Provider to get model from. Can be a ProviderType instance,
                a provider name as string, or None (uses current_provider).
            model_name: Name of the model to retrieve.

        Returns:
            Model name if validated and available, else None.
        """
        provider = await self._validate_provider(chat_id=chat_id, provider=provider)

        # Validate model using provider's validate_model method
        validated_model = await provider.validate_model(model_name)
        return validated_model

    async def is_model_available(
        self,
        chat_id: int,
        model_name: str,
        provider: Optional[Union[ProviderType, str]] = None,
    ) -> bool:
        """
        Check if model is available for the given provider.

        Args:
            chat_id: Current chat id
            provider: Provider to check model availability. Can be a ProviderType instance,
                a provider name as string, or None (uses current_provider).
            model_name: Name of the model to check.

        Returns:
            True if model is available for the provider.
        """
        provider = await self._validate_provider(chat_id=chat_id, provider=provider)
        if not provider:
            return False

        # Check if model exists in provider's available models
        validated_model = await provider.validate_model(model_name)
        if not validated_model:
            return False

        # Check if model is currently supported
        return await provider.is_model_supports(validated_model)

    # =========================================OTHER====================================================
    @log
    async def reset_to_defaults(self, chat_id: int) -> bool:
        """
        Reset current provider and model to default values.

        Args:
            chat_id: Current chat id

        Returns:
            True if reset was successful.
        """
        try:
            # Get default provider and model
            provider = self.providers.get(
                settings.ai.default_provider,
                NotImplementedProvider(settings.ai.default_provider),
            )
            model = settings.ai.default_model

            # Set provider
            await self.set_provider(
                chat_id=chat_id, provider_name=provider.provider_name
            )

            # Set model
            await self.set_model(chat_id=chat_id, model_name=model)

            # Return
            return True

        except Exception as e:
            raise ProviderManagementError(f"Can not reset to defaults: {e}")

    async def get_status(self, chat_id: int) -> ProviderStatus:
        """
        Get current status of the provider manager.

        Returns:
            Dictionary with current status including:
            - current_provider: name of current provider
            - current_model: name of current model
            - available_providers: set of available provider names
            - registered_providers: list of registered provider names
        """
        provider = await self.get_current_provider(chat_id=chat_id)
        model = await self.get_current_model(chat_id=chat_id)
        return ProviderStatus(
            current_provider=provider.provider_name,
            current_model=model,
            available_providers=await self.get_available_providers(),
            registered_providers=await self.get_registered_providers(),
        )
