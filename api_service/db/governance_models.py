"""Tabelas de governança do model_service.

Três tabelas, e só três. `estados_braco` **não** migrou do api_service: o estado aprendido
vive no Redis, agora chaveado por `policy_id` (`bandit:state:{policy_id}`), então cada
política guarda os próprios pesos e o rollback recupera intacto sem cópia nenhuma — que é
exatamente a propriedade que a governança promete. Manter linhas por braço no Postgres
duplicaria o mesmo estado em dois lugares, com as duas cópias divergindo a cada `/update`.
Os pesos por braço são projetados do estado em `GET /policies/{policy_id}/arms`.

`aprovacoes_humanas.user_id` é referência **solta** para `users.id` do api_service: são
bancos diferentes, então não há FK. O id vem do JWT validado na borda.
"""

from datetime import datetime
from enum import Enum
from typing import Any

from sqlalchemy import Enum as SAEnum
from sqlalchemy import Float, ForeignKey, Integer, String, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

from enums.governanca import DecisaoAprovacao, StatusCicloRetreino
from enums.politica import AlgoritmoPolitica, StatusPolitica
from models.base import Base


class GovernanceBase(DeclarativeBase):
    """Baseia as tabelas no mesmo metadata, sem herdar campos de auditoria de domínio."""

    metadata = Base.metadata
    created_at: Mapped[datetime] = mapped_column(nullable=False, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        nullable=False, server_default=func.now(), onupdate=func.now()
    )


def enum_column(enum_cls: type[Enum], **kwargs: Any):
    """Enum como VARCHAR pelo **valor** do StrEnum — mesmo idioma do api_service."""
    length = max(len(str(member.value)) for member in enum_cls)
    return mapped_column(
        SAEnum(
            enum_cls,
            native_enum=False,
            values_callable=lambda e: [str(member.value) for member in e],
            length=length,
        ),
        **kwargs,
    )


class Politica(GovernanceBase):
    """Versão de política de decisão. No máximo uma `active` por vez."""

    __tablename__ = "politicas"

    policy_id: Mapped[str] = mapped_column(String(60), primary_key=True)
    version: Mapped[str] = mapped_column(String(20), nullable=False)
    algorithm: Mapped[AlgoritmoPolitica] = enum_column(AlgoritmoPolitica, nullable=False)
    hyperparams: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
    status: Mapped[StatusPolitica] = enum_column(
        StatusPolitica, nullable=False, default=StatusPolitica.SHADOW
    )


class CicloRetreino(GovernanceBase):
    """Um ciclo de retreino: candidata → gate humano → promovida / reprovada / revertida."""

    __tablename__ = "ciclos_retreino"

    run_id: Mapped[str] = mapped_column(String(80), primary_key=True)
    policy_id: Mapped[str] = mapped_column(
        ForeignKey("politicas.policy_id", ondelete="CASCADE"), nullable=False
    )
    status: Mapped[StatusCicloRetreino] = enum_column(
        StatusCicloRetreino, nullable=False, default=StatusCicloRetreino.CANDIDATE
    )
    metrics: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
    # Versão registrada no MLflow quando o ciclo foi aberto — liga o ciclo ao artefato.
    registry_version: Mapped[str | None] = mapped_column(String(40), nullable=True)


class AprovacaoHumana(GovernanceBase):
    """Veredito humano sobre promover uma candidata (approval gate)."""

    __tablename__ = "aprovacoes_humanas"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    run_id: Mapped[str] = mapped_column(
        ForeignKey("ciclos_retreino.run_id", ondelete="CASCADE"), nullable=False
    )
    # Referência solta para api_service.users.id — bancos distintos, sem FK possível.
    user_id: Mapped[int] = mapped_column(Integer, nullable=False)
    decision: Mapped[DecisaoAprovacao] = enum_column(DecisaoAprovacao, nullable=False)
    note: Mapped[str | None] = mapped_column(String(500), nullable=True)


class MetricaSnapshot(GovernanceBase):
    """Métrica publicada pelo api_service, que é quem tem `decisao`/`recompensa`.

    O model_service **não calcula** regret/conversão/PSI: os dados de origem vivem no outro
    serviço. Isto aqui é só a cópia exibida ao lado da política, para que o operador veja o
    número que sustentou uma promoção sem sair da tela de governança.
    """

    __tablename__ = "metricas_snapshot"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    policy_id: Mapped[str] = mapped_column(
        ForeignKey("politicas.policy_id", ondelete="CASCADE"), nullable=False
    )
    metric: Mapped[str] = mapped_column(String(40), nullable=False)
    value: Mapped[float] = mapped_column(Float, nullable=False)
    alert: Mapped[bool] = mapped_column(nullable=False, default=False)
