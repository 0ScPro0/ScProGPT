from typing import List
import json
from fastapi import APIRouter, Depends

from api.dependencies import get_chat_service
from core.exceptions import AuthError
from database import User
from core.security import get_current_user
from services.chat import ChatService
from schemas.chat import ChatResponse, ChatCreate
from utils.logger import log, logger

router = APIRouter(prefix="/chats", tags=["chats"])


# Create a new chat
@router.post(
    "/create",
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
    "/user",
    summary="Get user chats",
    description="Get all chats for the current user",
    response_model=List[ChatResponse],
)
@log
async def get_user_chats(
    current_user: User = Depends(get_current_user),
    chat_service: ChatService = Depends(get_chat_service),
):
    if not current_user:
        raise AuthError("Not authenticated")
    return await chat_service.get_user_chats(current_user.id)


# Delete chat
@router.delete(
    "/{chat_id}/delete",
    summary="Delete chat by id",
    description="Delete chat by id",
    response_model=ChatResponse,
)
@log
async def delete_chat(
    chat_id: int,
    current_user: User = Depends(get_current_user),
    chat_service: ChatService = Depends(get_chat_service),
):
    if not current_user:
        raise AuthError("Not authenticated")
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
    current_user: User = Depends(get_current_user),
    chat_service: ChatService = Depends(get_chat_service),
):
    if not current_user:
        raise AuthError("Not authenticated")
    return await chat_service.get_chat(chat_id)
