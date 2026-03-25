from datetime import timedelta, datetime, timezone
from typing import List
from sqlalchemy.ext.asyncio import AsyncSession

from core.config import settings
from utils.logger import logger, log
from database import User, CRUDUser, user_crud
from schemas.user import (
    UserSchema,
    UserCreate,
    UserResponse,
)
from schemas.user import UserSchema, UserCreate, UserUpdate
from services.base import BaseService


class UserService(BaseService[User, UserCreate, UserUpdate, CRUDUser]):
    """Service for working with User"""

    def __init__(self, session: AsyncSession, user_crud: CRUDUser):
        super().__init__(
            crud=user_crud,
            session=session,
        )

    async def get_all_users(self) -> List[UserResponse]:
        users = await self.crud.get_many(self.session, skip=0, limit=10, order_by=None)
        return [UserResponse.model_validate(user) for user in users]

    async def get_user(self, user_id: int) -> UserResponse:
        user = await self.crud.get(self.session, user_id)
        return UserResponse.model_validate(user)

    async def update_user(self, user_id: int, user: UserUpdate) -> UserResponse:
        user = await self.crud.update(self.session, user_id, user)
        return UserResponse.model_validate(user)

    async def delete_user(self, user_id: int) -> UserResponse:
        user = await self.crud.delete(self.session, user_id)
        return UserResponse.model_validate(user)
