from sqlalchemy import ForeignKey, String
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from enums.governanca import StatusCicloRetreino
from models.base import Base
from models.columns import enum_column


class CicloRetreino(Base):
    """Ciclo de vida de uma política candidata (candidate → approved → promoted → rolled_back).

    Documenta como uma nova hipótese chega à produção controlada, com a versão no MLflow (Etapa 7).
    """

    __tablename__ = "ciclos_retreino"

    run_id: Mapped[str] = mapped_column(String(80), primary_key=True)
    policy_id: Mapped[str] = mapped_column(
        String(60),
        ForeignKey("politicas.policy_id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    status: Mapped[StatusCicloRetreino] = enum_column(
        StatusCicloRetreino, nullable=False, default=StatusCicloRetreino.CANDIDATE
    )
    metrics: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
