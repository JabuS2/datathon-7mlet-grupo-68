from fastapi import APIRouter

from .endpoints import (
    account,
    admin,
    auth,
    catalog,
    demo,
    feedback,
    governance,
    health,
    monitoring,
    offers,
    rank,
    registry,
    serving,
    update,
)

router = APIRouter()
router.include_router(health.router)
router.include_router(auth.router)
router.include_router(offers.router)
router.include_router(feedback.router)
router.include_router(admin.router)
router.include_router(serving.router)
router.include_router(demo.router)
router.include_router(account.router)
router.include_router(catalog.router)
router.include_router(monitoring.router)
router.include_router(rank.router)
router.include_router(update.router)
router.include_router(registry.router)
router.include_router(governance.router)
