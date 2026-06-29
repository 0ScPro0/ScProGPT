from typing import List
import json
from fastapi import APIRouter, Depends

from api.dependencies import ChatService, AIService, get_chat_service, get_ai_service

from core.exceptions import AuthError, PermissionDeniedError
from core.security import get_current_user

from database import User

from schemas.base import OperationResponse
from schemas.chat import ChatResponse, ChatCreate, SetTitleRequest
from schemas.ai import (
    ProviderStatus,
    SetProviderRequest,
    SetModelRequest,
)

from utils.logger import log, logger

router = APIRouter(prefix="/chats", tags=["chats"])


# Create a new chat
@router.post(
    "/",
    response_model=ChatResponse,
    summary="Create a chat",
    description="Create a chat with the specified user",
)
@log
async def create_chat(
    chat: ChatCreate,
    current_user: User = Depends(get_current_user),
    chat_service: ChatService = Depends(get_chat_service),
) -> ChatResponse:
    if not current_user:
        raise AuthError("Not authenticated")

    try:
        chat.user_id = current_user.id
        return await chat_service.create_chat(chat)
    except Exception as e:  # TODO more exceptions
        raise e


# Get all chats for the current user
@router.get(
    "/me",
    summary="Get user chats",
    description="Get all chats for the current user",
    response_model=List[ChatResponse],
)
@log
async def get_user_chats(
    chat_service: ChatService = Depends(get_chat_service),
    current_user: User = Depends(get_current_user),
):
    if not current_user:
        raise AuthError("Not authenticated")

    return await chat_service.get_user_chats(current_user.id)


# Update chat provider
@router.patch(
    "/{chat_id}/provider",
    response_model=OperationResponse,
)
@log
async def update_chat_provider(
    chat_id: int,
    request: SetProviderRequest,
    chat_service: ChatService = Depends(get_chat_service),
    ai_service: AIService = Depends(get_ai_service),
    current_user: User = Depends(get_current_user),
):
    if not current_user:
        raise AuthError("Not authenticated")

    if not await chat_service.is_user_has_chat(
        user_id=current_user.id, chat_id=chat_id
    ):
        raise PermissionDeniedError(f"User does not have access to this chat")

    return await ai_service.set_provider(
        chat_id=chat_id, provider_name=request.provider
    )


# Update chat model
@router.patch("/{chat_id}/model", response_model=OperationResponse)
@log
async def update_chat_model(
    chat_id: int,
    request: SetModelRequest,
    chat_service: ChatService = Depends(get_chat_service),
    ai_service: AIService = Depends(get_ai_service),
    current_user: User = Depends(get_current_user),
):
    if not current_user:
        raise AuthError("Not authenticated")

    if not await chat_service.is_user_has_chat(
        user_id=current_user.id, chat_id=chat_id
    ):
        raise PermissionDeniedError(f"User does not have access to this chat")

    return await ai_service.set_model(chat_id=chat_id, model_name=request.model)


# Update chat title
@router.patch("/{chat_id}/title", response_model=OperationResponse)
@log
async def update_chat_title(
    chat_id: int,
    request: SetTitleRequest,
    chat_service: ChatService = Depends(get_chat_service),
    current_user: User = Depends(get_current_user),
):
    if not current_user:
        raise AuthError("Not authenticated")

    if not await chat_service.is_user_has_chat(
        user_id=current_user.id, chat_id=chat_id
    ):
        raise PermissionDeniedError(f"User does not have access to this chat")

    return await chat_service.set_title(chat_id=chat_id, new_title=request.title)


# Get chat current provider status
@router.get("/{chat_id}/status", response_model=ProviderStatus)
@log
async def get_provider_status(
    chat_id: int,
    chat_service: ChatService = Depends(get_chat_service),
    ai_service: AIService = Depends(get_ai_service),
    current_user: User = Depends(get_current_user),
):
    """Get current provider status"""

    if not current_user:
        raise AuthError("Not authenticated")

    if not await chat_service.is_user_has_chat(
        user_id=current_user.id, chat_id=chat_id
    ):
        raise PermissionDeniedError(f"User does not have access to this chat")

    return await ai_service.get_status(chat_id=chat_id)


# Delete chat
@router.delete(
    "/{chat_id}",
    summary="Delete chat by id",
    description="Delete chat by id",
    response_model=ChatResponse,
)
@log
async def delete_chat(
    chat_id: int,
    chat_service: ChatService = Depends(get_chat_service),
    current_user: User = Depends(get_current_user),
):
    if not current_user:
        raise AuthError("Not authenticated")

    if not await chat_service.is_user_has_chat(
        user_id=current_user.id, chat_id=chat_id
    ):
        raise PermissionDeniedError(f"User does not have access to this chat")

    return await chat_service.delete_chat(chat_id)


# Get a chat by id
@router.get(
    "/{chat_id}",
    summary="Get chat by id",
    description="Get a chat by id",
    response_model=ChatResponse,
)
@log
async def get_chat(
    chat_id: int,
    chat_service: ChatService = Depends(get_chat_service),
    current_user: User = Depends(get_current_user),
):
    if not current_user:
        raise AuthError("Not authenticated")
    return await chat_service.get_chat(chat_id)
