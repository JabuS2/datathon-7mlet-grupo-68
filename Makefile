.PHONY: install api dashboard simulate evaluate retrain test lint run start-project

install:
	pip install -e ".[dev]"

api:
	uvicorn src.interface.api.main:app --reload --port 8000

dashboard:
	streamlit run src/interface/dashboard/app.py

simulate:
	python -m src.interface.cli.main simulate

evaluate:
	python -m src.interface.cli.main evaluate

retrain:
	python -m src.interface.cli.main retrain

test:
	pytest tests/ -v

lint:
	ruff check src/ tests/

run:
	docker-compose up --build

# Interactively fill in the required env vars (writes repo-root .env), bring the
# whole stack up in Docker (infra + api + app: mcp_server/agent_service/dashboard
# /front_service), then generate and open an HTML page listing every service URL.
start-project:
	@node scripts/start-project.mjs
