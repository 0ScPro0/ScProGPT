from typing import Any, Dict, Generic, List, Optional, Set, Type, TypeVar, Union
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from core.config import settings
from database import Base, CRUDBase
from services.base import BaseService


class ChatService(BaseService):
    def __init__(self, crud: CRUDBase, session: AsyncSession):
        super().__init__(crud, session)
