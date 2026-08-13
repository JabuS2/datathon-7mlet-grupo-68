from pathlib import Path

from pydantic import computed_field, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

# O backend pode ser iniciado a partir de `api_service/`, mas o `.env` fica na raiz.
ENV_FILE = Path(__file__).resolve().parent.parent / ".env"

# Valores de SECRET_KEY conhecidos/fracos que nunca podem ir para produção.
_WEAK_SECRETS = {"", "your_secret_key", "changeme", "secret"}
_PROD_ENVS = {"production", "prod", "staging"}


class Settings(BaseSettings):
    """Settings for the application."""

    PROJECT_NAME: str = "HP Invest API"
    VERSION: str = "1.0.0"
    DESCRIPTION: str = "API for HP Invest"
    # development | staging | production — controla validações de segurança.
    ENVIRONMENT: str = "development"
    BACKEND_CORS_ORIGINS: list[str] = [
        "http://localhost:4200"
    ]  # Rotas que podem acessar a API
    API_PORT: int = 8000

    # Diretório dos dados de referência (catálogo, golden set). Default: <repo>/data;
    # no Docker o compose monta ./data em /app/data (sobrescreva via env DATA_DIR).
    DATA_DIR: str = str(Path(__file__).resolve().parent.parent / "data")

    ### Bandits (executados nesta API)
    CATALOG_PATH: str | None = None
    CLIENTS_CSV_PATH: str | None = None
    DEFAULT_ALGORITHM: str = "linucb"
    MLFLOW_TRACKING_URI: str = "http://localhost:5000"
    MLFLOW_EXPERIMENT_NAME: str = "datathon-mab"

    ### Database Settings
    # Se DATABASE_URL for definida, tem precedência sobre os POSTGRES_* (ex.: Docker/Compose).
    DATABASE_URL: str | None = None
    POSTGRES_SERVER: str = "localhost"
    POSTGRES_USER: str = "postgres"
    POSTGRES_PASSWORD: str = "postgres"
    POSTGRES_DB: str = "postgres"
    POSTGRES_PORT: int = 5432
    SQLALCHEMY_ECHO: bool = False

    ### JWT Settings
    SECRET_KEY: str = "your_secret_key"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    ### Redis Settings
    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379
    REDIS_PASSWORD: str = ""
    REDIS_DB: int = 0

    @property
    def REDIS_URL(self) -> str:
        if self.REDIS_PASSWORD:
            return f"redis://:{self.REDIS_PASSWORD}@{self.REDIS_HOST}:{self.REDIS_PORT}/{self.REDIS_DB}"
        return f"redis://{self.REDIS_HOST}:{self.REDIS_PORT}/{self.REDIS_DB}"

    @property
    def catalog_path(self) -> str:
        return str(Path(self.DATA_DIR) / "golden_set" / "offer_catalog.json")

    @property
    def clients_csv_path(self) -> str:
        return self.CLIENTS_CSV_PATH or str(
            Path(self.DATA_DIR) / "golden_set" / "golden_clients.csv"
        )

    ### OpenSearch Settings
    OPENSEARCH_HOST: str = "localhost"
    OPENSEARCH_PORT: int = 9200
    OPENSEARCH_USER: str = "admin"
    OPENSEARCH_ADMIN_PASSWORD: str = ""

    @property
    def OPENSEARCH_URL(self) -> str:
        return f"https://{self.OPENSEARCH_HOST}:{self.OPENSEARCH_PORT}"

    ### Neo4j Settings
    NEO4J_URI: str = "bolt://localhost:7687"
    NEO4J_USER: str = "neo4j"
    NEO4J_PASSWORD: str = "neo4j_password"

    # `extra="ignore"`: o .env da raiz é compartilhado com agent_service / mcp_server /
    # dashboard / pgAdmin. Sem isso o pydantic-settings rejeita (extra_forbidden) toda chave
    # que não seja campo desta classe e o backend não sobe com um .env real.
    model_config = SettingsConfigDict(
        env_file=ENV_FILE, env_file_encoding="utf-8", extra="ignore"
    )

    @property
    def is_production(self) -> bool:
        return self.ENVIRONMENT.strip().lower() in _PROD_ENVS

    @computed_field  # type: ignore[prop-decorator]
    @property
    def sync_database_url(self) -> str:
        """URL síncrona (psycopg2) — usada pelo Alembic."""
        if self.DATABASE_URL:
            return self.DATABASE_URL
        return (
            f"postgresql://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}"
            f"@{self.POSTGRES_SERVER}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"
        )

    @computed_field  # type: ignore[prop-decorator]
    @property
    def async_database_url(self) -> str:
        """URL assíncrona (asyncpg) — usada pela aplicação."""
        return self.sync_database_url.replace(
            "postgresql://", "postgresql+asyncpg://", 1
        )

    @model_validator(mode="after")
    def _validate_secret_in_production(self) -> "Settings":
        """Em produção, exige um SECRET_KEY forte (impede subir com o default inseguro)."""
        if self.is_production:
            secret = self.SECRET_KEY.strip()
            if secret in _WEAK_SECRETS or len(secret) < 32:
                raise ValueError(
                    "SECRET_KEY inseguro para produção: defina um segredo aleatório com "
                    "pelo menos 32 caracteres (ex.: `openssl rand -hex 32`)."
                )
        return self


settings = Settings()
