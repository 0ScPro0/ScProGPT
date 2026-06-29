from typing import Optional, List, Type, Any, Dict, Union
from pydantic import EmailStr
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, or_
from datetime import datetime

from utils.logger import logger, log_database_queries
from database.models.user import User
from schemas.user import UserCreate, UserUpdate
from repositories.base import BaseRepository


class UserRepository(BaseRepository[User, UserCreate, UserUpdate]):
    """Class for user CRUD operations"""

    async def get_by_email(
        self, session: AsyncSession, email: EmailStr
    ) -> Optional[User]:
        """
        Get user by email

        Args:
            session: Database session
            email: EmailStr

        Returns:
            User object or None if not found
        """
        user = await self.get_by_field(
            session=session, field_name="email", field_value=email
        )
        return user

    async def get_by_username(
        self, session: AsyncSession, username: str
    ) -> Optional[User]:
        """
        Get user by username

        Args:
            session: Database session
            username: str

        Returns:
            User object or None if not found
        """
        user = await self.get_by_field(
            session=session, field_name="username", field_value=username
        )
        return user

    async def create_user(
        self, session: AsyncSession, *, user_object: Union[UserCreate, Dict[str, Any]]
    ) -> User:
        """
        Create user

        Args:
            session: Database session
            user_object: UserCreate object or dict

        Returns:
            Created user object
        """
        user = await self.create(session=session, object_in=user_object)
        return user

    async def update_api_key(
        self, session: AsyncSession, *, user_id: int, api_key: str
    ) -> Optional[User]:
        """
        Update user api key

        Args:
            session: Database session
            user_id: int
            api_key: str

        Returns:
           Updated user object or None if not found
        """
        updated_user = await self.update_field(
            session=session,
            object_id=user_id,
            field_name="api_key",
            field_value=api_key,
        )
        return updated_user

    async def update_password(
        self, session: AsyncSession, *, user_id: int, password_hash: str
    ) -> Optional[User]:
        """
        Update user password

        Args:
            session: Database session
            user_id: int
            password_hash: str

        Returns:
            Updated user object or None if not found
        """
        updated_user = await self.update_field(
            session=session,
            object_id=user_id,
            field_name="password_hash",
            field_value=password_hash,
        )
        return updated_user

    async def update_settings(
        self, session: AsyncSession, *, user_id: int, settings: Dict[str, Any]
    ) -> Optional[User]:
        """
        Update user password

        Args:
            session: Database session
            user_id: int
            settings: Dict[str, Any]

        Returns:
            Updated user object or None if not found
        """
        updated_user = await self.update_field(
            session=session,
            object_id=user_id,
            field_name="settings",
            field_value=settings,
        )
        return updated_user

    async def update_refresh_token(
        self,
        session: AsyncSession,
        *,
        user_id: int,
        refresh_token: str,
        expires_at: datetime,
    ) -> Optional[User]:
        """
        Update user refresh token and its expiration time

        Args:
            session: Database session
            user_id: int
            refresh_token: str
            expires_at: datetime

        Returns:
            Updated user object or None if not found
        """
        updated_user = await self.update_fields(
            session=session,
            object_id=user_id,
            fields={
                "refresh_token": refresh_token,
                "refresh_token_expires_at": expires_at,
            },
        )
        return updated_user

    async def clear_refresh_token(
        self, session: AsyncSession, *, user_id: int
    ) -> Optional[User]:
        """
        Clear user refresh token (set to None)

        Args:
            session: Database session
            user_id: int

        Returns:
            Updated user object or None if not found
        """
        updated_user = await self.update_fields(
            session=session,
            object_id=user_id,
            fields={"refresh_token": None, "refresh_token_expires_at": None},
        )
        return updated_user

    async def activate(self, session: AsyncSession, *, user_id: int) -> Optional[User]:
        """
        Activate user

        Args:
            session: Database session
            user_id: int

        Returns:
            Activated user object or None if not found
        """
        updated_user = await self.update_field(
            session=session, object_id=user_id, field_name="is_active", field_value=True
        )
        return updated_user

    async def deactivate(
        self,
        session: AsyncSession,
        *,
        user_id: int,
    ) -> Optional[User]:
        """
        Deactivate user

        Args:
            session: Database session
            user_id: int

        Returns:
            Deactivated user object or None if not found
        """
        updated_user = await self.update_field(
            session=session,
            object_id=user_id,
            field_name="is_active",
            field_value=False,
        )
        return updated_user

    async def delete_user(
        self, session: AsyncSession, *, user_id: int
    ) -> Optional[User]:
        """
        Delete user

        Args:
            session: Database session
            user_id: int

        Returns:
            Deleted user object or None if not found
        """
        deleted_user = await self.delete(session=session, id=user_id)
        return deleted_user

    async def is_active(self, session: AsyncSession, *, user_id: int) -> bool:
        """
        Check if user is active

        Args:
            session: Database session
            user_id: int

        Returns:
            bool: True if user is active, False otherwise
        """
        user = await self.get(session=session, id=user_id)
        return user.is_active if user else False


user_repository = UserRepository(User)
