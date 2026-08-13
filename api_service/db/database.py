from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from settings import settings


class Database:
    def __init__(self, url: str):
        self._engine = create_async_engine(
            url,
            echo=settings.SQLALCHEMY_ECHO,
            pool_pre_ping=True,  # descarta conexões quebradas antes de usar
        )
        self._session_factory = async_sessionmaker(
            bind=self._engine, expire_on_commit=False, class_=AsyncSession
        )

    @property
    def engine(self) -> Any:
        return self._engine

    async def session(self):
        async with self._session_factory() as session:
            yield session

    async def dispose(self):
        await self._engine.dispose()
