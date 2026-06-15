# Kubernetes Infrastructure — datathon-7mlet-grupo-68

All infrastructure services are available in **two deployment targets**:

| Target | Command | Use case |
|---|---|---|
| Docker Compose | `docker-compose up` | Fast local dev, no cluster needed |
| Kubernetes | `helmfile apply` | Full cluster deployment |

---

## Services & Access URLs

| Service | Docker Compose | Kubernetes (NodePort) |
|---|---|---|
| FastAPI | http://localhost:8001 | http://localhost:30800 |
| PostgreSQL | localhost:5432 | localhost:5432 (via port-forward) |
| pgAdmin 4 | http://localhost:5050 | http://localhost:30050 |
| Redis | localhost:6379 | localhost:6379 (via port-forward) |
| OpenSearch | https://localhost:9200 | https://localhost:9200 (via port-forward) |
| OpenSearch Dashboards | http://localhost:5601 | http://localhost:30601 |
| Neo4j Browser | http://localhost:7474 | http://localhost:30474 |
| Neo4j Bolt | localhost:7687 | localhost:30687 |

---

## Prerequisites (Kubernetes)

- [kubectl](https://kubernetes.io/docs/tasks/tools/)
- [Helm 3](https://helm.sh/docs/intro/install/)
- [Helmfile](https://helmfile.readthedocs.io/en/latest/#installation)
- A local cluster: [minikube](https://minikube.sigs.k8s.io/docs/start/), [kind](https://kind.sigs.k8s.io/), or Docker Desktop with Kubernetes enabled

---

## Kubernetes Setup

### 1. Create the namespace

```bash
kubectl apply -f infra/k8s/namespace.yaml
```

### 2. Create secrets

Copy each `.example` file, fill in real values, then apply:

```bash
cd infra/k8s/secrets

cp postgres.secrets.yaml.example postgres.secrets.yaml
cp redis.secrets.yaml.example redis.secrets.yaml
cp opensearch.secrets.yaml.example opensearch.secrets.yaml
cp neo4j.secrets.yaml.example neo4j.secrets.yaml
cp app.secrets.yaml.example app.secrets.yaml

# Edit each file with real credentials, then:
kubectl apply -f infra/k8s/secrets/postgres.secrets.yaml
kubectl apply -f infra/k8s/secrets/redis.secrets.yaml
kubectl apply -f infra/k8s/secrets/opensearch.secrets.yaml
kubectl apply -f infra/k8s/secrets/neo4j.secrets.yaml
kubectl apply -f infra/k8s/secrets/app.secrets.yaml
```

> ⚠️ Real secret files are gitignored. Never commit them.

### 3. Build the API image into the local cluster

**minikube:**
```bash
eval $(minikube docker-env)   # point Docker CLI at minikube's daemon
docker build -t datathon-mab-api:latest -f infra/docker/Dockerfile.api .
```

**kind:**
```bash
docker build -t datathon-mab-api:latest -f infra/docker/Dockerfile.api .
kind load docker-image datathon-mab-api:latest
```

**Docker Desktop:** just build normally — the image is already in the local registry.

### 4. Deploy everything

```bash
cd infra/k8s
helmfile apply
```

To deploy only one release:
```bash
helmfile apply --selector name=datathon-postgresql
```

### 5. Verify

```bash
kubectl get pods -n datathon
kubectl get services -n datathon
```

---

## Port-forwarding (for ClusterIP services)

```bash
# PostgreSQL
kubectl port-forward -n datathon svc/datathon-postgresql 5432:5432

# Redis
kubectl port-forward -n datathon svc/datathon-redis-master 6379:6379

# OpenSearch
kubectl port-forward -n datathon svc/datathon-opensearch-master 9200:9200
```

---

## Docker Compose Setup

```bash
cp .env.example .env
# Edit .env with real credentials

docker-compose up -d
```

---

## Tearing Down

```bash
# Kubernetes
cd infra/k8s && helmfile destroy

# Docker Compose
docker-compose down -v   # -v removes volumes
```

---

## File Structure

```
infra/k8s/
├── namespace.yaml                 # datathon namespace
├── helmfile.yaml                  # orchestrates all Helm releases
├── secrets/
│   ├── .gitignore                 # ignores real secret YAMLs
│   ├── postgres.secrets.yaml.example
│   ├── redis.secrets.yaml.example
│   ├── opensearch.secrets.yaml.example
│   ├── neo4j.secrets.yaml.example
│   └── app.secrets.yaml.example
├── values/
│   ├── postgres.values.yaml
│   ├── pgadmin.values.yaml
│   ├── redis.values.yaml
│   ├── opensearch.values.yaml
│   ├── opensearch-dashboards.values.yaml
│   └── neo4j.values.yaml
└── charts/
    └── api/                       # custom Helm chart for FastAPI
        ├── Chart.yaml
        ├── values.yaml
        └── templates/
            ├── _helpers.tpl
            ├── configmap.yaml
            ├── deployment.yaml
            ├── service.yaml
            └── ingress.yaml       # disabled by default
```
