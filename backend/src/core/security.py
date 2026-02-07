from datetime import datetime, timedelta, timezone
from typing import Optional

from fastapi import Depends
import jwt  # PyJWT
from jwt import ExpiredSignatureError, InvalidTokenError
from passlib.context import CryptContext
from fastapi.security import HTTPBearer, OAuth2PasswordBearer

from sqlalchemy.ext.asyncio import AsyncSession

from src.core.config import settings
from src.database import database, user_crud, User

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/login")
security = HTTPBearer(auto_error=False)  # Разрешаем запросы без токена


def verify_password(password: str, hashed_password: str) -> bool:
    """
    Verify password against hash

    Args:
        password: Password to verify
        hashed_password: Hashed password

    Returns:
        True if password matches, False otherwise
    """
    return pwd_context.verify(password, hashed_password)


def hash_password(password: str) -> str:
    """
    Hash password

    Args:
        password: Password to hash

    Returns:
        Hashed password
    """
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
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(
            minutes=settings.security.access_token_expire_minutes
        )

    # Create payload
    payload = {
        "exp": expire,  # expiration time
        "iat": datetime.now(timezone.utc),  # issued at
        "type": "access",  # token type
        **subject,
    }

    # Encode token
    token = jwt.encode(
        payload, settings.security.secret_key, algorithm=settings.security.algorithm
    )

    return token


def create_refresh_token(
    subject: dict, expires_delta: Optional[timedelta] = None
) -> str:
    """
    Create JWT refresh token

    Args:
        subject: Data to include in token (usually {"sub": user_id})
        expires_delta: Optional custom expiration time

    Returns:
        JWT token string
    """
    # Set expiration
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(
            days=settings.security.refresh_token_expire_days
        )

    # Create payload
    payload = {
        "exp": expire,  # expiration time
        "iat": datetime.now(timezone.utc),  # issued at
        "type": "refresh",  # token type
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
            token,
            settings.security.secret_key,
            algorithms=[settings.security.algorithm],
        )
        return payload
    except ExpiredSignatureError:
        # Token expired
        return None
    except InvalidTokenError:
        # Invalid token
        return None


async def get_current_user(
    token: str = Depends(oauth2_scheme),
    session: AsyncSession = Depends(database.get_session),
) -> Optional[User]:
    """
    Get user from JWT token

    Args:
        token: JWT token
        session: Database session

    Returns:
        User object or None if invalid/expired
    """
    # Get payload
    payload = decode_token(token)
    if not payload:
        return None
    if payload.get("type") != "access":  # Check token type
        return None

    # Get user ID
    user_id = payload.get("sub")
    if not user_id:
        return None

    # Get user
    user: User = await user_crud.get(session, user_id)

    # Check user is active
    is_active = await user_crud.is_active(session=session, user_id=user.id)
    if user and not is_active:
        return None

    return user
