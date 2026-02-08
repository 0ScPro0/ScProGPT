from typing import Optional
from pydantic import BaseModel, EmailStr, ConfigDict, Field
from datetime import datetime


class UserBase(BaseModel):
    username: str = Field(..., min_length=3, max_length=50)
    email: EmailStr = Field(..., max_length=255)


class UserCreate(UserBase):
    password: str = Field(
        ...,
        min_length=8,
        max_length=72,
    )


class UserSchema(BaseModel):
    id: int
    username: str
    email: EmailStr
    is_active: bool
    is_superuser: bool
    settings: dict = Field(default_factory=dict)
    balance: float = Field(default=0.0, ge=0)  # ge=0 - больше или равно 0
    api_key: Optional[str] = None
    refresh_token: Optional[str] = None
    refresh_token_expires_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class UserUpdate(BaseModel):
    username: Optional[str] = Field(None, min_length=3, max_length=50)
    email: Optional[EmailStr] = Field(None, max_length=255)
    is_active: Optional[bool] = None
    is_superuser: Optional[bool] = None
    settings: Optional[dict] = None
    balance: Optional[float] = Field(None, ge=0)  # ge=0 - больше или равно 0
    api_key: Optional[str] = Field(None, min_length=32, max_length=255)
    refresh_token: Optional[str] = Field(None, max_length=512)
    refresh_token_expires_at: Optional[datetime] = None

    model_config = ConfigDict(extra="forbid")  # Запрещаем лишние поля


class UserUpdatePassword(BaseModel):
    current_password: str = Field(..., min_length=8, max_length=100)
    new_password: str = Field(..., min_length=8, max_length=100)


class UserResponse(UserBase):
    id: int
    is_active: bool
    is_superuser: bool
    settings: dict = Field(default_factory=dict)
    balance: float = Field(default=0.0, ge=0)
    api_key: Optional[str] = None
    refresh_token: Optional[str] = None
    refresh_token_expires_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class UserPublic(BaseModel):
    id: int
    username: str
