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

    #: Já está na carteira do usuário. A vitrine mostra o ranking COMPLETO do modelo e
    #: sinaliza o que foi adquirido, em vez de omitir: com 10 braços no catálogo, esconder
    #: os adquiridos esvaziava a tela em poucos cliques e dava a impressão de que o modelo
    #: tinha parado de recomendar.
    ja_adquirida: bool = False
