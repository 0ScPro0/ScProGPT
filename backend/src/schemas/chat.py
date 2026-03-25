from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field, ConfigDict


class BaseChat(BaseModel):
    title: str = Field(
        default="New chat",
        min_length=1,
        max_length=200,
        description="Chat title displayed to the user",
    )

    model: str = Field(
        default="gpt-4o-mini",
        min_length=1,
        max_length=100,
        description="AI model identifier (gpt-4, claude-3, etc.)",
    )

    provider: str = Field(
        default="openai",
        min_length=1,
        max_length=50,
        description="AI provider name (openai, anthropic, deepseek, etc.)",
    )


class ChatCreate(BaseChat):
    user_id: int = Field(..., description="ID of chat owner")


class ChatUpdate(BaseModel):
    title: Optional[str] = Field(
        None, min_length=1, max_length=200, description="New chat title"
    )

    model: Optional[str] = Field(
        None, min_length=1, max_length=100, description="Change AI model for this chat"
    )

    provider: Optional[str] = Field(
        None, min_length=1, max_length=50, description="Change AI provider"
    )

    pinned: Optional[bool] = Field(
        None, description="Pin/unpin chat in user's chat list"
    )

    system_prompt: Optional[str] = Field(
        None,
        max_length=4000,  # Increased for longer system prompts
        description="System prompt that guides AI behavior for this chat",
    )

    temperature: Optional[float] = Field(
        None, ge=0.0, le=2.0, description="AI creativity/randomness (0.0-2.0)"
    )

    max_tokens: Optional[int] = Field(
        None, ge=1, le=32000, description="Maximum tokens per AI response"
    )

    is_deleted: Optional[bool] = Field(
        None, description="Soft delete flag - hides chat without permanent deletion"
    )

    model_config = ConfigDict(
        extra="forbid",  # Prevent extra fields in update payload
        json_schema_extra={
            "example": {
                "title": "Updated Chat Title",
                "pinned": True,
                "temperature": 0.9,
            }
        },
    )


class ChatSchema(BaseChat):
    id: int = Field(..., description="Unique chat identifier")
    user_id: int = Field(..., description="ID of chat owner")

    # Additional fields from database
    pinned: bool = Field(default=False, description="Is chat pinned")
    system_prompt: Optional[str] = Field(None, description="System prompt")
    temperature: float = Field(default=0.7, description="AI temperature")
    max_tokens: int = Field(default=2000, description="Max tokens per response")

    # Statistics
    message_count: int = Field(default=0, description="Total messages in chat")
    total_tokens_used: int = Field(default=0, description="Tokens used in chat")

    # Status flags
    is_deleted: bool = Field(default=False, description="Soft delete flag")
    is_archived: Optional[bool] = Field(None, description="Archive status")

    # Timestamps
    created_at: datetime = Field(..., description="Chat creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")
    deleted_at: Optional[str] = Field(None, description="Deletion timestamp")

    model_config = ConfigDict(
        from_attributes=True,  # Enable ORM mode for SQLAlchemy
        json_schema_extra={
            "example": {
                "id": 123,
                "user_id": 456,
                "title": "My AI Chat",
                "model": "gpt-4",
                "provider": "openai",
                "pinned": True,
                "message_count": 42,
                "created_at": "2024-01-15T10:30:00Z",
            }
        },
    )


class ChatResponse(ChatSchema):
    position: int = Field(..., description="Chat position in user's chat list")
    pass
