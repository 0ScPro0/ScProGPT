from typing import AsyncGenerator, Union, Optional, List
from sqlalchemy.ext.asyncio import AsyncSession

from core.exceptions import AIServiceError
from services.base import BaseService
from services.ai.providers import OpenAIProvider
from services.ai.manager import ProviderManager
from schemas.ai import (
    ProviderResponse,
    ProviderResponseStream,
    ProviderResponseChunk,
    ProviderInfo,
    ProviderStatus,
    AIServiceStatusResponse,
    ProviderListResponse,
    ProviderDetailResponse,
    ModelListResponse,
    OperationResponse,
    AssistantMessage,
    UserMessage,
)
from utils.logger import log


class AIService:
    """
    AI Service for integrating with external AI providers.

    Provides:
    - Text generation (sync/stream)
    - Provider and model management
    - Service status and information
    """

    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.provider_manager = ProviderManager(session=session)

    # ==========================================GENERATION==================================================

    @log
    async def generate_text(
        self,
        prompt: str,
        provider: Optional[str] = None,
        model: Optional[str] = None,
    ) -> ProviderResponse:
        """
        Generate text response from AI provider.

        Args:
            prompt: User prompt for generation
            provider: Optional provider name (uses current if not specified)
            model: Optional model name (uses current if not specified)

        Returns:
            ProviderResponse with generated text and metadata
        """
        # Resolve provider and model
        provider_instance = await self._resolve_provider(provider)
        model_name = await self._resolve_model(model, provider_instance)

        # Build messages as UserMessage objects
        messages = [UserMessage(role="user", content=prompt)]

        # Generate
        response = await provider_instance.generate_text(
            messages=messages,
            model=model_name,
        )

        # Enrich with usage data if available
        if hasattr(response, "usage") and response.usage:
            pass  # Usage already in response
        else:
            # TODO: Get usage from provider response if not already included
            pass

        return response

    @log
    async def generate_stream(
        self,
        prompt: str,
        provider: Optional[str] = None,
        model: Optional[str] = None,
    ) -> AsyncGenerator[Union[ProviderResponseChunk, ProviderResponseStream], None]:
        """
        Generate streaming text response from AI provider.

        Args:
            prompt: User prompt for generation
            provider: Optional provider name (uses current if not specified)
            model: Optional model name (uses current if not specified)

        Yields:
            ProviderResponseChunk for each token, then ProviderResponseStream at the end
        """
        # Resolve provider and model
        provider_instance = await self._resolve_provider(provider)
        model_name = await self._resolve_model(model, provider_instance)

        # Build messages as UserMessage objects
        messages = [UserMessage(role="user", content=prompt)]

        # Stream
        stream = provider_instance.generate_stream(
            messages=messages,
            model=model_name,
        )
        async for chunk in stream:
            yield chunk

    # =========================================PROVIDER MANAGEMENT==========================================

    @log
    async def set_provider(self, chat_id: int, provider_name: str) -> OperationResponse:
        """
        Set current AI provider.

        Args:
            chat_id: Current chat id
            provider_name: Name of the provider to set as current

        Returns:
            OperationResponse with success status and values
        """
        # Get current provider name for response
        old_provider = self.provider_manager.current_provider.provider_name

        # Validate provider exists
        if not await self.provider_manager.is_provider_available(provider_name):
            raise AIServiceError(f"Provider '{provider_name}' is not available")

        # Set new provider
        await self.provider_manager.set_provider(chat_id, provider_name)

        return OperationResponse(
            success=True,
            message=f"Provider switched from '{old_provider}' to '{provider_name}'",
            previous_value=old_provider,
            new_value=provider_name,
        )

    @log
    async def set_model(self, chat_id: int, model_name: str) -> OperationResponse:
        """
        Set current AI model.

        Args:
            model_name: Name of the model to set as current

        Returns:
            OperationResponse with success status and values
        """
        old_model = self.provider_manager.current_model

        # Validate model exists
        if not await self.provider_manager.is_model_available(chat_id, model_name):
            raise AIServiceError(f"Model '{model_name}' is not available")

        # Set new model
        success = await self.provider_manager.set_model(model_name)

        return OperationResponse(
            success=success,
            message=f"Model switched from '{old_model}' to '{model_name}'",
            previous_value=old_model,
            new_value=model_name,
        )

    @log
    async def set_provider_and_model(
        self,
        chat_id: int,
        provider_name: Optional[str] = None,
        model_name: Optional[str] = None,
    ) -> OperationResponse:
        """
        Switch both provider and model atomically.

        Args:
            provider_name: Optional provider name to switch to
            model_name: Optional model name to switch to

        Returns:
            OperationResponse with success status and values
        """
        old_provider = self.provider_manager.current_provider.provider_name
        old_model = self.provider_manager.current_model

        changes = []

        # Switch provider if specified
        if provider_name:
            if not await self.provider_manager.is_provider_available(provider_name):
                raise AIServiceError(f"Provider '{provider_name}' is not available")
            await self.provider_manager.set_provider(provider_name)
            changes.append(f"provider: '{old_provider}' → '{provider_name}'")

        # Switch model if specified
        if model_name:
            if not await self.provider_manager.is_model_available(chat_id, model_name):
                raise AIServiceError(f"Model '{model_name}' is not available")
            await self.provider_manager.set_model(model_name)
            changes.append(f"model: '{old_model}' → '{model_name}'")

        if not changes:
            return OperationResponse(
                success=True,
                message="No changes requested",
                previous_value=None,
                new_value=None,
            )

        return OperationResponse(
            success=True,
            message=f"Updated: {', '.join(changes)}",
            previous_value=f"provider={old_provider}, model={old_model}",
            new_value=f"provider={provider_name or old_provider}, model={model_name or old_model}",
        )

    @log
    async def reset_to_defaults(self) -> OperationResponse:
        """
        Reset provider and model to default values from settings.

        Returns:
            OperationResponse with success status and values
        """
        old_provider = self.provider_manager.current_provider.provider_name
        old_model = self.provider_manager.current_model

        await self.provider_manager.reset_to_defaults()

        new_provider = self.provider_manager.current_provider.provider_name
        new_model = self.provider_manager.current_model

        return OperationResponse(
            success=True,
            message="Reset to default provider and model",
            previous_value=f"provider={old_provider}, model={old_model}",
            new_value=f"provider={new_provider}, model={new_model}",
        )

    # =========================================INFORMATION==================================================

    async def get_status(self) -> AIServiceStatusResponse:
        """
        Get AI service status and configuration.

        Returns:
            AIServiceStatusResponse with current state
        """
        status = await self.provider_manager.get_status()

        # Check if service is configured (has valid provider and model)
        is_configured = (
            status.current_provider is not None
            and status.current_model is not None
            and len(status.registered_providers) > 0
        )

        return AIServiceStatusResponse(
            current_provider=status.current_provider,
            current_model=status.current_model,
            available_providers=status.available_providers,
            registered_providers=status.registered_providers,
            is_configured=is_configured,
        )

    async def get_providers(self) -> ProviderListResponse:
        """
        Get list of all available providers.

        Returns:
            ProviderListResponse with providers list and current provider
        """
        providers = await self.provider_manager.get_available_providers()
        current = self.provider_manager.current_provider.provider_name

        return ProviderListResponse(
            providers=sorted(list(providers)),
            current_provider=current,
        )

    async def get_provider_info(
        self,
        provider_name: Optional[str] = None,
    ) -> ProviderDetailResponse:
        """
        Get detailed information about a provider.

        Args:
            provider_name: Optional provider name (uses current if not specified)

        Returns:
            ProviderDetailResponse with provider info and whether it's current
        """
        target_provider = (
            provider_name or self.provider_manager.current_provider.provider_name
        )

        info = await self.provider_manager.get_provider_info(target_provider)
        if not info:
            raise AIServiceError(
                f"Provider '{target_provider}' not found or not implemented"
            )

        current_provider = self.provider_manager.current_provider.provider_name

        return ProviderDetailResponse(
            provider=info,
            is_current=(target_provider == current_provider),
        )

    async def get_models(
        self, provider_name: Optional[str] = None
    ) -> ModelListResponse:
        """
        Get list of available models for a provider.

        Args:
            provider_name: Optional provider name (uses current if not specified)

        Returns:
            ModelListResponse with models list and current model
        """
        target_provider = (
            provider_name or self.provider_manager.current_provider.provider_name
        )
        provider_instance = await self._resolve_provider(target_provider)

        models = provider_instance.get_supports_models()
        current_model = self.provider_manager.current_model

        return ModelListResponse(
            provider=target_provider,
            models=sorted(models),
            current_model=current_model,
        )

    async def get_current_provider_name(self) -> str:
        """Get current provider name."""
        return self.provider_manager.current_provider.provider_name

    async def get_current_model_name(self) -> str:
        """Get current model name."""
        return self.provider_manager.current_model

    # =========================================HELPERS======================================================

    async def _resolve_provider(
        self, chat_id: int, provider_name: Optional[str] = None
    ):
        """
        Resolve provider name to provider instance.

        Args:
            provider_name: Optional provider name (uses current if not specified)

        Returns:
            Provider instance
        """
        if provider_name:
            if not await self.provider_manager.is_provider_available(provider_name):
                raise AIServiceError(f"Provider '{provider_name}' is not available")
            provider = await self.provider_manager.get_provider(provider_name)
        else:
            provider = await self.provider_manager.get_current_provider(chat_id)

        if not provider:
            raise AIServiceError("Can not get current provider")

        return provider

    async def _resolve_model(
        self,
        model_name: Optional[str] = None,
        provider=None,
    ) -> str:
        """
        Resolve model name, validating against provider.

        Args:
            model_name: Optional model name (uses current if not specified)
            provider: Provider instance to validate against

        Returns:
            Validated model name
        """
        if model_name:
            # Validate model exists for this provider
            validated = await provider.validate_model(model_name)
            if not validated:
                raise AIServiceError(
                    f"Model '{model_name}' is not available for provider"
                )
            return validated
        else:
            return self.provider_manager.current_model
