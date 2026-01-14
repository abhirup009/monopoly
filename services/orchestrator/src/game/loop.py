"""Game loop controller for orchestrating game flow."""

import asyncio
import logging
from typing import Any
from uuid import UUID

from src.clients.ai_agent import AIAgentClient
from src.clients.game_engine import GameEngineClient
from src.game.state import GameSession
from src.ws.events import EventBus

logger = logging.getLogger(__name__)


class GameLoopController:
    """Controls the game loop execution."""

    def __init__(
        self,
        game_engine: GameEngineClient,
        ai_agent: AIAgentClient,
        event_bus: EventBus,
        turn_timeout: float = 30.0,
    ):
        """Initialize the game loop controller.

        Args:
            game_engine: Game Engine HTTP client.
            ai_agent: AI Agent HTTP client.
            event_bus: Event bus for broadcasting.
            turn_timeout: Timeout for AI decisions in seconds.
        """
        self.game_engine = game_engine
        self.ai_agent = ai_agent
        self.event_bus = event_bus
        self.turn_timeout = turn_timeout

    async def run_game(self, session: GameSession) -> dict[str, Any]:
        """Run the main game loop.

        Args:
            session: The game session to run.

        Returns:
            Final game result.
        """
        game_id = session.game_id
        session.is_running = True
        logger.info(f"Starting game loop for {game_id}")

        try:
            # Emit game started event
            await self.event_bus.emit(
                "game:started",
                {"game_id": str(game_id), "agents": session.agents},
                game_id=game_id,
            )

            while session.is_running:
                # Get current game state
                state = await self.game_engine.get_state(game_id)
                session.update_state(state)

                # Check if game is completed
                if state.get("status") == "completed":
                    await self._handle_game_end(session, state)
                    break

                # Execute a turn
                await self._execute_turn(session, state)

                # Apply speed delay
                await asyncio.sleep(session.get_delay())

            return {
                "game_id": str(game_id),
                "status": "completed",
                "final_state": session.current_state,
            }

        except asyncio.CancelledError:
            logger.info(f"Game {game_id} was cancelled")
            session.is_running = False
            await self.event_bus.emit(
                "game:stopped",
                {"game_id": str(game_id), "reason": "cancelled"},
                game_id=game_id,
            )
            raise

        except Exception as e:
            logger.error(f"Error in game loop for {game_id}: {e}")
            session.is_running = False
            await self.event_bus.emit(
                "game:error",
                {"game_id": str(game_id), "error": str(e)},
                game_id=game_id,
            )
            raise

        finally:
            session.is_running = False

    async def _execute_turn(self, session: GameSession, state: dict[str, Any]) -> None:
        """Execute a single turn.

        Args:
            session: The game session.
            state: Current game state.
        """
        game_id = session.game_id
        players = state.get("players", [])
        current_index = state.get("current_player_index", 0)

        if not players or current_index >= len(players):
            logger.error(f"Invalid player state for game {game_id}")
            return

        player = players[current_index]
        player_id = UUID(player["id"])
        turn_number = state.get("turn_number", 0)

        # Emit turn start
        await self.event_bus.emit(
            "turn:start",
            {
                "game_id": str(game_id),
                "player_id": str(player_id),
                "player_name": player.get("name"),
                "turn_number": turn_number,
            },
            game_id=game_id,
        )

        # Get valid actions
        valid_actions_response = await self.game_engine.get_valid_actions(game_id)
        valid_actions = valid_actions_response.get("actions", [])

        if not valid_actions:
            logger.warning(f"No valid actions for player {player_id} in game {game_id}")
            return

        # Emit thinking event
        await self.event_bus.emit(
            "agent:thinking",
            {"game_id": str(game_id), "player_id": str(player_id)},
            game_id=game_id,
        )

        # Get AI decision with timeout
        try:
            decision = await asyncio.wait_for(
                self.ai_agent.get_decision(
                    game_id=game_id,
                    player_id=player_id,
                    game_state=state,
                    valid_actions=valid_actions,
                ),
                timeout=self.turn_timeout,
            )
            action = decision.get("action", valid_actions[0])
        except asyncio.TimeoutError:
            logger.warning(f"AI timeout for player {player_id}, using default action")
            action = self._get_default_action(valid_actions)
            await self.event_bus.emit(
                "turn:timeout",
                {"game_id": str(game_id), "player_id": str(player_id)},
                game_id=game_id,
            )

        # Execute the action
        result = await self.game_engine.execute_action(game_id, player_id, action)

        # Emit action result
        await self.event_bus.emit(
            "turn:action",
            {
                "game_id": str(game_id),
                "player_id": str(player_id),
                "player_name": player.get("name"),
                "action": action,
                "result": result,
            },
            game_id=game_id,
        )

    async def _handle_game_end(self, session: GameSession, state: dict[str, Any]) -> None:
        """Handle game completion.

        Args:
            session: The game session.
            state: Final game state.
        """
        game_id = session.game_id
        winner_id = state.get("winner_id")
        players = state.get("players", [])

        winner_name = None
        if winner_id:
            for player in players:
                if player["id"] == winner_id:
                    winner_name = player.get("name")
                    break

        await self.event_bus.emit(
            "game:ended",
            {
                "game_id": str(game_id),
                "winner_id": winner_id,
                "winner_name": winner_name,
                "final_state": state,
            },
            game_id=game_id,
        )

        logger.info(f"Game {game_id} ended. Winner: {winner_name or 'None'}")

    def _get_default_action(self, valid_actions: list[dict[str, Any]]) -> dict[str, Any]:
        """Get a safe default action when AI times out.

        Args:
            valid_actions: List of valid actions.

        Returns:
            A safe default action.
        """
        # Priority order for default actions
        priority = ["end_turn", "pass_property", "roll_dice", "pay_jail_fine"]

        for action_type in priority:
            for action in valid_actions:
                if action.get("type") == action_type:
                    return action

        # Fallback to first available action
        return valid_actions[0] if valid_actions else {"type": "end_turn"}

    def stop_game(self, session: GameSession) -> None:
        """Stop a running game.

        Args:
            session: The game session to stop.
        """
        session.is_running = False
        logger.info(f"Stopping game {session.game_id}")


