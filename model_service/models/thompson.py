from __future__ import annotations

from typing import Any

import numpy as np

from models.base import BanditContext, BanditModel, RankedArm


class ThompsonSampling(BanditModel):
    """Thompson Sampling com prior Beta(1,1) (crença neutra), context-free.

    Refatorado de notebooks/mab_exploracao_algoritmos.ipynb (cell 4572d5b9).

    Como o reward já é o click (0/1), a atualização Beta é direta: sucesso incrementa
    ``alpha``, falha incrementa ``beta`` (sem a Bernoulli-ização do notebook, que só
    existia para reward contínuo).
    """

    name = "thompson"

    def __init__(self, n_arms: int):
        self.n_arms = n_arms
        self.alpha = np.ones(n_arms)
        self.beta = np.ones(n_arms)

    def rank(
        self,
        ctx: BanditContext,
        eligible_mask: list[bool],
        exclude: tuple[int, ...] = (),
    ) -> list[RankedArm]:
        samples = np.random.beta(self.alpha, self.beta)
        rows: list[RankedArm] = []
        for j in range(self.n_arms):
            if not eligible_mask[j] or j in exclude:
                continue
            mean = float(self.alpha[j] / (self.alpha[j] + self.beta[j]))
            sample = float(samples[j])
            rows.append(RankedArm(j, sample, mean, sample - mean))
        return sorted(rows, key=lambda r: -r.score)

    def update(self, arm_index: int, reward: float, ctx: BanditContext) -> None:
        if reward >= 1:
            self.alpha[arm_index] += 1
        else:
            self.beta[arm_index] += 1

    def get_state(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "n_arms": self.n_arms,
            "alpha": self.alpha.tolist(),
            "beta": self.beta.tolist(),
        }

    @classmethod
    def from_state(cls, state: dict[str, Any]) -> ThompsonSampling:
        model = cls(n_arms=state["n_arms"])
        model.alpha = np.array(state["alpha"], dtype=float)
        model.beta = np.array(state["beta"], dtype=float)
        return model
