"""As três políticas de decisão. Operam sobre `ArmState` + vetor de contexto `x` (numpy).

Cada `rank` devolve `RankedArm` ordenados por score desc; cada `update` realimenta o estado do
braço com a recompensa observada. Todas atualizam `n_pulls`/`sum_reward` (bookkeeping comum).
"""

from __future__ import annotations

from abc import ABC, abstractmethod

import numpy as np

from enums.politica import AlgoritmoPolitica
from services.bandit.state import ArmState, RankedArm

_LAM = 1.0  # ridge do cold-start do LinUCB


class Policy(ABC):
    algorithm: AlgoritmoPolitica

    @abstractmethod
    def rank(self, x: np.ndarray, states: list[ArmState]) -> list[RankedArm]: ...

    @abstractmethod
    def update(self, state: ArmState, reward: float, x: np.ndarray) -> None: ...

    @staticmethod
    def _bookkeep(state: ArmState, reward: float) -> None:
        state.n_pulls += 1
        state.sum_reward += reward


class BaselinePolicy(Policy):
    """Controle determinístico: escolhe o braço elegível de maior receita esperada. Não aprende."""

    algorithm = AlgoritmoPolitica.BASELINE

    def rank(self, x: np.ndarray, states: list[ArmState]) -> list[RankedArm]:
        ranked = [
            RankedArm(
                arm_id=s.arm_id,
                score=s.expected_revenue_brl,
                pred=s.expected_revenue_brl,
                reason_codes=["policy:baseline", "best_expected_revenue"],
            )
            for s in states
        ]
        return sorted(ranked, key=lambda r: -r.score)

    def update(self, state: ArmState, reward: float, x: np.ndarray) -> None:
        self._bookkeep(state, reward)  # baseline não aprende, mas registra tráfego


class ThompsonPolicy(Policy):
    """Exploração bayesiana: amostra p ~ Beta(alpha, beta) por braço e escolhe o maior."""

    algorithm = AlgoritmoPolitica.THOMPSON

    def __init__(self, rng: np.random.Generator | None = None):
        self.rng = rng or np.random.default_rng()

    def rank(self, x: np.ndarray, states: list[ArmState]) -> list[RankedArm]:
        ranked = []
        for s in states:
            sample = float(self.rng.beta(s.alpha, s.beta))
            mean = s.alpha / (s.alpha + s.beta)
            reasons = ["policy:thompson", "cold_start" if s.n_pulls == 0 else "posterior"]
            ranked.append(
                RankedArm(
                    arm_id=s.arm_id,
                    score=sample,
                    pred=mean,
                    bonus=sample - mean,
                    reason_codes=reasons,
                )
            )
        return sorted(ranked, key=lambda r: -r.score)

    def update(self, state: ArmState, reward: float, x: np.ndarray) -> None:
        r = min(max(reward, 0.0), 1.0)  # Beta espera reward em [0,1]
        state.alpha += r
        state.beta += 1.0 - r
        self._bookkeep(state, reward)


class LinUCBPolicy(Policy):
    """LinUCB contextual (porte do notebook): score = θᵀx + α·sqrt(xᵀA⁻¹x), θ = A⁻¹b.

    Persiste A (matriz de design, cold-start = λ·I) e b; α = fator de exploração · `scale` (0.2).
    """

    algorithm = AlgoritmoPolitica.LINUCB

    def __init__(self, dimension: int, scale: float = 0.2, lam: float = _LAM):
        self.d = dimension
        self.scale = scale
        self.lam = lam

    def _AB(self, state: ArmState) -> tuple[np.ndarray, np.ndarray]:
        A = np.array(state.A, dtype=float) if state.A is not None else np.eye(self.d) * self.lam
        b = np.array(state.b, dtype=float) if state.b is not None else np.zeros(self.d)
        return A, b

    def rank(self, x: np.ndarray, states: list[ArmState]) -> list[RankedArm]:
        ranked = []
        for s in states:
            A, b = self._AB(s)
            A_inv = np.linalg.inv(A)
            theta = A_inv @ b
            pred = float(theta @ x)
            alpha = s.exploration_factor * self.scale
            bonus = alpha * float(np.sqrt(max(x @ A_inv @ x, 1e-9)))
            reasons = [
                "policy:linucb",
                "cold_start" if s.n_pulls == 0 else _explore_or_exploit(bonus, pred),
            ]
            ranked.append(
                RankedArm(
                    arm_id=s.arm_id,
                    score=pred + bonus,
                    pred=pred,
                    bonus=bonus,
                    reason_codes=reasons,
                )
            )
        return sorted(ranked, key=lambda r: -r.score)

    def update(self, state: ArmState, reward: float, x: np.ndarray) -> None:
        A, b = self._AB(state)
        A = A + np.outer(x, x)
        b = b + reward * x
        state.A = A.tolist()
        state.b = b.tolist()
        self._bookkeep(state, reward)


def _explore_or_exploit(bonus: float, pred: float) -> str:
    return "explore" if bonus > abs(pred) else "exploit"


def build_policy(
    algorithm: AlgoritmoPolitica,
    *,
    dimension: int,
    hyperparams: dict | None = None,
    rng: np.random.Generator | None = None,
) -> Policy:
    """Fábrica: instancia a política a partir do algoritmo + hiperparâmetros da `politica`."""
    hyperparams = hyperparams or {}
    if algorithm == AlgoritmoPolitica.BASELINE:
        return BaselinePolicy()
    if algorithm == AlgoritmoPolitica.THOMPSON:
        return ThompsonPolicy(rng=rng)
    if algorithm == AlgoritmoPolitica.LINUCB:
        return LinUCBPolicy(dimension=dimension, scale=float(hyperparams.get("alpha_scale", 0.2)))
    raise ValueError(f"Algoritmo não suportado: {algorithm}")
