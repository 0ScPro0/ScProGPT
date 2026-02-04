from typing import TYPE_CHECKING
from datetime import datetime
from sqlalchemy import String, Integer, Float, Boolean, ForeignKey, DateTime
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base

if TYPE_CHECKING:
    from .user import User
    from .message import Message

class Chat(Base):
    __tablename__ = "chats"
    
    # Main
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), nullable=False)
    title: Mapped[str] = mapped_column(String, default="New Chat")
    
    # Metadata
    model: Mapped[str] = mapped_column(String, default="gpt-3.5-turbo")  # Текущая модель
    provider: Mapped[str] = mapped_column(String)  # openai, anthropic, gemini, openrouter
    
    # Settings
    system_prompt: Mapped[str] = mapped_column(String, nullable=True)
    temperature: Mapped[float] = mapped_column(Float, default=0.7)
    max_tokens: Mapped[int] = mapped_column(Integer, default=2000)
    
    # Statistics
    message_count: Mapped[int] = mapped_column(Integer, default=0)
    total_tokens_used: Mapped[int] = mapped_column(Integer, default=0)
    
    # Soft delete
    is_deleted: Mapped[bool] = mapped_column(Boolean, default=False)
    deleted_at: Mapped[datetime] = mapped_column(DateTime, nullable=True)
    
    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="chats")
    messages: Mapped["Message"] = relationship("Message", back_populates="chat", cascade="all, delete-orphan")
