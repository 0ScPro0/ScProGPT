from typing import Any, Dict, Generic, List, Optional, Set, Type, TypeVar, Union
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from core.config import settings
from database import Base, CRUDBase, Message, CRUDMessage, message_crud
from services.base import BaseService
from schemas.message import MessageSchema, MessageCreate, MessageUpdate


class MessageService(BaseService[Message, MessageCreate, MessageUpdate, CRUDMessage]):
    def __init__(self, session: AsyncSession, message_crud: CRUDMessage):
        super().__init__(crud=message_crud, session=session)

    async def create_message(self, message: MessageCreate):
        """Create a new message in the specified chat."""
        return await self.crud.create_message(
            session=self.session, message_object=message
        )

    async def get_message(self, message_id: int):
        """Get a message by id."""
        return await self.crud.get_message(session=self.session, message_id=message_id)

    async def get_chat_messages(self, chat_id: int):
        """Get all messages in the specified chat."""
        return await self.crud.get_chat_messages(session=self.session, chat_id=chat_id)
