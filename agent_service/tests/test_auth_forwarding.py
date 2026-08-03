import jwt
from fastapi.testclient import TestClient
from langchain_core.runnables import RunnableLambda
from langchain_mcp_adapters.interceptors import MCPToolCallRequest

import agent_service.agent as agent_module
from agent_service.app import build_app
from agent_service.config import Settings
from agent_service.mcp import DOWNSTREAM_AUTH_CONFIG_KEY, AuthForwardingInterceptor


def _settings(**overrides) -> Settings:
    overrides.setdefault("DOWNSTREAM_API_TOKEN", "")
    return Settings(SECRET_KEY="test_secret", ALGORITHM="HS256", **overrides)


async def _run_interceptor(interceptor: AuthForwardingInterceptor, configurable: dict):
    """Invoke the interceptor inside a RunnableConfig context.

    Wrapping in a RunnableLambda makes ``ensure_config()`` inside the
    interceptor see ``configurable``, exactly as it would during a real graph
    tool call.
    """
    captured: dict = {}

    async def handler(request: MCPToolCallRequest):
        captured["headers"] = request.headers
        return "ok"

    request = MCPToolCallRequest(name="get_users_overview", args={}, server_name="mcp_server")

    async def _invoke(_):
        return await interceptor(request, handler)

    result = await RunnableLambda(_invoke).ainvoke({}, config={"configurable": configurable})
    return captured, result


async def test_forwards_caller_token_from_run_config():
    interceptor = AuthForwardingInterceptor(_settings())
    captured, result = await _run_interceptor(
        interceptor, {DOWNSTREAM_AUTH_CONFIG_KEY: "Bearer caller-jwt"}
    )
    assert captured["headers"] == {"Authorization": "Bearer caller-jwt"}
    assert result == "ok"


async def test_caller_token_takes_precedence_over_static_fallback():
    interceptor = AuthForwardingInterceptor(_settings(DOWNSTREAM_API_TOKEN="static-service"))
    captured, _ = await _run_interceptor(
        interceptor, {DOWNSTREAM_AUTH_CONFIG_KEY: "Bearer caller-jwt"}
    )
    assert captured["headers"] == {"Authorization": "Bearer caller-jwt"}


async def test_falls_back_to_static_token_and_prefixes_bearer():
    interceptor = AuthForwardingInterceptor(_settings(DOWNSTREAM_API_TOKEN="static-service"))
    captured, _ = await _run_interceptor(interceptor, {})
    assert captured["headers"] == {"Authorization": "Bearer static-service"}


async def test_no_token_leaves_headers_untouched():
    interceptor = AuthForwardingInterceptor(_settings())
    captured, _ = await _run_interceptor(interceptor, {})
    assert captured["headers"] is None


async def test_endpoint_injects_caller_token_into_run_config(monkeypatch):
    async def _no_tools(_settings):
        return []

    monkeypatch.setattr(agent_module, "load_mcp_tools", _no_tools)

    captured: dict = {}

    async def _fake_run(self, input_data):
        captured["config"] = self.config
        return
        yield  # unreachable; makes _fake_run an async generator

    from ag_ui_langgraph import LangGraphAgent

    monkeypatch.setattr(LangGraphAgent, "run", _fake_run)

    settings = _settings(OPENAI_API_KEY="sk-test-dummy")
    app = await build_app(settings)
    client = TestClient(app)

    token = jwt.encode(
        {"sub": "1", "iat": 0, "exp": 9999999999},
        settings.SECRET_KEY,
        algorithm=settings.ALGORITHM,
    )
    body = {
        "threadId": "t1",
        "runId": "r1",
        "state": {},
        "messages": [],
        "tools": [],
        "context": [],
        "forwardedProps": {},
    }

    resp = client.post("/", json=body, headers={"Authorization": f"Bearer {token}"})

    assert resp.status_code == 200
    assert captured["config"]["configurable"][DOWNSTREAM_AUTH_CONFIG_KEY] == f"Bearer {token}"
