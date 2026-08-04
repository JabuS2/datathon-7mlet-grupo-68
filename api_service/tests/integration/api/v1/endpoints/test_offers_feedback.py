import pytest
import pytest_asyncio
from fastapi import status

from db.unit_of_work import UnitOfWork
from services.seed.seeder import seed_all
from settings import settings


class _FakeModelClient:
    """Fake do model_service que respeita o contrato de /rank e /update."""

    def __init__(self):
        self.clicks: dict[str, int] = {}
        self.updates: list[tuple[str, float]] = []

    async def rank(self, algorithm, client, segments, top=None, exclude_arm_ids=None):
        arms = ["OFF-CR-001", "OFF-INV-004", "OFF-SEG-003"]
        ranked = sorted(arms, key=lambda a: -self.clicks.get(a, 0))
        out = [
            {
                "arm_id": a,
                "rank": i,
                "score": float(self.clicks.get(a, 0)),
                "pred": 0.0,
                "bonus": 0.0,
                "category": "credito",
                "product_name": "Produto",
                "description": "Descricao",
                "valor_total": 100.0,
                "desconto_pct": 20,
                "valor_final": 80.0,
            }
            for i, a in enumerate(ranked, start=1)
        ]
        if top:
            out = out[:top]
        return {"algorithm": algorithm or "linucb", "ranked": out}

    async def update(self, algorithm, arm_id, reward, client, segments):
        self.updates.append((arm_id, reward))
        if reward >= 1:
            self.clicks[arm_id] = self.clicks.get(arm_id, 0) + 1
        return {"algorithm": algorithm or "linucb", "arm_id": arm_id, "status": "updated"}


@pytest.fixture
def mock_model(monkeypatch):
    import api.v1.endpoints.feedback as fb
    import api.v1.endpoints.offers as off

    fake = _FakeModelClient()
    monkeypatch.setattr(off, "model_client", fake)
    monkeypatch.setattr(fb, "model_client", fake)
    return fake


@pytest_asyncio.fixture
async def seeded(session_factory):
    """Catálogo + clientes de seed — o onboarding sorteia um template real daqui."""
    async with session_factory() as s, UnitOfWork(s) as uow:
        await seed_all(uow, settings.DATA_DIR, client_limit=60)


async def _auth_headers(client, email="offers@example.com"):
    """Conta da vitrine: `/onboarding` cria o `Cliente` e vincula em `users.cod_cliente`.

    `/register` não serve mais aqui — cria operador, que não tem cliente vinculado e agora
    recebe 409 NO_CLIENT_PROFILE nas rotas de oferta (ver test_offers_requires_client_profile).
    """
    resp = await client.post(
        "/onboarding",
        json={"email": email, "password": "password123", "idade": 30, "segmento": "02 - VAREJO"},
    )
    assert resp.status_code == status.HTTP_200_OK, resp.text
    return {"Authorization": f"Bearer {resp.json()['accessToken']}"}


@pytest.mark.asyncio
async def test_list_offers_returns_price_fields(client, mock_model, seeded):
    headers = await _auth_headers(client)
    resp = await client.get("/offers", headers=headers)
    assert resp.status_code == status.HTTP_200_OK
    offers = resp.json()
    assert len(offers) == 3
    first = offers[0]
    assert {"armId", "rank", "valorTotal", "descontoPct", "valorFinal"} <= set(first)
    assert first["rank"] == 1


@pytest.mark.asyncio
async def test_list_offers_requires_auth(client, mock_model):
    resp = await client.get("/offers")
    assert resp.status_code in (status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN)


@pytest.mark.asyncio
async def test_feedback_click_sets_reward_and_updates_model(client, mock_model, seeded):
    headers = await _auth_headers(client)
    resp = await client.post(
        "/feedback", headers=headers, json={"armId": "OFF-SEG-003", "clicked": True}
    )
    assert resp.status_code == status.HTTP_200_OK
    body = resp.json()
    assert body["reward"] == 1.0
    assert body["status"] == "applied"
    assert ("OFF-SEG-003", 1.0) in mock_model.updates


@pytest.mark.asyncio
async def test_feedback_no_click_reward_zero(client, mock_model, seeded):
    headers = await _auth_headers(client)
    resp = await client.post(
        "/feedback", headers=headers, json={"armId": "OFF-CR-001", "clicked": False}
    )
    assert resp.status_code == status.HTTP_200_OK
    assert resp.json()["reward"] == 0.0


@pytest.mark.asyncio
async def test_feedback_recomputes_next_offers(client, mock_model, seeded):
    headers = await _auth_headers(client)
    # arm que começa em último
    before = await client.get("/offers", headers=headers)
    target = before.json()[-1]["armId"]
    for _ in range(3):
        await client.post("/feedback", headers=headers, json={"armId": target, "clicked": True})
    after = await client.get("/offers", headers=headers)
    assert after.json()[0]["armId"] == target


@pytest.mark.asyncio
async def test_profile_update_is_partial_and_typed(client, mock_model, seeded):
    """`PUT /profile` atualiza colunas de `clientes`; campos omitidos não mudam."""
    headers = await _auth_headers(client)
    antes = (await client.get("/me/profile", headers=headers)).json()

    put = await client.put(
        "/profile", headers=headers, json={"idade": 45, "rendaEstimadaAnualBrl": 120000}
    )
    assert put.status_code == status.HTTP_200_OK, put.text
    body = put.json()
    assert body["idade"] == 45
    assert body["rendaEstimadaAnualBrl"] == 120000
    # não mencionado no corpo → preservado
    assert body["codCliente"] == antes["codCliente"]
    assert body["segmento"] == antes["segmento"]

    # a leitura canônica (/me/profile) enxerga a mesma coisa
    depois = (await client.get("/me/profile", headers=headers)).json()
    assert depois["idade"] == 45


@pytest.mark.asyncio
async def test_profile_update_rejects_unknown_field(client, mock_model, seeded):
    """`extra="forbid"` no BaseSchema: chave que o modelo ignoraria vira 422, não silêncio."""
    headers = await _auth_headers(client)
    resp = await client.put("/profile", headers=headers, json={"featureInventada": 1})
    assert resp.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


@pytest.mark.asyncio
async def test_offers_requires_client_profile(client, mock_model, seeded):
    """Operador (criado por /register) não tem `cod_cliente` → 409, não perfil default."""
    await client.post("/register", json={"email": "op@example.com", "password": "password123"})
    token = (
        await client.post("/login", json={"email": "op@example.com", "password": "password123"})
    ).json()["accessToken"]
    headers = {"Authorization": f"Bearer {token}"}

    offers = await client.get("/offers", headers=headers)
    assert offers.status_code == status.HTTP_409_CONFLICT
    assert offers.json()["code"] == "NO_CLIENT_PROFILE"

    fb = await client.post(
        "/feedback", headers=headers, json={"armId": "OFF-CR-001", "clicked": True}
    )
    assert fb.status_code == status.HTTP_409_CONFLICT
