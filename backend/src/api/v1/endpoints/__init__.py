from api.v1.endpoints.auth import router as auth_router
from api.v1.endpoints.users import router as user_router
from api.v1.endpoints.chats import router as chat_router
from api.v1.endpoints.messages.messages import router as message_router

__all__ = [
    "message_router",
    "user_router",
    "chat_router",
    "auth_router",
]
