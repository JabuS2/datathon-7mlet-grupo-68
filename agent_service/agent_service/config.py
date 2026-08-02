from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Configuration for the agent service."""

    # Service
    HOST: str = "0.0.0.0"
    PORT: int = 8100
    AGENT_NAME: str = "admin_dashboard_agent"
    AGENT_PATH: str = "/"
    # Origins allowed to reach the AG-UI endpoint (the dashboard frontend).
    CORS_ORIGINS: list[str] = ["http://localhost:3000"]

    # LLM
    OPENAI_API_KEY: str = ""
    OPENAI_MODEL: str = "openai:gpt-4o-mini"

    # MCP server (JavaScript) exposing tools + widgets
    MCP_SERVER_URL: str = "http://localhost:8200/mcp"
    # Admin token forwarded to the MCP server (and on to api_service) for
    # downstream data access. Should be a valid admin JWT / service token.
    DOWNSTREAM_API_TOKEN: str = ""

    # JWT validation of incoming admin requests. Must match api_service.
    SECRET_KEY: str = "your_secret_key"
    ALGORITHM: str = "HS256"
    # When true, requests to the agent endpoint must carry a valid JWT.
    REQUIRE_AUTH: bool = True

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")


settings = Settings()
