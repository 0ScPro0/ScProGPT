from typing import Any, Dict, Generic, List, Optional, Set, Type, TypeVar, Union
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from core.config import settings
from database import Base, Message
from repositories import MessageRepository
from services.base import BaseService
from schemas.message import MessageSchema, MessageResponse, MessageCreate, MessageUpdate
from schemas.ai import UserMessage, AssistantMessage
from utils.logger import log


class MessageService(
    BaseService[Message, MessageCreate, MessageUpdate, MessageRepository]
):
    def __init__(self, session: AsyncSession, message_repository: MessageRepository):
        super().__init__(repository=message_repository, session=session)

    @log
    async def create_message(self, message: MessageCreate) -> MessageResponse:
        """Create a new message in the specified chat."""
        new_message = await self.repository.create_message(
            session=self.session, message_object=message
        )
        return MessageResponse.model_validate(new_message)

    @log
    async def get_message(self, message_id: int):
        """Get a message by id."""
        return await self.repository.get_message(
            session=self.session, message_id=message_id
        )

    @log
    async def get_chat_messages(
        self, chat_id: int
    ) -> List[Union[UserMessage, AssistantMessage]]:
        """
        Get all messages in the specified chat.

        Args:
            chat_id: Current chat id

        Returns:
            List of UserMessage and AssistantMessage
        """
        # Get messages
        messages = await self.repository.get_chat_messages(
            session=self.session, chat_id=chat_id
        )

        # Validate messages
        validated_messages = []
        for message in messages:
            if message.role == "user":
                validated_messages.append(
                    UserMessage.model_validate(message, from_attributes=True)
                )
            else:
                validated_messages.append(
                    AssistantMessage.model_validate(message, from_attributes=True)
                )

        return validated_messages

    @log
    async def get_chat_response_messages(self, chat_id: int) -> List[MessageResponse]:
        """
        Get all messages in the specified chat as MessageResponse.

        Args:
            chat_id: Current chat id

        Returns:
            List of MessageResponse
        """
        # Get messages
        messages = await self.repository.get_chat_messages(
            session=self.session, chat_id=chat_id
        )

        # Validate messages
        validated_messages = [
            MessageResponse.model_validate(message) for message in messages
        ]
        return validated_messages
