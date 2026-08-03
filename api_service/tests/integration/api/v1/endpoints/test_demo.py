"""E8 — onboarding da vitrine (§6): cadastro → perfil sintético demo → recomendação ao vivo."""

import pytest
import pytest_asyncio

from db.unit_of_work import UnitOfWork
from services.seed.seeder import seed_all
from settings import settings


@pytest_asyncio.fixture
async def seeded(session_factory):
    async with session_factory() as s, UnitOfWork(s) as uow:
        await seed_all(uow, settings.DATA_DIR, client_limit=60)


@pytest.mark.asyncio
async def test_onboarding_creates_demo_profile_and_decides(client, seeded):
    payload = {
        "email": "visitante@demo.com",
        "password": "segredo123",
        "idade": 30,
        "segmento": "02 - VAREJO",
    }
    resp = await client.post("/onboarding", json=payload)
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["accessToken"]
    cliente = body["cliente"]
    assert cliente["codCliente"] >= 9_000_000  # faixa reservada de perfis demo
    assert cliente["origem"] == "demo"

    # o perfil novo (que o bandit nunca viu) recebe uma recomendação — cold-start ao vivo
    decide = await client.post(
        "/decide", json={"codCliente": cliente["codCliente"], "channel": "app"}
    )
    assert decide.status_code == 200
    assert decide.json()["armId"].startswith("OFF-")


@pytest.mark.asyncio
async def test_onboarding_duplicate_email_conflicts(client, seeded):
    payload = {
        "email": "dup@demo.com",
        "password": "segredo123",
        "idade": 40,
        "segmento": "02 - VAREJO",
    }
    assert (await client.post("/onboarding", json=payload)).status_code == 200
    resp = await client.post("/onboarding", json=payload)
    assert resp.status_code == 409
    assert resp.json()["code"] == "EMAIL_EXISTS"
