.PHONY: install api dashboard simulate evaluate retrain test lint run

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
