# Datathon 7MLET — Grupo 68

Plataforma de experimentação adaptativa com Multi-Armed Bandit para recomendação de produtos financeiros.

**Dataset:** Santander Product Recommendation (Kaggle)  
**Algoritmos:** LinUCB contextual (ativo) · Thompson Sampling · Baseline determinístico  
**Recompensa:** binária (clique/conversão)  
**Frontends:** HP Invest / `front_service` (cliente final) · `apps/dashboard` (assistente admin)  
**Assistente:** agente LangChain + MCP (`agent_service` + `mcp_server`)

---

## Infraestrutura

A infraestrutura inclui PostgreSQL, Redis, OpenSearch e Neo4j, disponíveis em dois targets:

| Serviço | Docker Compose | Kubernetes (NodePort) |
|---|---|---|
| FastAPI | http://localhost:8001 | http://localhost:30800 |
| pgAdmin 4 | http://localhost:5050 | http://localhost:30050 |
| OpenSearch Dashboards | http://localhost:5601 | http://localhost:30601 |
| Neo4j Browser | http://localhost:7474 | http://localhost:30474 |
| Neo4j Bolt | localhost:7687 | localhost:30687 |
| PostgreSQL | localhost:5432 | port-forward (ver abaixo) |
| Redis | localhost:6379 | port-forward (ver abaixo) |
| OpenSearch | https://localhost:9200 | port-forward (ver abaixo) |

### Docker Compose

**Pré-requisitos:** Docker + Docker Compose

```bash
cp .env.example .env   # preencher credenciais
```

```bash
# Apenas infra (rodar a API localmente com make api ou uvicorn):
docker-compose up -d

# Infra + API no Docker:
docker-compose --profile api up -d

# Parar tudo:
docker-compose down

# Parar e remover volumes:
docker-compose down -v
```

### Kubernetes (Helm + Helmfile)

