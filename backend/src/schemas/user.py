from pydantic import BaseModel

class BaseUser(BaseModel):
    username: str
    email: str
    password_hash: str

class CreateUser(BaseUser):
    pass

class UpdateUser(BaseUser):
    is_active: bool
    is_superuser: bool
    settings: dict
    balance: float
    api_key: str