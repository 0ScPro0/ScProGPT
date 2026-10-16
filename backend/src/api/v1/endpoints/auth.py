from typing import Optional

from fastapi import APIRouter, Depends, Request, Response

from api.dependencies import AuthService, get_auth_service
from core.security import (
    get_current_user,
    ACCESS_TOKEN_COOKIE,
    REFRESH_TOKEN_COOKIE,
)
from core.config import settings
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


def _cookie_kwargs():
    return {
        "httponly": settings.security.cookie_httponly,
        "secure": settings.security.cookie_secure,
        "samesite": settings.security.cookie_samesite,
        "path": "/",
    }


def set_auth_cookies(response: Response, access_token: str, refresh_token: str) -> None:
    """Store access and refresh tokens in httpOnly cookies."""
    response.set_cookie(
        key=ACCESS_TOKEN_COOKIE,
        value=access_token,
        **_cookie_kwargs(),
    )
    response.set_cookie(
        key=REFRESH_TOKEN_COOKIE,
        value=refresh_token,
        **_cookie_kwargs(),
    )


def clear_auth_cookies(response: Response) -> None:
    """Delete auth cookies."""
    response.delete_cookie(ACCESS_TOKEN_COOKIE, path="/")
    response.delete_cookie(REFRESH_TOKEN_COOKIE, path="/")


@router.post("/signup", response_model=SignUpResponse)
async def sign_up(
    user: SignUpRequest,
    response: Response,
    auth_service: AuthService = Depends(get_auth_service),
):
    """
    Register a new user
    """
    data = await auth_service.signup(user)
    set_auth_cookies(response, data.access_token, data.refresh_token)
    return data


@router.post("/signin", response_model=SignInResponse)
async def sign_in(
    user: SignInRequest,
    response: Response,
    auth_service: AuthService = Depends(get_auth_service),
):
    """
    Authenticate a user
    """
    data = await auth_service.signin(user)
    set_auth_cookies(response, data.access_token, data.refresh_token)
    return data


@router.post("/refresh", response_model=TokenRefreshResponse)
async def refresh_token(
    request: Request,
    response: Response,
    refresh_request: Optional[TokenRefreshRequest] = None,
    auth_service: AuthService = Depends(get_auth_service),
):
    """
    Refresh access token using refresh token
    from httpOnly cookie (or request body as fallback).
    """

    refresh_token_value = request.cookies.get(REFRESH_TOKEN_COOKIE)
    if refresh_token_value:
        refresh_request = TokenRefreshRequest(refresh_token=refresh_token_value)

    if refresh_request is None or not refresh_request.refresh_token:
        raise AuthError("Refresh token is missing")

    result = await auth_service.refresh_token(refresh_request)

    response.set_cookie(
        key=ACCESS_TOKEN_COOKIE,
        value=result["access_token"],
        **_cookie_kwargs(),
    )
    return result


@router.post("/logout")
async def logout(
    current_user: User = Depends(get_current_user),
    auth_service: AuthService = Depends(get_auth_service),
    response: Response = None,
):
    """Logout user"""
    await auth_service.logout(current_user.id)
    if response:
        clear_auth_cookies(response)
    return {"message": "Successfully logged out"}
