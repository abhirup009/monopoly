"""Pytest fixtures for AI Agent Service tests."""

import pytest
from uuid import uuid4

from src.client.models import (
    Action,
    ActionType,
    GameState,
    GameStatus,
    Player,
    PropertyState,
    TurnPhase,
    ValidAction,
    ValidActions,
)
from src.llm.session import AgentSession, SessionManager
from src.prompts.personalities import get_personality


@pytest.fixture
def sample_player_id():
    """Generate a sample player ID."""
    return uuid4()


@pytest.fixture
def sample_game_id():
    """Generate a sample game ID."""
    return uuid4()


@pytest.fixture
def sample_players():
    """Create sample players."""
    return [
        Player(
            id=uuid4(),
            name="Baron Von Moneybags",
            model="llama3",
            personality="aggressive",
            position=5,
            cash=1200,
            in_jail=False,
            jail_turns=0,
            get_out_of_jail_cards=0,
            is_bankrupt=False,
            player_order=0,
        ),
        Player(
            id=uuid4(),
            name="Professor Pennypincher",
            model="llama3",
            personality="analytical",
            position=12,
            cash=1800,
            in_jail=False,
            jail_turns=0,
            get_out_of_jail_cards=1,
            is_bankrupt=False,
            player_order=1,
        ),
        Player(
            id=uuid4(),
            name="Lady Luck",
            model="llama3",
            personality="chaotic",
            position=24,
            cash=900,
            in_jail=False,
            jail_turns=0,
            get_out_of_jail_cards=0,
            is_bankrupt=False,
            player_order=2,
        ),
    ]


@pytest.fixture
def sample_properties(sample_players):
    """Create sample property states."""
    return [
        PropertyState(property_id="mediterranean", owner_id=sample_players[0].id, houses=0),
        PropertyState(property_id="baltic", owner_id=sample_players[0].id, houses=0),
        PropertyState(property_id="reading_rr", owner_id=sample_players[1].id, houses=0),
        PropertyState(property_id="boardwalk", owner_id=None, houses=0),
        PropertyState(property_id="park_place", owner_id=None, houses=0),
    ]


@pytest.fixture
def sample_game_state(sample_game_id, sample_players, sample_properties):
    """Create a sample game state."""
    return GameState(
        id=sample_game_id,
        status=GameStatus.IN_PROGRESS,
        current_player_index=0,
        turn_number=10,
        turn_phase=TurnPhase.POST_ROLL,
        free_parking_pool=0,
        winner_id=None,
        players=sample_players,
        properties=sample_properties,
    )


@pytest.fixture
def sample_valid_actions(sample_players):
    """Create sample valid actions."""
    return ValidActions(
        player_id=sample_players[0].id,
        turn_phase=TurnPhase.POST_ROLL,
        actions=[
            ValidAction(type=ActionType.BUY_PROPERTY, property_id="boardwalk", cost=400),
            ValidAction(type=ActionType.PASS_PROPERTY, property_id=None, cost=None),
            ValidAction(type=ActionType.END_TURN, property_id=None, cost=None),
        ],
    )


@pytest.fixture
def roll_dice_actions(sample_players):
    """Create valid actions for rolling dice."""
    return ValidActions(
        player_id=sample_players[0].id,
        turn_phase=TurnPhase.PRE_ROLL,
        actions=[
            ValidAction(type=ActionType.ROLL_DICE, property_id=None, cost=None),
        ],
    )


@pytest.fixture
def session_manager():
    """Create a session manager."""
    return SessionManager()


@pytest.fixture
def agent_session(sample_player_id):
    """Create an agent session."""
    return AgentSession(
        agent_id=sample_player_id,
        personality="analytical",
        temperature=0.3,
    )


@pytest.fixture
def aggressive_personality():
    """Get aggressive personality config."""
    return get_personality("aggressive")


@pytest.fixture
def analytical_personality():
    """Get analytical personality config."""
    return get_personality("analytical")


@pytest.fixture
def chaotic_personality():
    """Get chaotic personality config."""
    return get_personality("chaotic")
