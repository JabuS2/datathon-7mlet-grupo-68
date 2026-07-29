from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any

import numpy as np

logger = logging.getLogger(__name__)


class Catalog:
    """Carrega o offer_catalog.json e expõe metadados de braços, elegibilidade e
    estatísticas de normalização do contexto.

    A ordem de ``offers[]`` define o índice do braço (arm_index).
    """

    def __init__(self, catalog_path: str, clients_csv_path: str | None = None):
        data = json.loads(Path(catalog_path).read_text(encoding="utf-8"))
        self.metadata: dict[str, Any] = data["catalog_metadata"]
        self.offers: list[dict[str, Any]] = data["offers"]

        self.arm_ids: list[str] = [o["arm_id"] for o in self.offers]
        self.categories: list[str] = [o["category"] for o in self.offers]
        self.ctx_cols: list[str] = list(self.offers[0]["context_features"])
        self.exploration: list[float] = [
            float(o["ucb_params"]["exploration_factor"]) for o in self.offers
        ]
        self._index: dict[str, int] = {aid: i for i, aid in enumerate(self.arm_ids)}

        self._mu, self._sd, self._income_sorted = self._compute_stats(clients_csv_path)

    @property
    def n_arms(self) -> int:
        return len(self.offers)

    def index_of(self, arm_id: str) -> int | None:
        return self._index.get(arm_id)

    def offer(self, arm_index: int) -> dict[str, Any]:
        return self.offers[arm_index]

    def context_stats(self) -> tuple[list[float], list[float]]:
        return self._mu.tolist(), self._sd.tolist()

    # ------------------------------------------------------------------ stats
    def _compute_stats(
        self, clients_csv_path: str | None
    ) -> tuple[np.ndarray, np.ndarray, np.ndarray | None]:
        n = len(self.ctx_cols)
        if not clients_csv_path or not Path(clients_csv_path).exists():
            logger.warning(
                "golden_clients.csv não encontrado (%s); usando normalização identidade "
                "(mu=0, sd=1) e percentil de renda default=50.",
                clients_csv_path,
            )
            return np.zeros(n), np.ones(n), None
        try:
            import pandas as pd

            df = pd.read_csv(clients_csv_path)
            mu = df[self.ctx_cols].astype(float).mean().to_numpy()
            sd = df[self.ctx_cols].astype(float).std().to_numpy()
            sd = np.where(sd == 0.0, 1.0, sd)
            income = np.sort(df["renda_estimada_anual_brl"].astype(float).to_numpy())
            return mu, sd, income
        except Exception:  # noqa: BLE001 - degrada com log, não derruba o serviço
            logger.exception("Falha ao computar stats do golden_clients.csv; usando defaults.")
            return np.zeros(n), np.ones(n), None

    def income_percentile(self, income: float) -> float:
        if self._income_sorted is None or self._income_sorted.size == 0:
            return 50.0
        pos = int(np.searchsorted(self._income_sorted, float(income), side="right"))
        return pos / self._income_sorted.size * 100.0

    # ------------------------------------------------------------ eligibility
    def is_eligible(self, client: dict[str, Any], filters: dict[str, Any]) -> bool:
        """Aplica os santander_filters de um braço a um cliente.

        Convenções de sufixo (catalog_metadata.filter_conventions):
        ``_atual`` (posse binária), ``_percentil_min`` (percentil de renda),
        ``_min``/``_max`` (piso/teto numérico), sem sufixo (igualdade).
        """
        for key, val in filters.items():
            if key.endswith("_atual"):
                if (client.get(key[:-6], 0) or 0) != val:
                    return False
            elif key.endswith("_percentil_min"):
                if client.get("_renda_pct", 0) < val:
                    return False
            elif key.endswith("_min"):
                if (client.get(key[:-4], 0) or 0) < val:
                    return False
            elif key.endswith("_max"):
                if (client.get(key[:-4], 1e18) or 1e18) > val:
                    return False
            elif client.get(key) != val:
                return False
        return True

    def eligibility_mask(self, client: dict[str, Any]) -> list[bool]:
        """Máscara de elegibilidade sobre todos os braços.

        Injeta ``_renda_pct`` derivado de ``renda_estimada_anual_brl`` se ausente.
        """
        enriched = dict(client)
        if "_renda_pct" not in enriched and "renda_estimada_anual_brl" in enriched:
            enriched["_renda_pct"] = self.income_percentile(
                enriched["renda_estimada_anual_brl"]
            )
        return [
            self.is_eligible(enriched, o["eligible_segment"]["santander_filters"])
            for o in self.offers
        ]
