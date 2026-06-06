from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Settings for the application."""

    PROJECT_NAME: str = "HP Invest API"
    VERSION: str = "1.0.0"
    DESCRIPTION: str = "API for HP Invest"
    BACKEND_CORS_ORIGINS: list[str] = ["http://localhost:4200"]  # Rotas que podem acessar a API
    API_PORT: int = 8000

    ### Database Settings
    POSTGRES_SERVER: str = "localhost"
    POSTGRES_USER: str = "postgres"
    POSTGRES_PASSWORD: str = "postgres"
    POSTGRES_DB: str = "postgres"
    POSTGRES_PORT: int = 5432

    ### JWT Settings
    SECRET_KEY: str = "your_secret_key"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


settings = Settings()
