# mcp_server

MCP server em TypeScript que expõe tools administrativas e widgets `mcpApp`
(via [MCP-UI](https://mcpui.dev)) para o deep agent. Consumido pelo
`agent_service` via conexão MCP streamable-HTTP.

| Tool | Widget | Descrição |
| --- | --- | --- |
| `get_users_overview` | `ui://mcp-server/users-overview` | KPIs de admin (total de usuários, admins, cadastros recentes) renderizado como card. |

## Rodando localmente

```bash
npm install
npm run dev      # tsx watch, http://localhost:8200
```

Health check: `GET /health`. Endpoint MCP: `POST /mcp`.

Detalhes completos: [`mcp_server/README.md`](https://github.com/andrevberaldo/datathon-7mlet-grupo-68/blob/main/mcp_server/README.md).
