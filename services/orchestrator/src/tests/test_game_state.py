"""Tests for game state management."""

from uuid import uuid4

from src.game.state import SPEED_DELAYS, GameSession, GameSpeed


class TestGameSpeed:
    """Tests for GameSpeed enum."""

    def test_speed_values(self):
        """Test all speed values exist."""
        assert GameSpeed.FAST == "fast"
        assert GameSpeed.NORMAL == "normal"
        assert GameSpeed.SLOW == "slow"

    def test_speed_delays(self):
        """Test speed delay values."""
        assert SPEED_DELAYS[GameSpeed.FAST] == 0.5
        assert SPEED_DELAYS[GameSpeed.NORMAL] == 2.0
        assert SPEED_DELAYS[GameSpeed.SLOW] == 5.0


class TestGameSession:
    """Tests for GameSession class."""

    def test_create_session(self, game_id, sample_agents):
        """Test creating a game session."""
        session = GameSession(
            game_id=game_id,
            agents=sample_agents,
            speed=GameSpeed.NORMAL,
        )

        assert session.game_id == game_id
        assert session.agents == sample_agents
        assert session.speed == GameSpeed.NORMAL
        assert session.is_running is False
        assert session.turn_count == 0
        assert session.current_state is None

    def test_set_speed_with_enum(self, game_session):
        """Test setting speed with GameSpeed enum."""
        game_session.set_speed(GameSpeed.SLOW)
        assert game_session.speed == GameSpeed.SLOW

    def test_set_speed_with_string(self, game_session):
        """Test setting speed with string."""
        game_session.set_speed("slow")
        assert game_session.speed == GameSpeed.SLOW

    def test_get_delay(self, game_session):
        """Test getting speed delay."""
        game_session.speed = GameSpeed.FAST
        assert game_session.get_delay() == 0.5

        game_session.speed = GameSpeed.NORMAL
        assert game_session.get_delay() == 2.0

        game_session.speed = GameSpeed.SLOW
        assert game_session.get_delay() == 5.0

    def test_update_state(self, game_session):
        """Test updating game state."""
        state = {"turn_number": 5, "status": "in_progress"}
        game_session.update_state(state)

        assert game_session.current_state == state
        assert game_session.turn_count == 5

    def test_update_state_none(self, game_session):
        """Test updating with None state."""
        game_session.update_state(None)
        assert game_session.current_state is None
        assert game_session.turn_count == 0


class TestGameSessionManager:
    """Tests for GameSessionManager class."""

    def test_create_session(self, session_manager, game_id, sample_agents):
        """Test creating a session through manager."""
        session = session_manager.create_session(
            game_id=game_id,
            agents=sample_agents,
            speed=GameSpeed.FAST,
        )

        assert session.game_id == game_id
        assert session.speed == GameSpeed.FAST

    def test_get_session(self, session_manager, game_id, sample_agents):
        """Test retrieving a session."""
        session_manager.create_session(game_id, sample_agents)

        # Get by UUID
        session = session_manager.get_session(game_id)
        assert session is not None
        assert session.game_id == game_id

        # Get by string
        session = session_manager.get_session(str(game_id))
        assert session is not None

    def test_get_nonexistent_session(self, session_manager):
        """Test getting a non-existent session."""
        session = session_manager.get_session(uuid4())
        assert session is None

    def test_remove_session(self, session_manager, game_id, sample_agents):
        """Test removing a session."""
        session_manager.create_session(game_id, sample_agents)

        session_manager.remove_session(game_id)

        assert session_manager.get_session(game_id) is None

    def test_list_sessions(self, session_manager, sample_agents):
        """Test listing all sessions."""
        game_id_1 = uuid4()
        game_id_2 = uuid4()

        session_manager.create_session(game_id_1, sample_agents, GameSpeed.FAST)
        session_manager.create_session(game_id_2, sample_agents, GameSpeed.SLOW)

        sessions = session_manager.list_sessions()

        assert len(sessions) == 2
        game_ids = {s["game_id"] for s in sessions}
        assert str(game_id_1) in game_ids
        assert str(game_id_2) in game_ids
