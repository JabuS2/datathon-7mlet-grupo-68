from schemas.base import BaseSchema


class FeedbackCreate(BaseSchema):
    arm_id: str
    clicked: bool
    algorithm: str | None = None


class FeedbackResponse(BaseSchema):
    """Resultado do clique: o que o modelo aprendeu e o que saiu do saldo."""

    arm_id: str
    clicked: bool
    reward: float
    algorithm: str
    status: str

    #: Quanto foi debitado do saldo (0 quando não há preço ou faltou saldo).
    valor_debitado: float = 0.0
    #: Saldo depois do débito — o front atualiza a tela com isto.
    saldo_ficticio: float | None = None
    #: `True` quando o produto tem preço mas o saldo não cobria. O interesse é registrado
    #: mesmo assim: o bandit precisa aprender com o clique independentemente do saldo.
    saldo_insuficiente: bool = False
