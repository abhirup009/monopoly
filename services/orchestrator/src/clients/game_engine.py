"""HTTP client for the Game Engine service."""

import logging
from typing import Any
from uuid import UUID

import httpx

from src.config import get_settings

logger = logging.getLogger(__name__)


class GameEngineClient:
    """Client for interacting with the Game Engine service."""

    def __init__(self, base_url: str | None = None, timeout: float | None = None):
        """Initialize the Game Engine client.

        Args:
            base_url: Base URL for the Game Engine service.
            timeout: Request timeout in seconds.
        """
        settings = get_settings()
        self.base_url = base_url or settings.game_engine_url
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
        """Check Game Engine health."""
        client = await self._get_client()
        response = await client.get("/health")
        response.raise_for_status()
        return response.json()

    async def create_game(self, players: list[dict[str, str]]) -> dict[str, Any]:
        """Create a new game.

        Args:
            players: List of player configurations with name, model, personality.

        Returns:
            Created game data including game_id.
        """
        client = await self._get_client()
        response = await client.post("/game", json={"players": players})
        response.raise_for_status()
        return response.json()

    async def start_game(self, game_id: UUID) -> dict[str, Any]:
        """Start a game.

        Args:
            game_id: The game UUID.

        Returns:
            Updated game state.
        """
        client = await self._get_client()
        response = await client.post(f"/game/{game_id}/start")
        response.raise_for_status()
        return response.json()

    async def get_state(self, game_id: UUID) -> dict[str, Any]:
        """Get current game state.

        Args:
            game_id: The game UUID.

        Returns:
            Full game state.
        """
        client = await self._get_client()
        response = await client.get(f"/game/{game_id}")
        response.raise_for_status()
        return response.json()

    async def get_valid_actions(self, game_id: UUID) -> dict[str, Any]:
        """Get valid actions for current player.

        Args:
            game_id: The game UUID.

        Returns:
            Valid actions data.
        """
        client = await self._get_client()
        response = await client.get(f"/game/{game_id}/actions")
        response.raise_for_status()
        return response.json()

    async def execute_action(
        self, game_id: UUID, player_id: UUID, action: dict[str, Any]
    ) -> dict[str, Any]:
        """Execute a game action.

        Args:
            game_id: The game UUID.
            player_id: The player UUID.
            action: The action to execute.

        Returns:
            Action result.
        """
        client = await self._get_client()
        response = await client.post(
            f"/game/{game_id}/action",
            json={"player_id": str(player_id), "action": action},
        )
        response.raise_for_status()
        return response.json()

    async def get_events(
        self, game_id: UUID, limit: int = 50, offset: int = 0
    ) -> list[dict[str, Any]]:
        """Get game events.

        Args:
            game_id: The game UUID.
            limit: Maximum number of events to return.
            offset: Number of events to skip.

        Returns:
            List of game events.
        """
        client = await self._get_client()
        response = await client.get(
            f"/game/{game_id}/events",
            params={"limit": limit, "offset": offset},
        )
        response.raise_for_status()
        return response.json()
