# dashboard

Next.js (App Router) admin frontend built with **CopilotKit** over the **AG-UI**
protocol. Admins sign in, chat with the assistant, and the assistant renders
**MCP-driven dashboards** (mcpApp widgets) inline.

## How it fits together

```
Browser (CopilotKit provider, admin JWT)
  └─ POST /api/copilotkit  (Next route, CopilotRuntime + AG-UI HttpAgent)
       └─ forwards the admin JWT ──► agent_service (deep agent)
            └─ MCP tools ──► mcp_server ──► api_service
  ◄── tool result incl. widget envelope ── rendered as a sandboxed iframe
```

- **Login** uses `api_service` (`/api/v1/login` + `/api/v1/me`); the JWT is
  stored in `localStorage` and only admins (`isAdmin`) reach the dashboard.
- **`/api/copilotkit`** bridges the browser to `agent_service` and forwards the
  admin JWT so the agent can reach admin-only tools.
- **Widgets** returned by the agent's `get_users_overview` tool arrive as a
  single JSON envelope (`{ type: "mcp_ui_widget", html, summary, … }`) in the
  tool result. The frontend registers a render-only `useCopilotAction` for
  `get_users_overview`; CopilotKit invokes its `render` with the tool `result`
  once the call completes, and `McpUiResources` renders the self-contained
  `html` in a sandboxed `<iframe>` inline in the chat (it also re-renders for
  historical tool calls, so widgets persist across reloads). The envelope is a
  single content block on purpose: the AG-UI/LangGraph bridge persists only the
  first content block of a tool message, so a separately-attached MCP-UI
  resource would be dropped.

## Configuration

Copy `.env.example` to `.env.local`:

| Variable                      | Default                     | Description                                   |
| ----------------------------- | --------------------------- | --------------------------------------------- |
| `NEXT_PUBLIC_API_SERVICE_URL` | `http://localhost:8000`     | api_service base URL (browser: login/me)      |
| `AGENT_SERVICE_URL`           | `http://localhost:8100/`    | agent_service AG-UI endpoint (server-side)    |
| `NEXT_PUBLIC_AGENT_NAME`      | `admin_dashboard_agent`     | Agent name registered in agent_service        |

## Development

```bash
npm install
npm run dev      # http://localhost:3000
# or
npm run build && npm run start
```

Requires `api_service`, `agent_service`, and `mcp_server` running for full
functionality.
