from typing import List, Literal, Optional, Dict
from pydantic import BaseModel, Field


# ============================================MESSAGE=======================================================
class AssistantMessage(BaseModel):
    role: Literal["assistant"] = Field(default="assistant")
    content: Optional[str]


class UserMessage(BaseModel):
    role: Literal["user"] = Field(default="user")
    content: Optional[str]


# ============================================RESPONSE=======================================================
class ProviderResponse(BaseModel):
    provider: str = Field(default="openai")
    model: str = Field(default="gpt-4o-mini")
    message: AssistantMessage = Field(
        default=AssistantMessage(role="assistant", content="")
    )
    usage: Dict[str, int] = Field(
        default={"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0}
    )
    cost: float = Field(default=0.0)


class ProviderResponseStream(ProviderResponse):
    pass


class ProviderResponseChunk(BaseModel):
    provider: str = Field(default="openai")
    model: str = Field(default="gpt-4o-mini")
    content: str = Field(default="")
    usage: Dict = Field(default={})


# ============================================PROVIDER=======================================================
class ProviderInfo(BaseModel):
    name: str
    prefix: str
    supported_models: List[str]
    current_model: str


class ProviderStatus(BaseModel):
    current_provider: str
    current_model: str
    available_providers: List[str]
    registered_providers: List[str]


# ============================================API REQUESTS===================================================
class GenerateRequest(BaseModel):
    """Request for text generation"""

    prompt: str = Field(..., min_length=1, description="User prompt for AI generation")
    provider: Optional[str] = Field(
        None, description="Provider name (uses current if not specified)"
    )
    model: Optional[str] = Field(
        None, description="Model name (uses current if not specified)"
    )
    temperature: float = Field(1, ge=0.1, le=2)
    max_tokens: int = Field(4096, ge=4096, le=128000)


class SetProviderRequest(BaseModel):
    """Request to set current provider"""

    provider: str = Field(..., description="Provider name to set as current")


class SetModelRequest(BaseModel):
    """Request to set current model"""

    model: str = Field(..., description="Model name to set as current")


class ProviderSwitchRequest(BaseModel):
    """Request to switch both provider and model"""

    provider: Optional[str] = Field(None, description="Provider name to switch to")
    model: Optional[str] = Field(None, description="Model name to switch to")


# ============================================API RESPONSES==================================================
class AIServiceStatusResponse(BaseModel):
    """Response with AI service status"""

    current_provider: str
    current_model: str
    available_providers: List[str]
    registered_providers: List[str]
    is_configured: bool = Field(
        ..., description="Whether service is properly configured"
    )


class ProviderListResponse(BaseModel):
    """Response with list of available providers"""

    providers: List[str]
    current_provider: str


class ProviderDetailResponse(BaseModel):
    """Response with detailed provider information"""

    provider: ProviderInfo
    is_current: bool


class ModelListResponse(BaseModel):
    """Response with list of available models for provider"""

    provider: str
    models: List[str]
    current_model: str
