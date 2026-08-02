from collections.abc import Awaitable, Callable

from langchain_core.runnables import ensure_config
from langchain_core.tools import BaseTool
from langchain_mcp_adapters.client import MultiServerMCPClient
from langchain_mcp_adapters.interceptors import (
    MCPToolCallRequest,
    MCPToolCallResult,
)

from agent_service.config import Settings

# Key under RunnableConfig["configurable"] carrying the caller's admin JWT.
# The AG-UI endpoint injects it per request; this interceptor reads it back at
# tool-call time so each MCP call is authorized as the logged-in admin.
DOWNSTREAM_AUTH_CONFIG_KEY = "downstream_authorization"


class AuthForwardingInterceptor:
    """Forward the logged-in admin's JWT to the MCP server per tool call.

    The token is read from the active LangGraph run config (populated by the
    agent endpoint from the incoming ``Authorization`` header). This keeps
    downstream access control tied to the real user instead of a static,
    expiring service token. ``DOWNSTREAM_API_TOKEN`` is used only as a fallback
    (e.g. when ``REQUIRE_AUTH`` is disabled).
    """

    def __init__(self, settings: Settings):
        self.settings = settings

    async def __call__(
        self,
        request: MCPToolCallRequest,
        handler: Callable[[MCPToolCallRequest], Awaitable[MCPToolCallResult]],
    ) -> MCPToolCallResult:
        token = self._resolve_token()
        if token:
            request = request.override(headers={"Authorization": token})
        return await handler(request)

    def _resolve_token(self) -> str | None:
        config = ensure_config()
        token = (config.get("configurable") or {}).get(DOWNSTREAM_AUTH_CONFIG_KEY)

        if not token:
            token = self.settings.DOWNSTREAM_API_TOKEN

        if not token:
            return None

        if not token.lower().startswith("bearer "):
            token = f"Bearer {token}"

        return token


def build_mcp_client(settings: Settings) -> MultiServerMCPClient:
    """Create an MCP client pointed at the JavaScript MCP server.

    Authorization is attached per tool call by ``AuthForwardingInterceptor``,
    which forwards the logged-in admin's JWT; the MCP server relays it to
    api_service, which enforces admin access.
    """
    return MultiServerMCPClient(
        {
            "mcp_server": {
                "transport": "streamable_http",
                "url": settings.MCP_SERVER_URL,
            }
        },
        tool_interceptors=[AuthForwardingInterceptor(settings)],
    )


async def load_mcp_tools(settings: Settings) -> list[BaseTool]:
    client = build_mcp_client(settings)
    return await client.get_tools()
