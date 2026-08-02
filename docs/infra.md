# Infraestrutura

Todos os serviços de infra estão disponíveis em dois targets: Docker Compose
(dev rápido, sem cluster) e Kubernetes via Helm/Helmfile (deploy completo).

| Serviço | Docker Compose | Kubernetes (NodePort) |
| --- | --- | --- |
| FastAPI | http://localhost:8001 | http://localhost:30800 |
| PostgreSQL | localhost:5432 | localhost:5432 (port-forward) |
| pgAdmin 4 | http://localhost:5050 | http://localhost:30050 |
| Redis | localhost:6379 | localhost:6379 (port-forward) |
| OpenSearch | https://localhost:9200 | https://localhost:9200 (port-forward) |
| OpenSearch Dashboards | http://localhost:5601 | http://localhost:30601 |
| Neo4j Browser | http://localhost:7474 | http://localhost:30474 |
| Neo4j Bolt | localhost:7687 | localhost:30687 |

## Docker Compose

```bash
cp .env.example .env
docker-compose up -d
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
