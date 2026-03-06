from fastapi import APIRouter
import fastapi_swagger_dark as fsd

from api.v1.endpoints import (
    auth_router,
    user_router,
    chat_router,
    message_router,
    ai_router,
)

router = APIRouter(prefix="/api/v1")
docs_router = APIRouter()
fsd.install(docs_router)

router.include_router(docs_router)
router.include_router(auth_router)
router.include_router(user_router)
router.include_router(chat_router)
router.include_router(message_router)
router.include_router(ai_router)


@router.get("/")
def root():
    return {"message": "Welcome to ScProGPT API!"}
