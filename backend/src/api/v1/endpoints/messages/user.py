from fastapi import APIRouter, Depends

from api.dependencies import UserService, get_user_service
from core.exceptions import AuthError
from database import User
from core.security import get_current_user
from utils.logger import logger

router = APIRouter(prefix="/user", tags=["messages"])


@router.post("/create")
async def create_user_message(
    chat_id: int,
    user_service: UserService = Depends(get_user_service),
    current_user: User = Depends(get_current_user),
):
    """Create message from user"""
    if not current_user:
        raise AuthError(detail="Not authenticated")
