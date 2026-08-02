"""Runtime do bandit em cache: catálogo (arquivo) + estatísticas de referência ajustadas 1×.

A definição estática dos braços e o `reward_definition` vêm do `offer_catalog.json` (fonte de
verdade), e as estatísticas de contexto (média/desvio, distribuição de renda) são ajustadas do
`golden_clients.csv` — igual ao treino do notebook. Só o **estado aprendido** e o **cliente** vêm
do banco em cada requisição. Ajustado uma vez e memoizado (`lru_cache`).
"""

from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from typing import Any

from services.bandit.context import ReferenceStats
from services.bandit.engine import BanditEngine
from services.catalog.loaders import iter_seed_clients, load_offer_catalog
from settings import settings


@dataclass
class BanditRuntime:
    engine: BanditEngine
    stats: ReferenceStats
    offers_by_id: dict[str, dict[str, Any]]
    reward_definition: dict[str, Any]


@lru_cache(maxsize=1)
def get_runtime() -> BanditRuntime:
    golden = Path(settings.DATA_DIR) / "golden_set"
    reward_definition, offers = load_offer_catalog(golden / "offer_catalog.json")
    clients = list(iter_seed_clients(golden / "golden_clients.csv"))
    ctx_cols = offers[0]["context_features"]
    stats = ReferenceStats.fit(clients, ctx_cols)
    engine = BanditEngine(offers, stats, reward_definition)
    return BanditRuntime(
        engine=engine,
        stats=stats,
        offers_by_id={o["arm_id"]: o for o in offers},
        reward_definition=reward_definition,
    )
