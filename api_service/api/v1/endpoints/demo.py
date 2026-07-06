"""Endpoints da vitrine de demonstração (§6): onboarding → perfil sintético + conta demo."""

from fastapi import APIRouter, Depends

from core.jwt_token import JwtToken
from db.dependencies import get_uow
from db.unit_of_work import UnitOfWork
from schemas.cliente import OnboardingRequest, OnboardingResponse
from services.demo.service import OnboardingService

router = APIRouter(tags=["demo"])


@router.post("/onboarding", response_model=OnboardingResponse)
async def onboarding(body: OnboardingRequest, uow: UnitOfWork = Depends(get_uow)):
    service = OnboardingService(uow=uow, jwt=JwtToken())
    return await service.onboard(body)
