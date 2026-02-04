from typing import TYPE_CHECKING
from sqlalchemy import String, Integer, Numeric, ForeignKey, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base

if TYPE_CHECKING:
    from .chat import Chat

class Message(Base):
    __tablename__ = "messages"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    chat_id: Mapped[int] = mapped_column(Integer, ForeignKey("chats.id"), nullable=False)

    # Content
    role: Mapped[str] = mapped_column(String, nullable=False)  # "user", "assistant", "system"
    content: Mapped[str] = mapped_column(String, nullable=False)

    # Tokens/Price
    prompt_tokens: Mapped[int] = mapped_column(Integer, default=0)
    completion_tokens: Mapped[int] = mapped_column(Integer, default=0)
    total_tokens: Mapped[int] = mapped_column(Integer, default=0)
    cost: Mapped[float] = mapped_column(Numeric(10, 6), default=0.0) # USD
    
    # Relationships
    chat: Mapped["Chat"] = relationship("Chat", back_populates="messages")

    # Indexes
    __table_args__ = (
        Index('ix_messages_chat_created', 'chat_id', 'created_at'),
        Index('ix_messages_role', 'role'),
        Index('ix_messages_tokens', 'total_tokens'),
        Index('ix_messages_created_at', 'created_at'),
    )