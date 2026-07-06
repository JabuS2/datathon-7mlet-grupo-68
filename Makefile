.PHONY: install infra migrate seed reproduce api test lint down

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
