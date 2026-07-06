"""E12 — self-service: loga → vê conta/perfil → recebe sugestões → feedback/reward (com posse)."""
import pytest
import pytest_asyncio

from db.unit_of_work import UnitOfWork
from services.seed.seeder import seed_all
from settings import settings


@pytest_asyncio.fixture
async def seeded(session_factory):
    async with session_factory() as s:
        async with UnitOfWork(s) as uow:
            await seed_all(uow, settings.DATA_DIR, client_limit=60)


async def _onboard(client, email: str) -> dict:
    """Cadastra um visitante demo e devolve headers autenticados + o corpo do onboarding."""
    resp = await client.post(
        "/onboarding",
        json={"email": email, "password": "segredo123", "idade": 30, "segmento": "02 - VAREJO"},
    )
    assert resp.status_code == 200, resp.text
    body = resp.json()
    return {"headers": {"Authorization": f"Bearer {body['accessToken']}"}, "body": body}


@pytest.mark.asyncio
async def test_full_self_service_journey(client, seeded):
    session = await _onboard(client, "user@demo.com")
    h = session["headers"]
    cod = session["body"]["cliente"]["codCliente"]

    # 1) vê a conta — /me traz papel e cod_cliente vindos do token
    me = (await client.get("/me", headers=h)).json()
    assert me["tipo"] == "demo"
    assert me["codCliente"] == cod

    # 2) vê o próprio perfil (contexto do cliente)
    profile = await client.get("/me/profile", headers=h)
    assert profile.status_code == 200
    assert profile.json()["codCliente"] == cod

    # 3) catálogo de ofertas
    offers = (await client.get("/offers", headers=h)).json()
    assert len(offers) == 10

    # 4) recebe sugestões (sem passar cod_cliente — vem do token)
    recs = (await client.get("/me/recommendations", headers=h)).json()
    assert recs["codCliente"] == cod
    assert len(recs["items"]) >= 1

    # 5) decide → feedback → reward, tudo escopado no usuário
    decision = (await client.post("/me/decide", headers=h)).json()
    assert decision["armId"].startswith("OFF-")
    did = decision["decisionId"]

    assert (await client.post("/me/feedback", json={"decisionId": did, "type": "click"}, headers=h)).status_code == 200
    rw = await client.post("/me/reward", json={"decisionId": did, "converted": True}, headers=h)
    assert rw.status_code == 200 and rw.json()["status"] == "observed"

    # 6) histórico das próprias decisões
    history = (await client.get("/me/decisions", headers=h)).json()
    assert any(d["decisionId"] == did for d in history)


@pytest.mark.asyncio
async def test_cannot_touch_other_users_decision(client, seeded):
    a = await _onboard(client, "a@demo.com")
    b = await _onboard(client, "b@demo.com")

    decision = (await client.post("/me/decide", headers=a["headers"])).json()
    did = decision["decisionId"]

    # B tenta dar reward na decisão de A → 403 (posse)
    resp = await client.post("/me/reward", json={"decisionId": did, "converted": True}, headers=b["headers"])
    assert resp.status_code == 403
    assert resp.json()["code"] == "NOT_DECISION_OWNER"


@pytest.mark.asyncio
async def test_me_requires_auth(client, seeded):
    assert (await client.get("/me/profile")).status_code == 401


@pytest.mark.asyncio
async def test_operador_without_profile_gets_conflict(client, seeded):
    await client.post("/register", json={"email": "op@demo.com", "password": "segredo123"})
    token = (await client.post("/login", json={"email": "op@demo.com", "password": "segredo123"})).json()["accessToken"]
    resp = await client.get("/me/profile", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 409
    assert resp.json()["code"] == "NO_CLIENT_PROFILE"
