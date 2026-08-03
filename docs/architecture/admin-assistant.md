# Arquitetura do Admin Assistant

Um assistente voltado a administradores: admins conversam em um frontend
CopilotKit (AG-UI), um **deep agent** LangChain decide o que fazer, e um
**MCP server em JavaScript** expõe tools e widgets de dashboard (`mcpApp`).
A principal função do assistente é **renderizar dashboards**, chamando tools
MCP que retornam recursos MCP-UI, os quais o CopilotKit renderiza inline.

## Componentes

| Serviço          | Stack                         | Porta | Responsabilidade                                                   |
| ---------------- | ------------------------------ | ----- | ------------------------------------------------------------------ |
| `apps/dashboard`  | Next.js + CopilotKit (AG-UI)   | 3000  | Login do admin, UI de chat, renderiza widgets MCP-UI                |
| `agent_service`   | Python, deepagents + AG-UI     | 8100  | Deep agent (OpenAI), serve o endpoint AG-UI, carrega tools MCP      |
| `mcp_server`      | Node/TypeScript, MCP + mcp-ui  | 8200  | Expõe tools + widgets `mcpApp`, faz proxy dos dados administrativos |
| `api_service`     | FastAPI + Postgres              | 8000/8001 | Autenticação (JWT), dados administrativos (`/admin/users/overview`) |

## Fluxo de uma requisição

```
Navegador do admin (provider CopilotKit, JWT admin)
  │  POST /api/copilotkit  (rota Next.js: CopilotRuntime + AG-UI HttpAgent)
  ▼
agent_service  ── AdminAuthMiddleware valida o JWT admin (SECRET_KEY compartilhado)
  │  Deep agent LangChain (modelo OpenAI)
  │  Cliente MCP (langchain-mcp-adapters, streamable HTTP)
  ▼
mcp_server  ── tool get_users_overview
  │  encaminha o Authorization ▼
api_service  GET /api/v1/admin/users/overview  (guard get_current_admin)
  ▲  JSON de KPIs
mcp_server  ── constrói o recurso MCP-UI (widget HTML autocontido) + JSON
  ▲
agent_service ── transmite o resultado da tool via AG-UI
  ▲
dashboard  ── useCopilotAction("get_users_overview") → <UIResourceRenderer>
```

## Autenticação e autorização

- **api_service** emite os JWTs (`/login`) e expõe `is_admin` em `/me`. As
  rotas `/admin/*` exigem `get_current_admin` (403 para não-admins).
- **dashboard** guarda o JWT (localStorage), só deixa admins entrarem, e
  encaminha o JWT para `/api/copilotkit`, que o repassa ao `agent_service`.
- **agent_service** valida a assinatura/expiração do JWT na borda
  (`SECRET_KEY`/`ALGORITHM` compartilhados com o api_service).
- **Acesso a dados downstream:** o agent encaminha `DOWNSTREAM_API_TOKEN`
  para o MCP server, que o repassa ao api_service; a autorização de admin é
  aplicada lá. O encaminhamento completo do token por usuário, ponta a
  ponta, é uma melhoria planejada.

## Widgets (`mcpApp`)

As tools MCP retornam um **recurso MCP-UI** construído com `@mcp-ui/server`
(`createUIResource`, `ui://mcp-server/<widget>`). Os dados são embutidos no
HTML para que o iframe sandboxed seja autocontido. O frontend renderiza com
o `UIResourceRenderer` do `@mcp-ui/client`. Novos widgets vão em
`mcp_server/src/widgets/` e são registrados em `registry.ts`.

## Rodando localmente

Cada serviço tem seu próprio README. Com Docker Compose (perfis opt-in):

```bash
cp .env.example .env    # definir OPENAI_API_KEY, DOWNSTREAM_API_TOKEN, SECRET_KEY
docker compose --profile api --profile app up --build
```

- Dashboard: http://localhost:3000
- Agent AG-UI: http://localhost:8100
- MCP server: http://localhost:8200/mcp
- API: http://localhost:8001

Ou rode cada serviço diretamente (veja `apps/dashboard/README.md`,
`agent_service/README.md`, `mcp_server/README.md`, `api_service/README.md`).
