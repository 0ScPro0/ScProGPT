from fastapi import APIRouter, Depends

from api.dependencies import AuthService, get_auth_service
from core.security import get_current_user
from core.exceptions import AuthError

from database import User

from schemas.auth import (
    SignInResponse,
    SignUpResponse,
    SignInRequest,
    SignUpRequest,
    TokenRefreshRequest,
    TokenRefreshResponse,
)

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/signup", response_model=SignUpResponse)
async def sign_up(
    user: SignUpRequest, auth_service: AuthService = Depends(get_auth_service)
):
    """
    Register a new user
    """
    return await auth_service.signup(user)


@router.post("/signin", response_model=SignInResponse)
async def sign_in(
    user: SignInRequest, auth_service: AuthService = Depends(get_auth_service)
):
    """
    Authenticate a user
    """
    return await auth_service.signin(user)


@router.post("/refresh", response_model=TokenRefreshResponse)
async def refresh_token(
    refresh_request: TokenRefreshRequest,
    auth_service: AuthService = Depends(get_auth_service),
):
    """
    Refresh access token using refresh token
    """

    return await auth_service.refresh_token(refresh_request)


@router.post("/logout")
async def logout(
    current_user: User = Depends(get_current_user),
    auth_service: AuthService = Depends(get_auth_service),
):
    """Logout user"""
    await auth_service.logout(current_user.id)
    return {"message": "Successfully logged out"}
