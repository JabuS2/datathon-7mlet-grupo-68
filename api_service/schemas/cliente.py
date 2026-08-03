from pydantic import Field

from enums.catalogo import OrigemCliente
from schemas.base import BaseSchema


class OnboardingRequest(BaseSchema):
    """Cadastro curto da vitrine (2-3 perguntas) que gera um perfil sintético por template.

    A partir das respostas, o backend sorteia uma linha real do seed que case (mesmo segmento /
    faixa etária), copia o vetor de contexto como template e sobrescreve os campos respondidos.
    Também cria a conta de acesso (`tipo='demo'`) vinculada ao novo perfil.
    """

    email: str = Field(min_length=3, max_length=254)
    password: str = Field(min_length=6, max_length=128)
    idade: int = Field(ge=18, le=100)
    segmento: str  # objetivo/segmento escolhido (ex.: "02 - VAREJO")
    renda_estimada_anual_brl: float | None = Field(default=None, ge=0)


class ClienteResponse(BaseSchema):
    """Perfil do cliente (contexto do bandit). Campos sensíveis só para fairness, nunca decisão."""

    cod_cliente: int
    idade: int
    tempo_relacionamento_meses: int
    ind_ativo: bool
    segmento: str | None = None
    estado: str | None = None
    segmentos_sinteticos: list[str] = Field(default_factory=list)
    origem: OrigemCliente
    renda_estimada_anual_brl: float | None = None
    saldo_ficticio: float | None = None

    possui_poupanca: bool
    possui_conta_corrente: bool
    possui_conta_corrente_plus: bool
    possui_conta_premium: bool
    possui_conta_salario: bool
    possui_conta_junior: bool
    possui_conta_universitaria: bool
    possui_conta_digital: bool
    possui_conta_investimento: bool

    possui_cdb_curto_prazo: bool
    possui_cdb_medio_prazo: bool
    possui_cdb_longo_prazo: bool
    possui_fundo_investimento: bool
    possui_titulos_investimento: bool
    possui_previdencia_privada: bool

    possui_financiamento_imovel: bool
    possui_financiamento_veiculo: bool
    possui_emprestimo_pessoal: bool
    possui_cartao_credito: bool
    possui_aval_garantia: bool

    possui_pagamento_tributos: bool
    possui_folha_pagamento: bool
    possui_beneficio_previdencia: bool
    possui_debito_automatico: bool


class OnboardingResponse(BaseSchema):
    """Retorno do cadastro demo: token de acesso + o perfil sintético gerado."""

    access_token: str
    token_type: str = "bearer"
    cliente: ClienteResponse


class ClienteContexto(BaseSchema):
    """Vetor de contexto efetivamente consumido pelo LinUCB (auditável em `decisao.context`)."""

    idade: int
    renda_estimada_anual_brl: float | None = None
    tempo_relacionamento_meses: int
    ind_ativo: bool
    features: dict[str, object] = Field(
        default_factory=dict
    )  # flags possui_* usadas como contexto
