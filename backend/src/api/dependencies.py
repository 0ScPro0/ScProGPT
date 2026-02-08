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
from services.auth import AuthService


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


__all__ = [
    "SignInRequest",
    "SignUpRequest",
    "Token",
    "TokenRefreshRequest",
    "TokenRefreshResponse",
    "SignInResponse",
    "SignUpResponse",
    "get_db_session",
    "get_auth_service",
    "AuthService",
]
