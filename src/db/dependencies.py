from sqlalchemy.ext.asyncio import AsyncSession

from db.session import db


async def get_db() -> AsyncSession:
    async for session in db.session():
        yield session