from typing import Any, Dict, Generic, List, Optional, Type, TypeVar, Union
from pydantic import BaseModel
from fastapi.encoders import jsonable_encoder
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete
from sqlalchemy.sql.expression import func

from database.models.base import Base

ModelType = TypeVar("ModelType", bound=Base)
CreateSchemaType = TypeVar("CreateSchemaType", bound=BaseModel)
UpdateSchemaType = TypeVar("UpdateSchemaType", bound=BaseModel)

class CRUDBase(Generic[ModelType, CreateSchemaType, UpdateSchemaType]):
    """Base class for CRUD operations"""

    def __init__(self, model: Type[ModelType]):
        self.model = model
    
    #==========================================GET OBJECT==========================================
    async def get(
        self, 
        session: AsyncSession, 
        id: Any
    ) -> Optional[ModelType]:
        """Get object by id"""

        result = await session.execute(
            select(self.model).where(self.model.id == id)
        )
        return result.scalar_one_or_none()
    
    async def get_multy(
        self, 
        session: AsyncSession,
        *,
        skip: int = 0,
        limit: int = 100,
        order_by: Optional[Any]
    ) -> List[ModelType]:
        """Get object list with pagination"""

        query = select(self.model)
        
        if order_by is not None:
            query = query.order_by(order_by)
        
        query = query.offset(skip).limit(limit)
        result = await session.execute(query)
        return list(result.scalars().all())

    async def get_by_field(
        self,
        session: AsyncSession,
        field_name: str,
        field_value: Any
    ) -> Optional[ModelType]:
        """Get object by field (email, username etc.)"""

        if not hasattr(self.model, field_name):
            raise AttributeError(f"Model {self.model.__name__} has no field {field_name}")
        
        result = await session.execute(
            select(self.model).where(getattr(self.model, field_name) == field_value)
        )
        return result.scalar_one_or_none()
    
    #==========================================CREATE OBJECT==========================================
    async def create(
        self,
        session: AsyncSession,
        *,
        object_in: Union[CreateSchemaType, Dict[str, Any]]
    ) -> ModelType:
        """Create object"""

        if isinstance(object_in, dict):
            create_data = object_in
        else:
            create_data = object_in.model_dump(exclude_unset=True)
        
        database_object = self.model(**create_data)
        session.add(database_object)
        await session.commit()
        await session.refresh(database_object)
        return database_object

    #==========================================UPDATE OBJECT==========================================
    async def update(
        self,
        session: AsyncSession,
        *,
        database_object: ModelType,
        object_in: Union[UpdateSchemaType, Dict[str, Any]]
    ) -> ModelType:
        """Update object"""

        if isinstance(object_in, dict): 
            update_data = object_in
        else:
            update_data = object_in.model_dump(exclude_unset=True)
        
        for field in update_data: # Update every field
            if hasattr(database_object, field):
                setattr(database_object, field, update_data[field])
        
        session.add(database_object)
        await session.commit()
        await session.refresh(database_object)
        return database_object

    async def update_object_by_field(
        self,
        session: AsyncSession,
        *,
        field_name: str,
        field_value: Any,
        update_data: Dict[str, Any]
    ) -> Optional[ModelType]:
        """Update object by field"""
        
        # Get object
        database_object = await self.get_by_field(
            session=session,
            field_name=field_name,
            field_value=field_value
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

    async def update_field(
        self,
        session: AsyncSession,
        *,
        object_id: Any,
        field_name: str,
        field_value: Any
    ) -> Optional[ModelType]:
        """Update single field of an object"""
        
        # Get object
        object = await self.get(session, object_id)
        if not object:
            return None
        
        # Check field exists
        if not hasattr(object, field_name):
            raise AttributeError(
                f"Model {self.model.__name__} has no field '{field_name}'"
            )
        
        # Update field
        setattr(object, field_name, field_value)
        
        # Save
        session.add(object)
        await session.commit()
        await session.refresh(object)
        
        return object

    #==========================================DELETE OBJECT==========================================
    async def remove_object_by_id(
        self, 
        session: AsyncSession, 
        *, 
        id: int
    ) -> Optional[ModelType]:
        """Delete object by id"""

        result = await session.execute(
            select(self.model).where(self.model.id == id)
        )
        
        obj = result.scalar_one_or_none()
        
        if obj:
            await session.delete(obj)
            await session.commit()
        
        return obj
    
    async def delete_object_by_id(self, session: AsyncSession, *, id: int) -> bool:
        """Удалить объект по ID (возвращает bool)"""
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

    #==========================================USEFUL FUNCTIONS==========================================
    async def is_exists(
        self, 
        session: AsyncSession, 
        *, 
        id: int
    ) -> bool:
        """Check object exists"""

        result = await session.execute(
            select(self.model).where(self.model.id == id)
        )
        return result.scalar_one_or_none() is not None
    
    async def records_count(
        self, 
        session: AsyncSession
    ) -> int:
        """Get records count"""

        result = await session.execute(
            select(func.count()).select_from(self.model)
        )
        return result.scalar_one()