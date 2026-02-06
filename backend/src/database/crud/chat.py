# backend/src/database/crud/chat.py
from typing import List, Optional, Dict, Any, Union
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from sqlalchemy import select, desc, func

from src.utils.logger import logger, log_database_queries
from crud.base import CRUDBase
from database.models.chat import Chat
from src.schemas.chat import ChatCreate, ChatUpdate

class CRUDChat(CRUDBase[Chat, ChatCreate, ChatUpdate]):
    """Class for chat CRUD operations"""

    async def get_chat(
        self,
        session: AsyncSession,
        *,
        chat_id: int,
    ) -> Optional[Chat]:
        """Get chat"""
        
        chat = await self.get(
            session=session,
            id=chat_id
        )
        return chat

    async def get_user_chats(
        self, 
        session: AsyncSession, 
        *, 
        user_id: int,
        pinned_only: bool = False,
        skip: int = 0,
        limit: int = 100
    ) -> List[Chat]:
        """Get user's chats"""
        
        chats = await self.get_by_field_multy(
            session=session,
            field_name="user_id",
            field_value=user_id,
            skip=skip,
            limit=limit
        )
        return chats
    
    @log_database_queries
    async def get_chat_with_messages(
        self,
        session: AsyncSession,
        chat_id: int,
        user_id: Optional[int] = None
    ) -> Optional[Chat]:
        """
        Pure CRUD method: Get chat with eager-loaded messages.
        Returns SQLAlchemy Chat object or None.
        """
        query = (
            select(Chat)
            .where(Chat.id == chat_id)
            .options(selectinload(Chat.messages))
        )
        
        if user_id is not None:
            query = query.where(Chat.user_id == user_id)
        
        result = await session.execute(query)
        return result.scalar_one_or_none()

    async def create_chat(
        self,
        session: AsyncSession,
        *,
        chat_object: Union[ChatCreate, Dict[str, Any]]
    ) -> Chat:
        """Create chat"""

        chat = await self.create(
            session=session,
            object_in=chat_object
        )
        return chat
    
    async def pin_chat(
        self,
        session: AsyncSession,
        *,
        chat_id: int,
    ) -> Optional[Chat]:
        """Pin chat"""
        
        chat = await self.get_chat(
            session=session,
            chat_id=chat_id
        )
        if not chat:
            return None

        updated_chat = await self.update_field(
            session=session,
            object_id=chat_id,
            field_name="pinned",
            field_value=True
        )
        return updated_chat
    
    async def unpin_chat(
        self,
        session: AsyncSession,
        *,
        chat_id: int,
        user_id: int
    ) -> Optional[Chat]:
        """Unpin chat"""
        
        chat = await self.get_chat(
            session=session,
            chat_id=chat_id
        )
        if not chat:
            return None

        updated_chat = await self.update_field(
            session=session,
            object_id=chat_id,
            field_name="pinned",
            field_value=False
        )
        return updated_chat
    
    async def update_chat_position(
        self,
        session: AsyncSession,
        *,
        chat_id: int,
        position: int
    ) -> Optional[Chat]:
        """Update chat position in sidebar"""
        
        chat = await self.get_chat(
            session=session,
            chat_id=chat_id
        )
        if not chat:
            return None
        
        updated_chat = await self.update_field(
            session=session,
            object_id=chat_id,
            field_name="position",
            field_value=position
        )
        return updated_chat
    
    async def update_chat_model(
        self,
        session: AsyncSession,
        *,
        chat_id: int,
        model: str
    ) -> Optional[Chat]:
        """Update ai model for chat"""
        
        chat = await self.get_chat(
            session=session,
            chat_id=chat_id
        )
        if not chat:
            return None
        
        updated_chat = await self.update_field(
            session=session,
            object_id=chat_id,
            field_name="model",
            field_value=model
        )
        return updated_chat
    
    async def update_chat_provider_and_model(
        self,
        session: AsyncSession,
        *,
        chat_id: int,
        provider: str,
        model: str
    ) -> Optional[Chat]:
        """Update ai provider and model for chat"""

        chat = await self.get_chat(
            session=session,
            chat_id=chat_id
        )
        if not chat:
            return None
        
        fields = {"provider": provider, "model": model}
        
        updated_chat = await self.update_fields(
            session=session,
            object_id=chat_id,
            fields=fields
        )
        return updated_chat
    
    async def update_system_prompt(
        self,
        session: AsyncSession,
        *,
        chat_id: int,
        user_id: int,
        prompt: str
    ) -> Optional[Chat]:
        """Update system prompt for chat"""

        chat = await self.get_chat(
            session=session,
            chat_id=chat_id
        )
        if not chat:
            return None
        
        updated_chat = await self.update_field(
            session=session,
            object_id=chat_id,
            field_name="system_prompt",
            field_value=prompt
        )
        return updated_chat

chat_crud = CRUDChat(Chat)