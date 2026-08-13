# Infraestrutura

Todos os serviços de infra estão disponíveis em dois targets: Docker Compose
(dev rápido, sem cluster) e Kubernetes via Helm/Helmfile (deploy completo).

| Serviço | Docker Compose | Kubernetes (NodePort) |
| --- | --- | --- |
| api_service (FastAPI) | http://localhost:8001 | http://localhost:30800 |
| MLflow | http://localhost:5000 | — (sem chart) |
| front_service (Angular) | http://localhost:4200 | — (sem chart) |
| dashboard (Next) | http://localhost:3000 | — (sem chart) |
| agent_service | http://localhost:8100 | — (sem chart) |
| mcp_server | http://localhost:8200 | — (sem chart) |
| PostgreSQL | localhost:5432 | localhost:5432 (port-forward) |
| pgAdmin 4 | http://localhost:5050 | http://localhost:30050 |
| Redis | localhost:6379 | localhost:6379 (port-forward) |
| Datadog Agent (APM) | localhost:8126 | — (sem chart) |

> **OpenSearch e Neo4j não estão provisionados.** Sobraram variáveis em
> `.env.example`/`api_service/settings.py` e exemplos de secret em
> `infra/k8s/secrets/` de um desenho anterior (RAG + grafo). Nenhum serviço do
> compose ou do código usa esses valores hoje.
>
> **O Helm chart só cobre o `api_service`.** Os demais serviços rodam apenas via compose.

## Docker Compose

```bash
cp .env.example .env

# stack de backend (api + model + postgres + redis + mlflow)
docker-compose --profile api up -d

# + assistente administrativo (dashboard, agent_service, mcp_server)
docker-compose --profile app up -d

# + coleta Datadog (requer DD_API_KEY no .env)
docker-compose --profile api --profile datadog up -d
```

## Kubernetes (Helm + Helmfile)

```bash
kubectl apply -f infra/k8s/namespace.yaml
# criar secrets a partir dos .example em infra/k8s/secrets/
cd infra/k8s
helmfile apply
```

Setup completo (secrets, build de imagem local, port-forward, teardown):
[`infra/k8s/README.md`](https://github.com/andrevberaldo/datathon-7mlet-grupo-68/blob/main/infra/k8s/README.md).
