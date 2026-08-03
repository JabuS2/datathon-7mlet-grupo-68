from datetime import datetime

from pydantic import Field

from enums.politica import AlgoritmoPolitica, StatusPolitica
from schemas.base import BaseSchema


class PoliticaCreate(BaseSchema):
    """Registra uma nova versão de política (nasce em `shadow`)."""

    policy_id: str
    version: str
    algorithm: AlgoritmoPolitica
    hyperparams: dict = Field(default_factory=dict)


class PoliticaResponse(BaseSchema):
    policy_id: str
    version: str
    algorithm: AlgoritmoPolitica
    hyperparams: dict
    status: StatusPolitica
    created_at: datetime


class EstadoBracoResponse(BaseSchema):
    """Pesos aprendidos por (política, braço) — colunas polimórficas por algoritmo."""

    policy_id: str
    arm_id: str
    alpha: float
    beta: float
    n_pulls: int
    sum_reward: float
    updated_at: datetime
