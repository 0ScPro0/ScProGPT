from datetime import datetime
from typing import Dict, Literal, Optional
from pydantic import BaseModel, Field


class AssistantMessage(BaseModel):
    role: Literal["assistant"] = Field(default="assistant")
    content: Optional[str]


class ProviderResponse(BaseModel):
    provider: str = Field(default="openai")
    model: str = Field(default="gpt-4o-mini")
    message: AssistantMessage = Field(
        default=AssistantMessage(role="assistant", content="")
    )
    usage: dict[str, int] = Field(
        default={"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0}
    )


class ProviderResponseStream(ProviderResponse):
    pass


class ProviderResponseChunk(BaseModel):
    provider: str = Field(default="openai")
    model: str = Field(default="gpt-4o-mini")
    content: str = Field(default="")
    usage: dict[str, int] = Field(
        default={"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0}
    )
