# model_service

FastAPI + Redis + MLflow. Serve os **multi-armed bandits**: ranqueia as ofertas de um cliente
e aplica a recompensa observada. Não tem banco relacional — o estado aprendido vive no Redis e
os snapshots versionados no MLflow.

Três algoritmos: `linucb` (default), `thompson` e `baseline`.

## Endpoints

| Método | Rota | O que faz |
|---|---|---|
| `GET` | `/api/v1/health` | liveness |
| `POST` | `/api/v1/rank` | ranqueia as ofertas elegíveis para o contexto do cliente |
| `POST` | `/api/v1/update` | aplica a recompensa (0/1) ao braço e persiste o estado |
| `GET` | `/api/v1/registry/models` | lista as versões registradas no MLflow |
| `POST` | `/api/v1/registry/models` | snapshot do estado atual → nova versão |
| `POST` | `/api/v1/registry/models/{name}/load` | restaura um snapshot para o estado ativo |
| `DELETE` | `/api/v1/registry/models/{name}` | remove um modelo registrado |

`POST /rank` recebe `{ algorithm?, client, segments, top?, exclude_arm_ids? }` e devolve
`{ algorithm, ranked[] }`, já filtrado por elegibilidade. `POST /update` recebe
`{ algorithm?, arm_id, reward, client, segments }` — `reward` é binário.

## Quem consome

O `api_service` chama via `services/model_client.py`, que serve `GET /offers` e `POST /feedback`.
A URL vem de `MODEL_SERVICE_URL` (no compose, `http://model:8000`).

## Rodando localmente

```bash
cd model_service
cp .env.example .env
poetry install
poetry run uvicorn main:app --port 8002
```

Precisa de Redis no ar (`docker-compose up -d redis`) e, para o registry, de um MLflow em
`MLFLOW_TRACKING_URI`. Pelo compose: `docker-compose --profile api up -d model`.

## Catálogo

Lê o mesmo `offer_catalog.json` e `golden_clients.csv` do `api_service` (`CATALOG_PATH` e
`CLIENTS_CSV_PATH`), então as features de contexto e as regras de elegibilidade são idênticas
nos dois serviços.
