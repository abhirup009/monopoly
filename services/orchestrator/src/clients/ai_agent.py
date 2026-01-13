"""HTTP client for the AI Agent service."""

import logging
from typing import Any
from uuid import UUID

import httpx

from src.config import get_settings

logger = logging.getLogger(__name__)


class AIAgentClient:
    """Client for interacting with the AI Agent service."""

    def __init__(self, base_url: str | None = None, timeout: float | None = None):
        """Initialize the AI Agent client.

        Args:
            base_url: Base URL for the AI Agent service.
            timeout: Request timeout in seconds.
        """
        settings = get_settings()
        self.base_url = base_url or settings.ai_agent_url
        self.timeout = timeout or settings.http_timeout
        self._client: httpx.AsyncClient | None = None

    async def _get_client(self) -> httpx.AsyncClient:
        """Get or create the HTTP client."""
        if self._client is None or self._client.is_closed:
            self._client = httpx.AsyncClient(
                base_url=self.base_url,
                timeout=self.timeout,
            )
        return self._client

    async def close(self) -> None:
        """Close the HTTP client."""
        if self._client and not self._client.is_closed:
            await self._client.aclose()
            self._client = None

    async def health_check(self) -> dict[str, Any]:
        """Check AI Agent health."""
        client = await self._get_client()
        response = await client.get("/health")
        response.raise_for_status()
        return response.json()

    async def get_personalities(self) -> list[dict[str, Any]]:
        """Get available AI personalities."""
        client = await self._get_client()
        response = await client.get("/personalities")
        response.raise_for_status()
        return response.json()

    async def get_decision(
        self,
        game_id: UUID,
        player_id: UUID,
        game_state: dict[str, Any],
        valid_actions: list[dict[str, Any]],
    ) -> dict[str, Any]:
        """Get AI decision for a player's turn.

        Args:
            game_id: The game UUID.
            player_id: The player UUID.
            game_state: Current game state.
            valid_actions: List of valid actions.

        Returns:
            The chosen action.
        """
        client = await self._get_client()
        response = await client.post(
            f"/games/{game_id}/decide",
            json={
                "player_id": str(player_id),
                "game_state": game_state,
                "valid_actions": valid_actions,
            },
        )
        response.raise_for_status()
        return response.json()

    async def create_game(
        self,
        game_id: UUID,
        agents: list[dict[str, Any]],
    ) -> dict[str, Any]:
        """Register a game with the AI Agent service.

        Args:
            game_id: The game UUID from Game Engine.
            agents: List of agent configurations.

        Returns:
            Registration confirmation.
        """
        client = await self._get_client()
        response = await client.post(
            "/games",
            json={
                "game_id": str(game_id),
                "agents": agents,
            },
        )
        response.raise_for_status()
        return response.json()

    async def get_game_status(self, game_id: UUID) -> dict[str, Any]:
        """Get AI game status.

        Args:
            game_id: The game UUID.

        Returns:
            Game status from AI Agent service.
        """
        client = await self._get_client()
        response = await client.get(f"/games/{game_id}")
        response.raise_for_status()
        return response.json()

    async def stop_game(self, game_id: UUID) -> dict[str, Any]:
        """Stop an AI game.

        Args:
            game_id: The game UUID.

        Returns:
            Stop confirmation.
        """
        client = await self._get_client()
        response = await client.post(f"/games/{game_id}/stop")
        response.raise_for_status()
        return response.json()
