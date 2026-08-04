from __future__ import annotations

from collections.abc import AsyncIterator
from functools import lru_cache

from redis.asyncio import Redis, from_url
from sqlalchemy.ext.asyncio import AsyncSession

from catalog import Catalog
from db.session import db
from db.unit_of_work import UnitOfWork
from governance import GovernanceService
from registry import ModelRegistry
from service import BanditService
from settings import settings
from store import StateStore

_redis: Redis | None = None


async def get_session() -> AsyncIterator[AsyncSession]:
    async for session in db.session():
        yield session


async def get_uow() -> AsyncIterator[UnitOfWork]:
    """UnitOfWork por requisição — o `async with` de quem usa é que fecha a transação."""
    async for session in db.session():
        yield UnitOfWork(session)


async def get_governance() -> AsyncIterator[GovernanceService]:
    async for session in db.session():
        yield GovernanceService(UnitOfWork(session))


@lru_cache
def get_catalog() -> Catalog:
    return Catalog(settings.CATALOG_PATH, settings.CLIENTS_CSV_PATH)


def get_redis() -> Redis:
    global _redis
    if _redis is None:
        _redis = from_url(settings.REDIS_URL, decode_responses=True)
    return _redis


@lru_cache
def get_store() -> StateStore:
    return StateStore(get_redis())


@lru_cache
def get_service() -> BanditService:
    return BanditService(get_catalog(), get_store(), settings.DEFAULT_ALGORITHM)


@lru_cache
def get_registry() -> ModelRegistry:
    return ModelRegistry(settings.MLFLOW_TRACKING_URI, settings.MLFLOW_EXPERIMENT_NAME)
