from sqlalchemy import Float, String, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from enums.avaliacao import TipoCasoAvaliacao
from models.base import Base
from models.columns import enum_column


class CasoAvaliacao(Base):
    """Caso do golden set (≥20): contexto + ação/recompensa esperadas + critério pass/fail.

    Mede a qualidade da política offline (Etapa 4). Origem: `evaluation_cases.jsonl`.
    """

    __tablename__ = "casos_avaliacao"

    case_id: Mapped[str] = mapped_column(String(60), primary_key=True)
    context: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
    expected_arm: Mapped[str] = mapped_column(String(20), nullable=False)
    expected_reward: Mapped[float | None] = mapped_column(Float, nullable=True)
    rationale: Mapped[str | None] = mapped_column(Text, nullable=True)
    pass_fail_criteria: Mapped[str | None] = mapped_column(Text, nullable=True)
    type: Mapped[TipoCasoAvaliacao] = enum_column(
        TipoCasoAvaliacao, nullable=False, default=TipoCasoAvaliacao.TYPICAL
    )
