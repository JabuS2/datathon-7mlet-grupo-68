from __future__ import annotations

import asyncio
from collections.abc import AsyncIterator
from functools import lru_cache

from redis.asyncio import Redis, from_url
from sqlalchemy.ext.asyncio import AsyncSession

from db.session import db
from services.bandit import BanditService
from services.bandit.catalog import Catalog
from services.bandit.governance import GovernanceService
from services.bandit.governance_uow import UnitOfWork
from services.bandit.registry import ModelRegistry
from services.bandit.store import StateStore
from settings import settings

_redis: Redis | None = None


async def get_session() -> AsyncIterator[AsyncSession]:
    async for session in db.session():
        yield session


async def get_uow() -> AsyncIterator[UnitOfWork]:
    """UnitOfWork por requisição — o `async with` de quem usa é que fecha a transação."""
    async for session in db.session():
        yield UnitOfWork(session)


get_bandit_uow = get_uow


async def _snapshot_to_registry(policy) -> str | None:
    """Versiona o estado da política no MLflow e devolve a versão registrada."""
    state = await get_service().snapshot_state(policy.algorithm, policy=policy)
    info = await asyncio.to_thread(get_registry().register_version, policy.policy_id, state)
    return str(info.get("version")) if isinstance(info, dict) else None


async def get_governance() -> AsyncIterator[GovernanceService]:
    async for session in db.session():
        yield GovernanceService(UnitOfWork(session), snapshot=_snapshot_to_registry)


@lru_cache
def get_catalog() -> Catalog:
    return Catalog(settings.catalog_path, settings.clients_csv_path)


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