class GameManager:
    """High-level manager for game orchestration."""

    def __init__(
        self,
        game_engine: GameEngineClient,
        ai_agent: AIAgentClient,
        event_bus: EventBus,
        turn_timeout: float = 30.0,
    ):
        """Initialize the game manager.

        Args:
            game_engine: Game Engine HTTP client.
            ai_agent: AI Agent HTTP client.
            event_bus: Event bus for broadcasting.
            turn_timeout: Timeout for AI decisions.
        """
        self.game_engine = game_engine
        self.ai_agent = ai_agent
        self.event_bus = event_bus
        self.turn_timeout = turn_timeout
        self._tasks: dict[str, asyncio.Task] = {}

    def _create_controller(self) -> GameLoopController:
        """Create a new game loop controller."""
        return GameLoopController(
            game_engine=self.game_engine,
            ai_agent=self.ai_agent,
            event_bus=self.event_bus,
            turn_timeout=self.turn_timeout,
        )

    async def start_game(self, session: GameSession) -> None:
        """Start a game in the background.

        Args:
            session: The game session to start.
        """
        game_id = str(session.game_id)
        if game_id in self._tasks:
            raise ValueError(f"Game {game_id} is already running")

        controller = self._create_controller()
        task = asyncio.create_task(controller.run_game(session))
        self._tasks[game_id] = task
        logger.info(f"Started game task for {game_id}")

    async def stop_game(self, game_id: str | UUID) -> bool:
        """Stop a running game.

        Args:
            game_id: The game UUID.

        Returns:
            True if game was stopped, False if not found.
        """
        key = str(game_id)
        task = self._tasks.get(key)
        if task:
            task.cancel()
            try:
                await task
            except asyncio.CancelledError:
                pass
            del self._tasks[key]
            logger.info(f"Stopped game {game_id}")
            return True
        return False

    async def wait_for_game(self, game_id: str | UUID) -> dict[str, Any] | None:
        """Wait for a game to complete.

        Args:
            game_id: The game UUID.

        Returns:
            Game result or None if not found.
        """
        key = str(game_id)
        task = self._tasks.get(key)
        if task:
            try:
                result = await task
                return result
            finally:
                if key in self._tasks:
                    del self._tasks[key]
        return None

    def is_game_running(self, game_id: str | UUID) -> bool:
        """Check if a game is running.

        Args:
            game_id: The game UUID.

        Returns:
            True if game is running.
        """
        key = str(game_id)
        task = self._tasks.get(key)
        return task is not None and not task.done()
