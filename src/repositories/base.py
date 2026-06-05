# src/repositories/base.py

from typing import Generic, TypeVar, Type, Optional, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

ModelType = TypeVar("ModelType")


class BaseRepository(Generic[ModelType]):
    def __init__(self, session: AsyncSession, model: Type[ModelType]):
        self.session = session
        self.model = model

    async def get_by_id(self, id: int) -> Optional[ModelType]:
        result = await self.session.execute(
            select(self.model).where(self.model.id == id)
        )
        return result.scalar_one_or_none()

    async def get_by_field(self, field: Any, value: Any) -> Optional[ModelType]:
        result = await self.session.execute(
            select(self.model).where(field == value)
        )
        return result.scalar_one_or_none()

    async def exists(self, field: Any, value: Any) -> bool:
        result = await self.session.execute(
            select(self.model.id).where(field == value)
        )
        return result.scalar_one_or_none() is not None

    async def filter(self, *criteria) -> list[ModelType]:
        result = await self.session.execute(
            select(self.model).where(*criteria)
        )
        return result.scalars().all()

    async def get_all(self) -> list[ModelType]:
        result = await self.session.execute(select(self.model))
        return result.scalars().all()

    async def add(self, obj: ModelType) -> ModelType:
        self.session.add(obj)
        return obj

    async def delete(self, obj: ModelType) -> None:
        await self.session.delete(obj)