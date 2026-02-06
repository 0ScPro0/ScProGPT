from typing import Optional
from pathlib import Path
from pydantic import BaseModel, Field
from pydantic_settings import BaseSettings

BASE_DIR = Path(__file__).parent.parent.parent #backend.src..core.config

class ServerConfig(BaseModel):
    host: str = "0.0.0.0"
    port: int = 8000
    reload: bool = False
    cors_origins: list[str] = [
        "http://localhost:8000",
        "http://0.0.0.0:8000",
    ]

class DatabaseConfig(BaseModel):
    url: str = Field(default="")
    echo: bool = False
    echo_pool: bool = False
    pool_size: int = 20
    max_overflow: int = 40
    pool_pre_ping: bool = True

class JWTConfig(BaseModel):
    secret_key: str = Field(default="")
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    refresh_token_expire_days: int = 30
    environment: str = Field(default="development", description="Environment: development, staging, production")

class Settings(BaseSettings):
    server: ServerConfig = ServerConfig()
    database: DatabaseConfig = Field(default_factory=DatabaseConfig)
    jwt: JWTConfig = Field(default_factory=JWTConfig)
    
    class Config:
        env_nested_delimiter = "__"
        env_file = BASE_DIR / ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False

settings = Settings()