"""Tests for session management."""

from uuid import uuid4

from src.llm.session import AgentSession


class TestAgentSession:
    """Tests for AgentSession class."""

    def test_create_session(self, sample_player_id):
        """Test creating a session."""
        session = AgentSession(
            agent_id=sample_player_id,
            personality="aggressive",
            temperature=0.8,
        )

        assert session.agent_id == sample_player_id
        assert session.personality == "aggressive"
        assert session.temperature == 0.8
        assert session.context == []
        assert session.message_history == []
        assert session.decision_count == 0

    def test_update_context(self, agent_session):
        """Test updating context."""
        new_context = [1, 2, 3, 4, 5]
        agent_session.update_context(new_context)

        assert agent_session.context == new_context

    def test_add_message(self, agent_session):
        """Test adding messages."""
        agent_session.add_message("user", "Hello")
        agent_session.add_message("assistant", "Hi there")

        assert len(agent_session.message_history) == 2
        assert agent_session.message_history[0] == {"role": "user", "content": "Hello"}
        assert agent_session.message_history[1] == {"role": "assistant", "content": "Hi there"}

    def test_message_history_limit(self, agent_session):
        """Test that message history is limited."""
        # Add 25 messages
        for i in range(25):
            agent_session.add_message("user", f"Message {i}")

        # Should be limited to 20
        assert len(agent_session.message_history) == 20
        # Should keep most recent
        assert agent_session.message_history[-1]["content"] == "Message 24"

    def test_message_history_preserves_system(self, agent_session):
        """Test that system message is preserved when trimming."""
        agent_session.add_message("system", "System prompt")

        # Add 25 more messages
        for i in range(25):
            agent_session.add_message("user", f"Message {i}")

        # Should have system + 19 most recent
        assert len(agent_session.message_history) == 20
        assert agent_session.message_history[0]["role"] == "system"

    def test_increment_decision(self, agent_session):
        """Test incrementing decision count."""
        assert agent_session.decision_count == 0

        agent_session.increment_decision()
        assert agent_session.decision_count == 1

        agent_session.increment_decision()
        assert agent_session.decision_count == 2

    def test_reset_context(self, agent_session):
        """Test resetting context."""
        agent_session.update_context([1, 2, 3])
        agent_session.add_message("user", "Hello")

        agent_session.reset_context()

        assert agent_session.context == []
        assert agent_session.message_history == []

    def test_get_stats(self, agent_session):
        """Test getting session stats."""
        agent_session.update_context([1, 2, 3])
        agent_session.increment_decision()
        agent_session.increment_decision()

        stats = agent_session.get_stats()

        assert stats["personality"] == "analytical"
        assert stats["temperature"] == 0.3
        assert stats["decisions_made"] == 2
        assert stats["context_length"] == 3


class TestSessionManager:
    """Tests for SessionManager class."""

    def test_create_session(self, session_manager):
        """Test creating a session."""
        agent_id = uuid4()
        session = session_manager.create_session(
            agent_id=agent_id,
            personality="chaotic",
            temperature=1.0,
        )

        assert session.agent_id == agent_id
        assert session.personality == "chaotic"
        assert session.temperature == 1.0

    def test_get_session(self, session_manager):
        """Test getting an existing session."""
        agent_id = uuid4()
        session_manager.create_session(agent_id, "aggressive", 0.8)

        retrieved = session_manager.get_session(agent_id)

        assert retrieved is not None
        assert retrieved.agent_id == agent_id

    def test_get_session_not_found(self, session_manager):
        """Test getting non-existent session."""
        result = session_manager.get_session(uuid4())
        assert result is None

    def test_remove_session(self, session_manager):
        """Test removing a session."""
        agent_id = uuid4()
        session_manager.create_session(agent_id, "analytical", 0.3)

        result = session_manager.remove_session(agent_id)
        assert result is True

        # Should be gone
        assert session_manager.get_session(agent_id) is None

    def test_remove_session_not_found(self, session_manager):
        """Test removing non-existent session."""
        result = session_manager.remove_session(uuid4())
        assert result is False

    def test_clear_all(self, session_manager):
        """Test clearing all sessions."""
        # Create multiple sessions
        for _ in range(3):
            session_manager.create_session(uuid4(), "analytical", 0.3)

        session_manager.clear_all()

        assert len(session_manager.sessions) == 0

    def test_get_all_stats(self, session_manager):
        """Test getting stats for all sessions."""
        id1 = uuid4()
        id2 = uuid4()

        session_manager.create_session(id1, "aggressive", 0.8)
        session_manager.create_session(id2, "chaotic", 1.0)

        stats = session_manager.get_all_stats()

        assert len(stats) == 2
        personalities = {s["personality"] for s in stats}
        assert "aggressive" in personalities
        assert "chaotic" in personalities
