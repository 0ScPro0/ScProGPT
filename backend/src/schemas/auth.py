from typing import Optional
from pydantic import BaseModel, EmailStr

from src.schemas.user import UserCreate

class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: Optional[int] = None

class LoginRequest(BaseModel):
    email: EmailStr
    password: str

class RegisterRequest(UserCreate):
    pass