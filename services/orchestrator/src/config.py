"""Configuration settings for the Orchestrator Service."""

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # Service configuration
    host: str = "0.0.0.0"
    port: int = 3000

    # Dependency URLs
    game_engine_url: str = "http://localhost:8000"
    ai_agent_url: str = "http://localhost:8001"
    redis_url: str = "redis://localhost:6379"

    # Game settings
    turn_timeout: float = 30.0
    default_speed: str = "normal"

    # HTTP client settings
    http_timeout: float = 60.0
    http_retries: int = 3

    model_config = SettingsConfigDict(
        env_prefix="ORCHESTRATOR_",
        env_file=".env",
        extra="ignore",
    )


_settings: Settings | None = None


def get_settings() -> Settings:
    """Get cached settings instance."""
    global _settings
    if _settings is None:
        _settings = Settings()
    return _settings
