from fastapi import APIRouter

from .endpoints import auth, feedback, health, offers

router = APIRouter()
router.include_router(health.router)
router.include_router(auth.router)
router.include_router(offers.router)
router.include_router(feedback.router)
