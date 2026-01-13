"""Tests for dice rolling logic."""


from src.engine.dice import DiceRoll, get_total, is_doubles, roll_dice


class TestDiceRoll:
    """Tests for DiceRoll dataclass."""

    def test_total(self):
        """Test dice total calculation."""
        roll = DiceRoll(die1=3, die2=4)
        assert roll.total == 7

    def test_total_snake_eyes(self):
        """Test snake eyes total."""
        roll = DiceRoll(die1=1, die2=1)
        assert roll.total == 2

    def test_total_max(self):
        """Test maximum roll total."""
        roll = DiceRoll(die1=6, die2=6)
        assert roll.total == 12

    def test_is_doubles_true(self):
        """Test doubles detection."""
        roll = DiceRoll(die1=4, die2=4)
        assert roll.is_doubles is True

    def test_is_doubles_false(self):
        """Test non-doubles detection."""
        roll = DiceRoll(die1=3, die2=4)
        assert roll.is_doubles is False

    def test_to_list(self):
        """Test conversion to list."""
        roll = DiceRoll(die1=2, die2=5)
        assert roll.to_list() == [2, 5]


class TestRollDice:
    """Tests for roll_dice function."""

    def test_roll_dice_returns_dice_roll(self):
        """Test that roll_dice returns a DiceRoll."""
        roll = roll_dice()
        assert isinstance(roll, DiceRoll)

    def test_roll_dice_values_in_range(self):
        """Test that dice values are between 1 and 6."""
        for _ in range(100):
            roll = roll_dice()
            assert 1 <= roll.die1 <= 6
            assert 1 <= roll.die2 <= 6

    def test_roll_dice_total_in_range(self):
        """Test that total is between 2 and 12."""
        for _ in range(100):
            roll = roll_dice()
            assert 2 <= roll.total <= 12


class TestIsDubles:
    """Tests for is_doubles function."""

    def test_is_doubles_with_doubles(self):
        """Test is_doubles with matching values."""
        assert is_doubles([3, 3]) is True
        assert is_doubles([6, 6]) is True
        assert is_doubles([1, 1]) is True

    def test_is_doubles_without_doubles(self):
        """Test is_doubles with non-matching values."""
        assert is_doubles([3, 4]) is False
        assert is_doubles([1, 6]) is False

    def test_is_doubles_wrong_length(self):
        """Test is_doubles with wrong list length."""
        assert is_doubles([3]) is False
        assert is_doubles([1, 2, 3]) is False
        assert is_doubles([]) is False


class TestGetTotal:
    """Tests for get_total function."""

    def test_get_total(self):
        """Test get_total calculation."""
        assert get_total([3, 4]) == 7
        assert get_total([1, 1]) == 2
        assert get_total([6, 6]) == 12

    def test_get_total_empty(self):
        """Test get_total with empty list."""
        assert get_total([]) == 0
