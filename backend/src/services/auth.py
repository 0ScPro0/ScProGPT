from datetime import timedelta, datetime, timezone
from typing import List
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from core.config import settings
from utils.logger import logger, log
from core.exceptions import AuthError
from core.security import (
    create_access_token,
    create_refresh_token,
    hash_password,
    verify_password,
    decode_token,
)
from database import User
from repositories import UserRepository
from schemas.auth import (
    SignInRequest,
    SignUpRequest,
    Token,
    SignInResponse,
    SignUpResponse,
    TokenRefreshRequest,
    TokenRefreshResponse,
)
from schemas.user import UserSchema, UserResponse
from services.base import BaseService


class AuthService:
    """Service for authentication and authorization"""

    def __init__(self, session: AsyncSession, user_repository: UserRepository):
        self.session = session
        self.user_repository = user_repository

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
        if await self.user_repository.get_by_email(self.session, user.email):
            raise AuthError("User with this email already exists")

        # Hash password
        hashed_password = hash_password(user.password)

        # Dump user
        user_create_data = {
            "email": user.email,
            "username": user.username,
            "password_hash": hashed_password,
            "is_active": True,
            "is_superuser": False,
        }

        # Create user in database
        user_object = await self.user_repository.create_user(
            session=self.session, user_object=user_create_data
        )

        # Create tokens
        access_token = create_access_token({"sub": str(user_object.id)})
        refresh_token = create_refresh_token({"sub": str(user_object.id)})

        # Calculate expiration times
        access_token_expires_in = settings.security.access_token_expire_minutes
        refresh_token_expires_in = settings.security.refresh_token_expire_days

        # Store refresh token in database
        refresh_token_payload = decode_token(refresh_token)
        if refresh_token_payload:
            refresh_token_expires_at = datetime.fromtimestamp(
                refresh_token_payload["exp"], tz=timezone.utc
            )
            await self.user_repository.update_refresh_token(
                session=self.session,
                user_id=user_object.id,
                refresh_token=refresh_token,
                expires_at=refresh_token_expires_at,
            )

        # Return response
        return SignUpResponse(
            user=UserResponse.model_validate(user_object),
            access_token=access_token,
            refresh_token=refresh_token,
            access_token_expires_in=access_token_expires_in,
            refresh_token_expires_in=refresh_token_expires_in,
        )

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
        user_object = await self.user_repository.get_by_email(self.session, user.email)
        if not user_object:
            raise AuthError("Invalid credentials")

        # Verify password
        if not verify_password(user.password, user_object.password_hash):
            raise AuthError("Invalid credentials")

        # Check if user is active
        if not await self.user_repository.is_active(
            self.session, user_id=user_object.id
        ):
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
            await self.user_repository.update_refresh_token(
                session=self.session,
                user_id=user_object.id,
                refresh_token=refresh_token,
                expires_at=refresh_token_expires_at,
            )

        # Return response
        return SignInResponse(
            user=UserResponse.model_validate(user_object),
            access_token=access_token,
            refresh_token=refresh_token,
            access_token_expires_in=access_token_expires_in,
            refresh_token_expires_in=refresh_token_expires_in,
        )

    @log
    async def get_current_user(self, token: str):
        """
        Get current user from token

        Args:
            token (str): Access token

        Raises:
            AuthError: If token is invalid or expired

        Returns:
            User: Current user
        """
        # Decode token
        payload = decode_token(token)
        if not payload or payload.get("type") != "access":
            raise AuthError("Invalid token")

        # Get user ID from token
        user_id = payload.get("sub")
        if not user_id:
            raise AuthError("Invalid token")

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
        user_object = await self.user_repository.get(self.session, user_id)
        if not user_object:
            raise AuthError("User not found")

        # Check if user is active
        if not await self.user_repository.is_active(
            self.session, user_id=user_object.id
        ):
            raise AuthError("User is deactivated")

        # Verify refresh token matches stored token
        if user_object.refresh_token != refresh_request.refresh_token:
            raise AuthError("Invalid refresh token")

        # Check if stored refresh token is expired
        if user_object.refresh_token_expires_at:
            # Convert to aware datetime if necessary
            expires_at = user_object.refresh_token_expires_at
            if expires_at.tzinfo is None:
                expires_at = expires_at.replace(tzinfo=timezone.utc)

            if expires_at < datetime.now(timezone.utc):
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
        await self.user_repository.clear_refresh_token(
            session=self.session, user_id=user_id
        )

        return True
