"""Vetor de contexto do LinUCB — porte de `context_vec` do notebook.

x = [1.0 (bias)] ++ [features numéricas padronizadas (z-score)] ++ [one-hot dos segmentos].
As estatísticas de referência (média/desvio das numéricas e distribuição de renda para o
percentil de elegibilidade) são ajustadas uma vez sobre o seed e reutilizadas em cada decisão.
"""

from __future__ import annotations

import bisect
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from typing import Any

import numpy as np

# Segmentos que viram one-hot no contexto (ordem fixa = ordem das colunas do vetor).
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


def _num(value: Any) -> float:
    if value is None:
        return 0.0
    if isinstance(value, bool):
        return 1.0 if value else 0.0
    try:
        return float(value)
    except (TypeError, ValueError):
        return 0.0


@dataclass
class ReferenceStats:
    """Estatísticas de referência para padronizar o contexto e calcular o percentil de renda."""

    ctx_cols: list[str]
    mu: dict[str, float]
    sd: dict[str, float]
    renda_sorted: list[float]
    seg_keys: list[str]

    @classmethod
    def fit(
        cls,
        clients: Sequence[Mapping[str, Any]],
        ctx_cols: list[str],
        seg_keys: list[str] | None = None,
        renda_col: str = "renda_estimada_anual_brl",
    ) -> ReferenceStats:
        seg_keys = seg_keys or list(SEG_KEYS)
        mu: dict[str, float] = {}
        sd: dict[str, float] = {}
        for col in ctx_cols:
            vals = np.array([_num(c.get(col)) for c in clients], dtype=float)
            mu[col] = float(vals.mean()) if len(vals) else 0.0
            std = float(vals.std(ddof=1)) if len(vals) > 1 else 0.0
            sd[col] = std if std > 1e-9 else 1.0  # evita divisão por zero
        renda = sorted(_num(c.get(renda_col)) for c in clients if c.get(renda_col) is not None)
        return cls(ctx_cols=list(ctx_cols), mu=mu, sd=sd, renda_sorted=renda, seg_keys=seg_keys)

    @property
    def dimension(self) -> int:
        return 1 + len(self.ctx_cols) + len(self.seg_keys)

    def renda_percentile(self, renda: float | None) -> float:
        """Percentil (0–100) da renda na distribuição de referência."""
        if renda is None or not self.renda_sorted:
            return 0.0
        pos = bisect.bisect_right(self.renda_sorted, _num(renda))
        return 100.0 * pos / len(self.renda_sorted)

    def context_vector(self, client: Mapping[str, Any]) -> np.ndarray:
        """Vetor x do cliente: bias + numéricas padronizadas + one-hot de segmentos."""
        num = np.array(
            [(_num(client.get(col)) - self.mu[col]) / self.sd[col] for col in self.ctx_cols],
            dtype=float,
        )
        segs = _client_segments(client)
        seg = np.array([1.0 if k in segs else 0.0 for k in self.seg_keys], dtype=float)
        return np.concatenate([[1.0], num, seg])


def _client_segments(client: Mapping[str, Any]) -> set[str]:
    """Extrai os segmentos sintéticos do cliente (aceita list já parseada ou string JSON)."""
    raw = client.get("segmentos_sinteticos")
    if isinstance(raw, (list, set, tuple)):
        return {str(x) for x in raw}
    if isinstance(raw, str) and raw.strip():
        import json

        try:
            parsed = json.loads(raw)
        except ValueError:
            try:
                import ast

                parsed = ast.literal_eval(raw)
            except (ValueError, SyntaxError):
                return set()
        return {str(x) for x in parsed} if isinstance(parsed, (list, set, tuple)) else set()
    return set()
