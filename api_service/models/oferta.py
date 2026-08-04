from sqlalchemy import Float, String, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from enums.catalogo import CategoriaOferta
from models.base import Base
from models.columns import enum_column


class Oferta(Base):
    """Cada braço do multi-armed bandit — uma oferta que o `/decide` pode recomendar.

    Definição estática do braço (o peso aprendido vive em `estado_braco`).
    Origem: `data/golden_set/offer_catalog.json` (10 braços).
    """

    __tablename__ = "ofertas"

    arm_id: Mapped[str] = mapped_column(String(20), primary_key=True)  # OFF-{CAT}-{NNN}
    product_name: Mapped[str] = mapped_column(String(120), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    category: Mapped[CategoriaOferta] = enum_column(CategoriaOferta, nullable=False)

    # Receita esperada (termo de receita do reward composto)
    expected_revenue_brl: Mapped[float] = mapped_column(Float, nullable=False)

    # Valores comerciais do catálogo. Ficam aqui — e não só no JSON lido pelo model_service —
    # porque o débito no saldo do cliente precisa de um preço confiável do lado do servidor;
    # aceitar o valor que o front manda seria deixar o cliente escolher quanto pagar.
    valor_total: Mapped[float | None] = mapped_column(Float, nullable=True)
    desconto_pct: Mapped[float | None] = mapped_column(Float, nullable=True)
    valor_final: Mapped[float | None] = mapped_column(Float, nullable=True)

    # Colunas extraídas como contexto do LinUCB
    context_features: Mapped[list[str]] = mapped_column(JSONB, nullable=False, default=list)
    # Filtros de elegibilidade (ex.: {"santander_filters": {...}})
    eligible_segment: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
    # Fator de exploração `c` do UCB/LinUCB
    ucb_exploration_factor: Mapped[float] = mapped_column(Float, nullable=False, default=1.5)
