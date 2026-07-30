import pytest
from fastapi import status


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


async def _auth_headers(client, email="offers@example.com"):
    await client.post("/register", json={"email": email, "password": "password123"})
    resp = await client.post("/login", json={"email": email, "password": "password123"})
    return {"Authorization": f"Bearer {resp.json()['accessToken']}"}


@pytest.mark.asyncio
async def test_list_offers_returns_price_fields(client, mock_model):
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
async def test_feedback_click_sets_reward_and_updates_model(client, mock_model):
    headers = await _auth_headers(client)
    resp = await client.post("/feedback", headers=headers, json={"armId": "OFF-SEG-003", "clicked": True})
    assert resp.status_code == status.HTTP_200_OK
    body = resp.json()
    assert body["reward"] == 1.0
    assert body["status"] == "applied"
    assert ("OFF-SEG-003", 1.0) in mock_model.updates


@pytest.mark.asyncio
async def test_feedback_no_click_reward_zero(client, mock_model):
    headers = await _auth_headers(client)
    resp = await client.post("/feedback", headers=headers, json={"armId": "OFF-CR-001", "clicked": False})
    assert resp.status_code == status.HTTP_200_OK
    assert resp.json()["reward"] == 0.0


@pytest.mark.asyncio
async def test_feedback_recomputes_next_offers(client, mock_model):
    headers = await _auth_headers(client)
    # arm que começa em último
    before = await client.get("/offers", headers=headers)
    target = before.json()[-1]["armId"]
    for _ in range(3):
        await client.post("/feedback", headers=headers, json={"armId": target, "clicked": True})
    after = await client.get("/offers", headers=headers)
    assert after.json()[0]["armId"] == target


@pytest.mark.asyncio
async def test_profile_upsert_and_get(client, mock_model):
    headers = await _auth_headers(client)
    payload = {
        "features": {"idade": 45, "renda_estimada_anual_brl": 120000, "ind_ativo": 1},
        "segments": ["SEG-ALTA-RENDA", "SEG-VIP"],
    }
    put = await client.put("/profile", headers=headers, json=payload)
    assert put.status_code == status.HTTP_200_OK
    assert put.json()["segments"] == ["SEG-ALTA-RENDA", "SEG-VIP"]

    got = await client.get("/profile", headers=headers)
    assert got.status_code == status.HTTP_200_OK
    assert got.json()["features"]["idade"] == 45
