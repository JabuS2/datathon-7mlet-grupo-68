# mcp_server

JavaScript (TypeScript) **MCP server** that exposes admin tools and `mcpApp`
widgets (via [MCP-UI](https://mcpui.dev)) for the deep agent. It is consumed by
`agent_service` through a streamable-HTTP MCP connection.

## Tools & widgets

| Tool                 | Widget (`mcpApp`)      | Description                                                        |
| -------------------- | ---------------------- | ----------------------------------------------------------------- |
| `get_users_overview` | `ui://mcp-server/users-overview` | Admin KPIs (total users, admins, recent signups) + latest users, rendered as a self-contained dashboard card. |
| `get_db_schema`      | `ui://mcp-server/schema-explorer` | Lists tables/columns for `api_service` or `model_service` (text-to-SQL helper). |
| `run_sql_query`      | `ui://mcp-server/sql-results`    | Runs a single read-only `SELECT`/`WITH` against `api_service` or `model_service` and renders a table. Requires `READONLY_DATABASE_URL` / `READONLY_MODEL_DATABASE_URL` (see below) — no-ops with an error if unset. |

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
| `READONLY_DATABASE_URL`       | _(unset)_ | Read-only Postgres URL for `api_service`'s DB. Enables `run_sql_query`/`get_db_schema` for that database. |
| `READONLY_MODEL_DATABASE_URL` | _(unset)_ | Read-only Postgres URL for `model_service`'s DB. Same, for that database. |

Both readonly URLs point at the `readonly_reporting` role (SELECT-only, see
`infra/docker/initdb/02-readonly-role.sh`). Under Docker Compose they're
derived automatically from `READONLY_DB_USER`/`READONLY_DB_PASSWORD` in the
root `.env` — set `READONLY_DB_PASSWORD` there to turn the text-to-SQL tools
on.

**Existing Postgres volume?** `02-readonly-role.sh` (and
`01-model-service-db.sh`, which creates the `model_service` database itself)
only run on first init of the `postgres_data` volume. If you add
`READONLY_DB_PASSWORD` to an already-running stack, the role/database won't
appear on restart alone — apply by hand:

```bash
docker compose exec postgres createdb -U postgres model_service   # if missing
docker compose exec -e READONLY_DB_USER=readonly_reporting \
  -e READONLY_DB_PASSWORD=<pw> postgres \
  bash /docker-entrypoint-initdb.d/02-readonly-role.sh
```

If `run_sql_query` fails with a generic "issue accessing the database" from
the agent even though the URLs are set, this is the most likely cause — check
`docker compose logs mcp_server` for the actual thrown error.

## Development

```bash
npm install
npm run dev      # tsx watch
# or
npm run build && npm start
```

Health check: `GET /health`. MCP endpoint: `POST /mcp`.
