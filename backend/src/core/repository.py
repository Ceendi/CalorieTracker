import uuid
from typing import TypeVar, Type, Generic, Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.database import UUIDModel

ModelType = TypeVar("ModelType", bound=UUIDModel)


class BaseRepository(Generic[ModelType]):
    def __init__(self, model: Type[ModelType], db: AsyncSession):
        self.model = model
        self.db = db

    async def get_by_id(self, id: uuid.UUID) -> Optional[ModelType]:
        query = select(self.model).where(self.model.id == id)
        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def create(self, attributes: dict) -> ModelType:
        obj = self.model(**attributes)
        self.db.add(obj)
        await self.db.flush()
        return obj

    async def get_all(self) -> list[ModelType]:
        query = select(self.model)
        result = await self.db.execute(query)
        return list(result.scalars().all())
