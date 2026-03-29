from fastapi import APIRouter, Depends

from api.dependencies import MessageService, get_message_service

from database import User

from core.exceptions import AuthError, HTTPNotImplementedError
from core.security import get_current_user

from schemas.ai import GenerateRequest, ProviderResponse, ProviderResponseStream
from schemas.message import MessageCreate, MessageResponse

from utils.logger import log
from utils.serializator import serialize_model_to_json

router = APIRouter(prefix="/user", tags=["messages"])


@router.post("/create")
async def create_user_message(
    chat_id: int,
    content: str,
    message_service: MessageService = Depends(get_message_service),
    current_user: User = Depends(get_current_user),
):
    """Create message from user"""
    if not current_user:
        raise AuthError(detail="Not authenticated")
    raise HTTPNotImplementedError("Not implemented")  # TODO
