"""Prompt builder for game state formatting."""

from uuid import UUID

from src.client.models import GameState, ValidActions
from src.prompts.templates import get_property_name, get_space_name


class PromptBuilder:
    """Builds prompts from game state."""

    def build_decision_prompt(
        self,
        game_state: GameState,
        valid_actions: ValidActions,
        player_name: str,
    ) -> str:
        """Build the user prompt for a decision.

        Args:
            game_state: Current game state
            valid_actions: Valid actions for this player
            player_name: Name of the player making the decision

        Returns:
            Formatted user prompt
        """
        player = self._get_player(game_state, valid_actions.player_id)
        if not player:
            return "Error: Player not found"

        position_name = get_space_name(player.position)
        player_properties = self._get_player_properties(game_state, player.id)

        prompt = f"""=== CURRENT GAME STATE ===

YOUR STATUS ({player_name}):
- Position: {position_name} (space {player.position})
- Cash: ${player.cash}
- Properties owned: {len(player_properties)}
{self._format_owned_properties(player_properties)}
- In jail: {"Yes" if player.in_jail else "No"}
- Get Out of Jail cards: {player.get_out_of_jail_cards}

OPPONENTS:
{self._format_opponents(game_state, player.id)}

=== YOUR TURN (Turn {game_state.turn_number}) ===

Valid actions you can take:
{self._format_actions(valid_actions)}

Respond with ONLY valid JSON:
{{"action": "<action_type>", "property_id": "<id_or_null>"}}

Examples:
- {{"action": "roll_dice", "property_id": null}}
- {{"action": "buy_property", "property_id": "boardwalk"}}
- {{"action": "end_turn", "property_id": null}}

Your decision (JSON only):"""

        return prompt

    def _get_player(self, game_state: GameState, player_id: UUID):
        """Get player by ID."""
        for player in game_state.players:
            if player.id == player_id:
                return player
        return None

    def _get_player_properties(
        self,
        game_state: GameState,
        player_id: UUID,
    ) -> list[str]:
        """Get list of property IDs owned by player."""
        return [
            prop.property_id
            for prop in game_state.properties
            if prop.owner_id == player_id
        ]

    def _format_owned_properties(self, property_ids: list[str]) -> str:
        """Format owned properties list."""
        if not property_ids:
            return "  (none)"

        lines = []
        for prop_id in property_ids[:8]:  # Limit to 8 for brevity
            name = get_property_name(prop_id)
            lines.append(f"  - {name}")

        if len(property_ids) > 8:
            lines.append(f"  ... and {len(property_ids) - 8} more")

        return "\n".join(lines)

    def _format_opponents(self, game_state: GameState, current_player_id: UUID) -> str:
        """Format opponent information."""
        lines = []
        for player in game_state.players:
            if player.id != current_player_id and not player.is_bankrupt:
                prop_count = sum(
                    1 for p in game_state.properties if p.owner_id == player.id
                )
                status = " [IN JAIL]" if player.in_jail else ""
                position = get_space_name(player.position)
                lines.append(
                    f"- {player.name}: ${player.cash}, "
                    f"{prop_count} properties, at {position}{status}"
                )

        if not lines:
            return "  No active opponents"

        return "\n".join(lines)

    def _format_actions(self, valid_actions: ValidActions) -> str:
        """Format valid actions as a numbered list."""
        lines = []
        for i, action in enumerate(valid_actions.actions, 1):
            action_type = action.type.value

            parts = [f"{i}. {action_type}"]

            if action.property_id:
                name = get_property_name(action.property_id)
                parts.append(f'[property_id: "{action.property_id}" ({name})]')

            if action.cost:
                parts.append(f"(cost: ${action.cost})")

            lines.append(" ".join(parts))

        return "\n".join(lines)

    def build_summary_prompt(self, game_state: GameState) -> str:
        """Build a summary prompt for game state overview.

        Args:
            game_state: Current game state

        Returns:
            Summary prompt
        """
        lines = [
            f"Turn: {game_state.turn_number}",
            f"Phase: {game_state.turn_phase.value}",
            f"Status: {game_state.status.value}",
            "",
            "Players:",
        ]

        for player in game_state.players:
            status = "BANKRUPT" if player.is_bankrupt else "Active"
            jail = " [JAIL]" if player.in_jail else ""
            prop_count = sum(
                1 for p in game_state.properties if p.owner_id == player.id
            )
            lines.append(
                f"  {player.name}: ${player.cash}, "
                f"{prop_count} props, {status}{jail}"
            )

        return "\n".join(lines)
