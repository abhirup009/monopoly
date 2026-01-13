"""Tests for prompt builder."""

import pytest

from src.prompts.builder import PromptBuilder
from src.prompts.templates import get_property_name, get_space_name, get_color_group


class TestPromptBuilder:
    """Tests for PromptBuilder class."""

    @pytest.fixture
    def builder(self):
        """Create prompt builder instance."""
        return PromptBuilder()

    def test_build_decision_prompt_contains_player_info(
        self,
        builder,
        sample_game_state,
        sample_valid_actions,
    ):
        """Test that prompt contains player information."""
        prompt = builder.build_decision_prompt(
            game_state=sample_game_state,
            valid_actions=sample_valid_actions,
            player_name="Baron Von Moneybags",
        )

        assert "Baron Von Moneybags" in prompt
        assert "$1200" in prompt  # Player's cash
        assert "Reading Railroad" in prompt or "Position 5" in prompt

    def test_build_decision_prompt_contains_valid_actions(
        self,
        builder,
        sample_game_state,
        sample_valid_actions,
    ):
        """Test that prompt contains valid actions."""
        prompt = builder.build_decision_prompt(
            game_state=sample_game_state,
            valid_actions=sample_valid_actions,
            player_name="Baron Von Moneybags",
        )

        assert "buy_property" in prompt
        assert "pass_property" in prompt
        assert "end_turn" in prompt
        assert "boardwalk" in prompt

    def test_build_decision_prompt_contains_json_format(
        self,
        builder,
        sample_game_state,
        sample_valid_actions,
    ):
        """Test that prompt contains JSON format instructions."""
        prompt = builder.build_decision_prompt(
            game_state=sample_game_state,
            valid_actions=sample_valid_actions,
            player_name="Baron Von Moneybags",
        )

        assert '{"action":' in prompt or '"action"' in prompt
        assert "JSON" in prompt

    def test_build_decision_prompt_contains_opponents(
        self,
        builder,
        sample_game_state,
        sample_valid_actions,
    ):
        """Test that prompt contains opponent information."""
        prompt = builder.build_decision_prompt(
            game_state=sample_game_state,
            valid_actions=sample_valid_actions,
            player_name="Baron Von Moneybags",
        )

        assert "Professor Pennypincher" in prompt
        assert "Lady Luck" in prompt

    def test_build_decision_prompt_shows_turn_number(
        self,
        builder,
        sample_game_state,
        sample_valid_actions,
    ):
        """Test that prompt shows turn number."""
        prompt = builder.build_decision_prompt(
            game_state=sample_game_state,
            valid_actions=sample_valid_actions,
            player_name="Baron Von Moneybags",
        )

        assert "Turn 10" in prompt

    def test_build_summary_prompt(self, builder, sample_game_state):
        """Test building summary prompt."""
        summary = builder.build_summary_prompt(sample_game_state)

        assert "Turn: 10" in summary
        assert "Baron Von Moneybags" in summary
        assert "Professor Pennypincher" in summary
        assert "Lady Luck" in summary


class TestTemplates:
    """Tests for prompt templates."""

    def test_get_space_name_go(self):
        """Test getting GO space name."""
        assert get_space_name(0) == "GO"

    def test_get_space_name_jail(self):
        """Test getting Jail space name."""
        assert get_space_name(10) == "Jail / Just Visiting"

    def test_get_space_name_boardwalk(self):
        """Test getting Boardwalk space name."""
        assert get_space_name(39) == "Boardwalk"

    def test_get_space_name_invalid(self):
        """Test getting invalid space name."""
        assert get_space_name(100) == "Position 100"

    def test_get_property_name(self):
        """Test getting property names."""
        assert get_property_name("mediterranean") == "Mediterranean Avenue"
        assert get_property_name("boardwalk") == "Boardwalk"
        assert get_property_name("reading_rr") == "Reading Railroad"

    def test_get_property_name_unknown(self):
        """Test getting unknown property name."""
        assert get_property_name("fake_property") == "Fake Property"

    def test_get_color_group(self):
        """Test getting color groups."""
        assert get_color_group("mediterranean") == "brown"
        assert get_color_group("boardwalk") == "dark_blue"
        assert get_color_group("reading_rr") is None  # Railroad
