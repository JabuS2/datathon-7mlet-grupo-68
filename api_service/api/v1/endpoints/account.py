"""Camada self-service do usuário logado (E12): conta, perfil, sugestões e feedback.

Todas as rotas exigem JWT; o `cod_cliente` vem do **token** (não do body), e feedback/reward
verificam a **posse** da decisão. Reaproveita `DecisionService` (serving) e `AccountService`.
"""

from typing import Annotated

from fastapi import APIRouter, Depends

from core.auth_dependencies import get_current_user
from db.dependencies import get_uow
from db.unit_of_work import UnitOfWork
from enums.decisao import Canal
from models.user import User
from schemas.cliente import ClienteResponse
from schemas.decisao import (
    DecideResponse,
    DecisaoResponse,
    FeedbackRequest,
    FeedbackResponse,
    MeDecideRequest,
    RewardRequest,
    RewardResponse,
    ShowcaseResponse,
)
from services.account.service import AccountService
from services.decision.service import DecisionService

router = APIRouter(prefix="/me", tags=["account"])

CurrentUser = Annotated[User, Depends(get_current_user)]


@router.get("/profile", response_model=ClienteResponse)
async def my_profile(user: CurrentUser, uow: UnitOfWork = Depends(get_uow)):
    return await AccountService(uow).profile(user)


@router.get("/recommendations", response_model=ShowcaseResponse)
async def my_recommendations(
    user: CurrentUser,
    uow: UnitOfWork = Depends(get_uow),
    channel: Canal = Canal.APP,
    top_k: int = 5,
):
    cod = AccountService.require_cod_cliente(user)
    return await DecisionService(uow).showcase(cod, channel, top_k)


@router.post("/decide", response_model=DecideResponse)
async def my_decision(
    user: CurrentUser,
    uow: UnitOfWork = Depends(get_uow),
    channel: Canal = Canal.APP,
    body: MeDecideRequest | None = None,
):
    """Registra a decisão do usuário logado.

    Sem corpo, a política escolhe (oferta única). Com `{"armId": "..."}`, registra a oferta
    que o usuário clicou na vitrine — o corpo é opcional para não quebrar quem já chama sem ele.
    """
    cod = AccountService.require_cod_cliente(user)
    return await DecisionService(uow).decide(cod, channel, body.arm_id if body else None)


@router.post("/feedback", response_model=FeedbackResponse)
async def my_feedback(body: FeedbackRequest, user: CurrentUser, uow: UnitOfWork = Depends(get_uow)):
    await AccountService(uow).ensure_owns_decision(user, body.decision_id)
    return await DecisionService(uow).feedback(body.decision_id, body.type)


@router.post("/reward", response_model=RewardResponse)
async def my_reward(body: RewardRequest, user: CurrentUser, uow: UnitOfWork = Depends(get_uow)):
    await AccountService(uow).ensure_owns_decision(user, body.decision_id)
    return await DecisionService(uow).reward(body.decision_id, body.converted, body.value)


@router.get("/decisions", response_model=list[DecisaoResponse])
async def my_decisions(user: CurrentUser, uow: UnitOfWork = Depends(get_uow)):
    return await AccountService(uow).decisions(user)
