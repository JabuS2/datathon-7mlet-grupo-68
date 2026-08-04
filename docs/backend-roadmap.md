# Backend Roadmap — HP Invest / Plataforma MAB (Grupo 68)

Arquivo-guia da construção **incremental** do backend. Cada etapa (`Ex`) tem um objetivo, os
artefatos e um critério de "feito". Marque o checkbox ao concluir. Alinhado ao **catálogo real**
(`data/golden_set/offer_catalog.json` v2.0.0-prod): **LinUCB + reward binário** (clique).

> **Atualizações posteriores a este roadmap** (branch `feat/model-service-mlflow-datadog`):
> - **Reward composto removido.** Era `0.6·receita/vmax + 0.4·clique`, parametrizável por
>   `reward_definition`. Hoje é binário: `1.0` com clique/conversão, `0.0` sem. Saíram
>   `services/bandit/reward.py`, o campo `RewardRequest.value` e o `reward_definition` dos
>   `hyperparams` das políticas.
> - **UCB removido.** Restam três políticas: `baseline`, `thompson`, `linucb`.
> - **Bandit também vive fora do api_service:** o `model_service` serve `/rank` e `/update`
>   com estado em Redis e registry no MLflow. Hoje os dois coexistem — o in-process
>   (`services/bandit` + `services/decision`) atende `/decide`, `/showcase` e `/me/*`; o
>   model_service atende `/offers` e `/feedback`. Consolidar é decisão em aberto.
> - **Observabilidade:** logs JSON + Datadog (APM e coleta de logs) em `api_service` e
>   `model_service` — ver `docs/observability-datadog.md`.

Decisões de modelagem:

- `canal` → **enum** em `decisao` (não é tabela).
- `variante_mensagem` → **removida** (catálogo não tem variantes por canal).
- `estado_braco` → colunas **polimórficas** (thompson α/β · n_pulls/sum_reward · linucb A/b) para
  cobrir a Etapa 3 do PDF (referência a Thompson Sampling), mesmo com política ativa LinUCB.

Convenções: nomes de domínio em **português**; pacote raiz é `api_service/` (imports `from models...`,
`from schemas...`); reuso de `BaseModel`/`Base` (`models/base.py`), `BaseRepository`,
`UnitOfWork`, `BaseSchema`; enums `StrEnum` em `api_service/enums/`; JSON como `JSONB`; embeddings
no OpenSearch (fora do Postgres).

---

## Etapas

### E1 — Enums + modelos SQLAlchemy (todas as entidades) 🟢
- [x] Enums em `api_service/enums/` (catálogo, decisão, política, governança, usuário).
- [x] Models: `cliente`, `oferta`, `segmento`, `politica`, `estado_braco`, `decisao`,
      `evento_impressao`, `recompensa`, `caso_avaliacao`, `experimento`,
      `metrica_monitoramento`, `regra_adequacao`, `ciclo_retreino`, `aprovacao_humana`.
      (Assistente/RAG **removidos** — ver E9.)
- [x] `User` estendido (`tipo`, `cod_cliente`, `saldo_ficticio`).
- [x] `models/__init__.py` exporta tudo (para o autogenerate do Alembic).
- **Feito:** `import models` lista 17 tabelas; DDL Postgres compila (PK composta, FKs, 24 flags).

### E2 — Migração Alembic 🟢
- [x] `alembic revision --autogenerate` cobrindo todas as tabelas + colunas novas de `users`
      (`alembic/versions/13325b9a0f6e_domain_models_mab.py`).
- [x] Revisar PK composta de `estados_braco`, FKs, defaults de enum e `server_default` de `tipo`.
- **Feito:** `alembic upgrade head` cria as 17 tabelas no Postgres; autogenerate seguinte = `pass`
  (paridade model↔DB).

### E3 — Schemas Pydantic (contratos) + `docs/api-contracts.md` 🟢
- [x] Schemas entrada/saída: serving, catálogo/contexto, governança/MLOps, avaliação
      (`api_service/schemas/{oferta,segmento,cliente,decisao,politica,experimento,governanca,`
      `avaliacao}.py`).
