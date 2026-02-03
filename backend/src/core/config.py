from typing import Optional
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
    url: PostgresDsn    
    echo: bool = False
    echo_pool: bool = False
    pool_size: int = 20
    max_overflow: int = 40
    pool_pre_ping: bool = True

class JWTConfig(BaseModel):
    secret_key: str = Field(..., min_length=32)  # Обязательное поле
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 60 * 24  # 24 часа
    refresh_token_expire_days: int = 30

class Settings(BaseSettings):
    server: ServerConfig = ServerConfig()
    database: DatabaseConfig
    jwt: JWTConfig

    class Config:
        env_nested_delimiter = "__"
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False

settings = Settings() #type: ignore