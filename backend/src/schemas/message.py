from typing import Optional
from pydantic import BaseModel, Field, ConfigDict
from datetime import datetime


class BaseMessage(BaseModel):
    """Base message schema with common fields"""
    
    role: str = Field(
        ...,
        pattern=r"^(user|assistant|system)$",
        description="Message role: user, assistant, or system"
    )
    
    content: str = Field(
        ...,
        min_length=1,
        max_length=10000,
        description="Message content"
    )
    
    # Token usage and cost
    prompt_tokens: int = Field(
        default=0,
        ge=0,
        description="Number of tokens in the prompt"
    )
    
    completion_tokens: int = Field(
        default=0,
        ge=0,
        description="Number of tokens in the completion"
    )
    
    total_tokens: int = Field(
        default=0,
        ge=0,
        description="Total number of tokens (prompt + completion)"
    )
    
    cost: float = Field(
        default=0.0,
        ge=0.0,
        description="Cost of the message in USD"
    )


class MessageCreate(BaseMessage):
    """Schema for creating a new message"""
    
    chat_id: int = Field(
        ...,
        gt=0,
        description="ID of the chat this message belongs to"
    )


class MessageUpdate(BaseModel):
    """Schema for updating a message"""
    
    content: Optional[str] = Field(
        None,
        min_length=1,
        max_length=10000,
        description="Updated message content"
    )
    
    model_config = ConfigDict(extra="forbid")  # Prevent extra fields


class MessageResponse(BaseMessage):
    """Schema for message response with all database fields"""
    
    id: int = Field(..., description="Unique message identifier")
    chat_id: int = Field(..., description="ID of the chat this message belongs to")
    
    # Timestamps
    created_at: datetime = Field(..., description="Message creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")
    
    model_config = ConfigDict(
        from_attributes=True,  # Enable ORM mode for SQLAlchemy
        json_schema_extra={
            "example": {
                "id": 123,
                "chat_id": 456,
                "role": "user",
                "content": "Hello, AI assistant!",
                "prompt_tokens": 10,
                "completion_tokens": 25,
                "total_tokens": 35,
                "cost": 0.00035,
                "created_at": "2024-01-15T10:30:00Z",
                "updated_at": "2024-01-15T10:30:05Z"
            }
        }
    )