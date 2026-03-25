from typing import Any, Dict, Generic, List, Optional, Set, Type, TypeVar, Union
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from core.config import settings
from database import Base, CRUDBase

ModelType = TypeVar("ModelType", bound=Base)
CreateSchemaType = TypeVar("CreateSchemaType", bound=BaseModel)
UpdateSchemaType = TypeVar("UpdateSchemaType", bound=BaseModel)
CRUDType = TypeVar("CRUDType", bound=CRUDBase)


class BaseService(Generic[ModelType, CreateSchemaType, UpdateSchemaType, CRUDType]):
    def __init__(self, session: AsyncSession, crud: CRUDType):
        self.session = session
        self.crud = crud

    async def get(self, id: int) -> ModelType:
        return await self.crud.get(self.session, id)

    async def get_many(self, ids: List[int]) -> List[ModelType]:
        return await self.crud.get_many(self.session, ids)

    async def create(self, schema: CreateSchemaType) -> ModelType:
        return await self.crud.create(self.session, object_in=schema)

    async def update(self, id: int, schema: UpdateSchemaType) -> Optional[ModelType]:
        return await self.crud.update(self.session, id, schema)

    async def remove(self, id: int) -> ModelType:
        return await self.crud.remove(self.session, id)

    async def delete(self, id: int) -> ModelType:
        return await self.crud.delete(self.session, id)
