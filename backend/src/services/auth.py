from datetime import timedelta, datetime, timezone
from typing import List
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.config import settings
from src.utils.logger import logger, log
from src.api.exceptions import AuthError
from src.core.security import (
    create_access_token,
    create_refresh_token,
    hash_password,
    verify_password,
    decode_token,
)
from src.database import User, CRUDUser, user_crud
from src.schemas.auth import (
    SignInRequest,
    SignUpRequest,
    Token,
    SignInResponse,
    TokenRefreshRequest,
    TokenRefreshResponse,
)
from services.base import BaseService


class AuthService(BaseService):
    """Service for authentication and authorization"""

    def __init__(self, session: AsyncSession):
        super().__init__(session=session, crud=user_crud)

    @log
    async def signup(self, user: SignUpRequest):
        """
        Sign up a new user

        Args:
            user (SignUpRequest): User data

        Raises:
            AuthError: If user with the same email already exists

        Returns:
            User: Created user
        """
        # Check if user with the same email already exists
        if await user_crud.get_by_email(self.session, user.email):
            raise AuthError("User with this email already exists")

        # Hash password
        hashed_password = hash_password(user.password)

        # Dump user
        user_create_data = {
            "email": user.email,
            "username": user.username,
            "password": hashed_password,
            "is_active": True,
            "is_superuser": False,
        }

        # Create user in database
        user_object = await user_crud.create_user(
            session=self.session, user_object=user_create_data
        )

        # Create tokens
        access_token = create_access_token({"sub": str(user_object.id)})
        refresh_token = create_refresh_token({"sub": str(user_object.id)})

        # Calculate expiration times
        access_token_expires_in = settings.security.access_token_expire_minutes * 60
        refresh_token_expires_in = (
            settings.security.refresh_token_expire_days * 24 * 60 * 60
        )

        # Store refresh token in database
        refresh_token_payload = decode_token(refresh_token)
        if refresh_token_payload:
            refresh_token_expires_at = datetime.fromtimestamp(
                refresh_token_payload["exp"], tz=timezone.utc
            )
            await user_crud.update_refresh_token(
                session=self.session,
                user_id=user_object.id,
                refresh_token=refresh_token,
                expires_at=refresh_token_expires_at,
            )

        # Return response
        return {
            "user": user_object,
            "access_token": access_token,
            "refresh_token": refresh_token,
            "access_token_expires_in": access_token_expires_in,
            "refresh_token_expires_in": refresh_token_expires_in,
            "token_type": "bearer",
        }

    @log
    async def signin(self, user: SignInRequest):
        """
        Sign in a user

        Args:
            user (SignInRequest): User credentials

        Raises:
            AuthError: If credentials are invalid

        Returns:
            dict: User data and tokens
        """
        # Get user by email
        user_object = await user_crud.get_by_email(self.session, user.email)
        if not user_object:
            raise AuthError("Invalid credentials")

        # Verify password
        if not verify_password(user.password, user_object.password_hash):
            raise AuthError("Invalid credentials")

        # Check if user is active
        if not await user_crud.is_active(self.session, user_id=user_object.id):
            raise AuthError("User is deactivated")

        # Create tokens
        access_token = create_access_token({"sub": str(user_object.id)})
        refresh_token = create_refresh_token({"sub": str(user_object.id)})

        # Calculate expiration times
        access_token_expires_in = settings.security.access_token_expire_minutes * 60
        refresh_token_expires_in = (
            settings.security.refresh_token_expire_days * 24 * 60 * 60
        )

        # Store refresh token in database
        refresh_token_payload = decode_token(refresh_token)
        if refresh_token_payload:
            refresh_token_expires_at = datetime.fromtimestamp(
                refresh_token_payload["exp"], tz=timezone.utc
            )
            await user_crud.update_refresh_token(
                session=self.session,
                user_id=user_object.id,
                refresh_token=refresh_token,
                expires_at=refresh_token_expires_at,
            )

        # Return response
        return {
            "user": user_object,
            "access_token": access_token,
            "refresh_token": refresh_token,
            "access_token_expires_in": access_token_expires_in,
            "refresh_token_expires_in": refresh_token_expires_in,
            "token_type": "bearer",
        }

    @log
    async def refresh_token(self, refresh_request: TokenRefreshRequest):
        """
        Refresh access token using refresh token

        Args:
            refresh_request (TokenRefreshRequest): Refresh token

        Raises:
            AuthError: If refresh token is invalid or expired

        Returns:
            TokenRefreshResponse: New access token
        """
        # Decode refresh token
        payload = decode_token(refresh_request.refresh_token)
        if not payload or payload.get("type") != "refresh":
            raise AuthError("Invalid refresh token")

        # Check if token is expired
        exp = payload.get("exp")
        if not exp or datetime.fromtimestamp(exp, tz=timezone.utc) < datetime.now(
            timezone.utc
        ):
            raise AuthError("Refresh token expired")

        # Get user ID from token
        user_id = payload.get("sub")
        if not user_id:
            raise AuthError("Invalid refresh token")

        # Get user from database
        user_object = await user_crud.get(self.session, user_id)
        if not user_object:
            raise AuthError("User not found")

        # Check if user is active
        if not await user_crud.is_active(self.session, user_id=user_object.id):
            raise AuthError("User is deactivated")

        # Verify refresh token matches stored token
        if user_object.refresh_token != refresh_request.refresh_token:
            raise AuthError("Invalid refresh token")

        # Check if stored refresh token is expired
        if (
            user_object.refresh_token_expires_at
            and user_object.refresh_token_expires_at < datetime.now(timezone.utc)
        ):
            raise AuthError("Refresh token expired")

        # Create new access token
        new_access_token = create_access_token({"sub": str(user_object.id)})
        access_token_expires_in = settings.security.access_token_expire_minutes * 60

        # Return response
        return {
            "access_token": new_access_token,
            "access_token_expires_in": access_token_expires_in,
        }

    @log
    async def logout(self, user_id: int):
        """
        Logout user by clearing refresh token

        Args:
            user_id (int): User ID

        Returns:
            bool: True if successful
        """
        # Clear refresh token in database
        await user_crud.clear_refresh_token(session=self.session, user_id=user_id)

        return True
