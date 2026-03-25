from typing import Any, Dict, Generic, List, Optional, Set, Type, TypeVar, Union
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from core.config import settings
from database import Base, CRUDBase, Chat, CRUDChat
from services.base import BaseService
from schemas.chat import ChatCreate, ChatUpdate


class ChatService(BaseService[Chat, ChatCreate, ChatUpdate, CRUDChat]):
    def __init__(self, session: AsyncSession, chat_crud: CRUDChat):
        super().__init__(session=session, crud=chat_crud)

    async def create_chat(self, chat: ChatCreate) -> Chat:
        """Create a new chat"""
        return await self.crud.create_chat(self.session, chat_object=chat)

    async def get_chat(self, chat_id: int) -> Chat:
        """Get a chat by id"""
        return await self.crud.get(self.session, chat_id)
