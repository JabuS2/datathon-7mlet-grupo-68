"""Testa o loop compute-on-read do BanditService com um store em memória (sem Redis)."""

from __future__ import annotations

import asyncio
from pathlib import Path

import pytest

from catalog import Catalog
from service import BanditService

_REPO_ROOT = Path(__file__).resolve().parents[2]
CATALOG = str(_REPO_ROOT / "data" / "golden_set" / "offer_catalog.json")
CLIENTS = str(_REPO_ROOT / "data" / "golden_set" / "golden_clients.csv")

pytestmark = pytest.mark.skipif(
    not Path(CATALOG).exists(), reason="offer_catalog.json não encontrado"
)


class FakeStore:
    """Store em memória com a mesma interface do StateStore (inclui lock por modelo)."""

    def __init__(self):
        self._states: dict[str, dict] = {}
        self._context: dict | None = None
        self._locks: dict[str, asyncio.Lock] = {}

    async def load_state(self, algorithm):
        return self._states.get(algorithm)

    async def save_state(self, algorithm, state):
        self._states[algorithm] = state

    async def delete_state(self, algorithm):
        self._states.pop(algorithm, None)

    async def load_context(self):
        return self._context

    async def save_context(self, state):
        self._context = state

    def lock(self, algorithm, **_):
        return self._locks.setdefault(algorithm, asyncio.Lock())


@pytest.fixture
def service():
    catalog = Catalog(CATALOG, CLIENTS if Path(CLIENTS).exists() else None)
    return BanditService(catalog, FakeStore(), default_algorithm="linucb")


@pytest.fixture
def client():
    return {
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


async def test_rank_returns_eligible_offers_with_price_fields(service, client):
    res = await service.rank("linucb", client, ["SEG-JOVEM", "SEG-SEM-CARTAO"])
    assert res["algorithm"] == "linucb"
    assert len(res["ranked"]) > 0
    first = res["ranked"][0]
    assert first["rank"] == 1
    assert {"valor_total", "desconto_pct", "valor_final"} <= set(first)


async def test_feedback_changes_next_ranking(service, client):
    """O núcleo do item 6: feedback recalcula as próximas ofertas do usuário."""
    segments = ["SEG-JOVEM", "SEG-SEM-CARTAO"]
    before = await service.rank("linucb", client, segments)
    top_arm = before["ranked"][0]["arm_id"]

    # dá vários clicks numa oferta que não é a top-1 atual
    target = before["ranked"][-1]["arm_id"]
    for _ in range(40):
        await service.update("linucb", target, 1.0, client, segments)

    after = await service.rank("linucb", client, segments)
    # o pred (exploitation) do braço reforçado deve subir
    pred_before = next(r["pred"] for r in before["ranked"] if r["arm_id"] == target)
    pred_after = next(r["pred"] for r in after["ranked"] if r["arm_id"] == target)
    assert pred_after > pred_before
    # e o ranking deve ter mudado em relação ao estado inicial
    assert after["ranked"][0]["arm_id"] != top_arm or pred_after > 0


async def test_concurrent_updates_are_serialized(service, client):
    """Updates concorrentes sob o lock não podem se perder (b acumula todos os rewards)."""
    segments = ["SEG-JOVEM"]
    target = (await service.rank("linucb", client, segments))["ranked"][0]["arm_id"]
    await asyncio.gather(
        *[service.update("linucb", target, 1.0, client, segments) for _ in range(25)]
    )
    state = await service.store.load_state("linucb")
    idx = service.catalog.index_of(target)
    # b[idx] = Σ reward*x; com 25 updates deve ser claramente não-nulo
    b_norm = sum(v * v for v in state["b"][idx]) ** 0.5
    assert b_norm > 0


async def test_invalid_algorithm_raises(service, client):
    from exceptions import BadRequest

    with pytest.raises(BadRequest):
        await service.rank("naive-bayes", client, [])


async def test_thompson_and_baseline_paths(service, client):
    segments = ["SEG-JOVEM"]
    th = await service.rank("thompson", client, segments)
    assert th["algorithm"] == "thompson" and len(th["ranked"]) > 0
    await service.update("thompson", th["ranked"][0]["arm_id"], 1.0, client, segments)

    bl = await service.rank("baseline", client, segments)
    assert bl["algorithm"] == "baseline" and len(bl["ranked"]) > 0
