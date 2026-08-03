"""Elegibilidade de ofertas — porte direto de `is_eligible` do notebook.

`santander_filters` usa convenções de sufixo (ver `offer_catalog.json.filter_conventions`):
  - `_atual`          → valor ATUAL da coluna de produto do cliente deve ser igual ao filtro
  - `_percentil_min`  → percentil de renda do cliente deve ser ≥ filtro
  - `_min` / `_max`   → limites (idade, tempo de relacionamento…)
  - sem sufixo        → igualdade direta (ex.: `ind_ativo: 1`)
"""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

_BIG = 1e18


def is_eligible(client: Mapping[str, Any], filters: Mapping[str, Any], renda_pct: float) -> bool:
    """True se o cliente atende a todos os filtros de elegibilidade da oferta.

    `renda_pct` é o percentil (0–100) da renda do cliente na distribuição de referência.
    """
    for key, val in filters.items():
        if key.endswith("_atual"):
            if _num(client.get(key[:-6], 0)) != val:
                return False
        elif key.endswith("_percentil_min"):
            if renda_pct < val:
                return False
        elif key.endswith("_min"):
            if _num(client.get(key[:-4], 0)) < val:
                return False
        elif key.endswith("_max"):
            if _num(client.get(key[:-4], _BIG)) > val:
                return False
        elif _num(client.get(key)) != val:
            return False
    return True


def eligible_arm_ids(
    client: Mapping[str, Any],
    offers: list[Mapping[str, Any]],
    renda_pct: float,
) -> list[str]:
    """arm_ids elegíveis para o cliente (offers no formato do `offer_catalog.json`)."""
    out = []
    for offer in offers:
        filters = offer.get("eligible_segment", {}).get("santander_filters", {})
        if is_eligible(client, filters, renda_pct):
            out.append(offer["arm_id"])
    return out


def _num(value: Any) -> float:
    """Converte flags/booleanos/strings numéricas para float (True→1.0, None→0.0)."""
    if value is None:
        return 0.0
    if isinstance(value, bool):
        return 1.0 if value else 0.0
    try:
        return float(value)
    except (TypeError, ValueError):
        return 0.0
