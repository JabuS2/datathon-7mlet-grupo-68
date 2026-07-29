from fastapi import APIRouter

from .endpoints import health, rank, registry, update

router = APIRouter()
router.include_router(health.router)
router.include_router(rank.router)
router.include_router(update.router)
router.include_router(registry.router)
