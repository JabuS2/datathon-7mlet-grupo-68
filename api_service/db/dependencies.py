from collections.abc import AsyncGenerator

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from db.session import db
from db.unit_of_work import UnitOfWork


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async for session in db.session():
        yield session


async def get_uow(db: AsyncSession = Depends(get_db)) -> AsyncGenerator[UnitOfWork, None]:
    async with UnitOfWork(db) as uow:
        yield uow
