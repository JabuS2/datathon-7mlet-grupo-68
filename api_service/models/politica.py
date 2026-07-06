from sqlalchemy import String
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from enums.politica import AlgoritmoPolitica, StatusPolitica
from models.base import Base
from models.columns import enum_column


class Politica(Base):
    """Versão de um algoritmo de decisão (baseline/thompson/ucb/linucb) e hiperparâmetros.

    Permite versionar, comparar e promover/reverter políticas (Etapas 3/7). Mapeia o policy_store.
    """

    __tablename__ = "politicas"

    policy_id: Mapped[str] = mapped_column(String(60), primary_key=True)
    version: Mapped[str] = mapped_column(String(30), nullable=False)
    algorithm: Mapped[AlgoritmoPolitica] = enum_column(AlgoritmoPolitica, nullable=False)
    hyperparams: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
    status: Mapped[StatusPolitica] = enum_column(
        StatusPolitica, nullable=False, default=StatusPolitica.SHADOW
    )
