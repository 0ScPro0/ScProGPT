from datetime import datetime
from typing import Optional
from pydantic import BaseModel, EmailStr

from src.database.models.user import User
from src.schemas.user import UserCreate

class Token(BaseModel):
    access_token: str
    token_type: str = "jwt"
    expires_in: Optional[int] = None

class SignInRequest(BaseModel):
    email: EmailStr
    password: str

class SignUpRequest(UserCreate):
    pass

class SignInResponse(BaseModel):
    access_token: str
    expiration: datetime
    user_info: User