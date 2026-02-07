from typing import Any, Dict, Generic, List, Optional, Set, Type, TypeVar, Union
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.config import settings
from src.database import Base, CRUDBase

ModelType = TypeVar("ModelType", bound=Base)
CreateSchemaType = TypeVar("CreateSchemaType", bound=BaseModel)
UpdateSchemaType = TypeVar("UpdateSchemaType", bound=BaseModel)


class BaseService(Generic[ModelType, CreateSchemaType, UpdateSchemaType]):
    def __init__(self, crud: CRUDBase, session: AsyncSession):
        self.session = session
        self.crud = crud

    async def get(self, id: int) -> ModelType:
        return await self.crud.get(self.session, id)

    async def get_multy(self, ids: List[int]) -> List[ModelType]:
        return await self.crud.get_multy(self.session, ids)

    async def create(self, schema: CreateSchemaType) -> ModelType:
        return await self.crud.create(self.session, schema)

    async def update(self, id: int, schema: UpdateSchemaType) -> ModelType:
        return await self.crud.update(self.session, id, schema)

    async def remove(self, id: int) -> ModelType:
        return await self.crud.remove(self.session, id)

    async def delete(self, id: int) -> ModelType:
        return await self.crud.delete(self.session, id)
