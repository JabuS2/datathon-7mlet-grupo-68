"""E7 — endpoints de serving: /decide, /showcase, /feedback, /reward + log auditável.

Usa o harness de integração (conftest): Postgres migrado + `client` httpx. Semeia catálogo,
políticas e um subset de clientes antes de exercitar o fluxo ponta a ponta.
"""

import pytest
import pytest_asyncio
from sqlalchemy import func, select

from db.unit_of_work import UnitOfWork
from models.cliente import Cliente
from models.decisao import Decisao
from models.recompensa import Recompensa
from services.seed.seeder import seed_all
from settings import settings


@pytest_asyncio.fixture
async def cod_cliente(session_factory) -> int:
    """Semeia catálogo + políticas + 40 clientes (committed) e devolve um cliente ativo."""
    async with session_factory() as s, UnitOfWork(s) as uow:
        await seed_all(uow, settings.DATA_DIR, client_limit=40)
    async with session_factory() as s:
        cod: int = await s.scalar(select(Cliente.cod_cliente).where(Cliente.ind_ativo).limit(1))
        return cod


@pytest.mark.asyncio
async def test_decide_persists_auditable_decision(client, cod_cliente, session_factory):
    resp = await client.post("/decide", json={"codCliente": cod_cliente, "channel": "app"})
    assert resp.status_code == 200
    body = resp.json()
    assert body["armId"].startswith("OFF-")
    assert body["policyVersion"] == "linucb-v1"
    assert body["reasonCodes"]  # justificativa presente (Etapa 5)
    assert "decisionId" in body

    async with session_factory() as s:
        n = await s.scalar(select(func.count()).select_from(Decisao))
    assert n == 1  # decisão registrada no log auditável


@pytest.mark.asyncio
async def test_full_loop_decide_feedback_reward(client, cod_cliente, session_factory):
    decided = (
        await client.post("/decide", json={"codCliente": cod_cliente, "channel": "app"})
    ).json()
    did = decided["decisionId"]

    fb = await client.post("/feedback", json={"decisionId": did, "type": "click"})
    assert fb.status_code == 200
    assert fb.json()["type"] == "click"

    rw = await client.post("/reward", json={"decisionId": did, "converted": True})
    assert rw.status_code == 200
    assert rw.json()["status"] == "observed"
    assert rw.json()["value"] > 0  # reward composto realimentou o bandit

    async with session_factory() as s:
        n_reward = await s.scalar(select(func.count()).select_from(Recompensa))
    assert n_reward == 1


@pytest.mark.asyncio
async def test_showcase_returns_ranked_offers(client, cod_cliente):
    resp = await client.post("/showcase", json={"codCliente": cod_cliente, "topK": 3})
    assert resp.status_code == 200
    items = resp.json()["items"]
    assert 1 <= len(items) <= 3
    assert [it["rank"] for it in items] == sorted(it["rank"] for it in items)


@pytest.mark.asyncio
async def test_decide_unknown_client_returns_404(client, cod_cliente):
    resp = await client.post("/decide", json={"codCliente": 999_999_999, "channel": "app"})
    assert resp.status_code == 404
    assert resp.json()["code"] == "CLIENT_NOT_FOUND"
