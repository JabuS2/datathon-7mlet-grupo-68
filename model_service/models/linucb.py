from __future__ import annotations

from typing import Any

import numpy as np

from models.base import BanditContext, BanditModel, RankedArm, explore_or_exploit


class LinUCB(BanditModel):
    """LinUCB contextual (disjoint), versão de produção com Sherman-Morrison.

    Refatorado de notebooks/simulacao_portal_linucb.ipynb (cell f8c9b882).

    Estado por braço ``j``:
    - ``A_inv[j]`` = inversa da matriz de Gram ridge ``A_j = lam*I + Σ x xᵀ`` (guardada
      já invertida; init ``I/lam``).
    - ``b[j]`` = ``Σ reward*x``.

    Score UCB = ``θⱼ·x + αⱼ·√(xᵀ A_inv x)`` com ``θⱼ = A_inv·b`` e
    ``αⱼ = exploration_factor * scale`` (scale=0.2 conforme o catálogo).

    É um modelo GLOBAL contextual: parâmetros por braço, contexto do usuário no
    momento do scoring. Não há modelo por usuário.
    """

    name = "linucb"

    def __init__(
        self,
        n_arms: int,
        d: int,
        exploration: list[float],
        scale: float = 0.2,
        lam: float = 1.0,
    ):
        self.n_arms = n_arms
        self.d = d
        self.scale = scale
        self.lam = lam
        self.alpha = [float(e) * scale for e in exploration]
        self.A_inv = [np.eye(d) / lam for _ in range(n_arms)]
        self.b = [np.zeros(d) for _ in range(n_arms)]

    def _score(self, j: int, x: np.ndarray) -> tuple[float, float, float]:
        theta = self.A_inv[j] @ self.b[j]
        pred = float(theta @ x)
        bonus = float(self.alpha[j] * np.sqrt(max(x @ self.A_inv[j] @ x, 1e-9)))
        return pred + bonus, pred, bonus

    def rank(
        self,
        ctx: BanditContext,
        eligible_mask: list[bool],
        exclude: tuple[int, ...] = (),
    ) -> list[RankedArm]:
        x = ctx.x
        rows: list[RankedArm] = []
        for j in range(self.n_arms):
            if not eligible_mask[j] or j in exclude:
                continue
            s, pred, bonus = self._score(j, x)
            rows.append(RankedArm(j, s, pred, bonus, self._reasons(j, pred, bonus)))
        return sorted(rows, key=lambda r: -r.score)

    def _reasons(self, j: int, pred: float, bonus: float) -> list[str]:
        """Cold-start do LinUCB é `b[j]` ainda zerado: nenhum reward foi aplicado ao braço.

        (O estado do LinUCB não guarda contagem de pulls — `b` é o sinal disponível.)
        """
        if not self.b[j].any():
            return ["policy:linucb", "cold_start"]
        return ["policy:linucb", explore_or_exploit(bonus, pred)]

    def update(self, arm_index: int, reward: float, ctx: BanditContext) -> None:
        x = ctx.x
        j = arm_index
        Ax = self.A_inv[j] @ x
        self.A_inv[j] = self.A_inv[j] - np.outer(Ax, Ax) / (1.0 + x @ Ax)
        self.b[j] = self.b[j] + reward * x

    def get_state(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "n_arms": self.n_arms,
            "d": self.d,
            "scale": self.scale,
            "lam": self.lam,
            "alpha": list(self.alpha),
            "A_inv": [m.tolist() for m in self.A_inv],
            "b": [v.tolist() for v in self.b],
        }

    @classmethod
    def from_state(cls, state: dict[str, Any]) -> LinUCB:
        # exploration é reconstruído a partir de alpha/scale para preservar a assinatura
        scale = state["scale"]
        exploration = [a / scale for a in state["alpha"]]
        model = cls(
            n_arms=state["n_arms"],
            d=state["d"],
            exploration=exploration,
            scale=scale,
            lam=state["lam"],
        )
        model.A_inv = [np.array(m, dtype=float) for m in state["A_inv"]]
        model.b = [np.array(v, dtype=float) for v in state["b"]]
        return model
