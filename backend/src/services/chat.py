from typing import Any, Dict, Generic, List, Optional, Set, Type, TypeVar, Union
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from core.config import settings
from database import Base, Chat
from repositories import ChatRepository
from services.base import BaseService
from schemas.chat import ChatCreate, ChatUpdate, ChatResponse
from schemas.base import OperationResponse
from utils.logger import log


class ChatService(BaseService[Chat, ChatCreate, ChatUpdate, ChatRepository]):
    def __init__(self, session: AsyncSession, chat_repository: ChatRepository):
        super().__init__(session=session, repository=chat_repository)

    @log
    async def create_chat(self, chat: ChatCreate) -> ChatResponse:
        """Create a new chat"""
        created_chat = await self.repository.create_chat(self.session, chat_object=chat)
        return ChatResponse.model_validate(created_chat)

    @log
    async def get_chat(self, chat_id: int) -> ChatResponse:
        """Get a chat by id"""
        chat = await self.repository.get(self.session, chat_id)
        return ChatResponse.model_validate(chat)

    @log
    async def get_user_chats(self, user_id: int) -> List[ChatResponse]:
        """Get all chats for a user"""
        chats = await self.repository.get_user_chats(self.session, user_id=user_id)
        return [ChatResponse.model_validate(chat) for chat in chats]

    @log
    async def get_user_pinned_chats(self, user_id: int) -> List[ChatResponse]:
        """Get all pinned chats for a user"""
        chats = await self.repository.get_user_chats(
            self.session, user_id=user_id, pinned_only=True
        )
        return [ChatResponse.model_validate(chat) for chat in chats]

    @log
    async def delete_chat(self, chat_id: int) -> ChatResponse:
        """Delete chat by id"""
        deleted_chat = await self.repository.delete_chat(self.session, chat_id=chat_id)
        return ChatResponse.model_validate(deleted_chat)

    @log
    async def set_title(self, chat_id: int, new_title: str) -> OperationResponse:
        updated_chat = await self.repository.update_field(
            self.session, object_id=chat_id, field_name="title", field_value=new_title
        )
        return OperationResponse(
            success=True,
            message="Set new chat title",
            previous_value=None,
            new_value=updated_chat.title,
        )

    @log
    async def is_user_has_chat(self, user_id: int, chat_id: int) -> bool:
        """Check is user has the specified chat"""
        chat = await self.repository.get_chat_by_user_and_id(
            self.session, user_id=user_id, chat_id=chat_id
        )
        if not chat:
            return False
        return True
