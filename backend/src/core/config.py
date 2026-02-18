from typing import Optional
from pathlib import Path
from pydantic import BaseModel, Field
from pydantic_settings import BaseSettings
from datetime import timezone

from core.ai.openai.models import (
    BASE_MODELS,
    REASONING_MODELS,
    GPT_41_FAMILY,
    GPT_5_FAMILY,
    GPT_51_FAMILY,
    GPT_52_FAMILY,
    SUPPORTED_MODELS,
    get_all_possible_models,
)

BASE_DIR = Path(__file__).parent.parent.parent  # backend.src.core.config


class ServerConfig(BaseModel):
    host: str = Field(default="0.0.0.0")
    port: int = Field(default=8000)
    reload: bool = Field(default=False)
    cors_origins: list[str] = [
        "http://localhost:8000",
        "http://0.0.0.0:8000",
    ]


class DatabaseConfig(BaseModel):
    url: str = Field(default="")
    alembic_url: str = Field(default="")
    echo: bool = Field(default=False)
    echo_pool: bool = Field(default=False)
    pool_size: int = Field(default=5)
    max_overflow: int = Field(default=10)
    pool_pre_ping: bool = Field(default=True)


class SecurityConfig(BaseModel):
    secret_key: str = Field(default="")
    algorithm: str = Field(default="HS256")
    access_token_expire_minutes: int = Field(default=30)
    refresh_token_expire_days: int = Field(default=30)
    environment: str = Field(
        default="development",
        description="Environment: development, staging, production",
    )


class AIConfig(BaseModel):
    api_key: str = Field(default="")
    base_url: str = Field(default="https://api.proxyapi.ru/")

    class OpenAIConfig(BaseModel):
        # OpenAI model lists
        base_models: list[str] = Field(default_factory=lambda: BASE_MODELS)
        reasoning_models: list[str] = Field(default_factory=lambda: REASONING_MODELS)
        gpt_41_family: list[str] = Field(default_factory=lambda: GPT_41_FAMILY)
        gpt_5_family: list[str] = Field(default_factory=lambda: GPT_5_FAMILY)
        gpt_51_family: list[str] = Field(default_factory=lambda: GPT_51_FAMILY)
        gpt_52_family: list[str] = Field(default_factory=lambda: GPT_52_FAMILY)
        supported_models: list[str] = Field(default_factory=lambda: SUPPORTED_MODELS)

        @property
        def all_possible_models(self) -> list[str]:
            """Returns all possible models"""
            return get_all_possible_models()

    openai: OpenAIConfig = Field(default_factory=OpenAIConfig)


class DateConfig(BaseModel):
    datetime_format: str = "%Y-%m-%dT%H:%M:%S"
    date_format: str = "%Y-%m-%d"
    utc: timezone = timezone.utc

    class Config:
        arbitrary_types_allowed = True


class Settings(BaseSettings):
    server: ServerConfig = Field(default_factory=ServerConfig)
    database: DatabaseConfig = Field(default_factory=DatabaseConfig)
    security: SecurityConfig = Field(default_factory=SecurityConfig)
    ai: AIConfig = Field(default_factory=AIConfig)
    date: DateConfig = DateConfig()

    class Config:
        env_nested_delimiter = "__"
        env_file = BASE_DIR / ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False


settings = Settings()
