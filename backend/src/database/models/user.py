from typing import TYPE_CHECKING
from sqlalchemy import String, Integer, Boolean, Numeric, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base

if TYPE_CHECKING:
    from .chat import Chat


class User(Base):
    __tablename__ = "users"

    # Main
    username: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    # Permissions
    is_superuser: Mapped[bool] = mapped_column(Boolean, default=False)

    # Settings
    settings: Mapped[dict] = mapped_column(JSON, default={})

    # Business
    balance: Mapped[float] = mapped_column(Numeric(10, 2), default=0.00)
    api_key: Mapped[str] = mapped_column(String, unique=True, index=True)

    chats: Mapped[list["Chat"]] = relationship(
        "Chat", back_populates="users", cascade="all, delete-orphan"
    )
