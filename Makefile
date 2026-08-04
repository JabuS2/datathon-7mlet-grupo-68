.PHONY: install infra migrate seed reproduce api test lint down run start-project \
        data data-processed data-synthetic data-golden data-eval notebooks evaluate

API_DIR = api_service

# Instala as dependências do backend (Poetry).
install:
	cd $(API_DIR) && poetry install

# Sobe apenas a infraestrutura (Postgres) via docker-compose.
infra:
	docker-compose up -d postgres

# Aplica as migrações Alembic.
migrate:
	cd $(API_DIR) && poetry run alembic upgrade head

# Popula catálogo, políticas, priors e um subset de clientes.
seed:
	cd $(API_DIR) && poetry run python ../scripts/seed_db.py

# Pipeline ponta a ponta: migração + seed + ciclo de decisão auditável (Etapa 5).
# Requer o Postgres no ar (`make infra`).
reproduce:
	cd $(API_DIR) && poetry run python ../scripts/reproduce.py

# Sobe a API localmente.
api:
	cd $(API_DIR) && poetry run uvicorn main:app --reload --port 8000

# Suíte de testes (unit + integração; a integração usa testcontainers Postgres).
test:
	cd $(API_DIR) && poetry run pytest

# Lint.
lint:
	cd $(API_DIR) && poetry run ruff check .

# Derruba a infraestrutura.
down:
	docker-compose down

run:
	docker-compose up --build

# ── Camadas de dados (ver data/README.md) ───────────────────────────────────
# Só precisa rodar para regenerar o golden_set; ele já vem versionado.
# Pré-requisito manual: baixar data/kaggle/train_ver2.csv (exige credencial Kaggle).

# kaggle -> processed
data-processed:
	python scripts/prepare_data.py

# processed -> synthetic_enrichment
data-synthetic:
	python scripts/generate_synthetic_br.py

# synthetic_enrichment -> golden_set
data-golden:
	python scripts/generate_golden_sample.py

# golden_set -> evaluation_cases.jsonl (casos de avaliação offline; versionado)
data-eval:
	python scripts/generate_evaluation_cases.py

# A cadeia inteira (assume o download do Kaggle já feito).
data: data-processed data-synthetic data-golden data-eval

# Avaliação offline contra o golden set. Não precisa de Docker nem de serviço no ar;
# escreve reports/evaluation-report.md e sai != 0 se uma propriedade bloqueante falhar.
evaluate:
	python scripts/run_evaluation.py

# Executa os notebooks de análise ponta a ponta, descartando a saída (mesmo
# smoke test do job `notebooks` no CI).
notebooks:
	MPLBACKEND=Agg jupyter nbconvert --execute --to notebook \
		--output-dir /tmp/nbout notebooks/*.ipynb

# Interactively fill in the required env vars (writes repo-root .env), bring the
# whole stack up in Docker (infra + api + app: mcp_server/agent_service/dashboard
# /front_service), then generate and open an HTML page listing every service URL.
start-project:
	@node scripts/start-project.mjs
