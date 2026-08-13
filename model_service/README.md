# Model Service

Serviço de modelos (Multi-Armed Bandit) para recomendação de ofertas financeiras.
Espelha as convenções do `api_service/` (FastAPI + Poetry + Python 3.12).

## Responsabilidades

- **Modelos** (`models/`): `LinUCB` (contextual, produção Sherman-Morrison),
  `ThompsonSampling` (Beta(1,1)) e `DeterministicBaseline` (regras de negócio).
- **Contexto** (`models/context.py`): vetor bias + numéricos z-standardizados + one-hots
  de segmento (D=22). `mu`/`sd` persistidos no estado (senão o scoring fica errado).
- **Catálogo** (`catalog/loader.py`): carrega `offer_catalog.json`, calcula elegibilidade
  (`santander_filters`) e estatísticas de normalização do `golden_clients.csv`.
- **Estado** (`store/state_store.py`): estado dos bandits em Redis, com lock por modelo
  para serializar o read-modify-write do update.
- **Registry** (`registry/mlflow_registry.py`): versiona/registra os modelos no MLflow.

**Reward = click (0/1)** — simples, sem fórmula composta.

## Endpoints (`/api/v1`)

| Método | Rota | Descrição |
|---|---|---|
| `GET`  | `/health` | Health check. |
| `POST` | `/rank`   | Ranqueia ofertas elegíveis para um cliente/contexto. |
| `POST` | `/update` | Aplica feedback (reward=click) e persiste o novo estado. |
| `GET`  | `/registry/models` | Lista modelos registrados no MLflow. |
| `POST` | `/registry/models` | Cria/registra uma versão do modelo (snapshot atual). |
| `DELETE` | `/registry/models/{name}` | Remove um modelo registrado. |

O loop de aprendizado é **compute-on-read**: `POST /update` muta o estado no Redis; o
próximo `POST /rank` já reflete o aprendizado. LinUCB é um modelo **global contextual**
(parâmetros por braço, contexto do usuário no scoring) — não há modelo por usuário.

## Rodando

```bash
# via docker-compose (recomendado — sobe redis + mlflow + model)
docker-compose --profile api up -d model

# local (a partir da raiz do repo, para resolver data/golden_set/*)
cd model_service && poetry install
CATALOG_PATH=../data/golden_set/offer_catalog.json \
CLIENTS_CSV_PATH=../data/golden_set/golden_clients.csv \
poetry run uvicorn main:app --port 8002
```

## Testes

```bash
cd model_service && poetry run pytest
```
