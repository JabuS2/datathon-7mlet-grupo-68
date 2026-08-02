FROM python:3.12-slim

WORKDIR /app

ENV PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

COPY --from=ghcr.io/astral-sh/uv:0.11.32 /uv /uvx /usr/local/bin/

COPY pyproject.toml ./
RUN uv pip install --system \
    "fastapi==0.115.14" \
    "uvicorn[standard]==0.52.0" \
    "deepagents==0.6.12" \
    "langchain-openai==1.4.1" \
    "langchain-mcp-adapters==0.3.1" \
    "mcp==1.29.0" \
    "ag-ui-langgraph==0.0.42" \
    "PyJWT[crypto]==2.13.0" \
    "pydantic==2.13.4" \
    "pydantic-settings==2.14.2" \
    "python-dotenv==1.2.2"

COPY agent_service ./agent_service

EXPOSE 8100

CMD ["uvicorn", "agent_service.app:create_app", "--factory", "--host", "0.0.0.0", "--port", "8100"]
