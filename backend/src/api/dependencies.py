from typing import AsyncGenerator
from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from database import database, User, chat_crud, message_crud, user_crud
from schemas.auth import (
    SignInRequest,
    SignUpRequest,
    SignInResponse,
    SignUpResponse,
    Token,
    TokenRefreshRequest,
    TokenRefreshResponse,
)
from schemas.user import UserSchema, UserResponse
from services.auth import AuthService
from services.chat import ChatService
from services.message import MessageService
from services.user import UserService
from services.ai.service import AIService


async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    """Get database session"""
    async for session in database.get_session():
        try:
            yield session
        finally:
            await session.close()
        break


async def get_auth_service(
    session: AsyncSession = Depends(get_db_session),
) -> AuthService:
    """Get auth service"""
    return AuthService(session, user_crud)


async def get_user_service(
    session: AsyncSession = Depends(get_db_session),
) -> UserService:
    """Get user service"""
    return UserService(session, user_crud)


async def get_chat_service(
    session: AsyncSession = Depends(get_db_session),
) -> ChatService:
    """Get chat service"""
    return ChatService(session, chat_crud)


async def get_message_service(
    session: AsyncSession = Depends(get_db_session),
) -> MessageService:
    """Get message service"""
    return MessageService(session, message_crud)


async def get_ai_service(
    session: AsyncSession = Depends(get_db_session),
) -> AIService:
    """Get ai service"""
    return AIService(session)


__all__ = [
    "SignInRequest",
    "SignUpRequest",
    "Token",
    "TokenRefreshRequest",
    "TokenRefreshResponse",
    "SignInResponse",
    "SignUpResponse",
    "AuthService",
    "UserService",
    "UserSchema",
    "UserResponse",
    "AIService",
    "get_db_session",
    "get_auth_service",
    "get_user_service",
    "get_chat_service",
    "get_message_service",
    "get_ai_service",
]
