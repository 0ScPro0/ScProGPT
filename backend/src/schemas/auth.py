from datetime import datetime
from typing import Optional
from pydantic import BaseModel, EmailStr

from src.database.models.user import User
from src.schemas.user import UserCreate


class Token(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    access_token_expires_in: int
    refresh_token_expires_in: int


class TokenRefreshRequest(BaseModel):
    refresh_token: str


class TokenRefreshResponse(BaseModel):
    access_token: str
    access_token_expires_in: int


class SignInRequest(BaseModel):
    email: EmailStr
    password: str


class SignUpRequest(UserCreate):
    pass


class SignInResponse(BaseModel):
    access_token: str
    refresh_token: str
    access_token_expires_in: int
    refresh_token_expires_in: int
    user_info: User
