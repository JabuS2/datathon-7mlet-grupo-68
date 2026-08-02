"""Endpoints de serving do bandit (Etapa 5): decisão controlada e auditável.

Contratos documentados em `docs/api-contracts.md`. RBAC por papel entra em E8.
"""

from fastapi import APIRouter, Depends

from db.dependencies import get_uow
from db.unit_of_work import UnitOfWork
from schemas.decisao import (
    DecideRequest,
    DecideResponse,
    FeedbackRequest,
    FeedbackResponse,
    RewardRequest,
    RewardResponse,
    ShowcaseRequest,
    ShowcaseResponse,
)
from services.decision.service import DecisionService

router = APIRouter(tags=["serving"])


@router.post("/decide", response_model=DecideResponse)
async def decide(body: DecideRequest, uow: UnitOfWork = Depends(get_uow)):
    return await DecisionService(uow).decide(body.cod_cliente, body.channel, body.arm_id)


@router.post("/showcase", response_model=ShowcaseResponse)
async def showcase(body: ShowcaseRequest, uow: UnitOfWork = Depends(get_uow)):
    return await DecisionService(uow).showcase(body.cod_cliente, body.channel, body.top_k)


@router.post("/feedback", response_model=FeedbackResponse)
async def feedback(body: FeedbackRequest, uow: UnitOfWork = Depends(get_uow)):
    return await DecisionService(uow).feedback(body.decision_id, body.type)


@router.post("/reward", response_model=RewardResponse)
async def reward(body: RewardRequest, uow: UnitOfWork = Depends(get_uow)):
    return await DecisionService(uow).reward(body.decision_id, body.converted, body.value)
