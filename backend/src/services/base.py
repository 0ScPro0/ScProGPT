from typing import Any, Dict, Generic, List, Optional, Set, Type, TypeVar, Union
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from core.config import settings
from database import Base
from repositories import BaseRepository

ModelType = TypeVar("ModelType", bound=Base)
CreateSchemaType = TypeVar("CreateSchemaType", bound=BaseModel)
UpdateSchemaType = TypeVar("UpdateSchemaType", bound=BaseModel)
RepositoryType = TypeVar("RepositoryType", bound=BaseRepository)


class BaseService(
    Generic[ModelType, CreateSchemaType, UpdateSchemaType, RepositoryType]
):
    def __init__(self, session: AsyncSession, repository: RepositoryType):
        self.session = session
        self.repository = repository

    async def get(self, id: int) -> Optional[ModelType]:
        return await self.repository.get(self.session, id)

    async def get_many(
        self,
        *,
        skip: int = 0,
        limit: int = 100,
        order_by: Optional[Any],
        relationships: Optional[List[str]] = None,
    ) -> List[ModelType]:
        return await self.repository.get_many(
            self.session,
            skip=skip,
            limit=limit,
            order_by=order_by,
            relationships=relationships,
        )

    async def create(self, schema: CreateSchemaType) -> ModelType:
        return await self.repository.create(self.session, object_in=schema)

    async def update(self, id: int, schema: UpdateSchemaType) -> Optional[ModelType]:
        return await self.repository.update(
            self.session, update_object_id=id, object_in=schema
        )

    async def delete(self, id: int) -> Optional[ModelType]:
        return await self.repository.delete(self.session, id=id)
