from typing import AsyncGenerator
from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from database import database, User
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
    return AuthService(session)


async def get_user_service(
    session: AsyncSession = Depends(get_db_session),
) -> UserService:
    """Get user service"""
    return UserService(session)


async def get_ai_service() -> AIService:
    """Get ai service"""
    return AIService()


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
    "get_db_session",
    "get_auth_service",
    "get_user_service",
]
