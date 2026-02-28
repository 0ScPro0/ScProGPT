from fastapi import APIRouter

from api.v1.endpoints import auth_router, user_router, chat_router, message_router

router = APIRouter(prefix="/api/v1")

router.include_router(auth_router)
router.include_router(user_router)
router.include_router(chat_router)
router.include_router(message_router)


@router.get("/")
def root():
    return {"message": "Welcome to ScProGPT API!"}
