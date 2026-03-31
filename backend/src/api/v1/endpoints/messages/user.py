from fastapi import APIRouter, Depends

from api.dependencies import (
    MessageService,
    ChatService,
    get_message_service,
    get_chat_service,
)

from database import User

from core.exceptions import AuthError, HTTPNotImplementedError, PermissionDeniedError
from core.security import get_current_user

from utils.logger import log
from utils.serializator import serialize_model_to_json

router = APIRouter(prefix="/user", tags=["messages"])


# @router.post("/create")
async def create_user_message(
    chat_id: int,
    content: str,
    chat_service: ChatService = Depends(get_chat_service),
    message_service: MessageService = Depends(get_message_service),
    current_user: User = Depends(get_current_user),
):
    """Create message from user"""
    if not current_user:
        raise AuthError(detail="Not authenticated")

    if not await chat_service.is_user_has_chat(
        user_id=current_user.id, chat_id=chat_id
    ):
        raise PermissionDeniedError(f"User does not have access to this chat")

    raise HTTPNotImplementedError("Not implemented")  # TODO
