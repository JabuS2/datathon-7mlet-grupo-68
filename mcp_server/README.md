# mcp_server

JavaScript (TypeScript) **MCP server** that exposes admin tools and `mcpApp`
widgets (via [MCP-UI](https://mcpui.dev)) for the deep agent. It is consumed by
`agent_service` through a streamable-HTTP MCP connection.

## Tools & widgets

| Tool                 | Widget (`mcpApp`)      | Description                                                        |
| -------------------- | ---------------------- | ----------------------------------------------------------------- |
| `get_users_overview` | `ui://mcp-server/users-overview` | Admin KPIs (total users, admins, recent signups) + latest users, rendered as a self-contained dashboard card. |

Add new widgets in `src/widgets/` and register them in `src/widgets/registry.ts`;
add new tools in `src/tools/` and wire them in `src/server.ts`.

## Auth

Tools forward the incoming `Authorization` header (the admin JWT) to
`api_service`, so access control is enforced there — the MCP server holds no
credentials of its own.

## Configuration

Copy `.env.example` to `.env`:

| Variable          | Default                 | Description                             |
| ----------------- | ----------------------- | --------------------------------------- |
| `PORT`            | `8200`                  | Port the server listens on              |
| `MCP_HTTP_PATH`   | `/mcp`                  | Path of the streamable-HTTP endpoint    |
| `API_SERVICE_URL` | `http://localhost:8000` | Base URL of the FastAPI `api_service`   |

## Development

```bash
npm install
npm run dev      # tsx watch
# or
npm run build && npm start
```

Health check: `GET /health`. MCP endpoint: `POST /mcp`.
