"""HTTP clients for external services."""

from src.clients.ai_agent import AIAgentClient
from src.clients.game_engine import GameEngineClient

__all__ = ["GameEngineClient", "AIAgentClient"]
