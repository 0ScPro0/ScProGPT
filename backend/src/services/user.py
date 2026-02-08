from datetime import timedelta, datetime, timezone
from typing import List
from sqlalchemy.ext.asyncio import AsyncSession

from core.config import settings
from utils.logger import logger, log
from api.exceptions import PermissionDeniedError
from core.security import (
    create_access_token,
    create_refresh_token,
    hash_password,
    verify_password,
    decode_token,
    get_current_user,
)
from database import User, CRUDUser, user_crud
from schemas.user import (
    UserSchema,
    UserCreate,
    UserResponse,
)
from schemas.user import UserSchema, UserCreate
from services.base import BaseService


class UserService(BaseService):
    """Service for authentication and authorization"""

    def __init__(self, session: AsyncSession):
        super().__init__(session=session, crud=user_crud)

    async def get_all_users(self) -> List[UserResponse]:
        users = await self.crud.get_multy(self.session, skip=0, limit=10, order_by=None)
        return [UserResponse.model_validate(user) for user in users]
