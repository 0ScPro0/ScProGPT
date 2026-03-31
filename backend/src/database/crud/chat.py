# backend/src/database/crud/chat.py
from typing import List, Optional, Dict, Any, Union
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from sqlalchemy import select, desc, func

from utils.logger import logger, log_database_queries
from database.crud.base import CRUDBase
from database.models.chat import Chat
from schemas.chat import ChatCreate, ChatUpdate


class CRUDChat(CRUDBase[Chat, ChatCreate, ChatUpdate]):
    """Class for chat CRUD operations"""

    async def get_chat(
        self,
        session: AsyncSession,
        *,
        chat_id: int,
    ) -> Optional[Chat]:
        """
        Get chat by id

        Args:
            session: Database session
            chat_id: int

        Returns:
            Chat object or None if chat not found
        """
        chat = await self.get(session=session, id=chat_id)
        return chat

    async def get_user_chats(
        self,
        session: AsyncSession,
        *,
        user_id: int,
        pinned_only: bool = False,
        skip: int = 0,
        limit: int = 100,
    ) -> List[Chat]:
        """
        Get user's chats

        Args:
            session: Database session
            user_id: int
            pinned_only: bool
            skip: int
            limit: int

        Returns:
            List of Chat objects
        """
        chats: List[Chat] = await self.get_by_field_multy(
            session=session,
            field_name="user_id",
            field_value=user_id,
            skip=skip,
            limit=limit,
        )

        if pinned_only:
            chats = [chat for chat in chats if chat.pinned]

        return chats

    async def get_chat_by_user(
        self, session: AsyncSession, *, user_id: int
    ) -> Optional[Chat]:
        """
        Get chat by user

        Args:
            session: Database session
            user_id: int

        Returns:
            Chat or None if not found
        """
        chat = await self.get_by_field(
            session=session, field_name="user_id", field_value=user_id
        )
        return chat

    @log_database_queries
    async def get_chat_with_messages(
        self, session: AsyncSession, chat_id: int, user_id: Optional[int] = None
    ) -> Optional[Chat]:
        """
        Get chat with eager-loaded messages

        Args:
            session: Database session
            chat_id: int
            user_id: Optional[int]

        Returns:
            Chat object or None if chat not found
        """
        query = (
            select(Chat).where(Chat.id == chat_id).options(selectinload(Chat.messages))
        )

        if user_id is not None:
            query = query.where(Chat.user_id == user_id)

        result = await session.execute(query)
        return result.scalar_one_or_none()

    async def get_chat_provider(
        self,
        session: AsyncSession,
        *,
        chat_id: int,
    ) -> str:
        """
        Get current chat provider name

        Args:
            session: Database session
            chat_id: int

        Returns:
            Current chat provider name
        """
        chat = await self.get_chat(session=session, chat_id=chat_id)
        return chat.provider

    async def get_chat_model(
        self,
        session: AsyncSession,
        *,
        chat_id: int,
    ) -> str:
        """
        Get current chat model

        Args:
            session: Database session
            chat_id: int

        Returns:
            Current chat model
        """
        chat = await self.get_chat(session=session, chat_id=chat_id)
        return chat.model

    async def create_chat(
        self, session: AsyncSession, *, chat_object: Union[ChatCreate, Dict[str, Any]]
    ) -> Chat:
        """
        Create chat

        Args:
            session: Database session
            chat_object: Union[ChatCreate, Dict[str, Any]]

        Returns:
            Chat object
        """
        chat = await self.create(session=session, object_in=chat_object)
        return chat

    async def pin_chat(
        self,
        session: AsyncSession,
        *,
        chat_id: int,
    ) -> Optional[Chat]:
        """
        Pin chat

        Args:
            session: Database session
            chat_id: int

        Returns:
            Chat object or None if chat not found
        """
        chat = await self.get_chat(session=session, chat_id=chat_id)
        if not chat:
            return None

        updated_chat = await self.update_field(
            session=session, object_id=chat_id, field_name="pinned", field_value=True
        )
        return updated_chat

    async def unpin_chat(
        self, session: AsyncSession, *, chat_id: int, user_id: int
    ) -> Optional[Chat]:
        """
        Unpin chat

        Args:
            session: Database session
            chat_id: int
            user_id: int

        Returns:
            Chat object or None if chat not found
        """
        chat = await self.get_chat(session=session, chat_id=chat_id)
        if not chat:
            return None

        updated_chat = await self.update_field(
            session=session, object_id=chat_id, field_name="pinned", field_value=False
        )
        return updated_chat

    async def update_chat_position(
        self, session: AsyncSession, *, chat_id: int, position: int
    ) -> Optional[Chat]:
        """
        Update chat position in sidebar

        Args:
            session: Database session
            chat_id: int
            position: int

        Returns:
            Chat object or None if chat not found
        """
        chat = await self.get_chat(session=session, chat_id=chat_id)
        if not chat:
            return None

        updated_chat = await self.update_field(
            session=session,
            object_id=chat_id,
            field_name="position",
            field_value=position,
        )
        return updated_chat

    async def update_chat_model(
        self, session: AsyncSession, *, chat_id: int, model: str
    ) -> Optional[Chat]:
        """
        Update ai model for chat

        Args:
            session: Database session
            chat_id: int
            model: str

        Returns:
            Chat object or None if chat not found
        """

        chat = await self.get_chat(session=session, chat_id=chat_id)
        if not chat:
            return None

        updated_chat = await self.update_field(
            session=session, object_id=chat_id, field_name="model", field_value=model
        )
        return updated_chat

    async def update_chat_provider_and_model(
        self, session: AsyncSession, *, chat_id: int, provider: str, model: str
    ) -> Optional[Chat]:
        """
        Update ai provider and model for chat

        Args:
            session: Database session
            chat_id: int
            provider: str
            model: str

        Returns:
            Chat object or None if chat not found
        """

        chat = await self.get_chat(session=session, chat_id=chat_id)
        if not chat:
            return None

        fields = {"provider": provider, "model": model}

        updated_chat = await self.update_fields(
            session=session, object_id=chat_id, fields=fields
        )
        return updated_chat

    async def update_system_prompt(
        self, session: AsyncSession, *, chat_id: int, user_id: int, prompt: str
    ) -> Optional[Chat]:
        """
        Update system prompt for chat

        Args:
            session: Database session
            chat_id: int
            user_id: int
            prompt: str

        Returns:
            Chat object or None if chat not found
        """

        chat = await self.get_chat(session=session, chat_id=chat_id)
        if not chat:
            return None

        updated_chat = await self.update_field(
            session=session,
            object_id=chat_id,
            field_name="system_prompt",
            field_value=prompt,
        )
        return updated_chat

    async def delete_chat(
        self, session: AsyncSession, *, chat_id: int
    ) -> Optional[Chat]:
        """
        Delete chat

        Args:
            session: Database session
            chat_id: int

        Returns:
            Chat object or None if chat not found
        """
        chat = await self.get_chat(session=session, chat_id=chat_id)
        if not chat:
            return None

        deleted_chat = await self.delete(session=session, object_id=chat_id)
        return deleted_chat


chat_crud = CRUDChat(Chat)
