from sqlalchemy import BigInteger, Boolean, Float, Integer, String
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from enums.catalogo import OrigemCliente
from models.base import Base
from models.columns import enum_column

# As 24 flags de posse de produto do dataset Santander (base da recompensa: transição 0→1).
PRODUCT_FLAGS: tuple[str, ...] = (
    "possui_poupanca",
    "possui_conta_corrente",
    "possui_conta_corrente_plus",
    "possui_conta_premium",
    "possui_conta_salario",
    "possui_conta_junior",
    "possui_conta_universitaria",
    "possui_conta_digital",
    "possui_conta_investimento",
    "possui_cdb_curto_prazo",
    "possui_cdb_medio_prazo",
    "possui_cdb_longo_prazo",
    "possui_fundo_investimento",
    "possui_titulos_investimento",
    "possui_previdencia_privada",
    "possui_financiamento_imovel",
    "possui_financiamento_veiculo",
    "possui_emprestimo_pessoal",
    "possui_cartao_credito",
    "possui_aval_garantia",
    "possui_pagamento_tributos",
    "possui_folha_pagamento",
    "possui_beneficio_previdencia",
    "possui_debito_automatico",
)

_flag = lambda: mapped_column(Boolean, nullable=False, default=False)  # noqa: E731


class Cliente(Base):
    """Cliente do banco digital — sujeito elegível de cada decisão.

    Fornece o vetor de contexto (idade, segmento, produtos que já possui) que o bandit usa.
    Origem híbrida: subset seedado do `golden_clients.csv` (`origem='seed'`) + perfis criados
    no cadastro da vitrine (`origem='demo'`).
    """

    __tablename__ = "clientes"

    # Identificador sintético; perfis 'demo' usam faixa reservada (>= 9_000_000). Sem autoincrement.
    cod_cliente: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=False)

    # Contexto de decisão
    idade: Mapped[int] = mapped_column(Integer, nullable=False)
    tempo_relacionamento_meses: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    ind_ativo: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    segmento: Mapped[str | None] = mapped_column(String(40), nullable=True)
    estado: Mapped[str | None] = mapped_column(String(2), nullable=True)

    # Atributos protegidos/sensíveis — SÓ fairness, nunca feature de decisão (LGPD)
    sexo: Mapped[str | None] = mapped_column(String(1), nullable=True)
    renda_estimada_anual_brl: Mapped[float | None] = mapped_column(Float, nullable=True)

    # Segmentos sintéticos (elegibilidade / fairness de exposição) e gatilho de conversão
    segmentos_sinteticos: Mapped[list[str]] = mapped_column(JSONB, nullable=False, default=list)
    evento_viagem_sintetico: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)

    origem: Mapped[OrigemCliente] = enum_column(
        OrigemCliente, nullable=False, default=OrigemCliente.SEED
    )

    #: Nunca entram na decisão, em nenhuma forma (LGPD). O model_service declara a exclusão
    #: no bloco auditável; aqui garantimos que o valor não chega a sair do serviço.
    PROTECTED_ATTRIBUTES: tuple[str, ...] = ("sexo",)

    #: Metadados de linha: não são features e não são serializáveis em JSON (datetime).
    #: O contexto atravessa HTTP até o model_service, então mandá-los quebraria a chamada.
    _AUDIT_COLUMNS: tuple[str, ...] = ("created_at", "updated_at", "created_by", "updated_by")

    def to_context(self) -> dict:
        """Projeção do cliente como dicionário de contexto para o bandit.

        Sai daqui pela rede até o model_service, então:
        - atributos protegidos são removidos **na origem** — minimização de dado, não
          confiança no consumidor (o model_service descarta de novo na entrada);
        - metadados de linha ficam fora: não são features e `datetime` não é JSON.
        """
        skip = set(self.PROTECTED_ATTRIBUTES) | set(self._AUDIT_COLUMNS)
        return {
            col.name: getattr(self, col.name)
            for col in self.__table__.columns
            if col.name not in skip
        }

    # --- 24 flags de posse de produto (base da recompensa) ---
    possui_poupanca: Mapped[bool] = _flag()
    possui_conta_corrente: Mapped[bool] = _flag()
    possui_conta_corrente_plus: Mapped[bool] = _flag()
    possui_conta_premium: Mapped[bool] = _flag()
    possui_conta_salario: Mapped[bool] = _flag()
    possui_conta_junior: Mapped[bool] = _flag()
    possui_conta_universitaria: Mapped[bool] = _flag()
    possui_conta_digital: Mapped[bool] = _flag()
    possui_conta_investimento: Mapped[bool] = _flag()
    possui_cdb_curto_prazo: Mapped[bool] = _flag()
    possui_cdb_medio_prazo: Mapped[bool] = _flag()
    possui_cdb_longo_prazo: Mapped[bool] = _flag()
    possui_fundo_investimento: Mapped[bool] = _flag()
    possui_titulos_investimento: Mapped[bool] = _flag()
    possui_previdencia_privada: Mapped[bool] = _flag()
    possui_financiamento_imovel: Mapped[bool] = _flag()
    possui_financiamento_veiculo: Mapped[bool] = _flag()
    possui_emprestimo_pessoal: Mapped[bool] = _flag()
    possui_cartao_credito: Mapped[bool] = _flag()
    possui_aval_garantia: Mapped[bool] = _flag()
    possui_pagamento_tributos: Mapped[bool] = _flag()
    possui_folha_pagamento: Mapped[bool] = _flag()
    possui_beneficio_previdencia: Mapped[bool] = _flag()
    possui_debito_automatico: Mapped[bool] = _flag()
