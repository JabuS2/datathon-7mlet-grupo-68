"""E7 — endpoints de serving: /decide, /showcase, /reward + log auditável.

`POST /feedback` foi descontinuado aqui (o caminho agora é do fluxo novo via model_service);
o registro de `EventoImpressao(click)` segue coberto por `/me/feedback` em test_account.py.

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
async def test_decide_persists_auditable_decision(
    client, mock_model_service, cod_cliente, session_factory
):
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
async def test_full_loop_decide_reward(client, mock_model_service, cod_cliente, session_factory):
    decided = (
        await client.post("/decide", json={"codCliente": cod_cliente, "channel": "app"})
    ).json()
    did = decided["decisionId"]

    rw = await client.post("/reward", json={"decisionId": did, "converted": True})
    assert rw.status_code == 200
    assert rw.json()["status"] == "observed"
    assert rw.json()["value"] > 0  # reward composto realimentou o bandit

    async with session_factory() as s:
        n_reward = await s.scalar(select(func.count()).select_from(Recompensa))
    assert n_reward == 1


@pytest.mark.asyncio
async def test_showcase_returns_ranked_offers(client, mock_model_service, cod_cliente):
    resp = await client.post("/showcase", json={"codCliente": cod_cliente, "topK": 3})
    assert resp.status_code == 200
    items = resp.json()["items"]
    assert 1 <= len(items) <= 3
    assert [it["rank"] for it in items] == sorted(it["rank"] for it in items)


@pytest.mark.asyncio
async def test_reward_is_binary(client, mock_model_service, cod_cliente):
    """Recompensa é 1.0 com clique/conversão e 0.0 sem — não depende mais da receita do braço."""
    did = (
        await client.post("/decide", json={"codCliente": cod_cliente, "channel": "app"})
    ).json()["decisionId"]

    valor = (await client.post("/reward", json={"decisionId": did, "converted": True})).json()[
        "value"
    ]
    assert valor == pytest.approx(1.0)

    outra = (
        await client.post("/decide", json={"codCliente": cod_cliente, "channel": "app"})
    ).json()["decisionId"]
    sem_clique = (
        await client.post("/reward", json={"decisionId": outra, "converted": False})
    ).json()["value"]
    assert sem_clique == pytest.approx(0.0)


@pytest.mark.asyncio
async def test_audit_context_separates_excluded_from_monitored(
    client, mock_model_service, cod_cliente, session_factory
):
    """O log distingue atributo PROIBIDO (sexo) de atributo sensível EM USO (renda).

    Renda entra na decisão de forma legítima — compõe o contexto e governa a elegibilidade via
    `renda_percentil_min`. Declará-la "excluída" seria falso; o log a registra como monitorada,
    que é o que sustenta a análise de fairness por faixa de renda.
    """
    did = (
        await client.post("/decide", json={"codCliente": cod_cliente, "channel": "app"})
    ).json()["decisionId"]

    async with session_factory() as s:
        ctx = await s.scalar(select(Decisao.context).where(Decisao.decision_id == did))

    assert ctx["atributos_excluidos"] == ["sexo"]
    assert ctx["atributos_monitorados"] == ["renda_estimada_anual_brl"]
    # coerência: o que é monitorado está em uso, logo não pode constar como excluído
    assert set(ctx["atributos_excluidos"]).isdisjoint(ctx["atributos_monitorados"])
    assert "renda_estimada_anual_brl" in ctx["features_numericas"]
    assert "sexo" not in ctx["features_numericas"]


@pytest.mark.asyncio
async def test_decide_unknown_client_returns_404(client, mock_model_service, cod_cliente):
    resp = await client.post("/decide", json={"codCliente": 999_999_999, "channel": "app"})
    assert resp.status_code == 404
    assert resp.json()["code"] == "CLIENT_NOT_FOUND"
