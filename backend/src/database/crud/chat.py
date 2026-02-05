# backend/src/database/crud/chat.py
from typing import List, Optional, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc, func

from crud.base import CRUDBase
from database.models.chat import Chat
from src.schemas.chat import CreateChat, UpdateChat

class CRUDChat(CRUDBase[Chat, CreateChat, UpdateChat]):
    """CRUD операции для Chat с доп методами"""
    
    async def get_user_chats(
        self, 
        db: AsyncSession, 
        *, 
        user_id: int,
        pinned_only: bool = False,
        skip: int = 0,
        limit: int = 100
    ) -> List[Chat]:
        """Получить чаты пользователя"""
        ...
    
    async def get_chat_with_messages(
        self,
        db: AsyncSession,
        *,
        chat_id: int,
        user_id: Optional[int] = None
    ) -> Optional[Chat]:
        """Получить чат с сообщениями"""
        ...
    
    async def pin_chat(
        self,
        db: AsyncSession,
        *,
        chat_id: int,
        user_id: int,
        position: Optional[int] = None
    ) -> Chat:
        """Закрепить чат"""
        ...
    
    async def unpin_chat(
        self,
        db: AsyncSession,
        *,
        chat_id: int,
        user_id: int
    ) -> Chat:
        """Открепить чат"""
        ...
    
    async def update_pinned_order(
        self,
        db: AsyncSession,
        *,
        user_id: int,
        chat_order: List[int]
    ) -> List[Chat]:
        """Обновить порядок закрепленных чатов"""
        ...
    
    async def update_chat_model(
        self,
        db: AsyncSession,
        *,
        chat_id: int,
        user_id: int,
        model: str
    ) -> Chat:
        """Обновить модель AI для чата"""
        ...
    
    async def update_system_prompt(
        self,
        db: AsyncSession,
        *,
        chat_id: int,
        user_id: int,
        prompt: str
    ) -> Chat:
        """Обновить системный промпт"""
        ...
    
    async def get_chat_stats(
        self,
        db: AsyncSession,
        *,
        user_id: int
    ) -> Dict[str, Any]:
        """Получить статистику по чатам пользователя"""
        ...
    
    async def search_chats(
        self,
        db: AsyncSession,
        *,
        user_id: int,
        query: str,
        skip: int = 0,
        limit: int = 50
    ) -> List[Chat]:
        """Поиск по названию чатов"""
        ...
