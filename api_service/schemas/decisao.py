from datetime import datetime
from uuid import UUID

from pydantic import Field

from enums.catalogo import CategoriaOferta
from enums.decisao import Canal, StatusRecompensa, TipoEvento
from schemas.base import BaseSchema

# ─────────────────────────── /decide ───────────────────────────


class DecideRequest(BaseSchema):
    """Entrada do `/decide`: quem é o cliente e em qual canal decidir.

    `arm_id` opcional serve a vitrine clicável: quando informado, registra a oferta que o
    usuário escolheu na lista em vez de deixar a política escolher.
    """

    cod_cliente: int
    channel: Canal = Canal.APP
    arm_id: str | None = None


class MeDecideRequest(BaseSchema):
    """Corpo (opcional) do `/me/decide`: só a oferta escolhida na vitrine.

    Sem corpo — ou com `armId` nulo — a política decide, que é o fluxo de oferta única.
    """

    arm_id: str | None = None


class DecideResponse(BaseSchema):
    """Saída do `/decide`: braço escolhido + justificativa + versão da política (auditável)."""

    decision_id: UUID
    arm_id: str
    product_name: str
    description: str
    category: CategoriaOferta
    channel: Canal
    score: float
    reason_codes: list[str]
    policy_version: str


# ─────────────────────────── /showcase ───────────────────────────


class OfertaRankeada(BaseSchema):
    """Item da vitrine ranqueada pelo score UCB."""

    arm_id: str
    product_name: str
    description: str
    category: CategoriaOferta
    score: float
    reason_codes: list[str]
    rank: int


class ShowcaseRequest(BaseSchema):
    cod_cliente: int
    channel: Canal = Canal.APP
    top_k: int = Field(default=5, ge=1, le=10)


class ShowcaseResponse(BaseSchema):
    cod_cliente: int
    policy_version: str
    items: list[OfertaRankeada]


# ─────────────────────────── /feedback e /reward ───────────────────────────


class FeedbackRequest(BaseSchema):
    """Evento observado após a decisão (clique = sinal do termo `beta` do reward composto)."""

    decision_id: UUID
    type: TipoEvento = TipoEvento.CLICK


class FeedbackResponse(BaseSchema):
    event_id: UUID
    decision_id: UUID
    type: TipoEvento
    occurred_at: datetime


class RewardRequest(BaseSchema):
    """Resultado de uma decisão (adoção do produto). Pode chegar atrasado (delayed reward).

    A recompensa é binária e derivada aqui: 1.0 se houve clique ou conversão, 0.0 caso
    contrário. Não há valor arbitrado pelo chamador.
    """

    decision_id: UUID
    converted: bool = True


class RewardResponse(BaseSchema):
    reward_id: UUID
    decision_id: UUID
    value: float
    status: StatusRecompensa


# ─────────────────────────── views auditáveis ───────────────────────────


class DecisaoResponse(BaseSchema):
    """Registro auditável completo de uma decisão (Etapa 5)."""

    decision_id: UUID
    cod_cliente: int | None = None
    policy_version: str
    chosen_arm_id: str
    channel: Canal
    context: dict
    reason_codes: list[str]
    score: float
    created_at: datetime
