"""Governança & MLOps: ciclo de vida de políticas, approval gate e métricas publicadas.

Migrado do api_service. A autorização (operador) fica na borda do api_service, que é quem
tem `users` e valida o JWT; aqui o `user_id` do approval gate chega no corpo. Expor este
serviço fora da rede interna exigiria autenticação própria — ver README do model_service.
"""

from fastapi import APIRouter, Depends

from dependencies import get_governance, get_service
from governance import GovernanceService
from schemas.governance import (
    AprovacaoCreate,
    AprovacaoResponse,
    ArmStateResponse,
    CicloRetreinoResponse,
    MetricaPublish,
    MetricaResponse,
    PoliticaCreate,
    PoliticaResponse,
    RetrainCycleCreate,
    RollbackRequest,
)
from service import BanditService

router = APIRouter(tags=["governance"])


@router.post("/policies", response_model=PoliticaResponse)
async def register_policy(
    body: PoliticaCreate, gov: GovernanceService = Depends(get_governance)
):
    return await gov.register_policy(body)


@router.get("/policies", response_model=list[PoliticaResponse])
async def list_policies(gov: GovernanceService = Depends(get_governance)):
    return await gov.list_policies()


@router.get("/policies/{policy_id}/arms", response_model=list[ArmStateResponse])
async def list_arm_states(
    policy_id: str,
    gov: GovernanceService = Depends(get_governance),
    service: BanditService = Depends(get_service),
):
    """Pesos por braço da política — projetados do estado no Redis, não de tabela."""
    policy = await gov.resolved(policy_id)
    return await service.arm_states(policy)


@router.post("/policies/{policy_id}/promote", response_model=PoliticaResponse)
async def promote_policy(policy_id: str, gov: GovernanceService = Depends(get_governance)):
    return await gov.promote_policy(policy_id)


@router.post("/retrain-cycles", response_model=CicloRetreinoResponse)
async def start_cycle(
    body: RetrainCycleCreate, gov: GovernanceService = Depends(get_governance)
):
    return await gov.start_cycle(body)


@router.get("/retrain-cycles", response_model=list[CicloRetreinoResponse])
async def list_cycles(
    policy_id: str | None = None, gov: GovernanceService = Depends(get_governance)
):
    return await gov.list_cycles(policy_id)


@router.post("/retrain-cycles/{run_id}/rollback", response_model=CicloRetreinoResponse)
async def rollback(
    run_id: str, body: RollbackRequest, gov: GovernanceService = Depends(get_governance)
):
    return await gov.rollback(run_id, body.to_policy_id)


@router.post("/approvals", response_model=AprovacaoResponse)
async def decide_approval(
    body: AprovacaoCreate,
    user_id: int,
    gov: GovernanceService = Depends(get_governance),
):
    """`user_id` vem do JWT já validado pelo api_service (query param na chamada interna)."""
    return await gov.decide_approval(body, user_id)


@router.post("/metrics", response_model=MetricaResponse)
async def publish_metric(body: MetricaPublish, gov: GovernanceService = Depends(get_governance)):
    """O api_service calcula a métrica (tem `decisao`/`recompensa`) e publica aqui."""
    return await gov.publish_metric(body)


@router.get("/metrics", response_model=list[MetricaResponse])
async def list_metrics(
    policy_id: str | None = None,
    alerts_only: bool = False,
    gov: GovernanceService = Depends(get_governance),
):
    return await gov.list_metrics(policy_id, alerts_only)
