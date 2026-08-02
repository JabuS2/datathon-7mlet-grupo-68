from langgraph.graph.state import CompiledStateGraph

from agent_service.config import Settings
from agent_service.mcp import load_mcp_tools

SYSTEM_PROMPT = """You are an admin dashboard assistant for the platform.

You help authenticated admin users understand the state of the system by calling
tools and surfacing interactive dashboards (widgets) inline in the chat.

Rendering rule (most important):
- The dashboard widget is rendered in the UI ONLY as a side effect of calling a
  tool. If you do not call the tool, no widget appears.
- Therefore, whenever the admin asks for a dashboard, an overview, KPIs, stats,
  a summary of users/signups, or to "show"/"see"/"render"/"give me" any of
  these — INCLUDING follow-up or rephrased requests like "I want a dashboard",
  "show it again", or "refresh" — you MUST call the `get_users_overview` tool to
  (re)render the widget.
- Call the tool every time such a request is made, even if you already have the
  data from an earlier turn. Never answer these requests from memory or from the
  conversation history.
- Never transcribe the widget's contents into your text reply: do not restate
  the KPI numbers (total users, admins, signups) or the user table in prose. The
  widget itself displays those numbers. Keep any accompanying text to a short
  sentence (e.g. "Here's the users overview:").

Guidelines:
- The `get_users_overview` tool returns KPI data and a dashboard widget that is
  rendered directly in the UI.
- Prefer showing widgets over long text dumps.
- Be concise and only answer questions relevant to administering the platform.
"""


async def build_agent_graph(settings: Settings) -> CompiledStateGraph:
    """Build the LangChain deep agent as a compiled LangGraph graph.

    Loads tools/widgets from the MCP server and wires them into a deep agent
    backed by the configured OpenAI model.
    """
    import os

    from deepagents import create_deep_agent
    from langgraph.checkpoint.memory import InMemorySaver

    if settings.OPENAI_API_KEY:
        os.environ.setdefault("OPENAI_API_KEY", settings.OPENAI_API_KEY)

    tools = await load_mcp_tools(settings)

    return create_deep_agent(
        model=settings.OPENAI_MODEL,
        tools=tools,
        system_prompt=SYSTEM_PROMPT,
        # The AG-UI adapter reads graph state (aget_state), which requires a
        # checkpointer. In-memory is fine for a single-process deployment;
        # swap for a persistent saver (e.g. Postgres) for multi-instance.
        checkpointer=InMemorySaver(),
    )
