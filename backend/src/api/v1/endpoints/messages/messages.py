from fastapi import APIRouter

from api.v1.endpoints.messages.assistant import router as assistant_router
from api.v1.endpoints.messages.user import router as user_router

router = APIRouter(prefix="/chats/{chat_id}/messages", tags=["messages"])

router.include_router(assistant_router)
router.include_router(user_router)
