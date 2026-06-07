from typing import Any

from sqlalchemy import ColumnElement, exists, select
from sqlalchemy.ext.asyncio import AsyncSession


class BaseRepository[ModelType]:
    def __init__(self, session: AsyncSession, model: type[ModelType]):
        self.session = session
        self.model = model

    async def get_by_id(self, obj_id: int) -> ModelType | None:
        result = await self.session.execute(
            select(self.model).where(self.model.id == obj_id)  # type: ignore[attr-defined]
        )
        return result.scalar_one_or_none()

    async def get_by_field(
        self,
        field: Any,
        value: Any,
    ) -> ModelType | None:
        result = await self.session.execute(select(self.model).where(field == value))
        return result.scalar_one_or_none()

    async def exists(self, field: ColumnElement, value: Any) -> bool:
        stmt = select(exists().where(field == value))
        result = await self.session.scalar(stmt)
        return bool(result)

    async def filter(self, *criteria) -> list[ModelType]:
        result = await self.session.execute(select(self.model).where(*criteria))
        return list(result.scalars().all())

    async def get_all(self) -> list[ModelType]:
        result = await self.session.execute(select(self.model))
        return list(result.scalars().all())

    def add(self, obj: ModelType) -> ModelType:
        self.session.add(obj)
        return obj

    def delete(self, obj: ModelType) -> None:
        self.session.delete(obj)  # type: ignore[unused-coroutine]
