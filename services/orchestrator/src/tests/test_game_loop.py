"""Tests for game loop controller."""

import asyncio
from unittest.mock import AsyncMock

import pytest


class TestGameLoopController:
    """Tests for GameLoopController class."""

    @pytest.mark.asyncio
    async def test_execute_turn(
        self,
        game_loop_controller,
        game_session,
        mock_game_engine,
        mock_ai_agent,
        sample_game_state,
        sample_valid_actions,
    ):
        """Test executing a single turn."""
        mock_game_engine.get_valid_actions.return_value = sample_valid_actions
        mock_ai_agent.get_decision.return_value = {"action": {"type": "roll_dice"}}
        mock_game_engine.execute_action.return_value = {"success": True}

        await game_loop_controller._execute_turn(game_session, sample_game_state)

        mock_game_engine.get_valid_actions.assert_called_once()
        mock_ai_agent.get_decision.assert_called_once()
        mock_game_engine.execute_action.assert_called_once()

    @pytest.mark.asyncio
    async def test_execute_turn_timeout(
        self,
        game_loop_controller,
        game_session,
        mock_game_engine,
        mock_ai_agent,
        sample_game_state,
        sample_valid_actions,
        event_bus,
    ):
        """Test turn timeout handling."""
        mock_game_engine.get_valid_actions.return_value = sample_valid_actions

        # Make AI decision timeout
        async def slow_decision(*args, **kwargs):
            await asyncio.sleep(10)
            return {"action": {"type": "roll_dice"}}

        mock_ai_agent.get_decision = AsyncMock(side_effect=slow_decision)
        mock_game_engine.execute_action.return_value = {"success": True}

        # Use a very short timeout
        game_loop_controller.turn_timeout = 0.1

        await game_loop_controller._execute_turn(game_session, sample_game_state)

        # Should have used default action
        mock_game_engine.execute_action.assert_called_once()

    def test_get_default_action_end_turn(self, game_loop_controller):
        """Test default action selection prefers end_turn."""
        valid_actions = [
            {"type": "buy_property", "property_id": "baltic_ave"},
            {"type": "end_turn"},
        ]

        action = game_loop_controller._get_default_action(valid_actions)
        assert action["type"] == "end_turn"

    def test_get_default_action_pass_property(self, game_loop_controller):
        """Test default action selection prefers pass_property."""
        valid_actions = [
            {"type": "buy_property", "property_id": "baltic_ave"},
            {"type": "pass_property"},
        ]

        action = game_loop_controller._get_default_action(valid_actions)
        assert action["type"] == "pass_property"

    def test_get_default_action_roll_dice(self, game_loop_controller):
        """Test default action selection with roll_dice."""
        valid_actions = [
            {"type": "roll_dice"},
            {"type": "build_house", "property_id": "baltic_ave"},
        ]

        action = game_loop_controller._get_default_action(valid_actions)
        assert action["type"] == "roll_dice"

    def test_get_default_action_fallback(self, game_loop_controller):
        """Test default action fallback to first action."""
        valid_actions = [
            {"type": "build_house", "property_id": "baltic_ave"},
        ]

        action = game_loop_controller._get_default_action(valid_actions)
        assert action["type"] == "build_house"

    def test_stop_game(self, game_loop_controller, game_session):
        """Test stopping a game."""
        game_session.is_running = True

        game_loop_controller.stop_game(game_session)

        assert game_session.is_running is False


class TestGameManager:
    """Tests for GameManager class."""

    @pytest.mark.asyncio
    async def test_start_and_stop_game(
        self,
        game_manager,
        game_session,
        mock_game_engine,
        sample_game_state,
    ):
        """Test starting and stopping a game."""
        # Set up mock to return completed status after first call
        call_count = 0

        async def get_state_mock(game_id):
            nonlocal call_count
            call_count += 1
            if call_count > 1:
                return {**sample_game_state, "status": "completed"}
            return sample_game_state

        mock_game_engine.get_state = AsyncMock(side_effect=get_state_mock)
        mock_game_engine.get_valid_actions.return_value = {"actions": [{"type": "end_turn"}]}
        mock_game_engine.execute_action.return_value = {"success": True}

        # Start game
        await game_manager.start_game(game_session)

        assert game_manager.is_game_running(game_session.game_id)

        # Stop game
        stopped = await game_manager.stop_game(game_session.game_id)
        assert stopped is True

    @pytest.mark.asyncio
    async def test_start_duplicate_game(self, game_manager, game_session, mock_game_engine):
        """Test starting a game that's already running."""
        # Make the game loop run indefinitely
        mock_game_engine.get_state = AsyncMock(
            return_value={"status": "in_progress", "players": [], "turn_number": 1}
        )

        await game_manager.start_game(game_session)

        with pytest.raises(ValueError, match="already running"):
            await game_manager.start_game(game_session)

        # Cleanup
        await game_manager.stop_game(game_session.game_id)

    @pytest.mark.asyncio
    async def test_stop_nonexistent_game(self, game_manager):
        """Test stopping a non-existent game."""
        from uuid import uuid4

        stopped = await game_manager.stop_game(uuid4())
        assert stopped is False

    def test_is_game_running_false(self, game_manager):
        """Test checking if non-existent game is running."""
        from uuid import uuid4

        assert game_manager.is_game_running(uuid4()) is False
