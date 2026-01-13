"""Application configuration."""

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # Game Engine
    game_engine_url: str = "http://localhost:8000"

    # Ollama
    ollama_host: str = "http://localhost:11434"
    ollama_model: str = "llama3"

    # Game timing
    turn_delay: float = 1.0  # Seconds between turns
    action_delay: float = 0.5  # Seconds between actions

    # Server
    host: str = "0.0.0.0"
    port: int = 8001

    # Logging
    log_level: str = "INFO"
    log_prompts: bool = False  # Log full prompts (verbose)
    log_responses: bool = True  # Log LLM responses

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")


settings = Settings()
