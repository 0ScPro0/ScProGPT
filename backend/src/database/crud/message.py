# backend/src/database/crud/message.py
from typing import List, Optional, Dict, Any, Union
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from sqlalchemy import select

from src.utils.logger import logger, log_database_queries
from database.crud.base import CRUDBase
from database.models.message import Message
from src.schemas.message import MessageCreate, MessageUpdate


class CRUDMessage(CRUDBase[Message, MessageCreate, MessageUpdate]):
    """Class for message CRUD operations"""

    async def get_message(
        self,
        session: AsyncSession,
        *,
        message_id: int,
    ) -> Optional[Message]:
        """
        Get message by ID

        Args:
            session: Database session
            message_id: int

        Returns:
            Message object or None if message not found
        """
        message = await self.get(session=session, id=message_id)
        return message

    async def get_chat_messages(
        self, session: AsyncSession, *, chat_id: int, skip: int = 0, limit: int = 100
    ) -> List[Message]:
        """
        Get messages for a specific chat

        Args:
            session: Database session
            chat_id: int
            skip: int
            limit: int

        Returns:
            List of Message objects
        """
        messages = await self.get_by_field_multy(
            session=session,
            field_name="chat_id",
            field_value=chat_id,
            skip=skip,
            limit=limit,
        )
        return messages

    @log_database_queries
    async def get_message_with_chat(
        self, session: AsyncSession, message_id: int
    ) -> Optional[Message]:
        """
        Get message with eager-loaded chat

        Args:
            session: Database session
            message_id: int

        Returns:
            Message object or None if message not found
        """
        query = (
            select(Message)
            .where(Message.id == message_id)
            .options(selectinload(Message.chat))
        )

        result = await session.execute(query)
        return result.scalar_one_or_none()

    async def create_message(
        self,
        session: AsyncSession,
        *,
        message_object: Union[MessageCreate, Dict[str, Any]],
    ) -> Message:
        """
        Create a new message

        Args:
            session: Database session
            message_object: Union[MessageCreate, Dict[str, Any]]

        Returns:
            Message object
        """
        message = await self.create(session=session, object_in=message_object)
        return message

    @log_database_queries
    async def update_message_tokens(
        self,
        session: AsyncSession,
        *,
        message_id: int,
        prompt_tokens: int,
        completion_tokens: int,
        total_tokens: int,
        cost: float,
    ) -> Optional[Message]:
        """
        Update token usage and cost for a message

        Args:
            session: Database session
            message_id: int
            prompt_tokens: int
            completion_tokens: int
            total_tokens: int
            cost: float

        Returns:
            Message object or None if message not found
        """
        message = await self.get_message(session=session, message_id=message_id)
        if not message:
            return None

        fields = {
            "prompt_tokens": prompt_tokens,
            "completion_tokens": completion_tokens,
            "total_tokens": total_tokens,
            "cost": cost,
        }

        updated_message = await self.update_fields(
            session=session, object_id=message_id, fields=fields
        )
        return updated_message

    async def delete_message(
        self, session: AsyncSession, *, message_id: int
    ) -> Optional[Message]:
        """
        Delete message and return deleted object

        Args:
            session: Database session
            message_id: int

        Returns:
            Message object or None if message not found
        """
        deleted_message = await self.remove(session=session, id=message_id)
        return deleted_message


message_crud = CRUDMessage(Message)
