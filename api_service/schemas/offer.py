from schemas.base import BaseSchema


class OfferResponse(BaseSchema):
    arm_id: str
    rank: int
    score: float
    category: str
    product_name: str
    description: str
    valor_total: float | None = None
    desconto_pct: float | None = None
    valor_final: float | None = None
