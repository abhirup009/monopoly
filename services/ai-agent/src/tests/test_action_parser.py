"""Tests for action parser."""

import pytest

from src.client.models import ActionType, ValidAction, ValidActions
from src.parser.action_parser import ActionParser


class TestActionParser:
    """Tests for ActionParser class."""

    @pytest.fixture
    def parser(self):
        """Create action parser instance."""
        return ActionParser()

    @pytest.fixture
    def buy_or_pass_actions(self, sample_players):
        """Valid actions for buy/pass decision."""
        return ValidActions(
            player_id=sample_players[0].id,
            turn_phase="post_roll",
            actions=[
                ValidAction(type=ActionType.BUY_PROPERTY, property_id="boardwalk", cost=400),
                ValidAction(type=ActionType.PASS_PROPERTY),
            ],
        )

    def test_parse_valid_json_buy(self, parser, buy_or_pass_actions):
        """Test parsing valid JSON for buy action."""
        response = '{"action": "buy_property", "property_id": "boardwalk"}'
        action = parser.parse(response, buy_or_pass_actions)

        assert action.type == ActionType.BUY_PROPERTY
        assert action.property_id == "boardwalk"

    def test_parse_valid_json_pass(self, parser, buy_or_pass_actions):
        """Test parsing valid JSON for pass action."""
        response = '{"action": "pass_property", "property_id": null}'
        action = parser.parse(response, buy_or_pass_actions)

        assert action.type == ActionType.PASS_PROPERTY
        assert action.property_id is None

    def test_parse_json_with_surrounding_text(self, parser, buy_or_pass_actions):
        """Test parsing JSON embedded in text."""
        response = '''I think I should buy this property!
        {"action": "buy_property", "property_id": "boardwalk"}
        That's my decision.'''
        action = parser.parse(response, buy_or_pass_actions)

        assert action.type == ActionType.BUY_PROPERTY
        assert action.property_id == "boardwalk"

    def test_parse_json_single_quotes(self, parser, buy_or_pass_actions):
        """Test parsing JSON with single quotes."""
        response = "{'action': 'buy_property', 'property_id': 'boardwalk'}"
        action = parser.parse(response, buy_or_pass_actions)

        assert action.type == ActionType.BUY_PROPERTY

    def test_parse_keyword_buy(self, parser, buy_or_pass_actions):
        """Test keyword parsing for buy."""
        response = "I want to buy this property!"
        action = parser.parse(response, buy_or_pass_actions)

        assert action.type == ActionType.BUY_PROPERTY

    def test_parse_keyword_pass(self, parser, buy_or_pass_actions):
        """Test keyword parsing for pass."""
        response = "I'll pass on this one."
        action = parser.parse(response, buy_or_pass_actions)

        assert action.type == ActionType.PASS_PROPERTY

    def test_parse_keyword_decline(self, parser, buy_or_pass_actions):
        """Test keyword parsing for decline."""
        response = "No thanks, I decline this property."
        action = parser.parse(response, buy_or_pass_actions)

        assert action.type == ActionType.PASS_PROPERTY

    def test_parse_roll_dice(self, parser, roll_dice_actions):
        """Test parsing roll dice action."""
        response = '{"action": "roll_dice", "property_id": null}'
        action = parser.parse(response, roll_dice_actions)

        assert action.type == ActionType.ROLL_DICE

    def test_parse_roll_keyword(self, parser, roll_dice_actions):
        """Test keyword parsing for roll."""
        response = "Let's roll the dice!"
        action = parser.parse(response, roll_dice_actions)

        assert action.type == ActionType.ROLL_DICE

    def test_parse_invalid_returns_default(self, parser, buy_or_pass_actions):
        """Test that invalid response returns default action."""
        response = "completely invalid response with no keywords"
        action = parser.parse(response, buy_or_pass_actions)

        # Should return first priority default (pass_property in this case)
        assert action.type == ActionType.PASS_PROPERTY

    def test_parse_end_turn(self, parser, sample_valid_actions):
        """Test parsing end turn action."""
        response = '{"action": "end_turn", "property_id": null}'
        action = parser.parse(response, sample_valid_actions)

        assert action.type == ActionType.END_TURN

    def test_parse_end_turn_keyword(self, parser, sample_valid_actions):
        """Test keyword parsing for end turn."""
        response = "I'm done, end my turn."
        action = parser.parse(response, sample_valid_actions)

        assert action.type == ActionType.END_TURN

    def test_parse_action_not_in_valid_list(self, parser, roll_dice_actions):
        """Test that invalid action falls back to default."""
        # Response tries to buy but only roll_dice is valid
        response = '{"action": "buy_property", "property_id": "boardwalk"}'
        action = parser.parse(response, roll_dice_actions)

        # Should fall back to roll_dice (the only valid action)
        assert action.type == ActionType.ROLL_DICE

    def test_parse_empty_response(self, parser, roll_dice_actions):
        """Test parsing empty response."""
        response = ""
        action = parser.parse(response, roll_dice_actions)

        assert action.type == ActionType.ROLL_DICE

    def test_parse_null_property_variations(self, parser, roll_dice_actions):
        """Test various null property_id formats."""
        responses = [
            '{"action": "roll_dice", "property_id": null}',
            '{"action": "roll_dice", "property_id": "null"}',
            '{"action": "roll_dice", "property_id": "none"}',
            '{"action": "roll_dice", "property_id": ""}',
        ]

        for response in responses:
            action = parser.parse(response, roll_dice_actions)
            assert action.type == ActionType.ROLL_DICE
            assert action.property_id is None


class TestActionParserDefaults:
    """Tests for default action selection."""

    @pytest.fixture
    def parser(self):
        """Create action parser instance."""
        return ActionParser()

    def test_default_prefers_roll_dice(self, parser, sample_players):
        """Test that default prefers roll_dice when available."""
        valid_actions = ValidActions(
            player_id=sample_players[0].id,
            turn_phase="pre_roll",
            actions=[
                ValidAction(type=ActionType.END_TURN),
                ValidAction(type=ActionType.ROLL_DICE),
            ],
        )

        action = parser._get_default_action(valid_actions)
        assert action.type == ActionType.ROLL_DICE

    def test_default_prefers_end_turn_over_pass(self, parser, sample_players):
        """Test that default prefers end_turn over pass_property."""
        valid_actions = ValidActions(
            player_id=sample_players[0].id,
            turn_phase="post_roll",
            actions=[
                ValidAction(type=ActionType.PASS_PROPERTY),
                ValidAction(type=ActionType.END_TURN),
            ],
        )

        action = parser._get_default_action(valid_actions)
        assert action.type == ActionType.END_TURN

    def test_default_falls_back_to_first(self, parser, sample_players):
        """Test that default falls back to first action."""
        valid_actions = ValidActions(
            player_id=sample_players[0].id,
            turn_phase="post_roll",
            actions=[
                ValidAction(type=ActionType.BUILD_HOUSE, property_id="boardwalk"),
                ValidAction(type=ActionType.BUILD_HOTEL, property_id="boardwalk"),
            ],
        )

        action = parser._get_default_action(valid_actions)
        assert action.type == ActionType.BUILD_HOUSE
