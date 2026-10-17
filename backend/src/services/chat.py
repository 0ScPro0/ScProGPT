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

DEFAULT_CHAT_TITLES = {"New chat", "New Chat", ""}


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

    @log
    async def toggle_chat_pin(self, chat_id: int) -> Optional[ChatResponse]:
        """Pin/unpin the chat and return the updated chat."""
        chat = await self.repository.get(self.session, chat_id)
        if not chat:
            return None

        updated_chat = await self.repository.update_field(
            session=self.session,
            object_id=chat_id,
            field_name="pinned",
            field_value=not chat.pinned,
        )
        return ChatResponse.model_validate(updated_chat)

    @log
    async def apply_auto_title(self, chat_id: int, prompt: str) -> Optional[str]:
        """
        Auto-name the chat from the first user message.

        If the chat still has a default title ("New chat"/"New Chat"),
        it is replaced with a trimmed excerpt of the prompt (the topic of
        the dialog is usually the first generation).

        Returns:
            The assigned title, or None if nothing was changed.
        """
        chat = await self.repository.get(self.session, chat_id)
        if not chat or chat.title not in DEFAULT_CHAT_TITLES:
            return None

        title = self._make_title(prompt)
        if not title:
            return None

        await self.repository.update_field(
            session=self.session,
            object_id=chat_id,
            field_name="title",
            field_value=title,
        )
        return title

    @staticmethod
    def _make_title(prompt: str, limit: int = 30) -> Optional[str]:
        """Trim the user prompt into a short chat title."""
        cleaned = " ".join(prompt.split())
        if not cleaned:
            return None
        if len(cleaned) <= limit:
            return cleaned
        return cleaned[: limit + 1].rstrip() + "…"
