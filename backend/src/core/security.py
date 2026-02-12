from datetime import datetime, timedelta, timezone
from typing import Literal, Optional

from fastapi import Depends
import jwt
from jwt import (
    ExpiredSignatureError,
    InvalidTokenError,
    InvalidAlgorithmError,
    InvalidKeyError,
)
from passlib.context import CryptContext
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession

from core.config import settings
from core.exceptions import AuthError, InvalidTokenTypeError
from database import database, user_crud, User

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
http_bearer = HTTPBearer()


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


def create_token(
    subject: dict,
    token_type: Literal["access", "refresh"],
    expires_delta: Optional[timedelta] = None,
) -> str:
    """
    Create JWT token with specified type

    Args:
        subject: Data to include in token (usually {"sub": user_id})
        token_type: Type of token - either "access" or "refresh"
        expires_delta: Optional custom expiration time

    Returns:
        JWT token string

    Raises:
        InvalidTokenTypeError: If token_type is not "access" or "refresh"
    """
    # Validate token type
    if token_type not in ("access", "refresh"):
        raise InvalidTokenTypeError(
            f"Invalid token type: '{token_type}'. Must be 'access' or 'refresh'"
        )

    # Set default expiration if not provided
    if expires_delta is None:
        if token_type == "access":
            expires_delta = timedelta(
                minutes=settings.security.access_token_expire_minutes
            )
        else:  # refresh
            expires_delta = timedelta(days=settings.security.refresh_token_expire_days)

    # Create payload
    expire = datetime.now(timezone.utc) + expires_delta
    payload = {
        "exp": expire,
        "iat": datetime.now(timezone.utc),
        "type": token_type,
        **subject,
    }

    # Encode token with error handling
    try:
        token = jwt.encode(
            payload, settings.security.secret_key, algorithm=settings.security.algorithm
        )
        return token
    except Exception as e:
        # Log the error here if you have logging set up
        raise RuntimeError(f"Failed to encode JWT token: {str(e)}") from e


def create_access_token(
    subject: dict, expires_delta: Optional[timedelta] = None
) -> str:
    """Create JWT access token"""
    return create_token(subject, "access", expires_delta)


def create_refresh_token(
    subject: dict, expires_delta: Optional[timedelta] = None
) -> str:
    """Create JWT refresh token"""
    return create_token(subject, "refresh", expires_delta)


def encode_token(payload: dict) -> Optional[str]:
    """
    Encode and verify JWT token

    Returns:
        Encoded JWT token or None if invalid
    """
    try:
        token = jwt.encode(
            payload, settings.security.secret_key, algorithm=settings.security.algorithm
        )
        return token
    except InvalidKeyError:
        # Invalid key
        return None
    except InvalidAlgorithmError:
        # Invalid algorithm
        return None
    except Exception:
        # Other unexpected errors
        return None


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
    credentials: HTTPAuthorizationCredentials = Depends(http_bearer),
    session: AsyncSession = Depends(database.get_session),
) -> Optional[User]:
    """
    Get user from JWT token

    Args:
        credentials: HTTPAuthorizationCredentials
        session: Database session

    Returns:
        User object or None if invalid/expired
    """
    # Get payload
    token = credentials.credentials
    payload = decode_token(token)
    if not payload:
        raise AuthError("Invalid token")
    if payload.get("type") != "access":  # Check token type
        raise AuthError("Invalid token")

    # Get user ID
    user_id = payload.get("sub")
    if not user_id:
        raise AuthError("Invalid token")

    # Get user
    user: User = await user_crud.get(session, user_id)
    if not user:
        raise AuthError("User not found")

    # Check user is active
    is_active = await user_crud.is_active(session=session, user_id=user.id)
    if user and not is_active:
        raise AuthError("User is not active")

    return user
