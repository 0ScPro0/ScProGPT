import json
from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse

from api.dependencies import AIService, get_ai_service
from schemas.ai import ProviderResponseChunk, ProviderResponseStream
from core.exceptions import AuthError
from database import User
from core.security import get_current_user
from utils.logger import logger

router = APIRouter(prefix="/assistant", tags=["messages"])


@router.post("/create/text")
async def create_assistant_message(
    chat_id: int,
    ai_service: AIService = Depends(get_ai_service),
    current_user: User = Depends(get_current_user),
    prompt: str = "",
):
    if not current_user:
        raise AuthError(detail="Not authenticated")

    return await ai_service.generate_text(prompt=prompt)


@router.post("/create/text/stream")
async def create_assistant_message_stream(
    chat_id: int,
    ai_service: AIService = Depends(get_ai_service),
    current_user: User = Depends(get_current_user),
    prompt: str = "",
):
    if not current_user:
        raise AuthError(detail="Not authenticated")

    async def sse_stream():
        try:
            async for chunk in ai_service.generate_stream(prompt):
                if isinstance(chunk, (ProviderResponseChunk, ProviderResponseStream)):
                    yield f"data: {chunk.model_dump_json()}\n\n"

        except Exception as e:
            logger.error(f"Can not return response chunk: {e}")
            yield f"data: {json.dumps({'error': str(e)})}\n\n"

        finally:
            yield "data: [DONE]\n\n"

    return StreamingResponse(sse_stream(), media_type="text/event-stream")
