"""E12 — self-service: loga → vê conta/perfil → recebe sugestões → feedback/reward (com posse)."""

import pytest
import pytest_asyncio

from db.unit_of_work import UnitOfWork
from services.seed.seeder import seed_all
from settings import settings


@pytest_asyncio.fixture
async def seeded(session_factory):
    async with session_factory() as s, UnitOfWork(s) as uow:
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

    # 3) vitrine de ofertas — sem parâmetros internos do bandit
    offers = (await client.get("/offers", headers=h)).json()
    assert len(offers) == 10
    assert set(offers[0]) == {"armId", "productName", "description", "category"}

    # 4) recebe sugestões (sem passar cod_cliente — vem do token)
    recs = (await client.get("/me/recommendations", headers=h)).json()
    assert recs["codCliente"] == cod
    assert len(recs["items"]) >= 1

    # 5) decide → feedback → reward, tudo escopado no usuário
    decision = (await client.post("/me/decide", headers=h)).json()
    assert decision["armId"].startswith("OFF-")
    did = decision["decisionId"]

    assert (
        await client.post("/me/feedback", json={"decisionId": did, "type": "click"}, headers=h)
    ).status_code == 200
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
    resp = await client.post(
        "/me/reward", json={"decisionId": did, "converted": True}, headers=b["headers"]
    )
    assert resp.status_code == 403
    assert resp.json()["code"] == "NOT_DECISION_OWNER"


@pytest.mark.asyncio
async def test_me_requires_auth(client, seeded):
    assert (await client.get("/me/profile")).status_code == 401


@pytest.mark.asyncio
async def test_clickable_showcase_attributes_click_to_chosen_offer(client, seeded):
    """Vitrine clicável: o usuário escolhe da lista e o clique é atribuído àquela oferta."""
    h = (await _onboard(client, "clicador@demo.com"))["headers"]

    recs = (await client.get("/me/recommendations?top_k=5", headers=h)).json()["items"]
    assert len(recs) >= 2
    escolhida = recs[1]["armId"]  # de propósito NÃO é a que a política colocaria em 1º

    decision = (
        await client.post("/me/decide", json={"armId": escolhida}, headers=h)
    ).json()
    assert decision["armId"] == escolhida
    assert "user_selected" in decision["reasonCodes"]

    did = decision["decisionId"]
    assert (
        await client.post("/me/feedback", json={"decisionId": did, "type": "click"}, headers=h)
    ).status_code == 200
    assert (
        await client.post("/me/reward", json={"decisionId": did, "converted": True}, headers=h)
    ).status_code == 200

    # o log auditável registra a oferta clicada, não o topo do ranking
    historico = (await client.get("/me/decisions", headers=h)).json()
    assert historico[0]["chosenArmId"] == escolhida
    assert "user_selected" in historico[0]["reasonCodes"]


@pytest.mark.asyncio
async def test_decide_without_body_still_lets_policy_choose(client, seeded):
    """Regressão: o corpo é opcional — quem já chamava sem body não pode quebrar."""
    h = (await _onboard(client, "semcorpo@demo.com"))["headers"]

    decision = (await client.post("/me/decide", headers=h)).json()
    assert decision["armId"].startswith("OFF-")
    assert "user_selected" not in decision["reasonCodes"]


@pytest.mark.asyncio
async def test_decide_rejects_ineligible_arm(client, seeded):
    """Escolher da lista não vira brecha: braço fora do conjunto elegível é barrado."""
    h = (await _onboard(client, "espertinho@demo.com"))["headers"]

    recs = (await client.get("/me/recommendations?top_k=10", headers=h)).json()
    elegiveis = {i["armId"] for i in recs["items"]}
    todas = {o["armId"] for o in (await client.get("/offers", headers=h)).json()}
    inelegiveis = todas - elegiveis
    assert inelegiveis, "cenário exige ao menos uma oferta inelegível para este perfil"

    resp = await client.post("/me/decide", json={"armId": inelegiveis.pop()}, headers=h)
    assert resp.status_code == 409
    assert resp.json()["code"] == "ARM_NOT_ELIGIBLE"


@pytest.mark.asyncio
async def test_offers_hides_bandit_internals_from_demo(client, seeded):
    """A vitrine não expõe receita esperada, fator de exploração nem regras de elegibilidade.

    Regressão: `/offers` servia `OfertaResponse` a qualquer autenticado, entregando ao próprio
    cliente a régua comercial (`expectedRevenueBrl`) e como burlar o filtro (`eligibleSegment`).
    """
    h = (await _onboard(client, "curioso@demo.com"))["headers"]
    interno = {"expectedRevenueBrl", "ucbExplorationFactor", "contextFeatures", "eligibleSegment"}

    offers = (await client.get("/offers", headers=h)).json()
    assert all(interno.isdisjoint(o) for o in offers)

    # e a rota interna é barrada para o demo
    resp = await client.get("/offers/catalog", headers=h)
    assert resp.status_code == 403
    assert resp.json()["code"] == "ROLE_NOT_ALLOWED"


@pytest.mark.asyncio
async def test_offers_catalog_exposes_internals_to_operador(client, seeded):
    await client.post("/register", json={"email": "cat@demo.com", "password": "segredo123"})
    token = (
        await client.post("/login", json={"email": "cat@demo.com", "password": "segredo123"})
    ).json()["accessToken"]

    resp = await client.get("/offers/catalog", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 200
    assert len(resp.json()) == 10
    assert "expectedRevenueBrl" in resp.json()[0]
    assert "eligibleSegment" in resp.json()[0]


@pytest.mark.asyncio
async def test_operador_without_profile_gets_conflict(client, seeded):
    await client.post("/register", json={"email": "op@demo.com", "password": "segredo123"})
    token = (
        await client.post("/login", json={"email": "op@demo.com", "password": "segredo123"})
    ).json()["accessToken"]
    resp = await client.get("/me/profile", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 409
    assert resp.json()["code"] == "NO_CLIENT_PROFILE"
