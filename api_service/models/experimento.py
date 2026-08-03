from datetime import datetime

from sqlalchemy import DateTime, String, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from enums.avaliacao import StatusExperimento
from models.base import Base
from models.columns import enum_column


class Experimento(Base):
    """Rodada de experimentação que agrupa decisões sob uma ou mais políticas.

    Consolida métricas (regret, conversão, exploração). É o que o MLflow rastreia e o assistente
    LLM resume.
    """

    __tablename__ = "experimentos"

    experiment_id: Mapped[str] = mapped_column(String(60), primary_key=True)
    policy_ids: Mapped[list[str]] = mapped_column(JSONB, nullable=False, default=list)
    hypothesis: Mapped[str | None] = mapped_column(Text, nullable=True)
    metrics: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
    period_start: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    period_end: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    status: Mapped[StatusExperimento] = enum_column(
        StatusExperimento, nullable=False, default=StatusExperimento.RUNNING
    )
