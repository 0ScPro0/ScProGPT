from typing import Any, Dict, Generic, List, Optional, Set, Type, TypeVar, Union
from pydantic import BaseModel
from fastapi.encoders import jsonable_encoder
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete
from sqlalchemy.sql.expression import func

from src.utils.logger import logger, log_database_queries
from database.models.base import Base

ModelType = TypeVar("ModelType", bound=Base)
CreateSchemaType = TypeVar("CreateSchemaType", bound=BaseModel)
UpdateSchemaType = TypeVar("UpdateSchemaType", bound=BaseModel)


class CRUDBase(Generic[ModelType, CreateSchemaType, UpdateSchemaType]):
    """Base class for CRUD operations"""

    def __init__(self, model: Type[ModelType]):
        self._protected_fields: Set[str] = {"id", "created_at", "updated_at"}
        self.model = model

    @log_database_queries
    async def get(self, session: AsyncSession, id: Any) -> Optional[ModelType]:
        """
        Get object by id

        Args:
            session: Database session
            id: Object id

        Returns:
            Object or None if not found
        """
        result = await session.execute(select(self.model).where(self.model.id == id))
        return result.scalar_one_or_none()

    @log_database_queries
    async def get_multy(
        self,
        session: AsyncSession,
        *,
        skip: int = 0,
        limit: int = 100,
        order_by: Optional[Any],
    ) -> List[ModelType]:
        """
        Get object list with pagination

        Args:
            session: Database session
            skip: Skip number of objects
            limit: Limit number of objects
            order_by: Order by field

        Returns:
            List of objects
        """
        query = select(self.model)

        if order_by is not None:
            query = query.order_by(order_by)

        query = query.offset(skip).limit(limit)
        result = await session.execute(query)
        return list(result.scalars().all())

    @log_database_queries
    async def get_by_field(
        self, session: AsyncSession, field_name: str, field_value: Any
    ) -> Optional[ModelType]:
        """
        Get object by field value (email, username etc.)

        Args:
            session: Database session
            field_name: Field name
            field_value: Field value

        Returns:
            Object or None if not found
        """
        if not hasattr(self.model, field_name):
            raise AttributeError(
                f"Model {self.model.__name__} has no field {field_name}"
            )

        result = await session.execute(
            select(self.model).where(getattr(self.model, field_name) == field_value)
        )
        return result.scalar_one_or_none()

    @log_database_queries
    async def get_by_field_multy(
        self,
        session: AsyncSession,
        *,
        field_name: str,
        field_value: Any,
        skip: int = 0,
        limit: int = 100,
    ) -> List[ModelType]:
        """
        Get many objects by field value

        Args:
            session: Database session
            field_name: Field name
            field_value: Field value
            skip: Skip number of objects
            limit: Limit number of objects

        Returns:
            List of objects
        """
        if not hasattr(self.model, field_name):
            raise AttributeError(
                f"Model {self.model.__name__} has no field {field_name}"
            )

        result = await session.execute(
            select(self.model)
            .where(getattr(self.model, field_name) == field_value)
            .offset(skip)
            .limit(limit)
        )
        return list(result.scalars().all())

    @log_database_queries
    async def create(
        self,
        session: AsyncSession,
        *,
        object_in: Union[CreateSchemaType, Dict[str, Any]],
    ) -> ModelType:
        """
        Create object

        Args:
            session: Database session
            object_in: Object data

        Returns:
            Created object
        """
        if isinstance(object_in, dict):
            create_data = object_in
        else:
            create_data = object_in.model_dump(exclude_unset=True)

        database_object = self.model(**create_data)
        session.add(database_object)
        await session.commit()
        await session.refresh(database_object)
        return database_object

    @log_database_queries
    async def update(
        self,
        session: AsyncSession,
        *,
        database_object: ModelType,
        object_in: Union[UpdateSchemaType, Dict[str, Any]],
    ) -> ModelType:
        """
        Update object

        Args:
            session: Database session
            database_object: Object to update
            object_in: Object data

        Returns:
            Updated object
        """
        if isinstance(object_in, dict):
            update_data = object_in
        else:
            update_data = object_in.model_dump(exclude_unset=True)

        for field in update_data:  # Update every field
            if hasattr(database_object, field):
                setattr(database_object, field, update_data[field])

        session.add(database_object)
        await session.commit()
        await session.refresh(database_object)
        return database_object

    @log_database_queries
    async def update_by_field(
        self,
        session: AsyncSession,
        *,
        field_name: str,
        field_value: Any,
        update_data: Dict[str, Any],
    ) -> Optional[ModelType]:
        """
        Update object by field

        Args:
            session: Database session
            field_name: Field name
            field_value: Field value
            update_data: Data to update

        Returns:
            Updated object or None if not found
        """
        # Get object
        database_object = await self.get_by_field(
            session=session, field_name=field_name, field_value=field_value
        )

        if not database_object:
            return None

        # Update
        for field, value in update_data.items():
            if hasattr(database_object, field):
                setattr(database_object, field, value)

        session.add(database_object)
        await session.commit()
        await session.refresh(database_object)
        return database_object

    @log_database_queries
    async def update_field(
        self,
        session: AsyncSession,
        *,
        object_id: Any,
        field_name: str,
        field_value: Any,
    ) -> Optional[ModelType]:
        """
        Update single field of an object

        Args:
            session: Database session
            object_id: Object id
            field_name: Field name
            field_value: Field value

        Returns:
            Updated object or None if not found
        """
        # Get object
        object = await self.get(session, object_id)
        if not object:
            return None

        # Check field exists
        if not hasattr(object, field_name):
            raise AttributeError(
                f"Model {self.model.__name__} has no field '{field_name}'"
            )

        # Check for protected fields
        if field_name in self._protected_fields:
            raise PermissionError(f"Cannot change protected field: {field_name}")

        # Update field
        setattr(object, field_name, field_value)

        # Save
        session.add(object)
        await session.commit()
        await session.refresh(object)

        return object

    @log_database_queries
    async def update_fields(
        self, session: AsyncSession, *, object_id: Any, fields: Dict[str, Any]
    ) -> Optional[ModelType]:
        """
        Update single field of an object

        Args:
            session: Database session
            object_id: Object id
            fields: Dict[str, Any]

        Returns:
            Updated object or None if not found
        """
        # Get object
        object = await self.get(session, object_id)
        if not object:
            return None

        # Check field exists
        for name, value in fields.items():
            if value is None:
                logger.warning(f"Field {name} is None, skip it")
                continue

            if not hasattr(object, name):
                raise AttributeError(
                    f"Model {self.model.__name__} has no field '{name}'"
                )

            # Check for protected fields
            if name in self._protected_fields:
                raise PermissionError(f"Cannot change protected field: {name}")

            # Update field
            setattr(object, name, value)

        # Save
        session.add(object)
        await session.commit()
        await session.refresh(object)

        return object

    @log_database_queries
    async def remove(self, session: AsyncSession, *, id: int) -> Optional[ModelType]:
        """
        Delete object by id

        Args:
            session: Database session
            id: int

        Returns:
            Deleted object or None if not found
        """
        result = await session.execute(select(self.model).where(self.model.id == id))

        obj = result.scalar_one_or_none()

        if obj:
            await session.delete(obj)
            await session.commit()

        return obj

    @log_database_queries
    async def delete(self, session: AsyncSession, *, id: int) -> bool:
        """
        Delete object by id

        Args:
            id: int
        Returns:
            bool: True if object was deleted, False otherwise
        """
        try:
            result = await session.execute(
                select(self.model).where(self.model.id == id)
            )
            obj = result.scalar_one_or_none()

            await session.delete(obj)
            await session.commit()
            return True
        except Exception:
            await session.rollback()
            return False

    @log_database_queries
    async def is_exists(self, session: AsyncSession, *, id: int) -> bool:
        """
        Check object exists

        Args:
            session: Database session
            id: int

        Returns:
            bool: True if object exists, False otherwise
        """
        result = await session.execute(select(self.model).where(self.model.id == id))
        return result.scalar_one_or_none() is not None

    @log_database_queries
    async def records_count(self, session: AsyncSession) -> int:
        """
        Get records count

        Args:
            session: Database session

        Returns:
            int: Records count
        """
        result = await session.execute(select(func.count()).select_from(self.model))
        return result.scalar_one()
