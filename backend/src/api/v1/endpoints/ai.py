from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
import json

from core.exceptions import AIServiceError
from core.security import get_current_user
from database import User
from schemas.ai import (
    GenerateRequest,
    SetProviderRequest,
    SetModelRequest,
    ProviderSwitchRequest,
    AIServiceStatusResponse,
    ProviderListResponse,
    ProviderDetailResponse,
    ModelListResponse,
    OperationResponse,
    ProviderResponse,
)
from services.ai.service import AIService


router = APIRouter(prefix="/ai", tags=["ai"])


# =========================================DEPENDENCIES===================================================

def get_ai_service() -> AIService:
    """Dependency injector for AIService"""
    return AIService()


# =========================================GENERATION=====================================================

@router.post(
    "/generate",
    response_model=ProviderResponse,
    summary="Generate text response",
    description="Generate a complete text response from the AI provider",
)
async def generate_text(
    request: GenerateRequest,
    ai_service: AIService = Depends(get_ai_service),
    current_user: User = Depends(get_current_user),
) -> ProviderResponse:
    """
    Generate text from AI provider.
    
    - **prompt**: User input for generation
    - **provider**: Optional provider override
    - **model**: Optional model override
    """
    return await ai_service.generate_text(
        prompt=request.prompt,
        provider=request.provider,
        model=request.model,
    )


@router.post(
    "/generate/stream",
    summary="Generate streaming text response",
    description="Stream text response token by token",
)
async def generate_stream(
    request: GenerateRequest,
    ai_service: AIService = Depends(get_ai_service),
    current_user: User = Depends(get_current_user),
):
    """
    Generate streaming text from AI provider.
    
    Returns SSE-like stream with chunks.
    """
    async def stream_generator():
        async for chunk in ai_service.generate_stream(
            prompt=request.prompt,
            provider=request.provider,
            model=request.model,
        ):
            # Yield as JSON lines
            yield json.dumps(chunk.model_dump()) + "\n"

    return StreamingResponse(
        stream_generator(),
        media_type="application/x-ndjson",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
        },
    )


# =========================================PROVIDER MANAGEMENT============================================

@router.post(
    "/provider/set",
    response_model=OperationResponse,
    summary="Set current provider",
    description="Switch to a different AI provider",
)
async def set_provider(
    request: SetProviderRequest,
    ai_service: AIService = Depends(get_ai_service),
    current_user: User = Depends(get_current_user),
) -> OperationResponse:
    """
    Set the current AI provider.
    
    - **provider**: Provider name to switch to
    """
    return await ai_service.set_provider(request.provider)


@router.post(
    "/model/set",
    response_model=OperationResponse,
    summary="Set current model",
    description="Switch to a different AI model",
)
async def set_model(
    request: SetModelRequest,
    ai_service: AIService = Depends(get_ai_service),
    current_user: User = Depends(get_current_user),
) -> OperationResponse:
    """
    Set the current AI model.
    
    - **model**: Model name to switch to
    """
    return await ai_service.set_model(request.model)


@router.post(
    "/switch",
    response_model=OperationResponse,
    summary="Switch provider and/or model",
    description="Atomically switch both provider and model",
)
async def switch_provider_and_model(
    request: ProviderSwitchRequest,
    ai_service: AIService = Depends(get_ai_service),
    current_user: User = Depends(get_current_user),
) -> OperationResponse:
    """
    Switch provider and/or model atomically.
    
    - **provider**: Optional provider to switch to
    - **model**: Optional model to switch to
    """
    return await ai_service.switch_provider_and_model(
        provider_name=request.provider,
        model_name=request.model,
    )


@router.post(
    "/reset",
    response_model=OperationResponse,
    summary="Reset to defaults",
    description="Reset provider and model to default values from settings",
)
async def reset_to_defaults(
    ai_service: AIService = Depends(get_ai_service),
    current_user: User = Depends(get_current_user),
) -> OperationResponse:
    """Reset AI service to default configuration."""
    return await ai_service.reset_to_defaults()


# =========================================INFORMATION====================================================

@router.get(
    "/status",
    response_model=AIServiceStatusResponse,
    summary="Get AI service status",
    description="Get current status and configuration of AI service",
)
async def get_status(
    ai_service: AIService = Depends(get_ai_service),
    current_user: User = Depends(get_current_user),
) -> AIServiceStatusResponse:
    """Get AI service status including current provider, model, and availability."""
    return await ai_service.get_status()


@router.get(
    "/providers",
    response_model=ProviderListResponse,
    summary="Get available providers",
    description="Get list of all available AI providers",
)
async def get_providers(
    ai_service: AIService = Depends(get_ai_service),
    current_user: User = Depends(get_current_user),
) -> ProviderListResponse:
    """Get list of all available providers."""
    return await ai_service.get_providers()


@router.get(
    "/providers/{provider_name}",
    response_model=ProviderDetailResponse,
    summary="Get provider details",
    description="Get detailed information about a specific provider",
)
async def get_provider_info(
    provider_name: str,
    ai_service: AIService = Depends(get_ai_service),
    current_user: User = Depends(get_current_user),
) -> ProviderDetailResponse:
    """
    Get detailed provider information.
    
    - **provider_name**: Name of the provider
    """
    return await ai_service.get_provider_info(provider_name)


@router.get(
    "/models",
    response_model=ModelListResponse,
    summary="Get available models",
    description="Get list of models for current or specified provider",
)
async def get_models(
    provider: str | None = None,
    ai_service: AIService = Depends(get_ai_service),
    current_user: User = Depends(get_current_user),
) -> ModelListResponse:
    """
    Get list of available models.
    
    - **provider**: Optional provider name (uses current if not specified)
    """
    return await ai_service.get_models(provider)
