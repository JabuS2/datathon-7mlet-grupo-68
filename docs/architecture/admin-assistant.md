# Admin Assistant Architecture

An admin-facing assistant: admins chat in a CopilotKit (AG-UI) frontend, a
LangChain **deep agent** decides what to do, and a **JavaScript MCP server**
exposes tools and dashboard widgets (`mcpApp`). The assistant's main job is to
**render dashboards** by calling MCP tools that return MCP-UI resources, which
CopilotKit renders inline.

## Components

| Service         | Stack                        | Port  | Responsibility                                                     |
| --------------- | ---------------------------- | ----- | ----------------------------------------------------------------- |
| `apps/dashboard`| Next.js + CopilotKit (AG-UI) | 3000  | Admin login, chat UI, renders MCP-UI widgets                      |
| `agent_service` | Python, deepagents + AG-UI   | 8100  | Deep agent (OpenAI), serves AG-UI endpoint, loads MCP tools       |
| `mcp_server`    | Node/TypeScript, MCP + mcp-ui| 8200  | Exposes tools + `mcpApp` widgets, proxies admin data              |
| `api_service`   | FastAPI + Postgres           | 8000/8001 | Auth (JWT), admin data (`/admin/users/overview`)              |

## Request flow

```
Admin browser (CopilotKit provider, admin JWT)
  │  POST /api/copilotkit  (Next.js route: CopilotRuntime + AG-UI HttpAgent)
  ▼
agent_service  ── AdminAuthMiddleware validates the admin JWT (shared SECRET_KEY)
  │  LangChain deep agent (OpenAI model)
  │  MCP client (langchain-mcp-adapters, streamable HTTP)
  ▼
mcp_server  ── get_users_overview tool
  │  forwards Authorization ▼
api_service  GET /api/v1/admin/users/overview  (get_current_admin guard)
  ▲  KPI JSON
mcp_server  ── builds MCP-UI resource (self-contained HTML widget) + JSON
  ▲
agent_service ── streams tool result over AG-UI
  ▲
dashboard  ── useCopilotAction("get_users_overview") → <UIResourceRenderer>
```

## Authentication & authorization

- **api_service** issues JWTs (`/login`) and exposes `is_admin` on `/me`. The
  `/admin/*` routes require `get_current_admin` (403 for non-admins).
- **dashboard** stores the JWT (localStorage), only lets admins in, and forwards
  the JWT to `/api/copilotkit`, which passes it to `agent_service`.
- **agent_service** validates the JWT signature/expiry at the edge
  (`SECRET_KEY`/`ALGORITHM` shared with api_service).
- **Downstream data access:** the agent forwards `DOWNSTREAM_API_TOKEN` to the
  MCP server, which passes it to api_service; admin authorization is enforced
  there. Full per-user token forwarding end-to-end is a planned enhancement.

## Widgets (`mcpApp`)

MCP tools return an **MCP-UI resource** built with `@mcp-ui/server`
(`createUIResource`, `ui://mcp-server/<widget>`). Data is embedded into the HTML
so the sandboxed iframe is self-contained. The frontend renders it with
`@mcp-ui/client`'s `UIResourceRenderer`. Add widgets in
`mcp_server/src/widgets/` and register them in `registry.ts`.

## Running locally

Each service has its own README. With Docker Compose (opt-in profiles):

```bash
cp .env.example .env    # set OPENAI_API_KEY, DOWNSTREAM_API_TOKEN, SECRET_KEY
docker compose --profile api --profile app up --build
```

- Dashboard: http://localhost:3000
- Agent AG-UI: http://localhost:8100
- MCP server: http://localhost:8200/mcp
- API: http://localhost:8001

Or run each service directly (see `apps/dashboard/README.md`,
`agent_service/README.md`, `mcp_server/README.md`, `api_service/README.md`).