**Pré-requisitos:** kubectl · Helm 3 · [Helmfile](https://helmfile.readthedocs.io/en/latest/#installation) · cluster local (minikube / kind / Docker Desktop)

#### 1. Criar namespace

```bash
kubectl apply -f infra/k8s/namespace.yaml
```

#### 2. Criar os Secrets

```bash
cd infra/k8s/secrets

# Copiar e preencher cada arquivo com as credenciais reais
cp postgres.secrets.yaml.example   postgres.secrets.yaml
cp redis.secrets.yaml.example      redis.secrets.yaml
cp opensearch.secrets.yaml.example opensearch.secrets.yaml
cp neo4j.secrets.yaml.example      neo4j.secrets.yaml
cp app.secrets.yaml.example        app.secrets.yaml

kubectl apply -f postgres.secrets.yaml \
              -f redis.secrets.yaml \
              -f opensearch.secrets.yaml \
              -f neo4j.secrets.yaml \
              -f app.secrets.yaml
```

> ⚠️ Os arquivos de secret reais são ignorados pelo git. Nunca os commite.

#### 3. Build da imagem da API no cluster local

```bash
# minikube
eval $(minikube docker-env)
docker build -t datathon-mab-api:latest -f infra/docker/Dockerfile.api .

# kind
docker build -t datathon-mab-api:latest -f infra/docker/Dockerfile.api .
kind load docker-image datathon-mab-api:latest

# Docker Desktop — build normal, imagem já está no registry local
docker build -t datathon-mab-api:latest -f infra/docker/Dockerfile.api .
```

#### 4. Deploy

```bash
cd infra/k8s
helmfile apply              # sobe todos os serviços
helmfile apply --selector name=datathon-postgresql   # ou somente um
```

#### 5. Verificar

```bash
kubectl get pods     -n datathon
kubectl get services -n datathon
```

#### Port-forward (serviços ClusterIP)

```bash
kubectl port-forward -n datathon svc/datathon-postgresql     5432:5432
kubectl port-forward -n datathon svc/datathon-redis-master   6379:6379
kubectl port-forward -n datathon svc/datathon-opensearch-master 9200:9200
```

#### Teardown

```bash
cd infra/k8s && helmfile destroy
```

> Documentação completa do Kubernetes em [`infra/k8s/README.md`](infra/k8s/README.md).

---

## Execução local

```bash
cp .env.example .env        # configurar variáveis
pip install -e ".[dev]"     # instalar dependências
make api                    # subir API na porta 8000
make dashboard              # subir Streamlit
make simulate               # rodar simulação MAB
make evaluate               # avaliar com golden set
make test                   # rodar testes
```

## Arquitetura

O `api_service` segue camadas: `api/` (FastAPI) → `services/` (regra de negócio) →
`repositories/` + `models/` (persistência), com `UnitOfWork` controlando a transação.
A regra central: nada em `services/` importa FastAPI.

O bandit existe hoje em **dois lugares** — o in-process (`services/bandit` + `services/decision`,
estado na tabela `estados_braco`) que atende `/decide`, `/showcase` e `/me/*`, e o
`model_service` (Redis + MLflow) que atende `/offers` e `/feedback`. Consolidar os dois é
decisão em aberto; ver `docs/backend-roadmap.md`.

## Mapa de pastas

```
datathon-7mlet-grupo-68/
│
├── api_service/                    # esta API (FastAPI + Postgres)
│   ├── api/v1/endpoints/           # auth, offers, feedback, serving, account,
│   │                               # catalog, governance, admin, demo, health
│   ├── services/
│   │   ├── bandit/                 # políticas (linucb/thompson/baseline), contexto,
│   │   │                           # elegibilidade, engine
│   │   ├── decision/               # serving: liga o engine ao banco + log auditável
│   │   ├── governance/             # políticas, ciclos de retreino, aprovações, métricas
│   │   ├── offer/                  # ofertas/feedback via model_service
│   │   ├── account/ demo/ dashboard/ catalog/ seed/
│   │   └── model_client.py         # cliente HTTP do model_service
│   ├── models/ repositories/ schemas/ enums/
│   ├── alembic/                    # migrações
│   └── tests/                      # unit / integration / e2e
│
├── model_service/                  # bandits: /rank, /update, registry MLflow
│   ├── models/                     # linucb, thompson, baseline, context
│   ├── store/                      # StateStore (Redis)
│   └── registry/                   # MLflow model registry
│
├── front_service/                  # portal do cliente (Angular)
├── apps/dashboard/                 # assistente admin (Next + CopilotKit)
├── agent_service/                  # agente LangChain
├── mcp_server/                     # servidor MCP (tools/widgets)
│
├── data/
│   ├── kaggle/                     # fonte, versão, licença (só README)
│   ├── processed/                  # vazio
│   ├── synthetic_enrichment/       # vazio
│   ├── golden_set/                 # offer_catalog.json · golden_clients.csv
│   └── rag_corpus/                 # vazio
│
├── docs/                           # mkdocs (ver mkdocs.yml)
├── notebooks/                      # EDA, exploração MAB, simulação LinUCB
├── scripts/                        # reproduce.py, seed_db.py, smoke_e2e.ps1
├── infra/docker/                   # Dockerfiles + entrypoint
├── infra/k8s/                      # helm chart (só da api por enquanto)
├── .github/workflows/              # ci.yml, docs.yml
├── docker-compose.yml
└── Makefile
```

## Catálogo de ofertas (`data/golden_set/offer_catalog.json`)

Define os 10 braços do MAB com todos os parâmetros necessários para o pipeline:

| Campo | Descrição |
|---|---|
| `arm_id` | Identificador único — formato `OFF-{CAT}-{NNN}` |
| `santander_mapping` | Coluna original Santander + `br_product_column` (nome PT-BR no dataset sintético) |
| `context_features` | Colunas do dataset BR usadas como contexto no LinUCB/contextual MAB |
| `eligible_segment.santander_filters` | Filtros em nomes PT-BR (`ind_ativo`, `possui_*_atual`, `idade_min`, etc.) |
| `thompson_sampling_prior` | Priors Beta calibrados por benchmarks de mercado |
| `ucb_params` | Fator de exploração e nível de confiança por braço |
| `synthetic_simulation` | Taxa de conversão base + multiplicadores por segmento sintético |
| `reward` | Tipo, horizonte de atribuição e estratégia para delayed reward |

O campo `catalog_metadata.br_column_mapping` contém o dicionário completo de renomeação Santander → PT-BR, derivado de `scripts/generate_synthetic_br.py`.

**Distribuição de braços:** 3 crédito · 4 investimento · 3 seguro  
**Taxas de conversão:** 4% (OFF-CR-003) a 22% (OFF-SEG-003 com evento-gatilho)  
**Braço cold-start:** OFF-INV-004 — exploração maior, prior não-informativo  
**Braços sintéticos (sem coluna Santander):** OFF-SEG-001, OFF-SEG-002, OFF-SEG-003

## Limitações conhecidas
- Dataset Santander usa granularidade mensal — delayed rewards simulados dentro de cada mês
- 3 braços de seguro são 100% sintéticos (Santander não tem colunas de seguro)
- Sistema não é adequado para produção real regulada sem revisão de compliance
