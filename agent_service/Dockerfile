FROM python:3.12-slim

WORKDIR /app

ENV PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

RUN pip install --upgrade pip

COPY pyproject.toml ./
RUN pip install \
    "fastapi>=0.115,<0.116" \
    "uvicorn[standard]>=0.30" \
    "deepagents>=0.6,<0.7" \
    "langchain-openai>=1.3,<2" \
    "langchain-mcp-adapters>=0.3,<0.4" \
    "ag-ui-langgraph>=0.0.42,<0.1" \
    "PyJWT[crypto]>=2.9" \
    "pydantic>=2.9" \
    "pydantic-settings>=2.4" \
    "python-dotenv>=1.0"

COPY agent_service ./agent_service

EXPOSE 8100

CMD ["uvicorn", "agent_service.app:create_app", "--factory", "--host", "0.0.0.0", "--port", "8100"]
