"""Verifica o BanditService contra o StateStore REAL (Redis) usando fakeredis.

Exercita o round-trip JSON do estado pelo Redis e o lock (self.redis.lock(...)
como async context manager) com decode_responses=True — o caminho de concorrência
do item 6 que o FakeStore em test_service.py não cobre.
"""

from __future__ import annotations

import asyncio
from pathlib import Path

import pytest

pytest.importorskip("fakeredis", reason="fakeredis[lua] não instalado")
import fakeredis.aioredis  # noqa: E402

from catalog import Catalog  # noqa: E402
from service import BanditService  # noqa: E402
from service.policy_resolver import auto_policy  # noqa: E402
from store import StateStore  # noqa: E402

AUTO_LINUCB = auto_policy("linucb").policy_id

_REPO_ROOT = Path(__file__).resolve().parents[2]
CATALOG = str(_REPO_ROOT / "data" / "golden_set" / "offer_catalog.json")
CLIENTS = str(_REPO_ROOT / "data" / "golden_set" / "golden_clients.csv")

pytestmark = pytest.mark.skipif(
    not Path(CATALOG).exists(), reason="offer_catalog.json não encontrado"
)

CLIENT = {
    "idade": 24,
    "renda_estimada_anual_brl": 45000,
    "tempo_relacionamento_meses": 10,
    "ind_ativo": 1,
    "possui_conta_corrente": 1,
    "possui_cartao_credito": 0,
    "possui_conta_investimento": 0,
    "possui_fundo_investimento": 0,
    "possui_financiamento_imovel": 0,
    "segmento": "02 - VAREJO",
}
SEGMENTS = ["SEG-JOVEM", "SEG-SEM-CARTAO"]


@pytest.fixture
def service():
    redis = fakeredis.aioredis.FakeRedis(decode_responses=True)
    store = StateStore(redis)
    catalog = Catalog(CATALOG, CLIENTS if Path(CLIENTS).exists() else None)
    return BanditService(catalog, store, default_algorithm="linucb")


async def test_state_and_context_persist_through_real_store(service):
    before = await service.rank("linucb", CLIENT, SEGMENTS)
    assert await service.store.load_state(AUTO_LINUCB) is not None
    ctx = await service.store.load_context()
    assert ctx and "mu" in ctx and "sd" in ctx
    assert before["ranked"]


async def test_concurrent_updates_learn_through_real_lock(service):
    before = await service.rank("linucb", CLIENT, SEGMENTS)
    target = before["ranked"][-1]["arm_id"]
    pred_before = next(r["pred"] for r in before["ranked"] if r["arm_id"] == target)

    # updates concorrentes sob o lock real do Redis (fakeredis)
    await asyncio.gather(
        *[service.update("linucb", target, 1.0, CLIENT, SEGMENTS) for _ in range(30)]
    )

    after = await service.rank("linucb", CLIENT, SEGMENTS)
    pred_after = next(r["pred"] for r in after["ranked"] if r["arm_id"] == target)
    assert pred_after > pred_before

    state = await service.store.load_state(AUTO_LINUCB)
    idx = service.catalog.index_of(target)
    b_norm = sum(v * v for v in state["b"][idx]) ** 0.5
    assert b_norm > 0
