from datetime import datetime
from uuid import UUID, uuid4

from sqlalchemy import DateTime, ForeignKey, Uuid, func
from sqlalchemy.orm import Mapped, mapped_column

from enums.decisao import TipoEvento
from models.base import Base
from models.columns import enum_column


class EventoImpressao(Base):
    """Evento observado após a decisão — a oferta foi exibida (impression) e/ou clicada (click).

    Camada `offer_events` (Etapa 2) e fonte do sinal de clique do reward composto.
    """

    __tablename__ = "eventos_impressao"

    event_id: Mapped[UUID] = mapped_column(Uuid, primary_key=True, default=uuid4)
    decision_id: Mapped[UUID] = mapped_column(
        Uuid, ForeignKey("decisoes.decision_id", ondelete="CASCADE"), nullable=False, index=True
    )
    type: Mapped[TipoEvento] = enum_column(TipoEvento, nullable=False)
    occurred_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
