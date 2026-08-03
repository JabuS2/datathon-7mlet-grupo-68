from datetime import datetime
from uuid import UUID, uuid4

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text, Uuid, func
from sqlalchemy.orm import Mapped, mapped_column

from enums.governanca import DecisaoAprovacao
from models.base import Base
from models.columns import enum_column


class AprovacaoHumana(Base):
    """Registro da decisão de um operador (aprovar/rejeitar) sobre promover uma política.

    O human-in-the-loop e a base do rollback auditável (Etapa 7).
    """

    __tablename__ = "aprovacoes_humanas"

    gate_id: Mapped[UUID] = mapped_column(Uuid, primary_key=True, default=uuid4)
    run_id: Mapped[str] = mapped_column(
        String(80),
        ForeignKey("ciclos_retreino.run_id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    user_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("users.id", ondelete="RESTRICT"), nullable=False
    )
    decision: Mapped[DecisaoAprovacao] = enum_column(DecisaoAprovacao, nullable=False)
    note: Mapped[str | None] = mapped_column(Text, nullable=True)
    decided_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
