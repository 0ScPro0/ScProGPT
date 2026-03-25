from fastapi import APIRouter, Depends

from api.dependencies import (
    UserService,
    get_user_service,
)
from core.exceptions import PermissionDeniedError, AuthError
from database import User
from core.security import get_current_user
from utils.logger import log

router = APIRouter(prefix="/users", tags=["users"])


# Get all users
@router.get("/")
@log
async def get_all_users(
    user_service: UserService = Depends(get_user_service),
    current_user: User = Depends(get_current_user),
):
    if not current_user or not current_user.is_superuser:
        raise PermissionDeniedError(detail="Not enough permissions")
    return await user_service.get_all_users()


# Get current user
@router.get("/me")
@log
async def get_current_user_endpoint(
    user_service: UserService = Depends(get_user_service),
    current_user: User = Depends(get_current_user),
):
    if not current_user:
        raise AuthError(detail="Not authneticated")
    return await user_service.get_user(current_user.id)


# Get user by id
@router.get("/{user_id}")
@log
async def get_user(
    user_id: int,
    user_service: UserService = Depends(get_user_service),
    current_user: User = Depends(get_current_user),
):
    if not current_user or not current_user.is_superuser:
        raise PermissionDeniedError(detail="Not enough permissions")
    return await user_service.get_user(user_id)
