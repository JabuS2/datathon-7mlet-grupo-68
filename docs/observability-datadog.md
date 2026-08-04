# Conectar ao Datadog

Como ligar a observabilidade (logs + APM) dos serviços `api` e `model` ao Datadog.

O Datadog é **opcional** e fica atrás do profile `datadog` no compose — os itens 1–6 do
projeto rodam sem ele. Ligue quando quiser logs/traces.

## Pré-requisitos

- Uma conta Datadog e uma **API key** (Organization Settings → API Keys).
- O **site** da sua org (`DD_SITE`): normalmente `datadoghq.com` (US1) ou `datadoghq.eu` (EU).
- A stack já buildada (`docker-compose --profile api up -d --build`).

## 1. Configurar a key no `.env`

No arquivo `.env` (na raiz do repo, **gitignored** — nunca commite a key):

```dotenv
DD_API_KEY=<sua_api_key>
DD_SITE=datadoghq.com     # ou datadoghq.eu
DD_ENV=dev
DD_TRACE_ENABLED=true     # liga o tracing (APM) nas apps
```

## 2. Subir com o profile `datadog`

```bash
docker-compose --profile api --profile datadog up -d
```

Isso sobe o **`datadog-agent`** e recria `api`/`model` com `DD_TRACE_ENABLED=true`.
O agent:
- coleta os **logs** de todos os containers via socket do Docker (inclui os logs JSON
  estruturados das apps);
- recebe os **traces** APM enviados pelo `ddtrace` das apps (porta 8126).

## 3. Verificar

Gere tráfego (ou rode `pwsh scripts/smoke_e2e.ps1`):

```bash
curl -s -X POST localhost:8001/api/v1/register -H "Content-Type: application/json" \
  -d '{"email":"a@b.com","password":"password123"}'
TOKEN=$(curl -s -X POST localhost:8001/api/v1/login -H "Content-Type: application/json" \
  -d '{"email":"a@b.com","password":"password123"}' | python -c "import sys,json;print(json.load(sys.stdin)['accessToken'])")
curl -s localhost:8001/api/v1/offers -H "Authorization: Bearer $TOKEN"
curl -s -X POST localhost:8001/api/v1/feedback -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" -d '{"armId":"OFF-CR-001","clicked":true}'
```

Checagens:
- **Agent conectado**: `docker-compose exec datadog-agent agent status` → em *API Keys status*
  deve constar `API key ending with ...: API Key valid`, e a seção *Logs Agent* ativa.
- **Logs no Datadog**: **Logs → Log Explorer**, filtre `service:api` ou `service:model`.
  Eventos esperados: `user_registered`, `user_logged_in`, `offers_listed`,
  `feedback_submitted`, `bandit_update`, e `unhandled_exception` (com stacktrace) em erros.
- **Traces**: **APM → Traces**, correlacionados aos logs via `dd.trace_id`.

## Como funciona (resumo técnico)

- **Logs estruturados**: `api_service/logging_config.py` e `model_service/logging_config.py`
  emitem uma linha JSON por log, com os campos extras de cada ação. O agent coleta o stdout
  dos containers (label `com.datadoghq.ad.logs` nos serviços `api`/`model`).
- **Toda ação logada**: auth (`user_registered`/`user_logged_in`), ofertas (`offers_listed`),
  feedback (`feedback_submitted`), modelo (`bandit_update`, `model_registered`), além do
  handler global de exceção.
- **Tracing (APM)**: as apps sobem com `ddtrace-run uvicorn ...`. Com `DD_TRACE_ENABLED=true`
  e `DD_AGENT_HOST=datadog-agent`, os spans vão para o agent; sem isso (default), o `ddtrace`
  não conecta e não há impacto.

## Desligar

```bash
# tudo, incluindo o agent:
docker-compose --profile api --profile datadog down
# ou suba sem o profile `datadog` para rodar SEM o agent
```

> Nota (Docker Desktop / Windows): o serviço `datadog-agent` monta apenas o socket do
> Docker (`/var/run/docker.sock`) — suficiente para coleta de logs. Os mounts de métricas
> de host (`/proc`, `/sys/fs/cgroup`) ficam comentados no compose (só para host Linux).
