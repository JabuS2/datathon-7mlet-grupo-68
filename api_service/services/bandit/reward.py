"""Reward composto do catálogo (v2.0.0-prod).

    reward = alpha * (expected_revenue_brl / v_max) + beta * click

`click` vem do evento real de feedback (`/feedback`). O termo de receita é constante por braço; o
termo de clique é o sinal observado. Defaults do `offer_catalog.json.reward_definition`.
"""

from __future__ import annotations

from collections.abc import Mapping

DEFAULT_ALPHA = 0.6
DEFAULT_BETA = 0.4
DEFAULT_V_MAX = 7000.0


def composite_reward(
    expected_revenue_brl: float,
    click: float | int | bool,
    reward_definition: Mapping | None = None,
) -> float:
    """Recompensa composta em [0, ~1] usada para atualizar o bandit."""
    rd = reward_definition or {}
    alpha = float(rd.get("alpha", DEFAULT_ALPHA))
    beta = float(rd.get("beta", DEFAULT_BETA))
    v_max = float(rd.get("v_max", DEFAULT_V_MAX)) or DEFAULT_V_MAX
    revenue_term = min(expected_revenue_brl / v_max, 1.0)
    click_term = 1.0 if bool(click) else 0.0
    return alpha * revenue_term + beta * click_term
