from datetime import datetime
from uuid import UUID, uuid4

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, String, Uuid, func
from sqlalchemy.orm import Mapped, mapped_column

from enums.governanca import TipoMetrica
from models.base import Base
from models.columns import enum_column


class MetricaMonitoramento(Base):
    """Série temporal de métricas de uma política (regret, conversão, reward, PSI drift).

    Detecta degradação — `alert=True` marca quando ultrapassa o limiar (Etapa 7).
    """

    __tablename__ = "metricas_monitoramento"

    snapshot_id: Mapped[UUID] = mapped_column(Uuid, primary_key=True, default=uuid4)
    policy_id: Mapped[str] = mapped_column(
        String(60),
        ForeignKey("politicas.policy_id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    metric: Mapped[TipoMetrica] = enum_column(TipoMetrica, nullable=False)
    value: Mapped[float] = mapped_column(Float, nullable=False)
    alert: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    captured_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