- [x] `docs/api-contracts.md` com exemplo de request/response e tratamento de erro (Etapa 5 PDF).
- **Feito:** `tests/unit/test_contracts_roundtrip.py` — 19 contratos passam round-trip (snake→camel→re-parse).

### E4 — Repositórios + UnitOfWork 🟢
- [x] Um repositório por agregado (`repositories/*.py`, padrão `UserRepository`) com getters de
      domínio (PKs naturais/uuid/compostas não usam o `get_by_id` da base).
- [x] `UnitOfWork` com 17 propriedades lazy memoizadas; transação (commit/rollback) preservada.
- **Feito:** construção de todos os repos via `UnitOfWork` validada (lazy + cache).

### E5 — Loaders/seeds 🟢
- [x] Loaders puros (`services/catalog/loaders.py`, stdlib): catálogo (10 ofertas), segmentos (13
      distintos do golden set), clientes (2595, 24 flags) e golden set (tolerante se ausente).
- [x] Seeder idempotente (`services/seed/seeder.py`) + entrypoint `scripts/seed_db.py`
      (`--client-limit`); seed do subset de `cliente(origem='seed')`.
- [x] Seed das 4 políticas (baseline/thompson/ucb **shadow** + linucb **active**) com priors de
      `estado_braco` por braço (40 = 4×10).
- **Feito:** seed rodado ponta a ponta em Postgres (asyncpg) — idempotente (2ª run = 0 inserts);
  enums persistidos pelo **valor** do StrEnum via `models/columns.py::enum_column`
  (`baseline`/`active`/`seed`, casando com os contratos). Migração regenerada
  (`027c5f3f811e`), autogenerate seguinte limpo.

### E6 — Núcleo do bandit (`services/bandit`) 🟢
- [x] LinUCB portado do notebook (`policies.py`): θ=A⁻¹b, bônus α·√(xᵀA⁻¹x), α=fator·0.2,
      cold-start ridge λ·I; persiste `A`/`b`.
- [x] `baseline` (maior receita), `thompson` (Beta), `ucb` (UCB1), `linucb`; `eligibility.py`
      (convenções de sufixo), `context.py` (z-score + one-hot de 12 segmentos, percentil de renda),
      `reward.py` (composto), `engine.py` (decisão + `context` auditável LGPD).
- **Feito:** `tests/unit/test_bandit_core.py` (9 testes) — elegibilidade no golden set, dimensão do
      contexto (22), reward composto, cada política e o `decide` ponta a ponta; LinUCB aprende
      (pred sobe com reward). Numpy adicionado ao `pyproject.toml`. Cold-start OK; delayed reward
      modelado em `recompensa.status` (aplicado no serving E7).

### E7 — Endpoints de serving + log auditável 🟢
- [x] `services/decision/`: `runtime.py` (catálogo+stats em cache) e `service.py` (liga engine↔DB).
- [x] `/decide` (persiste `Decisao` + `EventoImpressao(impression)`), `/showcase` (ranking read-only),
      `/feedback` (evento click), `/reward` (reward composto → atualiza `EstadoBraco` + grava
      `Recompensa`). Registrados em `api/v1/routes.py`.
- **Feito:** e2e contra Postgres (decide→feedback→reward: LinUCB aprende, `n_pulls 0→1`, `A`
      atualizado; reward composto 0.559) + `tests/integration/.../test_serving.py` (4 testes) passam
      pelo request path FastAPI (camelCase, envelope de erro 404). Suite: 40/41 (a 1 falha é
      comportamento de versão do FastAPI p/ HTTPBearer no auth — fora do E7).

### E8 — RBAC + onboarding demo 🟢
- [x] RBAC: `require_role`/`require_operador` em `core/auth_dependencies.py` (funções de módulo
      componíveis; `get_current_user` refatorado; compat mantido em `AuthDependencies`).
- [x] Onboarding da vitrine (`services/demo/service.py` + `POST /onboarding`): perfil sintético por
      **template** (`ClienteRepository.pick_seed_template`), `origem='demo'`, faixa `cod ≥ 9.000.000`,
      conta `tipo='demo'` + token.
- **Feito:** `tests/unit/test_rbac.py` (3) + `tests/integration/.../test_demo.py` (2) —
      onboarding→decide (cold-start ao vivo) e e-mail duplicado (409). Suite 45/46 (a 1 falha é o
      HTTPBearer 401/403 do auth, fora do E8).

