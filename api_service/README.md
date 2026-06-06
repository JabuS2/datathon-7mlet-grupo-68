# Datathon 7MLET — Grupo 68

Plataforma de experimentação adaptativa com Multi-Armed Bandit para recomendação de produtos financeiros.

**Dataset:** Santander Product Recommendation (Kaggle)  
**Algoritmos:** Thompson Sampling · Nilos-UCB · LinUCB contextual · Baseline determinístico  
**Frontends:** HP Invest (cliente final) · Dashboard operacional  
**Assistente:** LLM com RAG sobre políticas internas sintéticas

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

Arquitetura em 3 camadas (Layered Architecture):
- **interface/** — FastAPI, CLI, Streamlit, Assistente LLM
- **services/** — lógica de negócio pura, sem imports de framework
- **data/** — adaptadores: loaders, event store, policy store, vector store

A regra central: nenhum arquivo em `services/` importa FastAPI, Streamlit ou banco de dados. Isso garante testabilidade e separação de responsabilidades.

## Mapa de pastas

```
datathon-7mlet-grupo-68/
│
├── src/                            # Backend Python
│   ├── interface/                  # Camada de entrada
│   │   ├── api/                    # FastAPI — /decide /reward /experiments /audit
│   │   ├── cli/                    # Typer — simulate, evaluate, retrain
│   │   ├── assistant/              # LLM chat + RAG
│   │   └── dashboard/              # Streamlit — demo operacional
│   ├── services/                   # Lógica de negócio pura
│   │   ├── bandit/                 # Thompson Sampling, UCB, LinUCB, baseline
│   │   ├── evaluation/             # Golden set, métricas, fairness
│   │   ├── retrain/                # Drift, approval gate, rollback
│   │   ├── audit/                  # Audit logger, reason codes
│   │   └── rag/                    # RAG service, embedder, retriever
│   └── data/                       # Adaptadores de dados
│       ├── loader/                 # Santander, sintético, catálogo
│       ├── event_store/            # Impressões e rewards
│       ├── policy_store/           # Versionamento de política
│       └── vector_store/           # ChromaDB para RAG
│
├── apps/                           # Frontends React (Vite)
│   ├── hp-invest/                  # Experiência do cliente final
│   └── dashboard/                  # Painel operacional + chat LLM
│
├── data/                           # Camadas de dados (PDF Etapas 1-2)
│   ├── kaggle/README.md            # Fonte, versão, licença
│   ├── processed/                  # Dataset sem vazamento temporal
│   ├── synthetic_enrichment/       # offer_catalog.json, eventos, rewards
│   ├── golden_set/                 # evaluation_cases.jsonl (20+ casos)
│   └── rag_corpus/                 # 10 documentos de política sintética
│
├── docs/                           # Documentação obrigatória (PDF Etapa 8)
│   ├── model-card.md
│   ├── system-card.md
│   ├── lgpd-plan.md
│   ├── architecture/               # architecture-azure.md + ADRs
│   └── governance/                 # fairness-report, risk-scenarios
│
├── reports/                        # Relatório técnico e data-generation
├── tests/                          # unit / integration / e2e
├── notebooks/                      # EDA, simulação, demo day
├── infra/
│   ├── docker/                     # Dockerfiles por serviço
│   └── scripts/                    # setup-local, seed-data, simulate
├── .github/workflows/ci.yml        # CI — lint + test no push
├── docker-compose.yml
├── Makefile
├── pyproject.toml
└── .env.example
```

## Limitações conhecidas
- Dataset Santander usa granularidade mensal — delayed rewards simulados dentro de cada mês
- 3 braços de seguro são 100% sintéticos (Santander não tem colunas de seguro)
- Sistema não é adequado para produção real regulada sem revisão de compliance
