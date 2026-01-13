"""Tests for personality configurations."""

import pytest

from src.prompts.personalities import (
    PERSONALITIES,
    PersonalityConfig,
    get_personality,
    list_personalities,
)


class TestPersonalityConfig:
    """Tests for PersonalityConfig dataclass."""

    def test_personality_config_creation(self):
        """Test creating a personality config."""
        config = PersonalityConfig(
            name="test",
            temperature=0.5,
            system_prompt="Test prompt",
            decision_style="test style",
        )

        assert config.name == "test"
        assert config.temperature == 0.5
        assert config.system_prompt == "Test prompt"
        assert config.decision_style == "test style"


class TestPersonalities:
    """Tests for personality definitions."""

    def test_all_personalities_defined(self):
        """Test that all expected personalities are defined."""
        expected = {"aggressive", "analytical", "chaotic"}
        actual = set(PERSONALITIES.keys())
        assert expected == actual

    def test_aggressive_personality(self, aggressive_personality):
        """Test aggressive personality config."""
        assert aggressive_personality.name == "aggressive"
        assert aggressive_personality.temperature == 0.8
        assert "AGGRESSIVE" in aggressive_personality.system_prompt
        assert "bold" in aggressive_personality.decision_style

    def test_analytical_personality(self, analytical_personality):
        """Test analytical personality config."""
        assert analytical_personality.name == "analytical"
        assert analytical_personality.temperature == 0.3
        assert "ANALYTICAL" in analytical_personality.system_prompt
        assert "calculated" in analytical_personality.decision_style

    def test_chaotic_personality(self, chaotic_personality):
        """Test chaotic personality config."""
        assert chaotic_personality.name == "chaotic"
        assert chaotic_personality.temperature == 1.0
        assert "CHAOTIC" in chaotic_personality.system_prompt
        assert "unpredictable" in chaotic_personality.decision_style

    def test_personality_prompts_have_placeholder(self):
        """Test that all personalities have player_name placeholder."""
        for name, config in PERSONALITIES.items():
            assert "{player_name}" in config.system_prompt, f"{name} missing placeholder"

    def test_personality_prompts_have_json_instruction(self):
        """Test that all personalities have JSON format instruction."""
        for name, config in PERSONALITIES.items():
            assert "JSON" in config.system_prompt, f"{name} missing JSON instruction"


class TestGetPersonality:
    """Tests for get_personality function."""

    def test_get_aggressive(self):
        """Test getting aggressive personality."""
        config = get_personality("aggressive")
        assert config.name == "aggressive"

    def test_get_analytical(self):
        """Test getting analytical personality."""
        config = get_personality("analytical")
        assert config.name == "analytical"

    def test_get_chaotic(self):
        """Test getting chaotic personality."""
        config = get_personality("chaotic")
        assert config.name == "chaotic"

    def test_get_unknown_defaults_to_analytical(self):
        """Test that unknown personality defaults to analytical."""
        config = get_personality("unknown")
        assert config.name == "analytical"

    def test_get_case_insensitive(self):
        """Test that personality lookup is case insensitive."""
        config = get_personality("AGGRESSIVE")
        assert config.name == "aggressive"

        config = get_personality("Analytical")
        assert config.name == "analytical"


class TestListPersonalities:
    """Tests for list_personalities function."""

    def test_list_personalities(self):
        """Test listing all personalities."""
        personalities = list_personalities()

        assert "aggressive" in personalities
        assert "analytical" in personalities
        assert "chaotic" in personalities
        assert len(personalities) == 3

    def test_list_personalities_returns_list(self):
        """Test that list_personalities returns a list."""
        personalities = list_personalities()
        assert isinstance(personalities, list)
