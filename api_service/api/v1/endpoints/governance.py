"""Endpoints de governança & MLOps (Etapa 7) — restritos a operador (RBAC)."""

from typing import Annotated

from fastapi import APIRouter, Depends

from core.auth_dependencies import require_operador
from db.dependencies import get_uow
from db.unit_of_work import UnitOfWork
from models.user import User
from schemas.governanca import (
    AprovacaoHumanaCreate,
    AprovacaoHumanaResponse,
    CicloRetreinoResponse,
    MetricaCreate,
    MetricaResponse,
    RetrainCycleCreate,
    RollbackRequest,
)
from schemas.politica import EstadoBracoResponse, PoliticaCreate, PoliticaResponse
from services.governance.service import GovernanceService

router = APIRouter(tags=["governance"])

Operador = Annotated[User, Depends(require_operador)]


@router.post("/policies", response_model=PoliticaResponse)
async def register_policy(body: PoliticaCreate, _: Operador, uow: UnitOfWork = Depends(get_uow)):
    return await GovernanceService(uow).register_policy(body)


@router.get("/policies", response_model=list[PoliticaResponse])
async def list_policies(_: Operador, uow: UnitOfWork = Depends(get_uow)):
    return await GovernanceService(uow).list_policies()


@router.get("/policies/{policy_id}/arms", response_model=list[EstadoBracoResponse])
async def list_arm_states(policy_id: str, _: Operador, uow: UnitOfWork = Depends(get_uow)):
    return await GovernanceService(uow).list_arm_states(policy_id)


@router.post("/policies/{policy_id}/promote", response_model=PoliticaResponse)
async def promote_policy(policy_id: str, _: Operador, uow: UnitOfWork = Depends(get_uow)):
    return await GovernanceService(uow).promote_policy(policy_id)


@router.post("/retrain-cycles", response_model=CicloRetreinoResponse)
async def start_cycle(body: RetrainCycleCreate, _: Operador, uow: UnitOfWork = Depends(get_uow)):
    return await GovernanceService(uow).start_cycle(body)


@router.post("/retrain-cycles/{run_id}/rollback", response_model=CicloRetreinoResponse)
async def rollback(run_id: str, body: RollbackRequest, _: Operador, uow: UnitOfWork = Depends(get_uow)):
    return await GovernanceService(uow).rollback(run_id, body.to_policy_id)


@router.post("/approvals", response_model=AprovacaoHumanaResponse)
async def decide_approval(body: AprovacaoHumanaCreate, user: Operador, uow: UnitOfWork = Depends(get_uow)):
    return await GovernanceService(uow).decide_approval(body, user.id)


@router.post("/metrics", response_model=MetricaResponse)
async def record_metric(body: MetricaCreate, _: Operador, uow: UnitOfWork = Depends(get_uow)):
    return await GovernanceService(uow).record_metric(body)


@router.get("/metrics", response_model=list[MetricaResponse])
async def list_metrics(
    _: Operador,
    uow: UnitOfWork = Depends(get_uow),
    policy_id: str | None = None,
    alerts_only: bool = False,
):
    return await GovernanceService(uow).list_metrics(policy_id, alerts_only)
