import asyncio
import logging

from ag_ui.core.types import RunAgentInput
from ag_ui.encoder import EventEncoder
from ag_ui_langgraph import LangGraphAgent
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, StreamingResponse
from starlette.middleware.base import BaseHTTPMiddleware

from agent_service.agent import build_agent_graph
from agent_service.auth import InvalidToken, validate_request_token
from agent_service.config import Settings, settings
from agent_service.mcp import DOWNSTREAM_AUTH_CONFIG_KEY

logger = logging.getLogger(__name__)


class AdminAuthMiddleware(BaseHTTPMiddleware):
    """Validate the admin JWT on requests to the AG-UI agent endpoint."""

    def __init__(self, app, settings: Settings):
        super().__init__(app)
        self.settings = settings

    async def dispatch(self, request: Request, call_next):
        is_agent_path = request.url.path.rstrip("/") == self.settings.AGENT_PATH.rstrip("/")

        if (
            self.settings.REQUIRE_AUTH
            and is_agent_path
            and request.method not in ("OPTIONS", "GET")
        ):
            try:
                validate_request_token(request.headers.get("Authorization"), self.settings)
            except InvalidToken as err:
                return JSONResponse(
                    status_code=401,
                    content={"error": str(err), "code": "INVALID_TOKEN"},
                )

        return await call_next(request)


def add_admin_agent_endpoint(app: FastAPI, agent: LangGraphAgent, settings: Settings) -> None:
    """Register the AG-UI agent endpoint with per-request admin auth forwarding.

    Mirrors ``ag_ui_langgraph.add_langgraph_fastapi_endpoint`` but injects the
    caller's ``Authorization`` header into the LangGraph run config so the MCP
    ``AuthForwardingInterceptor`` can forward the logged-in admin's JWT to
    downstream tools instead of relying on a static service token.
    """

    @app.post(settings.AGENT_PATH)
    async def agent_endpoint(input_data: RunAgentInput, request: Request):
        encoder = EventEncoder(accept=request.headers.get("accept"))

        # Each request gets an isolated agent clone (LangGraphAgent stores
        # per-request state on the instance).
        request_agent = agent.clone()

        authorization = request.headers.get("Authorization")
        configurable = dict((request_agent.config or {}).get("configurable", {}))
        if authorization:
            configurable[DOWNSTREAM_AUTH_CONFIG_KEY] = authorization
        request_agent.config = {**(request_agent.config or {}), "configurable": configurable}

        async def event_generator():
            async for event in request_agent.run(input_data):
                yield encoder.encode(event)

        return StreamingResponse(
            event_generator(),
            media_type=encoder.get_content_type(),
        )


async def build_app(settings: Settings = settings) -> FastAPI:
    app = FastAPI(title="Agent Service", version="0.1.0")

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.CORS_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.add_middleware(AdminAuthMiddleware, settings=settings)

    @app.get("/health")
    async def health():
        return {"status": "ok"}

    graph = await build_agent_graph(settings)
    agent = LangGraphAgent(
        name=settings.AGENT_NAME,
        description="Admin dashboard assistant that renders MCP-driven dashboards.",
        graph=graph,
    )
    add_admin_agent_endpoint(app, agent, settings)

    return app


def create_app(settings: Settings = settings) -> FastAPI:
    """Synchronous factory for uvicorn.

    Building the agent graph is async. When uvicorn invokes this factory with
    ``--factory`` it does so from inside its own event loop, where
    ``asyncio.run`` is illegal, so we build in a dedicated worker thread. When
    called with no running loop (e.g. ``uvicorn module:app``), we build directly.
    """
    try:
        asyncio.get_running_loop()
    except RuntimeError:
        return asyncio.run(build_app(settings))

    import concurrent.futures

    with concurrent.futures.ThreadPoolExecutor(max_workers=1) as executor:
        return executor.submit(lambda: asyncio.run(build_app(settings))).result()
