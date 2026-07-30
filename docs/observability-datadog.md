# Observabilidade com Datadog

Este guia mostra como criar uma conta gratuita no Datadog e vincular os containers
(`api`, `model` e demais) para **coletar os logs** e traces da aplicação.

Os itens 1–6 do projeto **não dependem** do Datadog — ele é opcional e fica atrás do
profile `datadog` no compose. Ligue-o quando quiser observabilidade.

---

## 1. Criar a conta gratuita

Escolha **uma** das opções:

### Opção A — Free trial / conta gratuita
1. Acesse <https://www.datadoghq.com/> e clique em **Get Started Free**.
2. Cadastre-se (e-mail ou Google/GitHub). O trial é gratuito por 14 dias e há um
   plano free contínuo para métricas/infra básica.
3. Ao final do onboarding, escolha o método **Docker** (não precisa instalar nada
   agora — vamos usar o agent via docker-compose).

### Opção B — GitHub Student Developer Pack (recomendado p/ estudante)
1. Garanta o **GitHub Student Developer Pack**: <https://education.github.com/pack>
   (requer e-mail acadêmico ou comprovante).
2. No pack, procure por **Datadog** → **Get access**. Estudantes recebem o plano
   **Pro grátis por 2 anos**.
3. Isso cria/associa sua conta Datadog automaticamente.

> Ao criar a conta, anote o **site** da sua org (canto da URL): normalmente
> `datadoghq.com` (US1) ou `datadoghq.eu` (EU). Você vai precisar dele em `DD_SITE`.

## 2. Gerar a API Key

1. No Datadog: **Organization Settings → API Keys** (ou
   <https://app.datadoghq.com/organization-settings/api-keys>).
2. Clique **New Key**, dê um nome (ex.: `datathon-local`) e **copie** o valor.

## 3. Configurar o `.env`

No arquivo `.env` (copie de `.env.example` se ainda não existe):

```dotenv
DD_API_KEY=<sua_api_key_aqui>
DD_SITE=datadoghq.com        # ou datadoghq.eu conforme sua org
DD_ENV=dev
DD_TRACE_ENABLED=true        # liga o tracing (APM) nas apps
```

## 4. Subir a stack com o Datadog

```bash
docker-compose --profile api --profile datadog up -d --build
```

Isso sobe a infra + `api` + `model` + `mlflow` + o **`datadog-agent`**. O agent:
- coleta os **logs** de todos os containers (via socket do Docker), incluindo os logs
  JSON estruturados das apps;
- recebe os **traces** APM enviados pelo `ddtrace` (porta 8126).

## 5. Gerar tráfego e ver os logs

```bash
# registra, loga e navega para gerar logs de ação
curl -s -X POST localhost:8001/api/v1/register -H "Content-Type: application/json" \
  -d '{"email":"a@b.com","password":"password123"}'
TOKEN=$(curl -s -X POST localhost:8001/api/v1/login -H "Content-Type: application/json" \
  -d '{"email":"a@b.com","password":"password123"}' | python -c "import sys,json;print(json.load(sys.stdin)['accessToken'])")
curl -s localhost:8001/api/v1/offers -H "Authorization: Bearer $TOKEN"
curl -s -X POST localhost:8001/api/v1/feedback -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" -d '{"armId":"OFF-CR-001","clicked":true}'
```

No Datadog:
- **Logs → Log Explorer**: filtre por `service:api` ou `service:model`. Você verá
  eventos como `user_registered`, `user_logged_in`, `offers_listed`,
  `feedback_submitted`, `bandit_update`.
- **APM → Traces**: os traces das requisições, correlacionados aos logs via
  `dd.trace_id` (injetado pelo `ddtrace` com `DD_LOGS_INJECTION=true`).

---

## Como funciona (resumo técnico)

- **Logs estruturados**: `api_service/logging_config.py` e
  `model_service/logging_config.py` configuram um `JsonFormatter` que emite uma linha
  JSON por log, com os campos extras de cada ação. O agent coleta o stdout dos
  containers (label `com.datadoghq.ad.logs`).
- **Toda ação logada**: auth (`user_registered`/`user_logged_in`), ofertas
  (`offers_listed`), feedback (`feedback_submitted`), modelo (`bandit_update`),
  além do handler global de exceção (`unhandled_exception` com stacktrace).
- **Tracing (APM)**: as apps sobem com `ddtrace-run uvicorn ...`. Com
  `DD_TRACE_ENABLED=true` e `DD_AGENT_HOST=datadog-agent`, os spans vão para o agent.
  Sem isso (default), o `ddtrace` não conecta e não há impacto.

## Desligar

```bash
docker-compose --profile api --profile datadog down
```
Ou rode sem o profile `datadog` para subir tudo **sem** o agent.
