from sqlalchemy import ForeignKey, String
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from enums.governanca import AcaoAdequacao
from models.base import Base
from models.columns import enum_column


class RegraAdequacao(Base):
    """Regra de suitability que bloqueia ou exige revisão humana de uma oferta inadequada a um perfil.

    Cobre o cenário de risco "violação de suitability" (Etapa 8).
    """

    __tablename__ = "regras_adequacao"

    rule_id: Mapped[str] = mapped_column(String(60), primary_key=True)
    arm_id: Mapped[str] = mapped_column(
        String(20), ForeignKey("ofertas.arm_id", ondelete="CASCADE"), nullable=False, index=True
    )
    condition: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
    action: Mapped[AcaoAdequacao] = enum_column(AcaoAdequacao, nullable=False)
