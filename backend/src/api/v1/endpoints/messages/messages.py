from typing import List

from fastapi import APIRouter, Depends, Path

from api.v1.endpoints.messages.assistant import router as assistant_router
from api.v1.endpoints.messages.user import router as user_router

from api.dependencies import MessageService, get_message_service

from database import User

from core.exceptions import AuthError
from core.security import get_current_user

from schemas.ai import GenerateRequest, ProviderResponse, ProviderResponseStream
from schemas.message import MessageCreate, MessageResponse

from utils.logger import log
from utils.serializator import serialize_model_to_json

router = APIRouter(prefix="/chats/{chat_id}/messages", tags=["messages"])

router.include_router(assistant_router)
router.include_router(user_router)


@router.get("/", response_model=List[MessageResponse])
@log
async def get_chat_messages(
    chat_id: int = Path(..., description="The ID of the chat"),
    message_service: MessageService = Depends(get_message_service),
    current_user: User = Depends(get_current_user),
):
    if not current_user:
        raise AuthError(detail="Not authenticated")
    return await message_service.get_chat_messages(chat_id=chat_id)
