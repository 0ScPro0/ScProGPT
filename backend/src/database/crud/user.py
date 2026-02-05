from typing import Optional, List, Type, Any, Dict
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, or_

from crud.base import CRUDBase
from database.models.user import User 
from src.schemas.user import UserCreate, UserUpdate

class CRUDUser(CRUDBase[User, UserCreate, UserUpdate]):
    """Class for user CRUD operations"""

    async def get_by_email(
        self,
        session: AsyncSession,
        email: str
    ) -> Optional[User]:
        """Get user by email"""

        user = await self.get_by_field(
            session=session,
            field_name="email",
            field_value=email
        )
        return user

    async def get_by_username(
        self,
        session: AsyncSession,
        username: str
    ) -> Optional[User]:
        """Get user by username"""

        user = await self.get_by_field(
            session=session,
            field_name="username",
            field_value=username
        )
        return user

    async def update_api_key(
        self,
        session: AsyncSession,
        *,
        user_id: int,
        api_key: str
    ) -> Optional[User]:
        """Update user api key"""
        
        updated_user = await self.update_field(
            session=session,
            object_id=user_id,
            field_name="api_key",
            field_value=api_key
        )
        return updated_user

    async def update_password(
        self,
        session: AsyncSession,
        *,
        user_id: int,
        password_hash: str
    ) -> Optional[User]:
        """Update user password"""
        
        updated_user = await self.update_field(
            session=session,
            object_id=user_id,
            field_name="password_hash",
            field_value=password_hash
        )
        return updated_user
    
    async def update_settings(
        self,
        session: AsyncSession,
        *,
        user_id: int,
        settings: Dict[str, Any]
    ) -> Optional[User]:
        """Update user password"""
        
        updated_user = await self.update_field(
            session=session,
            object_id=user_id,
            field_name="settings",
            field_value=settings
        )
        return updated_user

    async def activate(
        self,
        session: AsyncSession,
        *,
        user_id: int
    ) -> Optional[User]:
        """Activate user"""
        
        updated_user = await self.update_field(
            session=session,
            object_id=user_id,
            field_name="is_active",
            field_value=True
        )
        return updated_user

    async def deactivate(
        self,
        session: AsyncSession,
        *,
        user_id: int,
    ) -> Optional[User]:
        """Deactivate user"""
        
        updated_user = await self.update_field(
            session=session,
            object_id=user_id,
            field_name="is_active",
            field_value=False
        )
        return updated_user
    
    async def delete_user(
        self,
        session: AsyncSession,
        *,
        user_id: int
    ) -> Optional[User]:
        """Delete user and return deleted object"""

        deleted_user = await self.remove_object_by_id(
            session=session,
            id=user_id
        )
        return deleted_user