from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Settings for the model service."""

    PROJECT_NAME: str = "HP Invest Model Service"
    VERSION: str = "1.0.0"
    DESCRIPTION: str = "Serviço de modelos (bandits) para recomendação de ofertas"
    BACKEND_CORS_ORIGINS: list[str] = ["http://localhost:4200", "http://localhost:8000"]
    MODEL_PORT: int = 8000

    ### Catalog / data
    CATALOG_PATH: str = "data/golden_set/offer_catalog.json"
    CLIENTS_CSV_PATH: str = "data/golden_set/golden_clients.csv"

    ### Default algorithm
    DEFAULT_ALGORITHM: str = "linucb"

    ### Redis (state store)
    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379
    REDIS_PASSWORD: str = ""
    REDIS_DB: int = 0

    @property
    def REDIS_URL(self) -> str:
        if self.REDIS_PASSWORD:
            return f"redis://:{self.REDIS_PASSWORD}@{self.REDIS_HOST}:{self.REDIS_PORT}/{self.REDIS_DB}"
        return f"redis://{self.REDIS_HOST}:{self.REDIS_PORT}/{self.REDIS_DB}"

    ### MLflow (model registry)
    MLFLOW_TRACKING_URI: str = "http://localhost:5000"
    MLFLOW_EXPERIMENT_NAME: str = "datathon-mab"

    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", extra="ignore"
    )


settings = Settings()
