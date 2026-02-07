from datetime import datetime, timedelta
from typing import Optional

import jwt  # PyJWT
from jwt import ExpiredSignatureError, InvalidTokenError
from passlib.context import CryptContext
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi import Request, HTTPException, status

from src.core.config import settings

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
security = HTTPBearer(auto_error=False)  # Разрешаем запросы без токена


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify password against hash"""
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """Hash password"""
    return pwd_context.hash(password)


def create_access_token(
    subject: dict, expires_delta: Optional[timedelta] = None
) -> str:
    """
    Create JWT access token

    Args:
        subject: Data to include in token (usually {"sub": user_id})
        expires_delta: Optional custom expiration time

    Returns:
        JWT token string
    """
    # Set expiration
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(
            minutes=settings.security.access_token_expire_minutes
        )

    # Create payload
    payload = {
        "exp": expire,  # expiration time
        "iat": datetime.utcnow(),  # issued at
        "type": "access",  # token type
        **subject,
    }

    # Encode token
    token = jwt.encode(
        payload, settings.security.secret_key, algorithm=settings.security.algorithm
    )

    return token


def decode_token(token: str) -> Optional[dict]:
    """
    Decode and verify JWT token

    Returns:
        Decoded payload or None if invalid/expired
    """
    try:
        payload = jwt.decode(
            token, settings.security.secret_key, algorithm=[settings.security.algorithm]
        )
        return payload
    except ExpiredSignatureError:
        # Token expired
        return None
    except InvalidTokenError:
        # Invalid token
        return None


def get_current_user(token: str):
    """
    Get user from token (basic example)
    In real app, you would fetch user from DB here
    """
    payload = decode_token(token)
    if not payload:
        return None

    # Check token type
    if payload.get("type") != "access":
        return None

    user_id = payload.get("sub")
    if not user_id:
        return None

    # Здесь ты бы получал пользователя из БД
    # user = await user_crud.get(user_id)
    # return user

    return {"id": user_id}  # Заглушка
