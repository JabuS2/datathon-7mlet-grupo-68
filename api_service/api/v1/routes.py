from fastapi import APIRouter

from .endpoints import admin, auth, health

router = APIRouter()
router.include_router(health.router)
router.include_router(auth.router)
router.include_router(admin.router)
