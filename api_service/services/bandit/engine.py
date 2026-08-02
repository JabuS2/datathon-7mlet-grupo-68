"""Engine do bandit: junta elegibilidade + contexto + política numa decisão auditável.

Fluxo (o que o `/decide` chamará em E7):
  cliente → filtra ofertas elegíveis → monta vetor de contexto → política ranqueia → decisão.
O `context` devolvido é o registro auditável (LGPD): quais features entraram e quais foram
explicitamente excluídas.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
from typing import Any

import numpy as np

from services.bandit.context import ReferenceStats
from services.bandit.eligibility import eligible_arm_ids
from services.bandit.policies import Policy
from services.bandit.reward import composite_reward
from services.bandit.state import ArmState, RankedArm

# Atributos protegidos/sensíveis registrados como EXCLUÍDOS da decisão (auditoria LGPD).
PROTECTED_ATTRIBUTES = ["sexo"]


class ArmNotEligible(Exception):
    """Braço pedido explicitamente não está entre os elegíveis para o cliente."""

    def __init__(self, arm_id: str):
        self.arm_id = arm_id
        super().__init__(f"Braço {arm_id} não é elegível para este cliente")


@dataclass
class Decision:
    arm_id: str
    score: float
    reason_codes: list[str]
    context: dict[str, Any]
    ranked: list[RankedArm] = field(default_factory=list)


class BanditEngine:
    def __init__(
        self,
        offers: Sequence[Mapping[str, Any]],
        stats: ReferenceStats,
        reward_definition: Mapping[str, Any] | None = None,
    ):
        self.offers_list = list(offers)
        self.offers = {o["arm_id"]: o for o in offers}
        self.stats = stats
        self.reward_definition = dict(reward_definition or {})

    # ── serving ──────────────────────────────────────────────────
    def rank(
        self, client: Mapping[str, Any], policy: Policy, states: Sequence[ArmState]
    ) -> tuple[list[RankedArm], np.ndarray, dict]:
        """Ranqueia as ofertas elegíveis. Devolve (ranking, vetor de contexto, auditoria)."""
        renda_pct = self.stats.renda_percentile(client.get("renda_estimada_anual_brl"))
        eligible = set(eligible_arm_ids(client, self.offers_list, renda_pct))
        x = self.stats.context_vector(client)

        elig_states = [self._decorate(s) for s in states if s.arm_id in eligible]
        ranked = policy.rank(x, elig_states) if elig_states else []
        return ranked, x, self._audit_context(client, renda_pct, sorted(eligible))

    def decide(
        self,
        client: Mapping[str, Any],
        policy: Policy,
        states: Sequence[ArmState],
        arm_id: str | None = None,
    ) -> Decision | None:
        """Escolhe o braço a servir. `None` se nenhum braço é elegível.

        Sem `arm_id`, vence o topo do ranking — a decisão é da política. Com `arm_id`
        (vitrine clicável), serve o braço que o usuário escolheu, desde que elegível, e marca
        `user_selected` nos reason codes: o log precisa distinguir o que a política escolheu do
        que o usuário escolheu, senão a auditoria credita à política uma decisão que não foi dela.

        Levanta `ArmNotEligible` se o braço pedido não está no conjunto elegível.
        """
        ranked, _x, context = self.rank(client, policy, states)
        if not ranked:
            return None

        if arm_id is None:
            top = ranked[0]
            extra = []
        else:
            found = next((r for r in ranked if r.arm_id == arm_id), None)
            if found is None:
                raise ArmNotEligible(arm_id)
            top = found
            extra = ["user_selected"]

        reasons = [*top.reason_codes, f"eligible:{len(context['ofertas_elegiveis'])}", *extra]
        return Decision(
            arm_id=top.arm_id, score=top.score, reason_codes=reasons, context=context, ranked=ranked
        )

    # ── aprendizado ──────────────────────────────────────────────
    def reward_value(self, arm_id: str, click: float | int | bool) -> float:
        """Recompensa composta (receita+clique) do braço, para realimentar a política."""
        offer = self.offers.get(arm_id, {})
        return composite_reward(
            offer.get("expected_revenue_brl", 0.0), click, self.reward_definition
        )

    def update(
        self, client: Mapping[str, Any], policy: Policy, state: ArmState, click: float | int | bool
    ) -> float:
        """Aplica a recompensa observada ao estado do braço. Devolve o valor da recompensa."""
        reward = self.reward_value(state.arm_id, click)
        x = self.stats.context_vector(client)
        policy.update(self._decorate(state), reward, x)
        return reward

    # ── helpers ──────────────────────────────────────────────────
    def decorate(self, state: ArmState) -> ArmState:
        """Anexa dados do catálogo (fator de exploração, receita esperada) ao estado do braço."""
        return self._decorate(state)

    def _decorate(self, state: ArmState) -> ArmState:
        offer = self.offers.get(state.arm_id, {})
        return state.with_catalog(
            exploration_factor=float(offer.get("ucb_exploration_factor", 1.5)),
            expected_revenue_brl=float(offer.get("expected_revenue_brl", 0.0)),
        )

    def _audit_context(
        self, client: Mapping[str, Any], renda_pct: float, eligible: list[str]
    ) -> dict:
        return {
            "features_numericas": {c: _num(client.get(c)) for c in self.stats.ctx_cols},
            "segmentos_sinteticos": sorted(_segments(client)),
            "renda_percentil": round(renda_pct, 2),
            "ofertas_elegiveis": eligible,
            "atributos_excluidos": PROTECTED_ATTRIBUTES,
        }


def _num(value: Any) -> float:
    if isinstance(value, bool):
        return 1.0 if value else 0.0
    try:
        return float(value) if value is not None else 0.0
    except (TypeError, ValueError):
        return 0.0


def _segments(client: Mapping[str, Any]) -> set[str]:
    from services.bandit.context import _client_segments

    return _client_segments(client)
