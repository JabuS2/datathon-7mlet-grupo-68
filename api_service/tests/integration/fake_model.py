"""Fake do model_service para os testes de integração do api_service.

O bandit deixou de rodar em processo: `/decide`, `/showcase` e `/me/*` dependem do `/rank`
e do `/update` por HTTP. Este fake respeita o contrato — inclusive `policy_id`,
`reason_codes` e o bloco `audit` — para que os testes continuem provando o que o log
auditável guarda, sem subir o model_service.

Elegibilidade é simplificada de propósito: a real é do model_service e tem teste lá. Aqui
o que importa é que `/decide` persista a decisão certa com a justificativa certa.
"""

from __future__ import annotations

from typing import Any

#: Braços do `offer_catalog.json` usados nos cenários. Um deles fica fora dos elegíveis
#: para exercitar o 409 ARM_NOT_ELIGIBLE sem depender das regras reais do catálogo.
ELIGIBLE_ARMS = ["OFF-CR-001", "OFF-INV-004", "OFF-SEG-003"]
INELIGIBLE_ARM = "OFF-INV-005"

_CATEGORIES = {"OFF-CR-001": "credito", "OFF-INV-004": "investimento", "OFF-SEG-003": "seguro"}


class FakeModelClient:
    """Mesma superfície de `BanditClient`, com estado em memória."""

    def __init__(self, policy_id: str = "linucb-v1", algorithm: str = "linucb"):
        self.policy_id = policy_id
        self.algorithm = algorithm
        self.rewards: dict[str, float] = {}
        #: (arm_id, reward, policy_id) de cada `/update` — é o que prova que a recompensa
        #: atrasada foi aplicada na política que gerou a decisão, não na ativa de agora.
        self.updates: list[tuple[str, float, str | None]] = []

    def _ranked(self) -> list[dict[str, Any]]:
        ordered = sorted(ELIGIBLE_ARMS, key=lambda a: -self.rewards.get(a, 0.0))
        return [
            {
                "arm_id": arm,
                "rank": i,
                "score": 1.0 + self.rewards.get(arm, 0.0),
                "pred": self.rewards.get(arm, 0.0),
                "bonus": 0.5,
                "reason_codes": [
                    "policy:linucb",
                    "cold_start" if arm not in self.rewards else "exploit",
                ],
                "category": _CATEGORIES[arm],
                "product_name": f"Produto {arm}",
                "description": "Descrição de teste",
                "valor_total": 100.0,
                "desconto_pct": 10.0,
                "valor_final": 90.0,
            }
            for i, arm in enumerate(ordered, start=1)
        ]

    async def rank(
        self,
        algorithm: str | None,
        client: dict[str, Any],
        segments: list[str],
        top: int | None = None,
        exclude_arm_ids: list[str] | None = None,
        policy_id: str | None = None,
    ) -> dict[str, Any]:
        ranked = self._ranked()
        if exclude_arm_ids:
            ranked = [r for r in ranked if r["arm_id"] not in exclude_arm_ids]
        audit = {
            "features_numericas": {
                "idade": float(client.get("idade") or 0),
                # renda entra na decisão de forma legítima e por isso é monitorada, não excluída
                "renda_estimada_anual_brl": float(client.get("renda_estimada_anual_brl") or 0),
            },
            "segmentos_sinteticos": sorted(segments),
            "renda_percentil": 50.0,
            # ignora o recorte de `top`, como o serviço real
            "ofertas_elegiveis": sorted(ELIGIBLE_ARMS),
            "atributos_excluidos": ["sexo"],
            "atributos_monitorados": ["renda_estimada_anual_brl"],
        }
        if top is not None:
            ranked = ranked[:top]
        return {
            "algorithm": algorithm or self.algorithm,
            "policy_id": policy_id or self.policy_id,
            "ranked": ranked,
            "audit": audit,
        }

    async def update(
        self,
        algorithm: str | None,
        arm_id: str,
        reward: float,
        client: dict[str, Any],
        segments: list[str],
        policy_id: str | None = None,
    ) -> dict[str, Any]:
        self.updates.append((arm_id, reward, policy_id))
        if reward >= 1:
            self.rewards[arm_id] = self.rewards.get(arm_id, 0.0) + 1.0
        return {
            "algorithm": algorithm or self.algorithm,
            "policy_id": policy_id or self.policy_id,
            "arm_id": arm_id,
            "status": "updated",
        }
