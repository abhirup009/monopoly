"""Pytest configuration and fixtures."""

from uuid import uuid4

import pytest

from src.data.properties import ALL_PROPERTY_IDS
from src.db.models import GameModel, PlayerModel, PropertyStateModel


@pytest.fixture
def sample_game() -> GameModel:
    """Create a sample game model for testing."""
    game = GameModel(
        id=uuid4(),
        status="in_progress",
        current_player_index=0,
        turn_number=1,
        turn_phase="pre_roll",
        doubles_count=0,
        last_dice_roll=None,
        winner_id=None,
    )
    return game


@pytest.fixture
def sample_players(sample_game: GameModel) -> list[PlayerModel]:
    """Create sample player models for testing."""
    players = [
        PlayerModel(
            id=uuid4(),
            game_id=sample_game.id,
            name="Player 1",
            model="gpt-4",
            personality="aggressive",
            player_order=0,
            position=0,
            cash=1500,
            in_jail=False,
            jail_turns=0,
            get_out_of_jail_cards=0,
            is_bankrupt=False,
        ),
        PlayerModel(
            id=uuid4(),
            game_id=sample_game.id,
            name="Player 2",
            model="claude-3",
            personality="analytical",
            player_order=1,
            position=0,
            cash=1500,
            in_jail=False,
            jail_turns=0,
            get_out_of_jail_cards=0,
            is_bankrupt=False,
        ),
        PlayerModel(
            id=uuid4(),
            game_id=sample_game.id,
            name="Player 3",
            model="llama-3",
            personality="chaotic",
            player_order=2,
            position=0,
            cash=1500,
            in_jail=False,
            jail_turns=0,
            get_out_of_jail_cards=0,
            is_bankrupt=False,
        ),
    ]
    return players


@pytest.fixture
def sample_property_states(sample_game: GameModel) -> list[PropertyStateModel]:
    """Create sample property states for testing."""
    states = [
        PropertyStateModel(
            id=uuid4(),
            game_id=sample_game.id,
            property_id=prop_id,
            owner_id=None,
            houses=0,
        )
        for prop_id in ALL_PROPERTY_IDS
    ]
    return states


@pytest.fixture
def player_in_jail(sample_players: list[PlayerModel]) -> PlayerModel:
    """Create a player who is in jail."""
    player = sample_players[0]
    player.in_jail = True
    player.jail_turns = 0
    player.position = 10  # Jail position
    return player


@pytest.fixture
def player_with_jail_card(sample_players: list[PlayerModel]) -> PlayerModel:
    """Create a player with a get out of jail free card."""
    player = sample_players[0]
    player.in_jail = True
    player.jail_turns = 0
    player.position = 10
    player.get_out_of_jail_cards = 1
    return player


@pytest.fixture
def wealthy_player(sample_players: list[PlayerModel]) -> PlayerModel:
    """Create a player with lots of cash."""
    player = sample_players[0]
    player.cash = 5000
    return player


@pytest.fixture
def poor_player(sample_players: list[PlayerModel]) -> PlayerModel:
    """Create a player with little cash."""
    player = sample_players[0]
    player.cash = 20
    return player
