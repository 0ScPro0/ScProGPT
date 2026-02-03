from typing import Optional
import warnings
from pydantic import BaseModel, Field, PostgresDsn, field_validator
from pydantic_settings import BaseSettings

class ServerConfig(BaseModel):
    host: str = "0.0.0.0"
    port: int = 8000
    reload: bool = False
    cors_origins: list[str] = [
        "http://localhost:8000",
        "http://0.0.0.0:8000",
    ]

class DatabaseConfig(BaseModel):
    url: Optional[PostgresDsn] = Field(default=None)
    echo: bool = False
    echo_pool: bool = False
    pool_size: int = 20
    max_overflow: int = 40
    pool_pre_ping: bool = True
    
    @field_validator('url', mode='after')
    @classmethod
    def warn_if_none(cls, v):
        if v is None:
            warnings.warn(
                "Database URL is None! Application may not work correctly.",
                UserWarning,
                stacklevel=3
            )
        return v

class JWTConfig(BaseModel):
    secret_key: Optional[str] = Field(default=None, min_length=32)
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 60 * 24
    refresh_token_expire_days: int = 30
    
    @field_validator('secret_key', mode='after')
    @classmethod
    def warn_if_none(cls, v):
        if v is None:
            warnings.warn(
                "JWT secret key is None! Authentication will not work.",
                UserWarning,
                stacklevel=3
            )
        return v

class Settings(BaseSettings):
    server: ServerConfig = ServerConfig()
    database: Optional[DatabaseConfig] = None
    jwt: Optional[JWTConfig] = None
    
    @field_validator('database', 'jwt', mode='after')
    @classmethod
    def warn_if_nested_none(cls, v, info):
        if v is None:
            field_name = info.field_name
            warnings.warn(
                f"{field_name.capitalize()} config is None! "
                f"Check your .env file for {field_name.upper()}__* variables.",
                UserWarning,
                stacklevel=3
            )
        return v
    
    class Config:
        env_nested_delimiter = "__"
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False

# При создании объекта
settings = Settings()

# Дополнительная проверка после создания
if settings.database is None:
    warnings.warn(
        "Database configuration is missing! "
        "Set DATABASE__URL in .env file.",
        UserWarning,
        stacklevel=2
    )

if settings.jwt is None:
    warnings.warn(
        "JWT configuration is missing! "
        "Set JWT__SECRET_KEY in .env file.",
        UserWarning,
        stacklevel=2
    )