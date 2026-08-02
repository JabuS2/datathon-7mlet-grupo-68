from datetime import datetime
from uuid import UUID, uuid4

from sqlalchemy import DateTime, Float, ForeignKey, Uuid
from sqlalchemy.orm import Mapped, mapped_column

from enums.decisao import StatusRecompensa
from models.base import Base
from models.columns import enum_column


class Recompensa(Base):
    """Resultado de uma decisão que realimenta o bandit (reward composto receita+clique).

    Pode chegar atrasada: `status='pending'` até observar a transição 0→1 (delayed reward).
    """

    __tablename__ = "recompensas"

    reward_id: Mapped[UUID] = mapped_column(Uuid, primary_key=True, default=uuid4)
    decision_id: Mapped[UUID] = mapped_column(
        Uuid, ForeignKey("decisoes.decision_id", ondelete="CASCADE"), nullable=False, index=True
    )
    value: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    status: Mapped[StatusRecompensa] = enum_column(
        StatusRecompensa, nullable=False, default=StatusRecompensa.PENDING
    )
    observed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
