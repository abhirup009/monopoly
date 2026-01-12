"""Parser for LLM responses into game actions."""

import json
import logging
import re

from src.client.models import Action, ActionType, ValidActions

logger = logging.getLogger(__name__)


class ActionParser:
    """Parses LLM responses into valid game actions."""

    def parse(self, response: str, valid_actions: ValidActions) -> Action:
        """Parse LLM response into a valid action.

        Attempts multiple parsing strategies:
        1. JSON extraction
        2. Keyword matching
        3. Default to safest action

        Args:
            response: Raw LLM response text
            valid_actions: List of valid actions to choose from

        Returns:
            Parsed Action object (guaranteed to be valid)
        """
        logger.debug(f"Parsing response: {response[:200]}...")

        # Strategy 1: Try JSON parsing
        action = self._try_json_parse(response)
        if action and self._is_valid(action, valid_actions):
            logger.debug(f"JSON parse succeeded: {action.type.value}")
            return action

        # Strategy 2: Try keyword matching
        action = self._try_keyword_parse(response, valid_actions)
        if action:
            logger.debug(f"Keyword parse succeeded: {action.type.value}")
            return action

        # Strategy 3: Default to safest action
        default = self._get_default_action(valid_actions)
        logger.warning(
            f"Parse failed, using default action: {default.type.value}"
        )
        return default

    def _try_json_parse(self, response: str) -> Action | None:
        """Extract JSON from response.

        Args:
            response: Raw LLM response

        Returns:
            Action or None if parsing fails
        """
        # Patterns to find JSON in response
        json_patterns = [
            r'\{[^{}]*"action"\s*:\s*"[^"]+"\s*(?:,\s*"property_id"\s*:\s*(?:"[^"]*"|null))?\s*\}',
            r"\{[^{}]*'action'\s*:\s*'[^']+'\s*(?:,\s*'property_id'\s*:\s*(?:'[^']*'|null))?\s*\}",
        ]

        for pattern in json_patterns:
            match = re.search(pattern, response, re.IGNORECASE | re.DOTALL)
            if match:
                try:
                    # Normalize quotes to double quotes
                    json_str = match.group().replace("'", '"')
                    data = json.loads(json_str)

                    action_type = data.get("action", "").lower().strip()
                    property_id = data.get("property_id")

                    # Handle null-like values
                    if property_id in ("null", "none", "", None):
                        property_id = None

                    # Try to create valid ActionType
                    try:
                        action_enum = ActionType(action_type)
                        return Action(type=action_enum, property_id=property_id)
                    except ValueError:
                        # Try variations
                        action_enum = self._match_action_type(action_type)
                        if action_enum:
                            return Action(type=action_enum, property_id=property_id)

                except (json.JSONDecodeError, ValueError, KeyError) as e:
                    logger.debug(f"JSON parse attempt failed: {e}")
                    continue

        # Also try direct JSON parse of entire response
        try:
            response_clean = response.strip()
            if response_clean.startswith("{"):
                data = json.loads(response_clean)
                action_type = data.get("action", "").lower().strip()
                property_id = data.get("property_id")
                if property_id in ("null", "none", "", None):
                    property_id = None
                action_enum = ActionType(action_type)
                return Action(type=action_enum, property_id=property_id)
        except (json.JSONDecodeError, ValueError):
            pass

        return None

    def _match_action_type(self, action_str: str) -> ActionType | None:
        """Try to match action string to ActionType.

        Args:
            action_str: Action string to match

        Returns:
            ActionType or None
        """
        action_str = action_str.lower().strip().replace("-", "_").replace(" ", "_")

        # Direct match
        for action_type in ActionType:
            if action_type.value == action_str:
                return action_type

        # Partial match
        mappings = {
            "roll": ActionType.ROLL_DICE,
            "dice": ActionType.ROLL_DICE,
            "buy": ActionType.BUY_PROPERTY,
            "purchase": ActionType.BUY_PROPERTY,
            "pass": ActionType.PASS_PROPERTY,
            "skip": ActionType.PASS_PROPERTY,
            "decline": ActionType.PASS_PROPERTY,
            "end": ActionType.END_TURN,
            "finish": ActionType.END_TURN,
            "done": ActionType.END_TURN,
            "house": ActionType.BUILD_HOUSE,
            "hotel": ActionType.BUILD_HOTEL,
            "pay_fine": ActionType.PAY_JAIL_FINE,
            "pay_jail": ActionType.PAY_JAIL_FINE,
            "use_card": ActionType.USE_JAIL_CARD,
            "jail_card": ActionType.USE_JAIL_CARD,
            "doubles": ActionType.ROLL_FOR_DOUBLES,
        }

        for key, action_type in mappings.items():
            if key in action_str:
                return action_type

        return None

    def _try_keyword_parse(
        self,
        response: str,
        valid_actions: ValidActions,
    ) -> Action | None:
        """Match keywords in response to valid actions.

        Args:
            response: Raw LLM response
            valid_actions: Valid actions to choose from

        Returns:
            Action or None
        """
        response_lower = response.lower()

        # Priority keywords for each action type
        action_keywords = {
            ActionType.BUY_PROPERTY: ["buy", "purchase", "acquire", "i'll take"],
            ActionType.ROLL_DICE: ["roll dice", "roll the dice", "let's roll"],
            ActionType.END_TURN: ["end turn", "end my turn", "finish", "done"],
            ActionType.PASS_PROPERTY: ["pass", "skip", "decline", "don't buy", "no thanks"],
            ActionType.BUILD_HOUSE: ["build house", "build a house", "add house"],
            ActionType.BUILD_HOTEL: ["build hotel", "upgrade to hotel", "add hotel"],
            ActionType.PAY_JAIL_FINE: ["pay fine", "pay $50", "pay the fine"],
            ActionType.USE_JAIL_CARD: ["use card", "get out of jail card", "use my card"],
            ActionType.ROLL_FOR_DOUBLES: ["roll for doubles", "try for doubles", "attempt doubles"],
        }

        # Check each valid action
        for valid_action in valid_actions.actions:
            keywords = action_keywords.get(valid_action.type, [])

            for keyword in keywords:
                if keyword in response_lower:
                    return Action(
                        type=valid_action.type,
                        property_id=valid_action.property_id,
                    )

        return None

    def _is_valid(self, action: Action, valid_actions: ValidActions) -> bool:
        """Check if action is in valid actions list.

        Args:
            action: Action to validate
            valid_actions: List of valid actions

        Returns:
            True if action is valid
        """
        for valid in valid_actions.actions:
            if valid.type == action.type:
                # For property actions, check property_id matches
                if action.property_id and valid.property_id:
                    if action.property_id == valid.property_id:
                        return True
                elif not valid.property_id:
                    # Valid action doesn't require specific property
                    return True
                elif action.property_id is None and valid.property_id:
                    # Action didn't specify property but valid action has one
                    # Accept it and use the valid action's property_id
                    action.property_id = valid.property_id
                    return True

        return False

    def _get_default_action(self, valid_actions: ValidActions) -> Action:
        """Get safest default action.

        Args:
            valid_actions: Valid actions to choose from

        Returns:
            Default action
        """
        # Priority order: roll_dice > end_turn > pass_property > first available
        priority = [
            ActionType.ROLL_DICE,
            ActionType.ROLL_FOR_DOUBLES,
            ActionType.END_TURN,
            ActionType.PASS_PROPERTY,
        ]

        for action_type in priority:
            for action in valid_actions.actions:
                if action.type == action_type:
                    return Action(type=action.type, property_id=action.property_id)

        # Last resort: first available action
        first = valid_actions.actions[0]
        return Action(type=first.type, property_id=first.property_id)
