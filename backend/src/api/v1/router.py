from fastapi import APIRouter

from core.config import settings

router = APIRouter(prefix="/api")

@router.get("/")
def read_root():
    return {"message": "Welcome to ScProGPT API!"}