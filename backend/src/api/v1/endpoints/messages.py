from fastapi import APIRouter

router = APIRouter(prefix="/chats/{chat_id}/messages", tags=["messages"])
