import json
import traceback
from fastapi import APIRouter, Depends, HTTPException, Path
from fastapi.responses import StreamingResponse

from api.dependencies import get_ai_service
from schemas.ai import (
    GenerateRequest,
    ProviderResponse,
)
from core.exceptions import AuthError, AIServiceError
from core.security import get_current_user
from database import User
from services.ai.service import AIService
from utils.logger import logger, log
from utils.serializator import serialize_model_to_json

router = APIRouter(prefix="/assistant", tags=["messages"])


@router.post(
    "/create/text",
    response_model=ProviderResponse,
    summary="Create assistant message",
    description="Generate a text response from the AI assistant",
)
@log
async def create_assistant_message(
    request: GenerateRequest,
    chat_id: int = Path(..., description="The ID of the chat"),
    ai_service: AIService = Depends(get_ai_service),
    current_user: User = Depends(get_current_user),
) -> ProviderResponse:
    """
    Create an assistant message by generating text from AI provider.

    - **chat_id**: ID of the chat conversation
    - **prompt**: User prompt for generation
    - **provider**: Optional provider override
    - **model**: Optional model override
    """
    if not current_user:
        raise AuthError(detail="Not authenticated")

    try:
        response = await ai_service.generate_text(
            chat_id=chat_id,
            prompt=request.prompt,
            provider=request.provider,
            model=request.model,
        )
        return response
    except AIServiceError as e:
        raise HTTPException(status_code=502, detail=str(e))


@router.post(
    "/create/text/stream",
    summary="Create assistant message stream",
    description="Generate a streaming text response from the AI assistant",
)
@log
async def create_assistant_message_stream(
    request: GenerateRequest,
    chat_id: int = Path(..., description="The ID of the chat"),
    ai_service: AIService = Depends(get_ai_service),
    current_user: User = Depends(get_current_user),
):
    """
    Create an assistant message stream by generating text token by token.

    - **chat_id**: ID of the chat conversation
    - **prompt**: User prompt for generation
    - **provider**: Optional provider override
    - **model**: Optional model override

    Returns SSE stream with chunks.
    """
    if not current_user:
        raise AuthError(detail="Not authenticated")

    async def sse_stream():
        try:
            async for chunk in ai_service.generate_stream(
                chat_id=chat_id,
                prompt=request.prompt,
                provider=request.provider,
                model=request.model,
            ):
                # Serialize chunk to JSON
                yield await serialize_model_to_json(chunk)

        except AIServiceError as e:
            yield f"data: {json.dumps({'error': str(e)})}\n\n"

        except Exception as e:
            yield f"data: {json.dumps({'error': f'Unexpected error: {str(e)}', 'traceback': traceback.format_exc()})}\n\n"

        finally:
            yield "data: [DONE]\n\n"

    return StreamingResponse(
        sse_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )
