from fastapi import APIRouter

from api.v1.endpoints.auth import router as auth_router
from api.v1.endpoints.chats import router as chat_router
from api.v1.endpoints.messages import router as message_router

router = APIRouter(prefix="/api/v1")

router.include_router(auth_router)
router.include_router(chat_router)
router.include_router(message_router)


@router.get("/")
def root():
    return {"message": "Welcome to ScProGPT API!"}
