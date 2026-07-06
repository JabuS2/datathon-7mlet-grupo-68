from fastapi import APIRouter

from .endpoints import account, auth, catalog, demo, governance, health, serving

router = APIRouter()
router.include_router(health.router)
router.include_router(auth.router)
router.include_router(serving.router)
router.include_router(demo.router)
router.include_router(governance.router)
router.include_router(account.router)
router.include_router(catalog.router)
