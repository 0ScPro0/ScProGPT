from typing import List, Optional

import json
import traceback

from fastapi import APIRouter, Depends, HTTPException, Path
from fastapi.responses import StreamingResponse

from api.dependencies import (
    AIService,
    ChatService,
    MessageService,
    get_ai_service,
    get_chat_service,
    get_message_service,
)

from database import User

from core.exceptions import AuthError, AIServiceError, PermissionDeniedError
from core.security import get_current_user

from schemas.ai import (
    GenerateRequest,
    ProviderResponse,
    ProviderResponseStream,
    UserMessage,
    AssistantMessage,
)
from schemas.message import MessageCreate, MessageResponse
from schemas.chat import ChatCreate

from utils.logger import log
from utils.serializator import serialize_model_to_json

router = APIRouter(prefix="/chats/{chat_id}/messages", tags=["messages"])


@router.get(
    "/",
    response_model=List[MessageResponse],
    summary="Get chat messages",
    description="Get chat messages",
)
@log
async def get_chat_messages(
    chat_id: int = Path(..., description="The ID of the chat"),
    chat_service: ChatService = Depends(get_chat_service),
    message_service: MessageService = Depends(get_message_service),
    current_user: User = Depends(get_current_user),
):
    if not current_user:
        raise AuthError(detail="Not authenticated")

    if not await chat_service.is_user_has_chat(
        user_id=current_user.id, chat_id=chat_id
    ):
        raise PermissionDeniedError(f"User does not have access to this chat")

    return await message_service.get_chat_response_messages(chat_id=chat_id)


@router.post(
    "/text",
    response_model=MessageResponse,
    summary="Create assistant message",
    description="Generate a text response from the AI assistant",
)
@log
async def create_assistant_message(
    request: GenerateRequest,
    chat_id: Optional[int] = Path(..., description="The ID of the chat"),
    ai_service: AIService = Depends(get_ai_service),
    chat_service: ChatService = Depends(get_chat_service),
    message_service: MessageService = Depends(get_message_service),
    current_user: User = Depends(get_current_user),
) -> MessageResponse:
    """
    Create an assistant message by generating text from AI provider.

    - **chat_id**: ID of the chat conversation
    - **prompt**: User prompt for generation
    - **provider**: Optional provider override
    - **model**: Optional model override
    """
    if not current_user:
        raise AuthError("Not authenticated")

    # If chat_id is not assign, create new chat
    if not chat_id:
        new_chat = await chat_service.create_chat(ChatCreate(user_id=current_user.id))
        chat_id = new_chat.id

    if not await chat_service.is_user_has_chat(
        user_id=current_user.id, chat_id=chat_id
    ):
        raise PermissionDeniedError(f"User does not have access to this chat")

    try:
        # Create and save UserMessage
        user_message = MessageCreate(
            role="user", content=request.prompt, chat_id=chat_id
        )
        await message_service.create_message(user_message)

        # Get all chat messages (to context)
        messages = await message_service.get_chat_messages(chat_id=chat_id)

        # Generate response
        response = await ai_service.generate_text(
            chat_id=chat_id,
            provider=request.provider,
            model=request.model,
            messages=messages,
            temperature=request.temperature,
            max_tokens=request.max_tokens,
        )

        # Create message
        new_message = MessageCreate(
            role="assistant",
            content=response.message.content or "",
            prompt_tokens=response.usage.get("prompt_tokens", 0),
            completion_tokens=response.usage.get("completion_tokens", 0),
            total_tokens=response.usage.get("total_tokens", 0),
            cost=response.cost,
            chat_id=chat_id,
        )

        # Save message
        message = await message_service.create_message(new_message)

        # Return MessageResponse
        return message

    except AIServiceError as e:
        raise HTTPException(status_code=502, detail=str(e))


@router.post(
    "/text/stream",
    summary="Create assistant message stream",
    description="Generate a streaming text response from the AI assistant",
)
@log
async def create_assistant_message_stream(
    request: GenerateRequest,
    chat_id: Optional[int] = Path(..., description="The ID of the chat"),
    ai_service: AIService = Depends(get_ai_service),
    chat_service: ChatService = Depends(get_chat_service),
    message_service: MessageService = Depends(get_message_service),
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

    if not await chat_service.is_user_has_chat(
        user_id=current_user.id, chat_id=chat_id
    ):
        raise PermissionDeniedError(f"User does not have access to this chat")

    try:
        # Create and save UserMessage
        user_message = MessageCreate(
            role="user", content=request.prompt, chat_id=chat_id
        )
        await message_service.create_message(user_message)

        # Get all chat messages (to context)
        messages = await message_service.get_chat_messages(chat_id=chat_id)

    except Exception as e:
        return f"data: {json.dumps({'error': f'Unexpected error: {str(e)}', 'traceback': traceback.format_exc()})}\n\n"

    async def sse_stream():
        try:
            async for chunk in ai_service.generate_stream(
                chat_id=chat_id,
                provider=request.provider,
                model=request.model,
                messages=messages,
                temperature=request.temperature,
                max_tokens=request.max_tokens,
            ):
                # Serialize chunk to JSON
                yield await serialize_model_to_json(chunk)

                # ProviderResponseStream is a last chunk so create message
                if isinstance(chunk, ProviderResponseStream):
                    new_message = MessageCreate(
                        role="assistant",
                        content=chunk.message.content or "",
                        prompt_tokens=chunk.usage.get("prompt_tokens", 0),
                        completion_tokens=chunk.usage.get("completion_tokens", 0),
                        total_tokens=chunk.usage.get("total_tokens", 0),
                        cost=chunk.cost,
                        chat_id=chat_id,
                    )

                    # Save message
                    message = await message_service.create_message(new_message)

                    # Yield MessageResponse as final event
                    yield f"event: message_complete\ndata: {message.model_dump_json()}\n\n"

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
