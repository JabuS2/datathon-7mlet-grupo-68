"""Estado aprendido de um braço (espelha a tabela `estado_braco`), desacoplado do ORM.

Colunas polimórficas por algoritmo:
  - thompson: `alpha`, `beta`
  - ucb:      `n_pulls`, `sum_reward`
  - linucb:   `A` (d×d) e `b` (d), serializados como listas para persistir em JSONB
"""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class ArmState:
    arm_id: str
    alpha: float = 1.0
    beta: float = 1.0
    n_pulls: int = 0
    sum_reward: float = 0.0
    A: list[list[float]] | None = None  # matriz de design do LinUCB
    b: list[float] | None = None  # vetor do LinUCB

    # Campos extras carregados do catálogo (não persistidos aqui)
    exploration_factor: float = 1.5
    expected_revenue_brl: float = 0.0

    def with_catalog(self, exploration_factor: float, expected_revenue_brl: float) -> ArmState:
        self.exploration_factor = exploration_factor
        self.expected_revenue_brl = expected_revenue_brl
        return self


@dataclass
class RankedArm:
    """Item ranqueado devolvido por uma política."""

    arm_id: str
    score: float
    reason_codes: list[str] = field(default_factory=list)
    pred: float = 0.0
    bonus: float = 0.0
