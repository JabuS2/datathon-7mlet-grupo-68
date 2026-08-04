"""Monitoramento (operador): apura as métricas do log auditável e publica no model_service."""

from typing import Annotated

from fastapi import APIRouter, Depends, Query

from core.auth_dependencies import require_operador
from db.dependencies import get_uow
from db.unit_of_work import UnitOfWork
from models.user import User
from schemas.monitoring import MetricsReport
from services.model_client import ModelServiceClient
from services.monitoring import MonitoringService
from services.monitoring.service import DEFAULT_WINDOW_DAYS

router = APIRouter(tags=["monitoring"])
model_client = ModelServiceClient()

Operador = Annotated[User, Depends(require_operador)]
WindowDays = Annotated[int, Query(ge=1, le=365)]


@router.get("/monitoring/metrics", response_model=MetricsReport)
async def compute_metrics(
    _: Operador,
    policy_version: str | None = None,
    window_days: WindowDays = DEFAULT_WINDOW_DAYS,
    uow: UnitOfWork = Depends(get_uow),
):
    """Calcula sem publicar — leitura barata para conferir antes de registrar."""
    return await MonitoringService(uow, model_client).compute(policy_version, window_days)


@router.post("/monitoring/metrics/{policy_version}/publish", response_model=MetricsReport)
async def publish_metrics(
    policy_version: str,
    _: Operador,
    window_days: WindowDays = DEFAULT_WINDOW_DAYS,
    uow: UnitOfWork = Depends(get_uow),
):
    """Calcula e publica no model_service, para exibição junto da política."""
    return await MonitoringService(uow, model_client).publish(policy_version, window_days)
