# agent_service

Serviço Python que roda um **LangChain deep agent** e o expõe via protocolo
**AG-UI** para o dashboard (CopilotKit). Carrega tools e widgets do
`mcp_server` e é apoiado por um modelo OpenAI.

```
dashboard (CopilotKit / AG-UI)
   └─ POST /  (eventos AG-UI)  ──► agent_service
        ├─ AdminAuthMiddleware   valida o JWT admin (segredo compartilhado com api_service)
        └─ deep agent (OpenAI)
             └─ MCP tools (langchain-mcp-adapters) ──► mcp_server ──► api_service
```

## Rodando localmente

```bash
poetry install
uvicorn agent_service.app:app --host 0.0.0.0 --port 8100
```

Requer `mcp_server` acessível em `MCP_SERVER_URL` na inicialização (tools são
carregadas no startup).

Configuração completa das variáveis de ambiente:
[`agent_service/README.md`](https://github.com/andrevberaldo/datathon-7mlet-grupo-68/blob/main/agent_service/README.md).
