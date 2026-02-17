from fastapi import APIRouter, Depends

from api.dependencies import (
    UserService,
    get_user_service,
)
from core.exceptions import PermissionDeniedError
from database import User
from core.security import get_current_user

router = APIRouter(prefix="/users", tags=["users"])


@router.get("/")
async def get_all_users(
    user_service: UserService = Depends(get_user_service),
    current_user: User = Depends(get_current_user),
):
    if not current_user or not current_user.is_superuser:
        raise PermissionDeniedError(detail="Not enough permissions")
    return await user_service.get_all_users()
