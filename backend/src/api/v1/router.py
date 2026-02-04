from fastapi import APIRouter

from .endpoints.auth import router as auth_router
from .endpoints.chats import router as chat_router
from .endpoints.messages import router as message_router

router = APIRouter(prefix="/api")

router.include_router(auth_router)
router.include_router(chat_router)
router.include_router(message_router)

@router.get("/")
def read_root():
    return {"message": "Welcome to ScProGPT API!"}