# model_service

FastAPI + Redis + MLflow + Postgres. Serve os **multi-armed bandits** (ranqueia ofertas,
aplica recompensa) e é dono do **ciclo de vida das políticas**. O estado aprendido vive no
Redis, os snapshots versionados no MLflow, e a governança num **banco próprio**.

Três algoritmos: `linucb` (default), `thompson` e `baseline`.

## Estado é escopado por política

A chave do Redis é `bandit:state:{policy_id}`, não `{algorithm}`. É o que permite duas
versões do mesmo algoritmo coexistirem — uma `active`, outra `shadow` — com pesos
independentes. Consequência: **promover não copia estado e o rollback recupera intacto**,
porque a chave da política anterior nunca foi tocada. Por isso não existe tabela
`estados_braco`: materializar os pesos em Postgres criaria uma segunda cópia divergindo a
cada `/update`. `GET /policies/{id}/arms` projeta os pesos do estado.

Qual política atende uma requisição, nesta ordem: o `policy_id` do corpo → a política
`active` → a política implícita `auto-{algorithm}`, que preserva o comportamento de quem
chama só com `algorithm` (é o caso do api_service hoje).

## Endpoints

| Método | Rota | O que faz |
|---|---|---|
| `GET` | `/api/v1/health` | liveness |
| `POST` | `/api/v1/rank` | ranqueia as ofertas elegíveis para o contexto do cliente |
| `POST` | `/api/v1/update` | aplica a recompensa (0/1) ao braço e persiste o estado |
| `POST` | `/api/v1/policies` | registra política (nasce `shadow`) |
| `GET` | `/api/v1/policies` | lista políticas |
| `GET` | `/api/v1/policies/{id}/arms` | pesos por braço, projetados do estado |
| `POST` | `/api/v1/policies/{id}/promote` | promoção atômica (uma `active` por vez) |
| `POST` | `/api/v1/retrain-cycles` | abre ciclo (`candidate`) |
| `GET` | `/api/v1/retrain-cycles` | lista ciclos |
| `POST` | `/api/v1/retrain-cycles/{run_id}/rollback` | volta para outra política |
| `POST` | `/api/v1/approvals` | approval gate humano (`approve` promove) |
| `POST` | `/api/v1/metrics` | recebe métrica calculada pelo api_service |
| `GET` | `/api/v1/metrics` | lista métricas (`?policy_id=&alerts_only=`) |
| `GET` | `/api/v1/registry/models` | lista as versões registradas no MLflow |
| `POST` | `/api/v1/registry/models` | snapshot do estado atual → nova versão |
| `POST` | `/api/v1/registry/models/{name}/load` | restaura um snapshot para o estado ativo |
| `DELETE` | `/api/v1/registry/models/{name}` | remove um modelo registrado |

`POST /rank` recebe `{ algorithm?, policy_id?, client, segments, top?, exclude_arm_ids? }` e
devolve `{ algorithm, policy_id, ranked[] }`, já filtrado por elegibilidade. `POST /update`
recebe `{ algorithm?, policy_id?, arm_id, reward, client, segments }` — `reward` é binário.

## O que **não** está aqui

**O cálculo das métricas.** Regret, conversão e PSI derivam de `decisao`/`recompensa`, que
ficam no api_service. Ele calcula e publica em `POST /metrics`; aqui só guardamos o valor
para exibir ao lado da política que ele justificou.

**Autorização.** O approval gate recebe `user_id` como parâmetro — quem valida o JWT e checa
o papel de operador é o api_service. Expor este serviço fora da rede interna exigiria
autenticação própria.

## Quem consome

O `api_service` chama via `services/model_client.py`, que serve `GET /offers` e `POST /feedback`.
A URL vem de `MODEL_SERVICE_URL` (no compose, `http://model:8000`).

## Rodando localmente

```bash
cd model_service
cp .env.example .env
poetry install
poetry run alembic upgrade head     # banco de governança
poetry run uvicorn main:app --port 8002
```

Precisa de Redis e Postgres no ar (`docker-compose up -d redis postgres`) e, para o
registry, de um MLflow em `MLFLOW_TRACKING_URI`. Pelo compose:
`docker-compose --profile api up -d model` — o entrypoint espera o banco, migra e sobe.

### Banco separado, de propósito

O model_service usa o database `model_service` na **mesma instância** Postgres do
api_service, não o mesmo database. Duas cadeias Alembic no mesmo database disputariam a
tabela `alembic_version`: a segunda a rodar `upgrade head` encontraria uma revisão que não
conhece. O database é criado por `infra/docker/initdb/01-model-service-db.sh` na primeira
subida do volume; num volume que já existe, crie à mão:

```bash
docker compose exec postgres createdb -U "$POSTGRES_USER" model_service
```

`aprovacoes_humanas.user_id` referencia `users.id` do api_service **sem FK** — bancos
diferentes. O id chega do JWT já validado na borda.

## Catálogo

Lê o mesmo `offer_catalog.json` e `golden_clients.csv` do `api_service` (`CATALOG_PATH` e
`CLIENTS_CSV_PATH`), então as features de contexto e as regras de elegibilidade são idênticas
nos dois serviços.
