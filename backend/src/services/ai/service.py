from typing import AsyncGenerator, Union, Optional, List
from sqlalchemy.ext.asyncio import AsyncSession

from core.exceptions import AIServiceError
from services.base import BaseService
from services.ai.providers import OpenAIProvider
from services.ai.manager import ProviderType, ProviderManager
from schemas.base import OperationResponse
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
        *,
        chat_id: int,
        provider: Optional[str] = None,
        model: Optional[str] = None,
        messages: List[Union[UserMessage, AssistantMessage]],
        temperature: float = 1,
        max_tokens: int = 4096,
    ) -> ProviderResponse:
        """
        Generate text response from AI provider.

        Args:
            chat_id: Current chat id
            prompt: User prompt for generation
            provider: Optional provider name (uses current if not specified)
            model: Optional model name (uses current if not specified)

        Returns:
            ProviderResponse with generated text and metadata
        """
        # Resolve provider and model
        provider_instance = await self._resolve_provider(
            chat_id=chat_id, provider_name=provider
        )
        model_name = await self._resolve_model(
            chat_id=chat_id, model_name=model, provider=provider_instance
        )

        # Generate
        response = await provider_instance.generate_text(
            messages=messages,
            model=model_name,
            temperature=temperature,
            max_tokens=max_tokens,
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
        *,
        chat_id: int,
        provider: Optional[str] = None,
        model: Optional[str] = None,
        messages: List[Union[UserMessage, AssistantMessage]],
        temperature: float = 1,
        max_tokens: int = 4096,
    ) -> AsyncGenerator[Union[ProviderResponseChunk, ProviderResponseStream], None]:
        """
        Generate streaming text response from AI provider.

        Args:
            chat_id: Current chat id
            prompt: User prompt for generation
            provider: Optional provider name (uses current if not specified)
            model: Optional model name (uses current if not specified)

        Yields:
            ProviderResponseChunk for each token, then ProviderResponseStream at the end
        """
        # Resolve provider and model
        provider_instance = await self._resolve_provider(
            chat_id=chat_id, provider_name=provider
        )
        model_name = await self._resolve_model(
            chat_id=chat_id, model_name=model, provider=provider_instance
        )

        # Stream
        stream = provider_instance.generate_stream(
            messages=messages,
            model=model_name,
            temperature=temperature,
            max_tokens=max_tokens,
        )
        async for chunk in stream:
            yield chunk

    # =========================================PROVIDER MANAGEMENT==========================================

    @log
    async def set_provider(
        self, *, chat_id: int, provider_name: str
    ) -> OperationResponse:
        """
        Set current AI provider.

        Args:
            chat_id: Current chat id
            provider_name: Name of the provider to set as current

        Returns:
            OperationResponse with success status and values
        """
        # Get current provider name for response
        old_provider = await self.provider_manager.get_current_provider(chat_id)

        # Validate provider exists
        if not await self.provider_manager.is_provider_available(provider_name):
            raise AIServiceError(f"Provider '{provider_name}' is not available")

        # Set new provider
        await self.provider_manager.set_provider(chat_id, provider_name)

        return OperationResponse(
            success=True,
            message=f"Provider switched from '{old_provider.provider_name}' to '{provider_name}'",
            previous_value=old_provider.provider_name,
            new_value=provider_name,
        )

    @log
    async def set_model(self, *, chat_id: int, model_name: str) -> OperationResponse:
        """
        Set current AI model.

        Args:
            model_name: Name of the model to set as current

        Returns:
            OperationResponse with success status and values
        """
        old_model = await self.provider_manager.get_current_model(chat_id)

        # Validate model exists
        if not await self.provider_manager.is_model_available(chat_id, model_name):
            raise AIServiceError(f"Model '{model_name}' is not available")

        # Set new model
        success = await self.provider_manager.set_model(chat_id, model_name)

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
        old_provider = await self.provider_manager.get_current_provider(chat_id)
        old_model = await self.provider_manager.get_current_model(chat_id)

        changes = []

        # Switch provider if specified
        if provider_name:
            if not await self.provider_manager.is_provider_available(provider_name):
                raise AIServiceError(f"Provider '{provider_name}' is not available")
            await self.provider_manager.set_provider(chat_id, provider_name)
            changes.append(f"provider: '{old_provider}' → '{provider_name}'")

        # Switch model if specified
        if model_name:
            if not await self.provider_manager.is_model_available(chat_id, model_name):
                raise AIServiceError(f"Model '{model_name}' is not available")
            await self.provider_manager.set_model(chat_id, model_name)
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
    async def reset_to_defaults(self, chat_id: int) -> OperationResponse:
        """
        Reset provider and model to default values from settings.

        Args:
            chat_id: current chat id

        Returns:
            OperationResponse with success status and values
        """
        old_provider = await self.provider_manager.get_current_provider(chat_id)
        old_model = await self.provider_manager.get_current_model(chat_id)

        await self.provider_manager.reset_to_defaults(chat_id)

        new_provider = await self.provider_manager.get_current_provider(chat_id)
        new_model = await self.provider_manager.get_current_model(chat_id)

        return OperationResponse(
            success=True,
            message="Reset to default provider and model",
            previous_value=f"provider={old_provider}, model={old_model}",
            new_value=f"provider={new_provider}, model={new_model}",
        )

    # =========================================INFORMATION==================================================

    async def get_status(self, chat_id: int) -> AIServiceStatusResponse:
        """
        Get AI service status and configuration.

        Args:
            chat_id: Current chat id

        Returns:
            AIServiceStatusResponse with current state
        """
        status = await self.provider_manager.get_status(chat_id)

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

    async def get_providers(self, chat_id: int) -> ProviderListResponse:
        """
        Get list of all available providers.

        Args:
            chat_id: Current chat id

        Returns:
            ProviderListResponse with providers list and current provider
        """
        providers = await self.provider_manager.get_available_providers()
        current = await self.provider_manager.get_current_provider(chat_id)

        return ProviderListResponse(
            providers=sorted(list(providers)),
            current_provider=current,
        )

    async def get_provider_info(
        self,
        chat_id: int,
        provider_name: Optional[str] = None,
    ) -> ProviderDetailResponse:
        """
        Get detailed information about a provider.

        Args:
            provider_name: Optional provider name (uses current if not specified)

        Returns:
            ProviderDetailResponse with provider info and whether it's current
        """
        target_provider = provider_name or await self.get_current_provider_name(chat_id)

        info = await self.provider_manager.get_provider_info(chat_id, target_provider)
        if not info:
            raise AIServiceError(
                f"Provider '{target_provider}' not found or not implemented"
            )

        current_provider = await self.provider_manager.get_current_provider(chat_id)

        return ProviderDetailResponse(
            provider=info,
            is_current=(target_provider == current_provider),
        )

    async def get_models(
        self, chat_id: int, provider_name: Optional[str] = None
    ) -> ModelListResponse:
        """
        Get list of available models for a provider.

        Args:
            chat_id: Current chat id
            provider_name: Optional provider name (uses current if not specified)

        Returns:
            ModelListResponse with models list and current model
        """
        target_provider = provider_name or await self.get_current_provider_name(chat_id)
        provider_instance = await self._resolve_provider(
            chat_id=chat_id, provider_name=target_provider
        )

        models = provider_instance.get_supported_models()
        current_model = self.provider_manager.get_current_model(chat_id)

        return ModelListResponse(
            provider=target_provider,
            models=sorted(models),
            current_model=current_model,
        )

    async def get_current_provider_name(self, chat_id: int) -> str:
        """
        Get current provider name.

        Args:
            chat_id: Current chat id

        Returns:
            Current provider name
        """
        provider = await self.provider_manager.get_current_provider(chat_id)
        return provider.provider_name

    async def get_current_model_name(self, chat_id: int) -> Optional[str]:
        """
        Get current model name.

        Args:
            chat_id: Current chat id

        Returns:
            Current model name
        """
        return await self.provider_manager.get_current_model(chat_id)

    # =========================================HELPERS======================================================

    async def _resolve_provider(
        self, *, chat_id: int, provider_name: Optional[str] = None
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
            provider = await self.provider_manager.get_provider(
                chat_id=chat_id, provider_name=provider_name
            )
        else:
            provider = await self.provider_manager.get_current_provider(chat_id=chat_id)

        if not provider:
            raise AIServiceError("Can not get current provider")

        return provider

    async def _resolve_model(
        self,
        *,
        chat_id: int,
        model_name: Optional[str] = None,
        provider: Optional[ProviderType] = None,
    ) -> Optional[str]:
        """
        Resolve model name, validating against provider.

        Args:
            model_name: Optional model name (uses current if not specified)
            provider: Provider instance to validate against

        Returns:
            Validated model name
        """
        if not provider:
            provider = await self.provider_manager.get_current_provider(chat_id)
        if model_name:
            # Validate model exists for this provider
            validated = await provider.validate_model(model_name)
            if not validated:
                raise AIServiceError(
                    f"Model '{model_name}' is not available for provider"
                )
            return validated
        else:
            return await self.provider_manager.get_current_model(chat_id)