### E9 — Assistente + RAG ❌ fora de escopo (API separada)
O assistente LLM + RAG serão implementados em **outra API**. Removidos deste backend: models
`documento_politica`/`sessao_assistente`, seus repos, `schemas/assistente.py` e o enum
`TipoDocumentoPolitica`. A migração foi regenerada sem essas tabelas (`c77a8e237caf`, 15 tabelas).

### E10 — Governança/MLOps 🟢
- [x] `services/governance/service.py` + endpoints **operador-only** (`require_operador`):
      registrar política (`shadow`+priors), abrir ciclo (`candidate`), **approval gate** humano
      (`approve`→promove), promoção atômica (uma ativa por vez), **rollback** auditável,
      monitoramento (regret/conversão/reward/PSI drift + alerta).
- [x] Rastreio de experimentos = tabelas `experimento`/`ciclo_retreino`/`metrica_monitoramento`
      (equivalente ao MLflow; MLflow como alvo documentado).
- **Feito:** `tests/integration/.../test_governance.py` (4) — promoção via gate, rollback,
      alerta de drift e `demo→403`. Suite 49/50 (a 1 falha é o HTTPBearer 401/403 do auth).

### E12 — Self-service do usuário 🟢
- [x] `GET /me` enriquecido (`tipo`, `codCliente`, `saldoFicticio`); `GET /me/profile`
      (`ClienteResponse`); `GET /offers` / `GET /segments`.
- [x] Sugestões escopadas no **token**: `GET /me/recommendations`, `POST /me/decide` — sem passar
      `cod_cliente`. `POST /me/feedback` / `POST /me/reward` com **checagem de posse**
      (`403 NOT_DECISION_OWNER`). `GET /me/decisions` (histórico). `services/account/`.
- [x] Rotas cruas de serving mantidas como superfície interna/ops.
- **Feito:** `tests/integration/.../test_account.py` (4) — jornada loga→conta→perfil→sugestão→
      feedback/reward, posse entre usuários, `401` sem token, `409` operador sem perfil.
      **Suíte 53/53.**

### E11 — Testes + reprodução ponta a ponta 🟢
- [x] Suíte por bloco: `tests/unit` (contratos, bandit, RBAC) + `tests/integration` (serving, demo,
      governança, auth). **49 testes** (1 falha pré-existente: HTTPBearer 401/403 no auth).
- [x] Comando único de reprodução: `scripts/reproduce.py` (migração + seed + ciclo decisão
      auditável) e `scripts/seed_db.py`. `Makefile` corrigido (`make infra/migrate/seed/reproduce/
      api/test/lint`) apontando para o layout real `api_service/`.
- **Feito:** `python scripts/reproduce.py` roda migração→seed→decide/feedback/reward imprimindo
      braço, reason codes, versão da política e decision_id (evidência da Etapa 5).

---

## Hardening 🟢 (feito)
- [x] `SECRET_KEY`: rejeitado no boot se fraco/curto quando `ENVIRONMENT` ∈ {production, staging}
      (dev/test seguem com default). `settings.py` com validador.
- [x] `DATABASE_URL` com precedência sobre `POSTGRES_*` (app em `db/session.py`, Alembic em `env.py`).
- [x] Engine com `echo=SQLALCHEMY_ECHO` (default false) + `pool_pre_ping`.
- [x] CORS restrito (métodos/headers explícitos, sem `expose_headers=["*"]`).
- [x] Handler global de exceção agora **loga** stack trace.
- [x] `401` determinístico para credenciais ausentes (`HTTPBearer(auto_error=False)`) — independe da
      versão do FastAPI; teste `test_me_endpoint_unauthorized` ajustado. **Suíte 49/49.**
- [x] `Dockerfile.api`: usuário não-root + `poetry install --only main`. Removidos `Dockerfile.assistant`
      (vazio, RAG separado) e `Dockerfile.dashboard` (stale). `.env.example` atualizado.

**Pendente (opcional):** rate limiting / lockout em `/login` (precisa de Redis/slowapi) — antes do Demo Day.

Legenda: 🟢 feito · 🟡 em andamento · 🔴 pendente.
