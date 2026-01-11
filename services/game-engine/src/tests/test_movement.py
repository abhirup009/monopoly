"""Tests for player movement logic."""

import pytest

from src.engine.movement import (
    BOARD_SIZE,
    GO_POSITION,
    JAIL_POSITION,
    GO_TO_JAIL_POSITION,
    move_player,
    move_to_position,
    send_to_jail,
    find_nearest_property_type,
    get_space_type,
    get_space_name,
    get_property_id_at_position,
)


class TestMovePlayer:
    """Tests for move_player function."""

    def test_simple_move(self):
        """Test simple forward movement."""
        result = move_player(0, 5)
        assert result.new_position == 5
        assert result.passed_go is False
        assert result.landed_on_go_to_jail is False
        assert result.spaces_moved == 5

    def test_move_wrap_around(self):
        """Test movement that wraps around the board."""
        result = move_player(35, 10)
        assert result.new_position == 5
        assert result.passed_go is True

    def test_pass_go(self):
        """Test passing GO during movement."""
        result = move_player(38, 4)
        assert result.new_position == 2
        assert result.passed_go is True

    def test_land_on_go_to_jail(self):
        """Test landing on Go To Jail."""
        result = move_player(25, 5)
        assert result.new_position == GO_TO_JAIL_POSITION
        assert result.landed_on_go_to_jail is True

    def test_negative_move_no_pass_go(self):
        """Test negative movement doesn't trigger pass GO."""
        result = move_player(5, -3)
        assert result.new_position == 2
        assert result.passed_go is False


class TestMoveToPosition:
    """Tests for move_to_position function."""

    def test_move_forward_no_wrap(self):
        """Test moving to a position ahead without wrapping."""
        result = move_to_position(5, 15)
        assert result.new_position == 15
        assert result.passed_go is False
        assert result.spaces_moved == 10

    def test_move_forward_with_wrap(self):
        """Test moving to a position that requires wrapping."""
        result = move_to_position(35, 5)
        assert result.new_position == 5
        assert result.passed_go is True

    def test_move_to_jail_no_pass_go(self):
        """Test moving to jail doesn't collect GO."""
        result = move_to_position(35, JAIL_POSITION)
        assert result.new_position == JAIL_POSITION
        assert result.passed_go is False  # Going to jail doesn't collect GO


class TestSendToJail:
    """Tests for send_to_jail function."""

    def test_send_to_jail(self):
        """Test getting jail position."""
        assert send_to_jail() == JAIL_POSITION


class TestFindNearestPropertyType:
    """Tests for find_nearest_property_type function."""

    def test_find_nearest_railroad_from_start(self):
        """Test finding nearest railroad from GO."""
        pos = find_nearest_property_type(0, "railroad")
        assert pos == 5  # Reading Railroad

    def test_find_nearest_railroad_middle(self):
        """Test finding nearest railroad from middle of board."""
        pos = find_nearest_property_type(10, "railroad")
        assert pos == 15  # Pennsylvania Railroad

    def test_find_nearest_railroad_wrap(self):
        """Test finding nearest railroad with wrap."""
        pos = find_nearest_property_type(36, "railroad")
        assert pos == 5  # Wraps to Reading Railroad

    def test_find_nearest_utility(self):
        """Test finding nearest utility."""
        pos = find_nearest_property_type(0, "utility")
        assert pos == 12  # Electric Company

        pos = find_nearest_property_type(15, "utility")
        assert pos == 28  # Water Works

        pos = find_nearest_property_type(30, "utility")
        assert pos == 12  # Wraps to Electric Company

    def test_invalid_property_type(self):
        """Test invalid property type raises error."""
        with pytest.raises(ValueError):
            find_nearest_property_type(0, "invalid")


class TestBoardConstants:
    """Tests for board constants."""

    def test_board_size(self):
        """Test board size is correct."""
        assert BOARD_SIZE == 40

    def test_go_position(self):
        """Test GO position is correct."""
        assert GO_POSITION == 0

    def test_jail_position(self):
        """Test jail position is correct."""
        assert JAIL_POSITION == 10

    def test_go_to_jail_position(self):
        """Test Go To Jail position is correct."""
        assert GO_TO_JAIL_POSITION == 30
