from datetime import datetime

from enums.catalogo import CategoriaOferta
from schemas.base import BaseSchema


class InteresseResponse(BaseSchema):
    """Oferta em que o usuário demonstrou interesse — um item da carteira.

    Deriva de `feedback_events`: é o mesmo clique que realimenta o bandit. Não há tabela de
    carteira separada, e não deveria haver — duas fontes para "o que a pessoa escolheu"
    divergiriam, e o log de feedback é o que o modelo enxerga.
    """

    arm_id: str
    product_name: str
    description: str
    category: CategoriaOferta
    #: Quantas vezes clicou. Repetir é mais interesse, não outro item.
    cliques: int
    ultimo_clique: datetime
