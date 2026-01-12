"""Agent manager for orchestrating multiple AI agents."""

import asyncio
import logging
from dataclasses import dataclass
from typing import Awaitable, Callable
from uuid import UUID

from src.agent.monopoly_agent import MonopolyAgent
from src.client.game_client import GameClient
from src.client.models import Action, ActionType, GameState
from src.llm.ollama_client import OllamaClient
from src.llm.session import SessionManager
from src.prompts.personalities import get_personality

logger = logging.getLogger(__name__)


@dataclass
class AgentConfig:
    """Configuration for creating an agent."""

    name: str
    personality: str  # aggressive, analytical, chaotic


@dataclass
class GameResult:
    """Result of a completed game."""

    game_id: UUID
    winner_id: UUID | None
    winner_name: str | None
    total_turns: int
    final_standings: list[dict]


class AgentManager:
    """Manages multiple AI agents playing a game."""

    def __init__(
        self,
        game_client: GameClient,
        ollama_client: OllamaClient,
        turn_delay: float = 1.0,
        action_delay: float = 0.5,
        on_action: Callable[[str, Action, dict], Awaitable[None]] | None = None,
        on_turn_start: Callable[[str, int], Awaitable[None]] | None = None,
        on_game_event: Callable[[str, dict], Awaitable[None]] | None = None,
    ):
        """Initialize the agent manager.

        Args:
            game_client: Client for game engine API
            ollama_client: Client for Ollama LLM
            turn_delay: Delay between turns (seconds)
            action_delay: Delay between actions within a turn (seconds)
            on_action: Optional callback for each action
            on_turn_start: Optional callback for turn start
            on_game_event: Optional callback for game events
        """
        self.game_client = game_client
        self.ollama = ollama_client
        self.turn_delay = turn_delay
        self.action_delay = action_delay
        self.on_action = on_action
        self.on_turn_start = on_turn_start
        self.on_game_event = on_game_event

        self.session_manager = SessionManager()
        self.agents: dict[UUID, MonopolyAgent] = {}
        self.game_id: UUID | None = None
        self.is_running: bool = False
        self._stop_requested: bool = False

    async def create_game(self, agent_configs: list[AgentConfig]) -> UUID:
        """Create a new game with the specified agents.

        Args:
            agent_configs: List of agent configurations

        Returns:
            Game ID

        Raises:
            RuntimeError: If Ollama is not available
        """
        # Verify Ollama is available
        if not await self.ollama.is_available():
            raise RuntimeError(
                "Ollama is not running or model not available. "
                "Start Ollama and ensure the model is pulled."
            )

        # Create game via API
        players = [
            {
                "name": config.name,
                "model": "llama3",
                "personality": config.personality,
            }
            for config in agent_configs
        ]

        game_response = await self.game_client.create_game(players)
        self.game_id = game_response.id

        logger.info(f"Created game {self.game_id}")

        # Create agent instances
        for config, player in zip(agent_configs, game_response.players):
            personality_config = get_personality(config.personality)

            # Create session for this agent
            session = self.session_manager.create_session(
                agent_id=player.id,
                personality=config.personality,
                temperature=personality_config.temperature,
            )

            # Create agent
            agent = MonopolyAgent(
                player_id=player.id,
                player_name=player.name,
                personality=config.personality,
                ollama_client=self.ollama,
                session=session,
            )
            self.agents[player.id] = agent

            logger.info(f"Created agent: {player.name} ({config.personality})")

        return self.game_id

    async def start_game(self) -> None:
        """Start the game.

        Raises:
            ValueError: If no game has been created
        """
        if not self.game_id:
            raise ValueError("No game created. Call create_game first.")

        await self.game_client.start_game(self.game_id)
        logger.info(f"Started game {self.game_id}")

    async def run_game(self, max_turns: int = 1000) -> GameResult:
        """Run the game until completion.

        Args:
            max_turns: Maximum number of turns before forcing end

        Returns:
            GameResult with winner and final standings

        Raises:
            ValueError: If no game has been created
        """
        if not self.game_id:
            raise ValueError("No game created. Call create_game first.")

        self.is_running = True
        self._stop_requested = False
        last_game_state: GameState | None = None

        logger.info(f"Running game {self.game_id}")

        try:
            while self.is_running and not self._stop_requested:
                # Get current game state
                game_state = await self.game_client.get_game_state(self.game_id)
                last_game_state = game_state

                # Check if game is over
                if game_state.status.value == "completed":
                    logger.info("Game completed!")
                    self.is_running = False
                    break

                # Check turn limit
                if game_state.turn_number >= max_turns:
                    logger.warning(f"Turn limit ({max_turns}) reached")
                    self.is_running = False
                    break

                # Get current player
                current_player = game_state.players[game_state.current_player_index]

                # Skip bankrupt players (shouldn't happen but safety check)
                if current_player.is_bankrupt:
                    logger.debug(f"Skipping bankrupt player: {current_player.name}")
                    await asyncio.sleep(0.1)
                    continue

                # Get agent for current player
                agent = self.agents.get(current_player.id)
                if not agent:
                    logger.error(f"No agent for player {current_player.id}")
                    break

                # Notify turn start
                if self.on_turn_start:
                    await self.on_turn_start(
                        current_player.name,
                        game_state.turn_number,
                    )

                # Execute turn
                await self._execute_turn(agent, game_state)

                # Delay between turns
                await asyncio.sleep(self.turn_delay)

        except Exception as e:
            logger.error(f"Game loop error: {e}")
            raise
        finally:
            self.is_running = False

        # Get final state if needed
        if last_game_state is None:
            last_game_state = await self.game_client.get_game_state(self.game_id)

        return self._build_result(last_game_state)

    async def _execute_turn(
        self,
        agent: MonopolyAgent,
        initial_state: GameState,
    ) -> None:
        """Execute a single turn for an agent.

        Args:
            agent: Agent taking the turn
            initial_state: Game state at start of turn
        """
        max_actions = 20  # Safety limit per turn
        action_count = 0

        logger.debug(f"Executing turn for {agent.player_name}")

        for _ in range(max_actions):
            if self._stop_requested:
                break

            # Get valid actions
            valid_actions = await self.game_client.get_valid_actions(self.game_id)

            # Check if still this agent's turn
            if valid_actions.player_id != agent.player_id:
                logger.debug(f"Turn ended for {agent.player_name}")
                break

            # Get current game state for decision
            game_state = await self.game_client.get_game_state(self.game_id)

            # Get agent's decision
            action = await agent.decide_action(game_state, valid_actions)
            action_count += 1

            # Callback for logging/UI
            if self.on_action:
                await self.on_action(
                    agent.player_name,
                    action,
                    {"turn": game_state.turn_number, "phase": valid_actions.turn_phase.value},
                )

            # Execute action
            result = await self.game_client.execute_action(
                self.game_id,
                agent.player_id,
                action,
            )

            logger.debug(
                f"{agent.player_name}: {action.type.value} -> "
                f"{'OK' if result.success else result.message}"
            )

            # Notify game events
            if self.on_game_event and result.state_changes:
                await self.on_game_event("action_result", result.state_changes)

            # Check if game over
            if result.game_over:
                logger.info("Game over detected")
                self.is_running = False
                break

            # Check if turn ended (phase changed to another player's pre_roll)
            if (
                result.next_phase == "pre_roll"
                and action.type != ActionType.ROLL_DICE
            ):
                break

            # Delay between actions
            await asyncio.sleep(self.action_delay)

        logger.debug(
            f"{agent.player_name} took {action_count} actions this turn"
        )

    def _build_result(self, game_state: GameState) -> GameResult:
        """Build game result from final state.

        Args:
            game_state: Final game state

        Returns:
            GameResult
        """
        winner = None
        winner_name = None

        if game_state.winner_id:
            for player in game_state.players:
                if player.id == game_state.winner_id:
                    winner = player.id
                    winner_name = player.name
                    break

        # Build standings
        standings = []
        for player in game_state.players:
            prop_count = sum(
                1 for prop in game_state.properties
                if prop.owner_id == player.id
            )
            standings.append({
                "name": player.name,
                "cash": player.cash,
                "properties": prop_count,
                "bankrupt": player.is_bankrupt,
                "personality": player.personality,
            })

        # Sort by: not bankrupt first, then by cash
        standings.sort(key=lambda x: (not x["bankrupt"], x["cash"]), reverse=True)

        return GameResult(
            game_id=self.game_id,
            winner_id=winner,
            winner_name=winner_name,
            total_turns=game_state.turn_number,
            final_standings=standings,
        )

    def stop(self) -> None:
        """Request the game to stop."""
        logger.info("Stop requested")
        self._stop_requested = True
        self.is_running = False

    def get_agent_stats(self) -> list[dict]:
        """Get stats for all agents.

        Returns:
            List of agent stats
        """
        return [agent.get_stats() for agent in self.agents.values()]

    async def cleanup(self) -> None:
        """Clean up resources."""
        self.session_manager.clear_all()
        self.agents.clear()
        await self.game_client.close()
        logger.info("Agent manager cleaned up")
