import json
from fastapi import APIRouter, Depends

from core.exceptions import AuthError
from database import User
from core.security import get_current_user
from utils.logger import logger

router = APIRouter(prefix="/chats", tags=["chats"])
