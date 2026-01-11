"""Application configuration using pydantic-settings."""

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )

    # Database
    database_url: str = "postgresql+asyncpg://monopoly:monopoly@localhost:5432/monopoly"

    # Redis (for future use)
    redis_url: str = "redis://localhost:6379"

    # Application
    environment: str = "development"
    log_level: str = "INFO"
    debug: bool = False

    # Game Configuration
    starting_cash: int = 1500

    @property
    def is_development(self) -> bool:
        """Check if running in development mode."""
        return self.environment == "development"


@lru_cache
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()
