import json
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse

from api.dependencies import get_ai_service
from schemas.ai import (
    GenerateRequest,
    ProviderResponse,
)
from core.exceptions import AuthError, AIServiceError
from database import User
from core.security import get_current_user
from services.ai.service import AIService
from utils.logger import log

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
    chat_id: int,
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
    chat_id: int,
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
                prompt=request.prompt,
                provider=request.provider,
                model=request.model,
            ):
                # Serialize chunk to JSON
                if hasattr(chunk, "model_dump_json"):
                    yield f"data: {chunk.model_dump_json()}\n\n"
                elif hasattr(chunk, "model_dump"):
                    yield f"data: {json.dumps(chunk.model_dump())}\n\n"
                else:
                    # Fallback for dict
                    yield f"data: {json.dumps(chunk)}\n\n"

        except AIServiceError as e:
            yield f"data: {json.dumps({'error': str(e)})}\n\n"

        except Exception as e:
            import traceback
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
