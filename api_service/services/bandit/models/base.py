from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any

import numpy as np


@dataclass
class BanditContext:
    """Tudo que um modelo pode precisar para ranquear/atualizar um braço.

    Modelos usam apenas o que precisam:
    - LinUCB usa ``x`` (vetor de contexto).
    - Thompson ignora o contexto (context-free).
    - Baseline usa ``client``/``segments``/``arm_categories`` (regras de negócio).
    """

    x: np.ndarray
    client: dict[str, Any] = field(default_factory=dict)
    segments: list[str] = field(default_factory=list)
    arm_categories: list[str] = field(default_factory=list)


@dataclass
class RankedArm:
    arm_index: int
    score: float
    pred: float
    bonus: float
    #: Justificativa da posição, preenchida por cada modelo. Entra no `Decisao.reason_codes`
    #: do api_service — é o que permite auditar por que uma oferta foi servida (Etapa 5).
    reason_codes: list[str] = field(default_factory=list)


def explore_or_exploit(bonus: float, pred: float) -> str:
    """Rótulo de exploração: o bônus de incerteza domina a predição?"""
    return "explore" if bonus > abs(pred) else "exploit"


class BanditModel(ABC):
    """Interface comum dos modelos de bandit."""

    name: str = "base"

    @abstractmethod
    def rank(
        self,
        ctx: BanditContext,
        eligible_mask: list[bool],
        exclude: tuple[int, ...] = (),
    ) -> list[RankedArm]:
        """Retorna os braços elegíveis ordenados por score decrescente."""

    @abstractmethod
    def update(self, arm_index: int, reward: float, ctx: BanditContext) -> None:
        """Aplica o feedback (reward) ao braço escolhido."""

    @abstractmethod
    def get_state(self) -> dict[str, Any]:
        """Estado serializável (JSON) do modelo — para Redis e MLflow."""

    @classmethod
    @abstractmethod
    def from_state(cls, state: dict[str, Any]) -> BanditModel:
        """Reconstrói o modelo a partir de um estado serializado."""
