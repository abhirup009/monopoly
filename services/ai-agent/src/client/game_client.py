"""HTTP client for Game Engine API."""

import logging
from uuid import UUID

import httpx
from tenacity import retry, stop_after_attempt, wait_exponential

from src.client.models import (
    Action,
    ActionResult,
    CreateGameResponse,
    CreateGameResult,
    GameState,
    ValidActions,
)

logger = logging.getLogger(__name__)


class GameClient:
    """Async HTTP client for the Game Engine API."""

    def __init__(self, base_url: str, timeout: float = 30.0):
        """Initialize the game client.

        Args:
            base_url: Base URL of the game engine API
            timeout: Request timeout in seconds
        """
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
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

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=10),
    )
    async def create_game(self, players: list[dict]) -> CreateGameResult:
        """Create a new game.

        Args:
            players: List of player configurations with name, model, personality

        Returns:
            CreateGameResult with game ID and player info
        """
        client = await self._get_client()
        response = await client.post("/game", json={"players": players})
        response.raise_for_status()
        create_response = CreateGameResponse(**response.json())

        # Fetch full game state to get player details
        game_state = await self.get_game_state(create_response.id)

        return CreateGameResult(
            id=create_response.id,
            status=create_response.status,
            players=game_state.players,
            message=create_response.message,
        )

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=10),
    )
    async def start_game(self, game_id: UUID) -> dict:
        """Start a game.

        Args:
            game_id: Game ID to start

        Returns:
            Response with game status
        """
        client = await self._get_client()
        response = await client.post(f"/game/{game_id}/start")
        response.raise_for_status()
        return response.json()

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=10),
    )
    async def get_game_state(self, game_id: UUID) -> GameState:
        """Get current game state.

        Args:
            game_id: Game ID to get

        Returns:
            Full game state
        """
        client = await self._get_client()
        response = await client.get(f"/game/{game_id}")
        response.raise_for_status()
        return GameState(**response.json())

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=10),
    )
    async def get_valid_actions(self, game_id: UUID) -> ValidActions:
        """Get valid actions for current player.

        Args:
            game_id: Game ID

        Returns:
            ValidActions with list of possible actions
        """
        client = await self._get_client()
        response = await client.get(f"/game/{game_id}/actions")
        response.raise_for_status()
        return ValidActions(**response.json())

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=10),
    )
    async def execute_action(
        self,
        game_id: UUID,
        player_id: UUID,
        action: Action,
    ) -> ActionResult:
        """Execute an action.

        Args:
            game_id: Game ID
            player_id: Player executing the action
            action: Action to execute

        Returns:
            ActionResult with success status and state changes
        """
        client = await self._get_client()
        response = await client.post(
            f"/game/{game_id}/action",
            json={
                "player_id": str(player_id),
                "action": {
                    "type": action.type.value,
                    "property_id": action.property_id,
                },
            },
        )
        response.raise_for_status()
        data = response.json()
        return ActionResult(
            success=data.get("success", True),
            message=data.get("message", ""),
            game_over=data.get("game_over", False),
            next_phase=data.get("turn_phase"),
            state_changes=data.get("state_changes"),
        )

    async def is_available(self) -> bool:
        """Check if the game engine is available.

        Returns:
            True if game engine is responding
        """
        try:
            client = await self._get_client()
            response = await client.get("/health")
            return response.status_code == 200
        except Exception:
            return False
