"""Monopoly-playing AI agent."""

import logging
import random
from uuid import UUID

from src.client.models import Action, ActionType, GameState, ValidActions
from src.llm.ollama_client import OllamaClient
from src.llm.session import AgentSession
from src.parser.action_parser import ActionParser
from src.prompts.builder import PromptBuilder
from src.prompts.personalities import PersonalityConfig, get_personality

logger = logging.getLogger(__name__)


class MonopolyAgent:
    """An AI agent that plays Monopoly using a local LLM."""

    def __init__(
        self,
        player_id: UUID,
        player_name: str,
        personality: str,
        ollama_client: OllamaClient,
        session: AgentSession,
    ):
        """Initialize the Monopoly agent.

        Args:
            player_id: Unique player ID from game engine
            player_name: Display name for the player
            personality: Personality type (aggressive, analytical, chaotic)
            ollama_client: Ollama LLM client
            session: Session for maintaining conversation context
        """
        self.player_id = player_id
        self.player_name = player_name
        self.personality_config: PersonalityConfig = get_personality(personality)
        self.ollama = ollama_client
        self.session = session
        self.prompt_builder = PromptBuilder()
        self.action_parser = ActionParser()

        logger.info(
            f"Created agent '{player_name}' with personality '{personality}' "
            f"(temp={self.personality_config.temperature})"
        )

    async def decide_action(
        self,
        game_state: GameState,
        valid_actions: ValidActions,
    ) -> Action:
        """Decide which action to take.

        Args:
            game_state: Current game state
            valid_actions: Valid actions for this player

        Returns:
            The chosen action
        """
        policy_action = self._get_buy_policy_action(game_state, valid_actions)
        if policy_action:
            logger.info(
                f"Agent '{self.player_name}' policy chose: {policy_action.type.value}"
                f"{f' ({policy_action.property_id})' if policy_action.property_id else ''}"
            )
            return policy_action

        # Build system prompt with personality
        system_prompt = self.personality_config.system_prompt.format(
            player_name=self.player_name
        )

        # Build user prompt with game state
        user_prompt = self.prompt_builder.build_decision_prompt(
            game_state=game_state,
            valid_actions=valid_actions,
            player_name=self.player_name,
        )

        logger.debug(f"Agent '{self.player_name}' deciding action...")

        try:
            # Generate response from LLM
            response, new_context = await self.ollama.generate(
                system_prompt=system_prompt,
                user_prompt=user_prompt,
                temperature=self.personality_config.temperature,
                context=self.session.context,
            )

            # Update session context for continuity
            self.session.update_context(new_context)
            self.session.increment_decision()

            logger.info(
                f"Agent '{self.player_name}' LLM response: {response[:100]}..."
            )

            # Parse response into action
            action = self.action_parser.parse(response, valid_actions)

            logger.info(
                f"Agent '{self.player_name}' chose: {action.type.value}"
                f"{f' ({action.property_id})' if action.property_id else ''}"
            )

            return action

        except Exception as e:
            logger.error(f"Agent '{self.player_name}' decision error: {e}")
            # Return default action on error
            return self.action_parser._get_default_action(valid_actions)

    @property
    def personality(self) -> str:
        """Get personality name."""
        return self.personality_config.name

    @property
    def temperature(self) -> float:
        """Get LLM temperature."""
        return self.personality_config.temperature

    def get_stats(self) -> dict:
        """Get agent statistics.

        Returns:
            Dict with agent stats
        """
        return {
            "player_id": str(self.player_id),
            "player_name": self.player_name,
            "personality": self.personality,
            "temperature": self.temperature,
            "decisions_made": self.session.decision_count,
        }

    def reset_context(self) -> None:
        """Reset the agent's conversation context."""
        self.session.reset_context()
        logger.info(f"Agent '{self.player_name}' context reset")

    def _get_buy_policy_action(
        self,
        game_state: GameState,
        valid_actions: ValidActions,
    ) -> Action | None:
        """Apply a deterministic buy/pass policy for property decisions."""
        buy_action = next(
            (action for action in valid_actions.actions if action.type == ActionType.BUY_PROPERTY),
            None,
        )
        if not buy_action:
            return None

        player = next(
            (p for p in game_state.players if p.id == self.player_id),
            None,
        )
        if not player or buy_action.cost is None:
            return None

        cash_after = player.cash - buy_action.cost

        if self.personality == "aggressive":
            should_buy = cash_after >= 0
        elif self.personality == "analytical":
            should_buy = cash_after >= 150
        else:
            should_buy = cash_after >= 0 and random.random() < 0.7

        if should_buy:
            return Action(type=ActionType.BUY_PROPERTY, property_id=buy_action.property_id)

        return Action(type=ActionType.PASS_PROPERTY, property_id=buy_action.property_id)
