"""E10 — governança/MLOps: registro, approval gate, promoção, rollback, monitoramento + RBAC."""
import pytest
import pytest_asyncio

from db.unit_of_work import UnitOfWork
from services.seed.seeder import seed_all
from settings import settings


@pytest_asyncio.fixture
async def seeded(session_factory):
    async with session_factory() as s:
        async with UnitOfWork(s) as uow:
            await seed_all(uow, settings.DATA_DIR, client_limit=30)


async def _operador_headers(client) -> dict:
    await client.post("/register", json={"email": "op@x.com", "password": "segredo123"})
    resp = await client.post("/login", json={"email": "op@x.com", "password": "segredo123"})
    return {"Authorization": f"Bearer {resp.json()['accessToken']}"}


_NEW_POLICY = {"policyId": "linucb-v2", "version": "2.0", "algorithm": "linucb", "hyperparams": {}}


@pytest.mark.asyncio
async def test_policy_promotion_via_approval_gate(client, seeded):
    h = await _operador_headers(client)
    assert (await client.post("/policies", json=_NEW_POLICY, headers=h)).json()["status"] == "shadow"

    cycle = (await client.post("/retrain-cycles", json={"policyId": "linucb-v2"}, headers=h)).json()
    assert cycle["status"] == "candidate"

    gate = await client.post(
        "/approvals", json={"runId": cycle["runId"], "decision": "approve", "note": "ok"}, headers=h
    )
    assert gate.status_code == 200

    policies = {p["policyId"]: p["status"] for p in (await client.get("/policies", headers=h)).json()}
    assert policies["linucb-v2"] == "active"  # candidata promovida
    assert policies["linucb-v1"] == "retired"  # anterior aposentada (uma ativa por vez)


@pytest.mark.asyncio
async def test_rollback_restores_previous_policy(client, seeded):
    h = await _operador_headers(client)
    await client.post("/policies", json=_NEW_POLICY, headers=h)
    run_id = (await client.post("/retrain-cycles", json={"policyId": "linucb-v2"}, headers=h)).json()["runId"]
    await client.post("/approvals", json={"runId": run_id, "decision": "approve"}, headers=h)

    rb = await client.post(
        f"/retrain-cycles/{run_id}/rollback", json={"toPolicyId": "linucb-v1"}, headers=h
    )
    assert rb.status_code == 200
    assert rb.json()["status"] == "rolled_back"

    policies = {p["policyId"]: p["status"] for p in (await client.get("/policies", headers=h)).json()}
    assert policies["linucb-v1"] == "active"
    assert policies["linucb-v2"] == "retired"


@pytest.mark.asyncio
async def test_monitoring_alert_listing(client, seeded):
    h = await _operador_headers(client)
    await client.post(
        "/metrics",
        json={"policyId": "linucb-v1", "metric": "psi_drift", "value": 0.3, "alert": True},
        headers=h,
    )
    alerts = (await client.get("/metrics?alerts_only=true", headers=h)).json()
    assert any(m["metric"] == "psi_drift" and m["alert"] for m in alerts)


@pytest.mark.asyncio
async def test_demo_is_forbidden_from_governance(client, seeded):
    onb = await client.post(
        "/onboarding",
        json={"email": "d@x.com", "password": "segredo123", "idade": 30, "segmento": "02 - VAREJO"},
    )
    demo_headers = {"Authorization": f"Bearer {onb.json()['accessToken']}"}
    resp = await client.post("/policies", json=_NEW_POLICY, headers=demo_headers)
    assert resp.status_code == 403
    assert resp.json()["code"] == "ROLE_NOT_ALLOWED"
