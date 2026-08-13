"""Contexto auditável de uma decisão (Etapa 5 / LGPD).

Migrado de `api_service/services/bandit/engine.py`. Quem ranqueia é este serviço, então é
aqui que dá para declarar honestamente o que entrou na decisão — o api_service só persiste
o bloco em `Decisao.context`.

A distinção entre **excluído** e **monitorado** é o ponto: dizer que renda é "excluída"
seria falso (ela compõe o contexto e governa a elegibilidade), e omiti-la esconderia um uso
sensível. Declarar as duas categorias é o que sustenta a análise de fairness.
"""

from __future__ import annotations

from typing import Any

# Atributos PROTEGIDOS: nunca entram na decisão, em nenhuma forma.
# O api_service já os remove de `Cliente.to_context()` antes de enviar — a declaração aqui
# é o registro de que a exclusão é deliberada, não acidente de serialização.
PROTECTED_ATTRIBUTES = ["sexo"]

# Atributos SENSÍVEIS que entram legitimamente na decisão e por isso são monitorados.
# Renda não é atributo protegido: além de compor o contexto, ela governa a elegibilidade
# (`renda_percentil_min` nos filtros do catálogo), e avaliar capacidade financeira é
# exigência de suitability. Registrá-la aqui deixa explícito no log que é uso consciente e
# fiscalizável — a checagem de fairness sobre ela é de *exposição por faixa de renda*, não
# de exclusão.
MONITORED_ATTRIBUTES = ["renda_estimada_anual_brl"]

_SEG_FIELD = "segmentos_sinteticos"


def _num(value: Any) -> float:
    if isinstance(value, bool):
        return 1.0 if value else 0.0
    try:
        return float(value) if value is not None else 0.0
    except (TypeError, ValueError):
        return 0.0


def build_audit(
    client: dict[str, Any],
    segments: list[str],
    ctx_cols: list[str],
    renda_percentil: float,
    eligible_arm_ids: list[str],
) -> dict[str, Any]:
    """Bloco auditável que acompanha o ranking."""
    return {
        "features_numericas": {c: _num(client.get(c)) for c in ctx_cols},
        "segmentos_sinteticos": sorted(segments or client.get(_SEG_FIELD) or []),
        "renda_percentil": round(renda_percentil, 2),
        "ofertas_elegiveis": sorted(eligible_arm_ids),
        "atributos_excluidos": list(PROTECTED_ATTRIBUTES),
        "atributos_monitorados": list(MONITORED_ATTRIBUTES),
    }


def strip_protected(client: dict[str, Any]) -> dict[str, Any]:
    """Descarta atributos protegidos que tenham chegado mesmo assim (defesa em profundidade)."""
    return {k: v for k, v in client.items() if k not in PROTECTED_ATTRIBUTES}
