from sqlalchemy import String, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from models.base import Base


class Segmento(Base):
    """Grupo sintético de clientes (ex.: SEG-VIP, SEG-JOVEM).

    Usado para elegibilidade de ofertas e para a análise de fairness de exposição entre grupos.
    """

    __tablename__ = "segmentos"

    segment_id: Mapped[str] = mapped_column(String(40), primary_key=True)  # SEG-...
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    filters: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
