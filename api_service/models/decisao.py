from uuid import UUID, uuid4

from sqlalchemy import BigInteger, Float, ForeignKey, String, Uuid
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from enums.decisao import Canal
from models.base import Base
from models.columns import enum_column


class Decisao(Base):
    """Registro auditável de cada chamada ao `/decide` — o coração do log da Etapa 5.

    Guarda qual braço foi escolhido, para qual cliente, com qual política e por quê
    (`reason_codes`), além do `context` (features que entraram — auditoria LGPD).
    """

    __tablename__ = "decisoes"

    decision_id: Mapped[UUID] = mapped_column(Uuid, primary_key=True, default=uuid4)
    cod_cliente: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("clientes.cod_cliente", ondelete="SET NULL"), nullable=True
    )
    # Referência SOLTA para a política: `politicas` migrou para o model_service (banco
    # próprio), então não há FK possível. O valor vem do `policy_id` que o /rank devolveu —
    # é o que amarra a decisão à versão do modelo que a produziu.
    policy_version: Mapped[str] = mapped_column(String(60), nullable=False)
    chosen_arm_id: Mapped[str] = mapped_column(
        String(20), ForeignKey("ofertas.arm_id", ondelete="RESTRICT"), nullable=False
    )
    channel: Mapped[Canal] = enum_column(Canal, nullable=False, default=Canal.APP)

    context: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
    reason_codes: Mapped[list[str]] = mapped_column(JSONB, nullable=False, default=list)
    score: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
