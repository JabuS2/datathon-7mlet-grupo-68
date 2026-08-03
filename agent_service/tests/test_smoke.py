import jwt
import pytest
from fastapi.testclient import TestClient

import agent_service.agent as agent_module
from agent_service.app import build_app
from agent_service.config import Settings


@pytest.fixture
def settings(monkeypatch):
    async def _no_tools(_settings):
        return []

    # Avoid needing a running MCP server; build the graph with no tools.
    monkeypatch.setattr(agent_module, "load_mcp_tools", _no_tools)

    return Settings(
        OPENAI_API_KEY="sk-test-dummy",
        OPENAI_MODEL="openai:gpt-4o-mini",
        SECRET_KEY="test_secret",
        ALGORITHM="HS256",
    )


@pytest.fixture
async def client(settings):
    app = await build_app(settings)
    return TestClient(app)


def _valid_token(settings: Settings) -> str:
    return jwt.encode(
        {"sub": "1", "iat": 0, "exp": 9999999999},
        settings.SECRET_KEY,
        algorithm=settings.ALGORITHM,
    )


async def test_health(client):
    resp = client.get("/health")
    assert resp.status_code == 200
    assert resp.json() == {"status": "ok"}


async def test_agent_endpoint_requires_auth(client):
    resp = client.post("/", json={})
    assert resp.status_code == 401
    assert resp.json()["code"] == "INVALID_TOKEN"


async def test_agent_endpoint_rejects_invalid_token(client):
    resp = client.post("/", json={}, headers={"Authorization": "Bearer nonsense"})
    assert resp.status_code == 401


async def test_valid_token_passes_auth_gate(client, settings):
    token = _valid_token(settings)
    resp = client.post("/", json={}, headers={"Authorization": f"Bearer {token}"})
    # Auth gate passed; the AG-UI endpoint rejects the empty body downstream.
    assert resp.status_code != 401


async def test_graph_has_checkpointer(settings):
    # The AG-UI adapter calls graph.aget_state(), which requires a checkpointer.
    # Regression guard for "ValueError: No checkpointer set".
    from agent_service.agent import build_agent_graph

    graph = await build_agent_graph(settings)
    assert graph.checkpointer is not None
