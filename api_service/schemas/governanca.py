from datetime import datetime
from uuid import UUID

from pydantic import Field

from enums.governanca import (
    AcaoAdequacao,
    DecisaoAprovacao,
    StatusCicloRetreino,
    TipoMetrica,
)
from schemas.base import BaseSchema


class RetrainCycleCreate(BaseSchema):
    """Abre um ciclo de retreino para uma política candidata (nasce `candidate`)."""

    policy_id: str
    run_id: str | None = None  # gerado se omitido
    metrics: dict = Field(default_factory=dict)


class RollbackRequest(BaseSchema):
    """Reverte uma promoção: reativa `to_policy_id` e marca o ciclo como `rolled_back`."""

    to_policy_id: str


class MetricaCreate(BaseSchema):
    """Registra um snapshot de métrica monitorada de uma política."""

    policy_id: str
    metric: TipoMetrica
    value: float
    alert: bool = False


class MetricaResponse(BaseSchema):
    """Snapshot de métrica monitorada de uma política (Etapa 7)."""

    snapshot_id: UUID
    policy_id: str
    metric: TipoMetrica
    value: float
    alert: bool
    captured_at: datetime


class RegraAdequacaoResponse(BaseSchema):
    """Regra de suitability que bloqueia/exige revisão de uma oferta inadequada (Etapa 8)."""

    rule_id: str
    arm_id: str
    condition: dict
    action: AcaoAdequacao


class CicloRetreinoResponse(BaseSchema):
    """Ciclo de vida de uma política candidata (candidate → approved → promoted → rolled_back)."""

    run_id: str
    policy_id: str
    status: StatusCicloRetreino
    metrics: dict


class AprovacaoHumanaCreate(BaseSchema):
    """Veredito humano sobre promover uma política (human-in-the-loop)."""

    run_id: str
    decision: DecisaoAprovacao
    note: str | None = None


class AprovacaoHumanaResponse(BaseSchema):
    gate_id: UUID
    run_id: str
    user_id: int
    decision: DecisaoAprovacao
    note: str | None = None
    decided_at: datetime
