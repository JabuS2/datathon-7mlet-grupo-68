# mcp_server

MCP server em TypeScript que expõe tools administrativas e widgets `mcpApp`
(via [MCP-UI](https://mcpui.dev)) para o deep agent. Consumido pelo
`agent_service` via conexão MCP streamable-HTTP.

| Tool | Widget | Descrição |
| --- | --- | --- |
| `get_users_overview` | `ui://mcp-server/users-overview` | KPIs de admin (total de usuários, admins, cadastros recentes) renderizado como card. |
| `get_db_schema` | `ui://mcp-server/schema-explorer` | Lista tabelas/colunas de `api_service` ou `model_service` (apoio ao texto-para-SQL). |
| `run_sql_query` | `ui://mcp-server/sql-results` | Executa um `SELECT`/`WITH` somente-leitura contra `api_service` ou `model_service`. Requer `READONLY_DATABASE_URL`/`READONLY_MODEL_DATABASE_URL` — sem eles, a tool falha. Ver `mcp_server/README.md` para setup (inclusive o caso de volume Postgres já existente). |

## Rodando localmente

```bash
npm install
npm run dev      # tsx watch, http://localhost:8200
```

Health check: `GET /health`. Endpoint MCP: `POST /mcp`.

Detalhes completos: [`mcp_server/README.md`](https://github.com/andrevberaldo/datathon-7mlet-grupo-68/blob/main/mcp_server/README.md).
