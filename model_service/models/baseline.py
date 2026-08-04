from __future__ import annotations

from typing import Any

from models.base import BanditContext, BanditModel, RankedArm


class DeterministicBaseline(BanditModel):
    """Baseline determinístico por regras de negócio (segmento/renda → categoria).

    Refatorado de notebooks/mab_exploracao_algoritmos.ipynb (cell 39002e73). No notebook
    a regra retorna uma categoria; aqui ranqueamos os braços elegíveis colocando a
    categoria-alvo primeiro (mantendo a ordem do catálogo dentro de cada grupo).

    ``update`` é no-op — o baseline não aprende.
    """

    name = "baseline"

    def __init__(self, arm_categories: list[str]):
        self.arm_categories = list(arm_categories)

    @staticmethod
    def _target_category(client: dict[str, Any], segments: list[str]) -> str:
        renda = float(client.get("renda_estimada_anual_brl", 0.0) or 0.0)
        seg = client.get("segmento", "")
        if seg == "01 - ALTA RENDA" or "SEG-VIP" in segments:
            return "investimento"
        if "SEG-INVESTIDOR-EXPERIENTE" in segments:
            return "investimento"
        if "SEG-SENIOR" in segments or "SEG-PROPRIETARIO" in segments:
            return "seguro"
        if "SEG-CREDITO-ATIVO" in segments or "SEG-SEM-CARTAO" in segments:
            return "credito"
        if "SEG-JOVEM" in segments:
            return "credito"
        if "SEG-PERFIL-FAMILIAR" in segments:
            return "seguro"
        if renda > 80_000:
            return "investimento"
        return "credito"

    def rank(
        self,
        ctx: BanditContext,
        eligible_mask: list[bool],
        exclude: tuple[int, ...] = (),
    ) -> list[RankedArm]:
        target = self._target_category(ctx.client, ctx.segments)
        rows: list[RankedArm] = []
        for j in range(len(self.arm_categories)):
            if not eligible_mask[j] or j in exclude:
                continue
            score = 1.0 if self.arm_categories[j] == target else 0.0
            # determinístico: não explora, então não há explore/exploit a declarar
            reasons = ["policy:baseline", f"target_category:{target}"]
            rows.append(RankedArm(j, score, score, 0.0, reasons))
        # categoria-alvo primeiro; empate mantém a ordem do catálogo (arm_index crescente)
        return sorted(rows, key=lambda r: (-r.score, r.arm_index))

    def update(self, arm_index: int, reward: float, ctx: BanditContext) -> None:
        # determinístico: não aprende
        return

    def get_state(self) -> dict[str, Any]:
        return {"name": self.name, "arm_categories": self.arm_categories}

    @classmethod
    def from_state(cls, state: dict[str, Any]) -> DeterministicBaseline:
        return cls(arm_categories=state["arm_categories"])
