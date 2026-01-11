"""Tests for bankruptcy detection and handling."""

import pytest
from uuid import uuid4

from src.engine.bankruptcy import (
    check_bankruptcy,
    can_afford,
    get_net_worth,
    handle_bankruptcy_to_bank,
    handle_bankruptcy_to_player,
    count_active_players,
    get_winner,
    is_game_over,
)
from src.db.models import PlayerModel, PropertyStateModel


class TestCheckBankruptcy:
    """Tests for check_bankruptcy function."""

    def test_not_bankrupt_with_funds(self, wealthy_player: PlayerModel):
        """Test player with funds is not bankrupt."""
        result = check_bankruptcy(wealthy_player, 100)
        assert result.is_bankrupt is False
        assert result.debt_amount == 100

    def test_bankrupt_without_funds(self, poor_player: PlayerModel):
        """Test player without funds is bankrupt."""
        result = check_bankruptcy(poor_player, 100)
        assert result.is_bankrupt is True
        assert result.debt_amount == 100

    def test_bankruptcy_to_bank(self, poor_player: PlayerModel):
        """Test bankruptcy to bank (no creditor)."""
        result = check_bankruptcy(poor_player, 100, creditor_id=None)
        assert result.is_bankrupt is True
        assert result.creditor_id is None

    def test_bankruptcy_to_player(
        self, poor_player: PlayerModel, sample_players: list[PlayerModel]
    ):
        """Test bankruptcy to another player."""
        creditor = sample_players[1]
        result = check_bankruptcy(poor_player, 100, creditor_id=creditor.id)
        assert result.is_bankrupt is True
        assert result.creditor_id == creditor.id


class TestCanAfford:
    """Tests for can_afford function."""

    def test_can_afford_when_wealthy(self, wealthy_player: PlayerModel):
        """Test wealthy player can afford."""
        assert can_afford(wealthy_player, 1000) is True

    def test_cannot_afford_when_poor(self, poor_player: PlayerModel):
        """Test poor player cannot afford."""
        assert can_afford(poor_player, 100) is False

    def test_can_afford_exact_amount(self, sample_players: list[PlayerModel]):
        """Test player can afford exact amount."""
        player = sample_players[0]
        player.cash = 100
        assert can_afford(player, 100) is True


class TestGetNetWorth:
    """Tests for get_net_worth function."""

    def test_net_worth_cash_only(
        self,
        sample_players: list[PlayerModel],
        sample_property_states: list[PropertyStateModel],
    ):
        """Test net worth with cash only."""
        player = sample_players[0]
        player.cash = 1000
        net_worth = get_net_worth(player, sample_property_states)
        assert net_worth == 1000

    def test_net_worth_with_property(
        self,
        sample_players: list[PlayerModel],
        sample_property_states: list[PropertyStateModel],
    ):
        """Test net worth with property."""
        player = sample_players[0]
        player.cash = 1000

        # Own Mediterranean (price $60)
        prop = next(
            ps for ps in sample_property_states if ps.property_id == "mediterranean"
        )
        prop.owner_id = player.id

        net_worth = get_net_worth(player, sample_property_states)
        assert net_worth == 1060  # 1000 + 60


class TestHandleBankruptcy:
    """Tests for bankruptcy handling functions."""

    def test_handle_bankruptcy_to_bank(
        self,
        sample_players: list[PlayerModel],
        sample_property_states: list[PropertyStateModel],
    ):
        """Test handling bankruptcy to bank."""
        player = sample_players[0]

        # Own some properties
        for prop in sample_property_states:
            if prop.property_id in ["mediterranean", "baltic"]:
                prop.owner_id = player.id

        released = handle_bankruptcy_to_bank(player, sample_property_states)
        assert "mediterranean" in released
        assert "baltic" in released

    def test_handle_bankruptcy_to_player(
        self,
        sample_players: list[PlayerModel],
        sample_property_states: list[PropertyStateModel],
    ):
        """Test handling bankruptcy to another player."""
        bankrupt = sample_players[0]
        creditor = sample_players[1]

        # Own some properties
        for prop in sample_property_states:
            if prop.property_id in ["mediterranean", "baltic"]:
                prop.owner_id = bankrupt.id

        transferred = handle_bankruptcy_to_player(
            bankrupt, creditor, sample_property_states
        )
        assert "mediterranean" in transferred
        assert "baltic" in transferred


class TestCountActivePlayers:
    """Tests for count_active_players function."""

    def test_all_active(self, sample_players: list[PlayerModel]):
        """Test counting when all players active."""
        count = count_active_players(sample_players)
        assert count == 3

    def test_one_bankrupt(self, sample_players: list[PlayerModel]):
        """Test counting with one bankrupt."""
        sample_players[0].is_bankrupt = True
        count = count_active_players(sample_players)
        assert count == 2

    def test_all_but_one_bankrupt(self, sample_players: list[PlayerModel]):
        """Test counting with all but one bankrupt."""
        sample_players[0].is_bankrupt = True
        sample_players[1].is_bankrupt = True
        count = count_active_players(sample_players)
        assert count == 1


class TestGetWinner:
    """Tests for get_winner function."""

    def test_no_winner_multiple_active(self, sample_players: list[PlayerModel]):
        """Test no winner when multiple active."""
        winner = get_winner(sample_players)
        assert winner is None

    def test_winner_one_active(self, sample_players: list[PlayerModel]):
        """Test winner when one player left."""
        sample_players[0].is_bankrupt = True
        sample_players[1].is_bankrupt = True
        winner = get_winner(sample_players)
        assert winner == sample_players[2]


class TestIsGameOver:
    """Tests for is_game_over function."""

    def test_not_over_multiple_active(self, sample_players: list[PlayerModel]):
        """Test game not over with multiple active."""
        assert is_game_over(sample_players) is False

    def test_over_one_active(self, sample_players: list[PlayerModel]):
        """Test game over with one active."""
        sample_players[0].is_bankrupt = True
        sample_players[1].is_bankrupt = True
        assert is_game_over(sample_players) is True
