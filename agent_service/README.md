# agent_service

A dedicated Python service that runs a **LangChain deep agent** and exposes it
over the **AG-UI protocol** so the CopilotKit dashboard frontend can chat with
it. The agent loads its tools and dashboard widgets from the JavaScript
`mcp_server` and is backed by an OpenAI model.

## Architecture

```
dashboard (CopilotKit / AG-UI)
   └─ POST /  (AG-UI events)  ──► agent_service
        ├─ AdminAuthMiddleware   validates the admin JWT (shared secret w/ api_service)
        └─ deep agent (OpenAI)
             └─ MCP tools (langchain-mcp-adapters) ──► mcp_server ──► api_service
```

- **Edge auth:** incoming requests to the agent endpoint must carry a valid
  admin JWT issued by `api_service` (signature + expiry checked here).
- **Downstream auth:** the agent forwards the **logged-in admin's JWT** (the
  same token used to authenticate to the agent endpoint) to the MCP server per
  tool call, which passes it to `api_service`; admin authorization is enforced
  there. `DOWNSTREAM_API_TOKEN` is used only as a fallback (e.g. when
  `REQUIRE_AUTH` is disabled).

## Configuration

Copy `.env.example` to `.env`:

| Variable              | Default                       | Description                                   |
| --------------------- | ----------------------------- | --------------------------------------------- |
| `PORT`                | `8100`                        | Port to listen on                             |
| `AGENT_PATH`          | `/`                           | Path of the AG-UI endpoint                    |
| `CORS_ORIGINS`        | `["http://localhost:3000"]`   | Allowed frontend origins                      |
| `OPENAI_API_KEY`      | –                             | OpenAI API key                                |
| `OPENAI_MODEL`        | `openai:gpt-4o-mini`          | Model spec passed to the deep agent           |
| `MCP_SERVER_URL`      | `http://localhost:8200/mcp`   | Streamable-HTTP MCP endpoint                  |
| `DOWNSTREAM_API_TOKEN`| –                             | Fallback admin JWT/service token (used only when no caller JWT is present) |
| `SECRET_KEY`          | `your_secret_key`             | JWT secret (must match `api_service`)         |
| `REQUIRE_AUTH`        | `true`                        | Gate the agent endpoint on a valid JWT        |

## Running

```bash
poetry install            # or: pip install -e . / see Dockerfile
python -m agent_service.main
# or
uvicorn agent_service.app:app --host 0.0.0.0 --port 8100
```

The `mcp_server` should be reachable at `MCP_SERVER_URL` when the service starts,
since tools are loaded at startup.

## Tests

```bash
pytest
```

The smoke tests build the app with no MCP tools and verify the health endpoint
and the JWT auth gate without calling OpenAI.
