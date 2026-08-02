# apps/dashboard

Frontend Next.js (App Router) do admin, construído com **CopilotKit** sobre o
protocolo **AG-UI**. Admins fazem login, conversam com o assistente e o
assistente renderiza dashboards vindos do MCP (widgets `mcpApp`) inline.

```
Browser (CopilotKit provider, JWT admin)
  └─ POST /api/copilotkit
       └─ agent_service (deep agent)
            └─ MCP tools ──► mcp_server ──► api_service
  ◄── resultado da tool com o widget ── renderizado em iframe sandboxed
```

## Rodando localmente

```bash
npm install
npm run dev      # http://localhost:3000
```

Requer `api_service`, `agent_service` e `mcp_server` rodando para
funcionalidade completa.

Detalhes completos: [`apps/dashboard/README.md`](https://github.com/andrevberaldo/datathon-7mlet-grupo-68/blob/main/apps/dashboard/README.md).
