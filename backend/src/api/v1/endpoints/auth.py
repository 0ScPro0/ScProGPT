from fastapi import APIRouter, Depends

from api.dependencies import (
    AuthService,
    SignInResponse,
    SignUpResponse,
    SignInRequest,
    SignUpRequest,
    get_auth_service,
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
