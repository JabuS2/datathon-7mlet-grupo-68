from __future__ import annotations

from functools import lru_cache

from redis.asyncio import Redis, from_url

from catalog import Catalog
from registry import ModelRegistry
from service import BanditService
from settings import settings
from store import StateStore

_redis: Redis | None = None


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
