from typing import Any, Dict, Generic, List, Optional, Set, Type, TypeVar, Union
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from core.config import settings
from database import Base, CRUDBase, Chat, CRUDChat
from services.base import BaseService
from schemas.chat import ChatCreate, ChatUpdate, ChatResponse
from utils.logger import log


class ChatService(BaseService[Chat, ChatCreate, ChatUpdate, CRUDChat]):
    def __init__(self, session: AsyncSession, chat_crud: CRUDChat):
        super().__init__(session=session, crud=chat_crud)

    @log
    async def create_chat(self, chat: ChatCreate) -> ChatResponse:
        """Create a new chat"""
        created_chat = await self.crud.create_chat(self.session, chat_object=chat)
        return ChatResponse.model_validate(created_chat)

    @log
    async def get_chat(self, chat_id: int) -> ChatResponse:
        """Get a chat by id"""
        chat = await self.crud.get(self.session, chat_id)
        return ChatResponse.model_validate(chat)

    @log
    async def get_user_chats(self, user_id: int) -> List[ChatResponse]:
        """Get all chats for a user"""
        chats = await self.crud.get_user_chats(self.session, user_id=user_id)
        return [ChatResponse.model_validate(chat) for chat in chats]

    @log
    async def get_user_pinned_chats(self, user_id: int) -> List[ChatResponse]:
        """Get all pinned chats for a user"""
        chats = await self.crud.get_user_chats(
            self.session, user_id=user_id, pinned_only=True
        )
        return [ChatResponse.model_validate(chat) for chat in chats]

    @log
    async def delete_chat(self, chat_id: int) -> ChatResponse:
        """Delete chat by id"""
        deleted_chat = await self.crud.delete_chat(self.session, chat_id=chat_id)
        return ChatResponse.model_validate(deleted_chat)
