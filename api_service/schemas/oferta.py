from enums.catalogo import CategoriaOferta
from schemas.base import BaseSchema


class OfertaResponse(BaseSchema):
    """Braço do bandit exposto no catálogo/admin."""

    arm_id: str
    product_name: str
    description: str
    category: CategoriaOferta
    expected_revenue_brl: float
    context_features: list[str]
    eligible_segment: dict
    ucb_exploration_factor: float


class OfertaPublica(BaseSchema):
    """Recorte da oferta visível ao cliente na vitrine (sem parâmetros internos do bandit)."""

    arm_id: str
    product_name: str
    description: str
    category: CategoriaOferta
