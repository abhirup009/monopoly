"""Game session state management."""

import logging
from enum import Enum
from typing import Any
from uuid import UUID

logger = logging.getLogger(__name__)


class GameSpeed(str, Enum):
    """Game speed settings."""

    FAST = "fast"
    NORMAL = "normal"
    SLOW = "slow"
    WATCH = "watch"  # Very slow for users to follow along


# Speed delays in seconds
SPEED_DELAYS = {
    GameSpeed.FAST: 0.5,
    GameSpeed.NORMAL: 2.0,
    GameSpeed.SLOW: 5.0,
    GameSpeed.WATCH: 10.0,  # 10 seconds between actions for easy following
}


class GameSession:
    """Manages state for a single game session."""

    def __init__(
        self,
        game_id: UUID,
        agents: list[dict[str, Any]],
        speed: GameSpeed = GameSpeed.NORMAL,
    ):
        """Initialize a game session.

        Args:
            game_id: The game UUID.
            agents: List of agent configurations.
            speed: Initial game speed.
        """
        self.game_id = game_id
        self.agents = agents
        self.speed = speed
        self.current_state: dict[str, Any] | None = None
        self.is_running = False
        self.turn_count = 0

    def set_speed(self, speed: str | GameSpeed) -> None:
        """Set the game speed.

        Args:
            speed: New speed setting.
        """
        if isinstance(speed, str):
            speed = GameSpeed(speed)
        self.speed = speed
        logger.info(f"Game {self.game_id} speed set to {speed.value}")

    def get_delay(self) -> float:
        """Get the current speed delay in seconds."""
        return SPEED_DELAYS[self.speed]

    def update_state(self, state: dict[str, Any]) -> None:
        """Update the current game state.

        Args:
            state: New game state.
        """
        self.current_state = state
        if state:
            self.turn_count = state.get("turn_number", 0)


class GameSessionManager:
    """Manages all active game sessions."""

    def __init__(self):
        """Initialize the session manager."""
        self._sessions: dict[str, GameSession] = {}

    def create_session(
        self,
        game_id: UUID,
        agents: list[dict[str, Any]],
        speed: GameSpeed = GameSpeed.NORMAL,
    ) -> GameSession:
        """Create a new game session.

        Args:
            game_id: The game UUID.
            agents: List of agent configurations.
            speed: Initial game speed.

        Returns:
            The created session.
        """
        session = GameSession(game_id, agents, speed)
        self._sessions[str(game_id)] = session
        logger.info(f"Created session for game {game_id}")
        return session

    def get_session(self, game_id: str | UUID) -> GameSession | None:
        """Get a game session by ID.

        Args:
            game_id: The game UUID.

        Returns:
            The session if found, None otherwise.
        """
        return self._sessions.get(str(game_id))

    def remove_session(self, game_id: str | UUID) -> None:
        """Remove a game session.

        Args:
            game_id: The game UUID.
        """
        key = str(game_id)
        if key in self._sessions:
            del self._sessions[key]
            logger.info(f"Removed session for game {game_id}")

    def list_sessions(self) -> list[dict[str, Any]]:
        """List all active sessions.

        Returns:
            List of session info dicts.
        """
        return [
            {
                "game_id": str(session.game_id),
                "is_running": session.is_running,
                "turn_count": session.turn_count,
                "speed": session.speed.value,
            }
            for session in self._sessions.values()
        ]
