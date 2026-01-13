"""Tests for jail mechanics."""


from src.db.models import PlayerModel
from src.engine.dice import DiceRoll
from src.engine.jail_rules import (
    JAIL_FINE,
    MAX_JAIL_TURNS,
    JailEscapeMethod,
    can_pay_jail_fine,
    can_use_jail_card,
    get_jail_options,
    pay_jail_fine,
    roll_for_doubles,
    should_force_jail_payment,
    use_jail_card,
)


class TestCanPayJailFine:
    """Tests for can_pay_jail_fine function."""

    def test_can_pay_with_enough_cash(self, player_in_jail: PlayerModel):
        """Test player can pay with sufficient funds."""
        player_in_jail.cash = 100
        can_pay, reason = can_pay_jail_fine(player_in_jail)
        assert can_pay is True
        assert reason == "OK"

    def test_cannot_pay_insufficient_funds(self, player_in_jail: PlayerModel):
        """Test player cannot pay with insufficient funds."""
        player_in_jail.cash = 30
        can_pay, reason = can_pay_jail_fine(player_in_jail)
        assert can_pay is False
        assert "Insufficient" in reason

    def test_cannot_pay_not_in_jail(self, sample_players: list[PlayerModel]):
        """Test player not in jail cannot pay."""
        player = sample_players[0]
        player.in_jail = False
        can_pay, reason = can_pay_jail_fine(player)
        assert can_pay is False
        assert "not in jail" in reason


class TestCanUseJailCard:
    """Tests for can_use_jail_card function."""

    def test_can_use_with_card(self, player_with_jail_card: PlayerModel):
        """Test player can use card when they have one."""
        can_use, reason = can_use_jail_card(player_with_jail_card)
        assert can_use is True
        assert reason == "OK"

    def test_cannot_use_no_card(self, player_in_jail: PlayerModel):
        """Test player cannot use card when they don't have one."""
        player_in_jail.get_out_of_jail_cards = 0
        can_use, reason = can_use_jail_card(player_in_jail)
        assert can_use is False
        assert "No Get Out of Jail" in reason

    def test_cannot_use_not_in_jail(self, sample_players: list[PlayerModel]):
        """Test player not in jail cannot use card."""
        player = sample_players[0]
        player.in_jail = False
        player.get_out_of_jail_cards = 1
        can_use, reason = can_use_jail_card(player)
        assert can_use is False


class TestPayJailFine:
    """Tests for pay_jail_fine function."""

    def test_pay_fine_success(self, player_in_jail: PlayerModel):
        """Test successful fine payment."""
        player_in_jail.cash = 100
        result = pay_jail_fine(player_in_jail)
        assert result.escaped is True
        assert result.method == JailEscapeMethod.PAY_FINE
        assert result.cost == JAIL_FINE

    def test_pay_fine_insufficient_funds(self, player_in_jail: PlayerModel):
        """Test failed fine payment."""
        player_in_jail.cash = 30
        result = pay_jail_fine(player_in_jail)
        assert result.escaped is False
        assert result.method is None
        assert result.cost == 0


class TestUseJailCard:
    """Tests for use_jail_card function."""

    def test_use_card_success(self, player_with_jail_card: PlayerModel):
        """Test successful card use."""
        result = use_jail_card(player_with_jail_card)
        assert result.escaped is True
        assert result.method == JailEscapeMethod.USE_CARD
        assert result.cost == 0

    def test_use_card_no_card(self, player_in_jail: PlayerModel):
        """Test failed card use (no card)."""
        player_in_jail.get_out_of_jail_cards = 0
        result = use_jail_card(player_in_jail)
        assert result.escaped is False
        assert result.method is None


class TestRollForDoubles:
    """Tests for roll_for_doubles function."""

    def test_roll_doubles_escape(self, player_in_jail: PlayerModel):
        """Test escaping with doubles."""
        dice = DiceRoll(die1=4, die2=4)
        result = roll_for_doubles(player_in_jail, dice)
        assert result.escaped is True
        assert result.method == JailEscapeMethod.ROLL_DOUBLES
        assert result.cost == 0

    def test_roll_no_doubles_stay(self, player_in_jail: PlayerModel):
        """Test staying in jail without doubles."""
        player_in_jail.jail_turns = 0
        dice = DiceRoll(die1=3, die2=4)
        result = roll_for_doubles(player_in_jail, dice)
        assert result.escaped is False
        assert result.method is None

    def test_roll_third_turn_forced_pay(self, player_in_jail: PlayerModel):
        """Test forced payment on third turn."""
        player_in_jail.jail_turns = MAX_JAIL_TURNS - 1  # 2
        dice = DiceRoll(die1=3, die2=4)
        result = roll_for_doubles(player_in_jail, dice)
        assert result.escaped is True
        assert result.method == JailEscapeMethod.FORCED_PAY
        assert result.cost == JAIL_FINE


class TestShouldForceJailPayment:
    """Tests for should_force_jail_payment function."""

    def test_should_force_after_max_turns(self, player_in_jail: PlayerModel):
        """Test force payment after max turns."""
        player_in_jail.jail_turns = MAX_JAIL_TURNS
        assert should_force_jail_payment(player_in_jail) is True

    def test_should_not_force_before_max_turns(self, player_in_jail: PlayerModel):
        """Test no force before max turns."""
        player_in_jail.jail_turns = 1
        assert should_force_jail_payment(player_in_jail) is False


class TestGetJailOptions:
    """Tests for get_jail_options function."""

    def test_all_options_available(self, player_with_jail_card: PlayerModel):
        """Test all options available for wealthy player with card."""
        player_with_jail_card.cash = 100
        options = get_jail_options(player_with_jail_card)
        assert "pay_fine" in options
        assert "use_card" in options
        assert "roll_for_doubles" in options

    def test_only_roll_option(self, player_in_jail: PlayerModel):
        """Test only roll option for poor player without card."""
        player_in_jail.cash = 20
        player_in_jail.get_out_of_jail_cards = 0
        options = get_jail_options(player_in_jail)
        assert "pay_fine" not in options
        assert "use_card" not in options
        assert "roll_for_doubles" in options


class TestConstants:
    """Tests for jail constants."""

    def test_jail_fine(self):
        """Test jail fine amount."""
        assert JAIL_FINE == 50

    def test_max_jail_turns(self):
        """Test max jail turns."""
        assert MAX_JAIL_TURNS == 3
