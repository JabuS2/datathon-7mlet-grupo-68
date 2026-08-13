from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from enums.governanca import DecisaoAprovacao, StatusCicloRetreino
from enums.politica import AlgoritmoPolitica, StatusPolitica


class _ORM(BaseModel):
    model_config = ConfigDict(from_attributes=True)


# ── políticas ────────────────────────────────────────────────────
class PoliticaCreate(BaseModel):
    policy_id: str = Field(max_length=60)
    version: str = Field(max_length=20)
    algorithm: AlgoritmoPolitica
    hyperparams: dict[str, Any] = Field(default_factory=dict)


class PoliticaResponse(_ORM):
    policy_id: str
    version: str
    algorithm: AlgoritmoPolitica
    hyperparams: dict[str, Any]
    status: StatusPolitica
    created_at: datetime


class ArmStateResponse(BaseModel):
    """Pesos por braço, projetados do estado da política (não há tabela `estados_braco`).

    `params` é específico do algoritmo — ver `BanditService._arm_params`.
    """

    arm_id: str
    algorithm: str | None = None
    params: dict[str, Any] = Field(default_factory=dict)


# ── ciclos de retreino ───────────────────────────────────────────
class RetrainCycleCreate(BaseModel):
    policy_id: str
    run_id: str | None = Field(default=None, max_length=80)
    metrics: dict[str, Any] = Field(default_factory=dict)


class CicloRetreinoResponse(_ORM):
    run_id: str
    policy_id: str
    status: StatusCicloRetreino
    metrics: dict[str, Any]
    registry_version: str | None = None
    created_at: datetime


class RollbackRequest(BaseModel):
    to_policy_id: str


# ── approval gate ────────────────────────────────────────────────
class AprovacaoCreate(BaseModel):
    run_id: str
    decision: DecisaoAprovacao
    note: str | None = Field(default=None, max_length=500)


class AprovacaoResponse(_ORM):
    id: int
    run_id: str
    user_id: int
    decision: DecisaoAprovacao
    note: str | None = None
    created_at: datetime


# ── métricas publicadas pelo api_service ─────────────────────────
class MetricaPublish(BaseModel):
    """O api_service calcula (tem `decisao`/`recompensa`) e publica aqui para exibição."""

    policy_id: str
    metric: str = Field(max_length=40)
    value: float
    alert: bool = False


class MetricaResponse(_ORM):
    id: int
    policy_id: str
    metric: str
    value: float
    alert: bool
    created_at: datetime
