"""Pytest fixtures for Orchestrator Service tests."""

from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest

from src.clients.ai_agent import AIAgentClient
from src.clients.game_engine import GameEngineClient
from src.game.loop import GameLoopController, GameManager
from src.game.state import GameSession, GameSessionManager, GameSpeed
from src.ws.events import EventBus


@pytest.fixture
def mock_sio():
    """Create a mock Socket.IO server."""
    sio = MagicMock()
    sio.emit = AsyncMock()
    sio.enter_room = AsyncMock()
    sio.leave_room = AsyncMock()
    return sio


@pytest.fixture
def event_bus(mock_sio):
    """Create an EventBus with mock Socket.IO."""
    return EventBus(mock_sio)


@pytest.fixture
def mock_game_engine():
    """Create a mock Game Engine client."""
    client = MagicMock(spec=GameEngineClient)
    client.health_check = AsyncMock(return_value={"status": "healthy"})
    client.create_game = AsyncMock()
    client.start_game = AsyncMock()
    client.get_state = AsyncMock()
    client.get_valid_actions = AsyncMock()
    client.execute_action = AsyncMock()
    client.get_events = AsyncMock(return_value=[])
    client.close = AsyncMock()
    return client


@pytest.fixture
def mock_ai_agent():
    """Create a mock AI Agent client."""
    client = MagicMock(spec=AIAgentClient)
    client.health_check = AsyncMock(return_value={"status": "healthy"})
    client.create_game = AsyncMock()
    client.get_decision = AsyncMock()
    client.stop_game = AsyncMock()
    client.close = AsyncMock()
    return client


@pytest.fixture
def game_id():
    """Generate a random game ID."""
    return uuid4()


@pytest.fixture
def player_ids():
    """Generate player IDs."""
    return [uuid4() for _ in range(3)]


@pytest.fixture
def sample_agents(player_ids):
    """Create sample agent configurations."""
    return [
        {"player_id": str(player_ids[0]), "name": "Agent 1", "personality": "aggressive"},
        {"player_id": str(player_ids[1]), "name": "Agent 2", "personality": "analytical"},
        {"player_id": str(player_ids[2]), "name": "Agent 3", "personality": "chaotic"},
    ]


@pytest.fixture
def game_session(game_id, sample_agents):
    """Create a game session."""
    return GameSession(
        game_id=game_id,
        agents=sample_agents,
        speed=GameSpeed.FAST,
    )


@pytest.fixture
def session_manager():
    """Create a session manager."""
    return GameSessionManager()


@pytest.fixture
def sample_game_state(game_id, player_ids):
    """Create a sample game state."""
    return {
        "id": str(game_id),
        "status": "in_progress",
        "current_player_index": 0,
        "turn_number": 1,
        "turn_phase": "awaiting_roll",
        "players": [
            {
                "id": str(player_ids[0]),
                "name": "Agent 1",
                "position": 0,
                "cash": 1500,
                "is_bankrupt": False,
            },
            {
                "id": str(player_ids[1]),
                "name": "Agent 2",
                "position": 0,
                "cash": 1500,
                "is_bankrupt": False,
            },
            {
                "id": str(player_ids[2]),
                "name": "Agent 3",
                "position": 0,
                "cash": 1500,
                "is_bankrupt": False,
            },
        ],
        "properties": [],
    }


@pytest.fixture
def sample_valid_actions():
    """Create sample valid actions."""
    return {
        "actions": [
            {"type": "roll_dice"},
        ]
    }


@pytest.fixture
def game_loop_controller(mock_game_engine, mock_ai_agent, event_bus):
    """Create a game loop controller with mocks."""
    return GameLoopController(
        game_engine=mock_game_engine,
        ai_agent=mock_ai_agent,
        event_bus=event_bus,
        turn_timeout=5.0,
    )


@pytest.fixture
def game_manager(mock_game_engine, mock_ai_agent, event_bus):
    """Create a game manager with mocks."""
    return GameManager(
        game_engine=mock_game_engine,
        ai_agent=mock_ai_agent,
        event_bus=event_bus,
        turn_timeout=5.0,
    )
