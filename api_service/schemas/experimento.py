from datetime import datetime

from pydantic import Field

from enums.avaliacao import StatusExperimento
from schemas.base import BaseSchema


class ExperimentoResponse(BaseSchema):
    """Rodada de experimentação (o que o MLflow / rastreio de experimentos consolida)."""

    experiment_id: str
    policy_ids: list[str]
    hypothesis: str | None = None
    metrics: dict = Field(default_factory=dict)
    period_start: datetime | None = None
    period_end: datetime | None = None
    status: StatusExperimento
