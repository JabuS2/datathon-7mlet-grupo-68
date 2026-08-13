from __future__ import annotations

from typing import Any

import numpy as np

# Segmentos sintéticos usados como one-hots no vetor de contexto.
# Origem: notebooks/simulacao_portal_linucb.ipynb (cell ebd300ff).
SEG_KEYS: list[str] = [
    "SEG-JOVEM",
    "SEG-SENIOR",
    "SEG-ALTA-RENDA",
    "SEG-VIP",
    "SEG-CREDITO-ATIVO",
    "SEG-INVESTIDOR-EXPERIENTE",
    "SEG-PERFIL-FAMILIAR",
    "SEG-POUPADOR",
    "SEG-CONTRIBUINTE-IR",
    "SEG-INVESTIDOR-INICIANTE",
    "SEG-SEM-CARTAO",
    "SEG-PROPRIETARIO",
]


class ContextBuilder:
    """Constrói o vetor de contexto do LinUCB.

    Dimensão = 1 (bias) + len(ctx_cols) numéricos z-standardizados + len(seg_keys) one-hots.
    Com os 9 ``context_features`` do catálogo e 12 segmentos => D = 22.

    IMPORTANTE: ``mu``/``sd`` (estatísticas de normalização) fazem parte do estado do
    modelo e DEVEM ser persistidas — sem elas o scoring em serving fica silenciosamente
    errado (ver notebooks/simulacao_portal_linucb.ipynb, cell 64f7822a).
    """

    def __init__(
        self,
        ctx_cols: list[str],
        mu: list[float],
        sd: list[float],
        seg_keys: list[str] | None = None,
    ):
        self.ctx_cols = list(ctx_cols)
        self.seg_keys = list(seg_keys) if seg_keys is not None else list(SEG_KEYS)
        self.mu = np.asarray(mu, dtype=float)
        self.sd = np.asarray(sd, dtype=float)
        # guarda contra desvio-padrão zero (colunas binárias constantes na amostra)
        self.sd = np.where(self.sd == 0.0, 1.0, self.sd)

    @property
    def dim(self) -> int:
        return 1 + len(self.ctx_cols) + len(self.seg_keys)

    def build(self, client: dict[str, Any], segments: list[str]) -> np.ndarray:
        num = np.array([float(client.get(c, 0.0) or 0.0) for c in self.ctx_cols], dtype=float)
        num = (num - self.mu) / self.sd
        seg = np.array([1.0 if k in segments else 0.0 for k in self.seg_keys], dtype=float)
        return np.concatenate([[1.0], num, seg])

    def to_state(self) -> dict[str, Any]:
        return {
            "ctx_cols": self.ctx_cols,
            "seg_keys": self.seg_keys,
            "mu": self.mu.tolist(),
            "sd": self.sd.tolist(),
        }

    @classmethod
    def from_state(cls, state: dict[str, Any]) -> ContextBuilder:
        return cls(
            ctx_cols=state["ctx_cols"],
            mu=state["mu"],
            sd=state["sd"],
            seg_keys=state.get("seg_keys"),
        )
