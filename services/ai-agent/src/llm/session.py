"""Session management for AI agents."""

from dataclasses import dataclass, field
from uuid import UUID


@dataclass
class AgentSession:
    """Maintains conversation context for one agent."""

    agent_id: UUID
    personality: str
    temperature: float
    context: list[int] = field(default_factory=list)
    message_history: list[dict[str, str]] = field(default_factory=list)
    decision_count: int = 0

    def update_context(self, new_context: list[int]) -> None:
        """Update conversation context after a response.

        Args:
            new_context: New context from Ollama response
        """
        self.context = new_context

    def add_message(self, role: str, content: str) -> None:
        """Add a message to history.

        Args:
            role: Message role (system, user, assistant)
            content: Message content
        """
        self.message_history.append({"role": role, "content": content})

        # Keep history manageable (last 20 messages)
        if len(self.message_history) > 20:
            # Keep system message if present, then last 19 messages
            if self.message_history[0]["role"] == "system":
                self.message_history = [self.message_history[0]] + self.message_history[-19:]
            else:
                self.message_history = self.message_history[-20:]

    def increment_decision(self) -> None:
        """Increment decision counter."""
        self.decision_count += 1

    def reset_context(self) -> None:
        """Reset conversation context (start fresh)."""
        self.context = []
        self.message_history = []

    def get_stats(self) -> dict:
        """Get session statistics.

        Returns:
            Dict with session stats
        """
        return {
            "agent_id": str(self.agent_id),
            "personality": self.personality,
            "temperature": self.temperature,
            "decisions_made": self.decision_count,
            "context_length": len(self.context),
            "message_count": len(self.message_history),
        }


class SessionManager:
    """Manages sessions for multiple agents."""

    def __init__(self):
        """Initialize the session manager."""
        self.sessions: dict[UUID, AgentSession] = {}

    def create_session(
        self,
        agent_id: UUID,
        personality: str,
        temperature: float,
    ) -> AgentSession:
        """Create a new agent session.

        Args:
            agent_id: Unique agent/player ID
            personality: Personality name (aggressive, analytical, chaotic)
            temperature: LLM temperature for this agent

        Returns:
            New AgentSession instance
        """
        session = AgentSession(
            agent_id=agent_id,
            personality=personality,
            temperature=temperature,
        )
        self.sessions[agent_id] = session
        return session

    def get_session(self, agent_id: UUID) -> AgentSession | None:
        """Get an existing session.

        Args:
            agent_id: Agent/player ID

        Returns:
            AgentSession or None if not found
        """
        return self.sessions.get(agent_id)

    def remove_session(self, agent_id: UUID) -> bool:
        """Remove a session.

        Args:
            agent_id: Agent/player ID

        Returns:
            True if session was removed, False if not found
        """
        if agent_id in self.sessions:
            del self.sessions[agent_id]
            return True
        return False

    def clear_all(self) -> None:
        """Clear all sessions."""
        self.sessions.clear()

    def get_all_stats(self) -> list[dict]:
        """Get stats for all sessions.

        Returns:
            List of session stats
        """
        return [session.get_stats() for session in self.sessions.values()]
