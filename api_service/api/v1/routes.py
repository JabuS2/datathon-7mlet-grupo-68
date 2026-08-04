from fastapi import APIRouter

from .endpoints import (
    account,
    admin,
    auth,
    catalog,
    demo,
    feedback,
    health,
    offers,
    serving,
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
