# AI Agent Service - Implementation Plan

## Overview

The AI Agent Service enables a locally-running LLM to play Monopoly as multiple AI agents. Each agent uses the same base model (Llama 3 via Ollama) but with different personalities achieved through:
- Distinct system prompts
- Different temperature settings
- Isolated conversation contexts

**Key Principle**: Zero cloud API costs. Everything runs locally.

---

## 1. Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                      AI Agent Service                            │
│                                                                  │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐       │
│  │   Agent 1    │    │   Agent 2    │    │   Agent 3    │       │
│  │  Aggressive  │    │  Analytical  │    │   Chaotic    │       │
│  │  temp=0.8    │    │  temp=0.3    │    │  temp=1.0    │       │
│  └──────┬───────┘    └──────┬───────┘    └──────┬───────┘       │
│         │                   │                   │                │
│         └───────────────────┼───────────────────┘                │
│                             │                                    │
│                    ┌────────▼────────┐                          │
│                    │  Agent Manager  │                          │
│                    │  (Orchestrator) │                          │
│                    └────────┬────────┘                          │
│                             │                                    │
│         ┌───────────────────┼───────────────────┐               │
│         │                   │                   │                │
│  ┌──────▼──────┐    ┌──────▼──────┐    ┌──────▼──────┐         │
│  │   Prompt    │    │   Ollama    │    │  Response   │         │
│  │   Builder   │    │   Client    │    │   Parser    │         │
│  └─────────────┘    └─────────────┘    └─────────────┘         │
│                             │                                    │
└─────────────────────────────┼────────────────────────────────────┘
                              │
              ┌───────────────┼───────────────┐
              │               │               │
              ▼               ▼               ▼
     ┌─────────────┐  ┌─────────────┐  ┌─────────────┐
     │   Ollama    │  │   Game      │  │   Redis     │
     │  (Llama 3)  │  │   Engine    │  │  (future)   │
     └─────────────┘  └─────────────┘  └─────────────┘
```

---

## 2. Why Single LLM + Personalities?

### Comparison

| Aspect | Multiple LLMs | Single LLM + Personalities |
|--------|---------------|---------------------------|
| Disk Space | ~24GB (3 models) | ~8GB (1 model) |
| VRAM Usage | Complex swapping | Single model loaded |
| Setup | Download 3 models | Download 1 model |
| Variety | Different architectures | Prompt + temperature |
| Debugging | 3 different behaviors | Consistent base |
| Upgrade Path | Already multi-model | Easy to add models later |

### How Personalities Work

**Same model, different behavior:**

```
Agent 1 (Aggressive)     Agent 2 (Analytical)     Agent 3 (Chaotic)
├─ System: "Be bold..."  ├─ System: "Calculate.." ├─ System: "Surprise..."
├─ Temperature: 0.8      ├─ Temperature: 0.3      ├─ Temperature: 1.0
└─ Context: [isolated]   └─ Context: [isolated]   └─ Context: [isolated]
```

Each agent maintains its own conversation history, so they don't "know" what other agents are thinking.

---

## 3. Project Structure

```
services/ai-agent/
├── src/
│   ├── __init__.py
│   ├── main.py                 # FastAPI app + game loop
│   ├── config.py               # Environment configuration
│   │
│   ├── client/                 # Game Engine API client
│   │   ├── __init__.py
│   │   ├── game_client.py      # HTTP client for game engine
│   │   └── models.py           # Response models
│   │
│   ├── llm/                    # Ollama integration
│   │   ├── __init__.py
│   │   ├── ollama_client.py    # Ollama API wrapper
│   │   └── session.py          # Per-agent session management
│   │
│   ├── prompts/                # Prompt engineering
│   │   ├── __init__.py
│   │   ├── builder.py          # Builds prompts from game state
│   │   ├── templates.py        # Base prompt templates
│   │   └── personalities.py    # Personality configurations
│   │
│   ├── parser/                 # Response parsing
│   │   ├── __init__.py
│   │   └── action_parser.py    # Extract actions from LLM response
│   │
│   ├── agent/                  # Agent logic
│   │   ├── __init__.py
│   │   ├── monopoly_agent.py   # Monopoly-playing agent
│   │   └── manager.py          # Multi-agent orchestration
│   │
│   ├── api/                    # REST API
│   │   ├── __init__.py
│   │   └── routes.py           # Control endpoints
│   │
│   └── tests/
│       ├── __init__.py
│       ├── conftest.py
│       ├── test_prompt_builder.py
│       ├── test_action_parser.py
│       ├── test_ollama_client.py
│       └── test_agent.py
│
├── pyproject.toml
├── Dockerfile
├── .env.example
└── README.md
```

---

## 4. Dependencies

```toml
[project]
name = "monopoly-ai-agent"
version = "0.1.0"
requires-python = ">=3.11"

dependencies = [
    "fastapi>=0.109.0",
    "uvicorn[standard]>=0.27.0",
    "pydantic>=2.5.0",
    "pydantic-settings>=2.1.0",
    "httpx>=0.26.0",           # Async HTTP client
    "ollama>=0.1.6",           # Ollama Python client
    "python-dotenv>=1.0.0",
    "tenacity>=8.2.0",         # Retry logic
]

[project.optional-dependencies]
dev = [
    "pytest>=7.4.0",
    "pytest-asyncio>=0.23.0",
    "pytest-cov>=4.1.0",
    "respx>=0.20.0",           # Mock httpx
    "ruff>=0.1.0",
    "mypy>=1.8.0",
]
```

---

## 5. Core Components

### 5.1 Ollama Client

Simple wrapper around Ollama's API with session management.

```python
# llm/ollama_client.py

from ollama import AsyncClient

class OllamaClient:
    """Client for local Ollama LLM."""

    def __init__(
        self,
        model: str = "llama3",
        host: str = "http://localhost:11434",
    ):
        self.model = model
        self.client = AsyncClient(host=host)

    async def generate(
        self,
        system_prompt: str,
        user_prompt: str,
        temperature: float = 0.7,
        context: list[int] | None = None,  # For conversation continuity
    ) -> tuple[str, list[int]]:
        """Generate a response.

        Args:
            system_prompt: System/personality prompt
            user_prompt: Current game state and question
            temperature: Randomness (0.0-1.0)
            context: Previous conversation context (for continuity)

        Returns:
            Tuple of (response_text, new_context)
        """
        response = await self.client.generate(
            model=self.model,
            system=system_prompt,
            prompt=user_prompt,
            context=context,
            options={
                "temperature": temperature,
                "num_predict": 200,  # Limit response length
            },
        )
        return response["response"], response.get("context", [])

    async def is_available(self) -> bool:
        """Check if Ollama is running and model is available."""
        try:
            models = await self.client.list()
            return any(m["name"].startswith(self.model) for m in models["models"])
        except Exception:
            return False
```

### 5.2 Agent Session

Manages per-agent conversation context.

```python
# llm/session.py

@dataclass
class AgentSession:
    """Maintains conversation context for one agent."""

    agent_id: UUID
    personality: str
    temperature: float
    context: list[int] = field(default_factory=list)

    def update_context(self, new_context: list[int]) -> None:
        """Update conversation context after a response."""
        self.context = new_context

    def reset_context(self) -> None:
        """Reset conversation (start fresh)."""
        self.context = []


class SessionManager:
    """Manages sessions for multiple agents."""

    def __init__(self):
        self.sessions: dict[UUID, AgentSession] = {}

    def create_session(
        self,
        agent_id: UUID,
        personality: str,
        temperature: float,
    ) -> AgentSession:
        """Create a new agent session."""
        session = AgentSession(
            agent_id=agent_id,
            personality=personality,
            temperature=temperature,
        )
        self.sessions[agent_id] = session
        return session

    def get_session(self, agent_id: UUID) -> AgentSession | None:
        """Get an existing session."""
        return self.sessions.get(agent_id)

    def clear_all(self) -> None:
        """Clear all sessions."""
        self.sessions.clear()
```

### 5.3 Personality Configuration

```python
# prompts/personalities.py

from dataclasses import dataclass


@dataclass
class PersonalityConfig:
    """Configuration for an agent personality."""

    name: str
    temperature: float
    system_prompt: str
    decision_style: str  # For logging/debugging


PERSONALITIES = {
    "aggressive": PersonalityConfig(
        name="aggressive",
        temperature=0.8,
        system_prompt="""You are an AGGRESSIVE Monopoly player named {player_name}.

Your strategy:
- ALWAYS buy properties when you can afford them
- Prioritize completing color sets at ANY cost
- Build houses immediately when you have a monopoly
- Take risks - being bold wins games
- Never pass on a property unless truly broke

You play to DOMINATE. Fortune favors the bold.""",
        decision_style="bold, risk-taking",
    ),

    "analytical": PersonalityConfig(
        name="analytical",
        temperature=0.3,
        system_prompt="""You are an ANALYTICAL Monopoly player named {player_name}.

Your strategy:
- Calculate expected ROI before every purchase
- Maintain cash reserves of at least $300 when possible
- Only buy properties that fit your strategy
- Build houses only when you have a safe financial buffer
- Consider probability: which properties get landed on most?

You play with PRECISION. Data drives decisions.""",
        decision_style="calculated, conservative",
    ),

    "chaotic": PersonalityConfig(
        name="chaotic",
        temperature=1.0,
        system_prompt="""You are a CHAOTIC Monopoly player named {player_name}.

Your strategy:
- Make unexpected moves that confuse opponents
- Sometimes pass on "obvious" good deals
- Occasionally make seemingly irrational choices
- Keep everyone guessing your true strategy
- Have fun - winning isn't everything

You play for CHAOS. Predictability is boring.""",
        decision_style="unpredictable, random",
    ),
}


def get_personality(name: str) -> PersonalityConfig:
    """Get personality config by name."""
    return PERSONALITIES.get(name, PERSONALITIES["analytical"])
```

### 5.4 Prompt Builder

```python
# prompts/builder.py

class PromptBuilder:
    """Builds prompts from game state."""

    def build_decision_prompt(
        self,
        game_state: GameState,
        valid_actions: ValidActions,
        player_name: str,
    ) -> str:
        """Build the user prompt for a decision.

        Args:
            game_state: Current game state
            valid_actions: Valid actions for this player
            player_name: Name of the player making the decision

        Returns:
            Formatted user prompt
        """
        return f"""
=== CURRENT GAME STATE ===

YOUR STATUS ({player_name}):
- Position: {self._get_space_name(game_state, valid_actions.player_id)}
- Cash: ${self._get_player_cash(game_state, valid_actions.player_id)}
- Properties: {self._get_player_properties(game_state, valid_actions.player_id)}

OPPONENTS:
{self._format_opponents(game_state, valid_actions.player_id)}

PROPERTY OWNERSHIP:
{self._format_property_summary(game_state)}

=== YOUR TURN ===

Valid actions you can take:
{self._format_actions(valid_actions)}

INSTRUCTIONS:
- Choose ONE action from the list above
- Respond with ONLY valid JSON in this exact format:
{{"action": "<action_type>", "property_id": "<id_or_null>"}}

Examples:
- {{"action": "roll_dice", "property_id": null}}
- {{"action": "buy_property", "property_id": "boardwalk"}}
- {{"action": "end_turn", "property_id": null}}

Your decision (JSON only):"""

    def _format_actions(self, valid_actions: ValidActions) -> str:
        """Format valid actions as a clear list."""
        lines = []
        for i, action in enumerate(valid_actions.actions, 1):
            cost_str = f" (cost: ${action.cost})" if action.cost else ""
            prop_str = f" [{action.property_id}]" if action.property_id else ""
            lines.append(f"  {i}. {action.type.value}{prop_str}{cost_str}")
        return "\n".join(lines)

    def _get_player_cash(self, game_state: GameState, player_id: UUID) -> int:
        """Get player's current cash."""
        for player in game_state.players:
            if player.id == player_id:
                return player.cash
        return 0

    def _format_opponents(self, game_state: GameState, current_player_id: UUID) -> str:
        """Format opponent information."""
        lines = []
        for player in game_state.players:
            if player.id != current_player_id and not player.is_bankrupt:
                status = " (IN JAIL)" if player.in_jail else ""
                lines.append(f"- {player.name}: ${player.cash}, {self._count_properties(game_state, player.id)} properties{status}")
        return "\n".join(lines) if lines else "  None remaining"

    def _format_property_summary(self, game_state: GameState) -> str:
        """Summarize property ownership by color group."""
        # Group properties by color and show ownership
        ownership = {}
        for prop in game_state.properties:
            if prop.owner_id:
                owner_name = self._get_player_name(game_state, prop.owner_id)
                ownership[prop.property_id] = owner_name

        if not ownership:
            return "  No properties owned yet"

        lines = [f"  - {prop_id}: {owner}" for prop_id, owner in list(ownership.items())[:10]]
        if len(ownership) > 10:
            lines.append(f"  ... and {len(ownership) - 10} more")
        return "\n".join(lines)

    def _get_player_name(self, game_state: GameState, player_id: UUID) -> str:
        """Get player name by ID."""
        for player in game_state.players:
            if player.id == player_id:
                return player.name
        return "Unknown"

    def _count_properties(self, game_state: GameState, player_id: UUID) -> int:
        """Count properties owned by a player."""
        return sum(1 for p in game_state.properties if p.owner_id == player_id)

    def _get_space_name(self, game_state: GameState, player_id: UUID) -> str:
        """Get the name of the space a player is on."""
        for player in game_state.players:
            if player.id == player_id:
                # Would need board data - for now return position number
                return f"Position {player.position}"
        return "Unknown"
```

### 5.5 Action Parser

```python
# parser/action_parser.py

import json
import re
from src.client.models import Action, ActionType, ValidActions


class ActionParser:
    """Parses LLM responses into game actions."""

    def parse(self, response: str, valid_actions: ValidActions) -> Action:
        """Parse LLM response into a valid action.

        Attempts multiple parsing strategies:
        1. JSON extraction
        2. Keyword matching
        3. Default to safest action

        Args:
            response: Raw LLM response text
            valid_actions: List of valid actions

        Returns:
            Parsed Action object (guaranteed to be valid)
        """
        # Strategy 1: Try JSON parsing
        action = self._try_json_parse(response)
        if action and self._is_valid(action, valid_actions):
            return action

        # Strategy 2: Try keyword matching
        action = self._try_keyword_parse(response, valid_actions)
        if action:
            return action

        # Strategy 3: Default to safest action
        return self._get_default_action(valid_actions)

    def _try_json_parse(self, response: str) -> Action | None:
        """Extract JSON from response."""
        # Find JSON object in response
        json_patterns = [
            r'\{[^{}]*"action"[^{}]*\}',  # Standard JSON
            r'\{[^{}]*\'action\'[^{}]*\}',  # Single quotes
        ]

        for pattern in json_patterns:
            match = re.search(pattern, response, re.IGNORECASE)
            if match:
                try:
                    # Normalize quotes
                    json_str = match.group().replace("'", '"')
                    data = json.loads(json_str)

                    action_type = data.get("action", "").lower().strip()
                    property_id = data.get("property_id")

                    # Handle "null" string
                    if property_id in ("null", "none", ""):
                        property_id = None

                    return Action(
                        type=ActionType(action_type),
                        property_id=property_id,
                    )
                except (json.JSONDecodeError, ValueError, KeyError):
                    continue

        return None

    def _try_keyword_parse(
        self,
        response: str,
        valid_actions: ValidActions
    ) -> Action | None:
        """Match keywords in response to valid actions."""
        response_lower = response.lower()

        # Priority order for matching
        action_keywords = {
            "buy_property": ["buy", "purchase", "acquire"],
            "roll_dice": ["roll", "dice"],
            "end_turn": ["end", "finish", "done", "pass turn"],
            "pass_property": ["pass", "skip", "decline"],
            "build_house": ["build house", "house"],
            "build_hotel": ["build hotel", "hotel"],
            "pay_jail_fine": ["pay fine", "pay jail", "pay 50"],
            "use_jail_card": ["use card", "jail card", "get out of jail"],
            "roll_for_doubles": ["roll for doubles", "try doubles"],
        }

        for action in valid_actions.actions:
            action_type = action.type.value
            keywords = action_keywords.get(action_type, [action_type])

            for keyword in keywords:
                if keyword in response_lower:
                    return Action(
                        type=action.type,
                        property_id=action.property_id,
                    )

        return None

    def _is_valid(self, action: Action, valid_actions: ValidActions) -> bool:
        """Check if action is in valid actions list."""
        for valid in valid_actions.actions:
            if valid.type == action.type:
                # For property actions, check property_id matches
                if action.property_id and valid.property_id:
                    if action.property_id == valid.property_id:
                        return True
                elif not action.property_id and not valid.property_id:
                    return True
                elif valid.property_id is None:
                    # Valid action doesn't require specific property
                    return True
        return False

    def _get_default_action(self, valid_actions: ValidActions) -> Action:
        """Get safest default action."""
        # Priority: roll_dice > end_turn > pass_property > first
        priority = ["roll_dice", "roll_for_doubles", "end_turn", "pass_property"]

        for action_type in priority:
            for action in valid_actions.actions:
                if action.type.value == action_type:
                    return Action(type=action.type, property_id=action.property_id)

        # Last resort: first available action
        first = valid_actions.actions[0]
        return Action(type=first.type, property_id=first.property_id)
```

### 5.6 Monopoly Agent

```python
# agent/monopoly_agent.py

from uuid import UUID
from src.llm.ollama_client import OllamaClient
from src.llm.session import AgentSession
from src.prompts.builder import PromptBuilder
from src.prompts.personalities import get_personality
from src.parser.action_parser import ActionParser
from src.client.models import GameState, ValidActions, Action


class MonopolyAgent:
    """An AI agent that plays Monopoly using a local LLM."""

    def __init__(
        self,
        player_id: UUID,
        player_name: str,
        personality: str,
        ollama_client: OllamaClient,
        session: AgentSession,
    ):
        self.player_id = player_id
        self.player_name = player_name
        self.personality_config = get_personality(personality)
        self.ollama = ollama_client
        self.session = session
        self.prompt_builder = PromptBuilder()
        self.action_parser = ActionParser()

    async def decide_action(
        self,
        game_state: GameState,
        valid_actions: ValidActions,
    ) -> Action:
        """Decide which action to take.

        Args:
            game_state: Current game state
            valid_actions: Valid actions for this player

        Returns:
            The chosen action
        """
        # Build system prompt with personality
        system_prompt = self.personality_config.system_prompt.format(
            player_name=self.player_name
        )

        # Build user prompt with game state
        user_prompt = self.prompt_builder.build_decision_prompt(
            game_state=game_state,
            valid_actions=valid_actions,
            player_name=self.player_name,
        )

        # Generate response from LLM
        response, new_context = await self.ollama.generate(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            temperature=self.personality_config.temperature,
            context=self.session.context,
        )

        # Update session context for continuity
        self.session.update_context(new_context)

        # Parse response into action
        action = self.action_parser.parse(response, valid_actions)

        return action

    @property
    def personality(self) -> str:
        """Get personality name."""
        return self.personality_config.name
```

### 5.7 Agent Manager

```python
# agent/manager.py

import asyncio
from uuid import UUID
from dataclasses import dataclass
from typing import Callable, Awaitable

from src.client.game_client import GameClient
from src.client.models import GameState, Action, ActionType
from src.llm.ollama_client import OllamaClient
from src.llm.session import SessionManager
from src.agent.monopoly_agent import MonopolyAgent
from src.prompts.personalities import get_personality


@dataclass
class AgentConfig:
    """Configuration for creating an agent."""
    name: str
    personality: str  # aggressive, analytical, chaotic


@dataclass
class GameResult:
    """Result of a completed game."""
    game_id: UUID
    winner_id: UUID | None
    winner_name: str | None
    total_turns: int
    final_standings: list[dict]


class AgentManager:
    """Manages multiple AI agents playing a game."""

    def __init__(
        self,
        game_client: GameClient,
        ollama_client: OllamaClient,
        turn_delay: float = 1.0,
        action_delay: float = 0.5,
        on_action: Callable[[str, Action], Awaitable[None]] | None = None,
    ):
        """Initialize the agent manager.

        Args:
            game_client: Client for game engine API
            ollama_client: Client for Ollama LLM
            turn_delay: Delay between turns (seconds)
            action_delay: Delay between actions within a turn (seconds)
            on_action: Optional callback for each action (for logging/UI)
        """
        self.game_client = game_client
        self.ollama = ollama_client
        self.turn_delay = turn_delay
        self.action_delay = action_delay
        self.on_action = on_action

        self.session_manager = SessionManager()
        self.agents: dict[UUID, MonopolyAgent] = {}
        self.game_id: UUID | None = None
        self.is_running: bool = False

    async def create_game(self, agent_configs: list[AgentConfig]) -> UUID:
        """Create a new game with the specified agents.

        Args:
            agent_configs: List of agent configurations

        Returns:
            Game ID
        """
        # Verify Ollama is available
        if not await self.ollama.is_available():
            raise RuntimeError("Ollama is not running or model not available")

        # Create game via API
        players = [
            {"name": config.name, "model": "llama3", "personality": config.personality}
            for config in agent_configs
        ]
        game_info = await self.game_client.create_game(players)
        self.game_id = game_info["id"]

        # Create agent instances
        for config, player in zip(agent_configs, game_info["players"]):
            personality_config = get_personality(config.personality)

            # Create session for this agent
            session = self.session_manager.create_session(
                agent_id=player["id"],
                personality=config.personality,
                temperature=personality_config.temperature,
            )

            # Create agent
            agent = MonopolyAgent(
                player_id=player["id"],
                player_name=player["name"],
                personality=config.personality,
                ollama_client=self.ollama,
                session=session,
            )
            self.agents[player["id"]] = agent

        return self.game_id

    async def start_game(self) -> None:
        """Start the game."""
        if not self.game_id:
            raise ValueError("No game created")
        await self.game_client.start_game(self.game_id)

    async def run_game(self) -> GameResult:
        """Run the game until completion.

        Returns:
            GameResult with winner and final standings
        """
        if not self.game_id:
            raise ValueError("No game created")

        self.is_running = True

        while self.is_running:
            # Get current game state
            game_state = await self.game_client.get_game_state(self.game_id)

            # Check if game is over
            if game_state.status == "completed":
                self.is_running = False
                return self._build_result(game_state)

            # Get current player
            current_player = game_state.players[game_state.current_player_index]

            # Skip bankrupt players
            if current_player.is_bankrupt:
                continue

            # Get agent for current player
            agent = self.agents.get(current_player.id)
            if not agent:
                raise ValueError(f"No agent for player {current_player.id}")

            # Execute turn
            await self._execute_turn(agent, game_state)

            # Delay between turns
            await asyncio.sleep(self.turn_delay)

        return self._build_result(game_state)

    async def _execute_turn(
        self,
        agent: MonopolyAgent,
        game_state: GameState,
    ) -> None:
        """Execute a single turn for an agent."""
        max_actions = 20  # Safety limit

        for _ in range(max_actions):
            # Get valid actions
            valid_actions = await self.game_client.get_valid_actions(self.game_id)

            # Check if still this agent's turn
            if valid_actions.player_id != agent.player_id:
                break

            # Get agent's decision
            action = await agent.decide_action(game_state, valid_actions)

            # Callback for logging/UI
            if self.on_action:
                await self.on_action(agent.player_name, action)

            # Execute action
            result = await self.game_client.execute_action(
                self.game_id,
                agent.player_id,
                action,
            )

            # Check if game over or turn complete
            if result.game_over:
                self.is_running = False
                break

            if result.next_phase == "pre_roll" and action.type != ActionType.ROLL_DICE:
                # Turn is complete (moved to next player's pre_roll)
                break

            # Delay between actions
            await asyncio.sleep(self.action_delay)

    def _build_result(self, game_state: GameState) -> GameResult:
        """Build game result from final state."""
        winner = None
        winner_name = None

        if game_state.winner_id:
            for player in game_state.players:
                if player.id == game_state.winner_id:
                    winner = player.id
                    winner_name = player.name
                    break

        standings = sorted(
            [
                {
                    "name": p.name,
                    "cash": p.cash,
                    "bankrupt": p.is_bankrupt,
                    "properties": sum(
                        1 for prop in game_state.properties
                        if prop.owner_id == p.id
                    ),
                }
                for p in game_state.players
            ],
            key=lambda x: (not x["bankrupt"], x["cash"]),
            reverse=True,
        )

        return GameResult(
            game_id=self.game_id,
            winner_id=winner,
            winner_name=winner_name,
            total_turns=game_state.turn_number,
            final_standings=standings,
        )

    def stop(self) -> None:
        """Stop the running game."""
        self.is_running = False
```

---

## 6. API Endpoints

Simple REST API for controlling games.

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/games` | Create and start a new AI game |
| GET | `/games/{id}` | Get game status |
| POST | `/games/{id}/stop` | Stop a running game |
| GET | `/health` | Health check (includes Ollama status) |

### Example Requests

```bash
# Create a new game
curl -X POST http://localhost:8001/games \
  -H "Content-Type: application/json" \
  -d '{
    "agents": [
      {"name": "Baron Von Moneybags", "personality": "aggressive"},
      {"name": "Professor Pennypincher", "personality": "analytical"},
      {"name": "Lady Luck", "personality": "chaotic"}
    ]
  }'

# Response
{
  "game_id": "uuid-here",
  "status": "running",
  "message": "Game started with 3 agents"
}

# Check game status
curl http://localhost:8001/games/{game_id}

# Response
{
  "game_id": "uuid-here",
  "status": "running",
  "current_turn": 42,
  "current_player": "Professor Pennypincher",
  "players": [
    {"name": "Baron Von Moneybags", "cash": 850, "properties": 6, "bankrupt": false},
    {"name": "Professor Pennypincher", "cash": 2100, "properties": 4, "bankrupt": false},
    {"name": "Lady Luck", "cash": 0, "properties": 0, "bankrupt": true}
  ]
}

# Health check
curl http://localhost:8001/health

# Response
{
  "status": "healthy",
  "ollama": "connected",
  "model": "llama3",
  "game_engine": "connected"
}
```

---

## 7. Configuration

```python
# config.py

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings."""

    # Game Engine
    game_engine_url: str = "http://localhost:8000"

    # Ollama
    ollama_host: str = "http://localhost:11434"
    ollama_model: str = "llama3"

    # Game timing
    turn_delay: float = 1.0       # Seconds between turns
    action_delay: float = 0.5    # Seconds between actions

    # Server
    host: str = "0.0.0.0"
    port: int = 8001

    # Logging
    log_level: str = "INFO"
    log_prompts: bool = False    # Log full prompts (verbose)
    log_responses: bool = True   # Log LLM responses

    model_config = SettingsConfigDict(env_file=".env")
```

---

## 8. Docker Setup

### docker-compose.yml addition

```yaml
  # Add to existing docker-compose.yml

  ollama:
    image: ollama/ollama:latest
    container_name: monopoly-ollama
    ports:
      - "11434:11434"
    volumes:
      - ollama_data:/root/.ollama
    deploy:
      resources:
        reservations:
          devices:
            - driver: nvidia
              count: all
              capabilities: [gpu]
    networks:
      - monopoly-network

  ai-agent:
    build: ./services/ai-agent
    container_name: monopoly-ai-agent
    ports:
      - "8001:8001"
    environment:
      - GAME_ENGINE_URL=http://game-engine:8000
      - OLLAMA_HOST=http://ollama:11434
    depends_on:
      - game-engine
      - ollama
    networks:
      - monopoly-network

volumes:
  ollama_data:
```

### First-time setup

```bash
# Pull Llama 3 model (only needed once)
docker exec -it monopoly-ollama ollama pull llama3

# Or for smaller/faster model:
docker exec -it monopoly-ollama ollama pull llama3:8b
```

---

## 9. Implementation Steps

### Phase 1: Foundation
- [ ] Create project structure
- [ ] Add pyproject.toml with dependencies
- [ ] Implement config.py
- [ ] Implement GameClient for game engine API
- [ ] Add client models

### Phase 2: Ollama Integration
- [ ] Implement OllamaClient
- [ ] Implement SessionManager
- [ ] Test connection to Ollama
- [ ] Verify model availability

### Phase 3: Prompt Engineering
- [ ] Define personality configurations
- [ ] Implement PromptBuilder
- [ ] Create prompt templates
- [ ] Test prompts manually

### Phase 4: Response Parsing
- [ ] Implement ActionParser
- [ ] Add JSON extraction
- [ ] Add keyword fallback
- [ ] Add default action logic

### Phase 5: Agent Implementation
- [ ] Implement MonopolyAgent
- [ ] Implement AgentManager
- [ ] Add game loop logic
- [ ] Add error handling

### Phase 6: API & Testing
- [ ] Implement REST endpoints
- [ ] Add health checks
- [ ] Write unit tests
- [ ] End-to-end testing

---

## 10. Files to Create

| Priority | File | Purpose |
|----------|------|---------|
| 1 | `pyproject.toml` | Dependencies |
| 1 | `src/config.py` | Settings |
| 1 | `src/main.py` | FastAPI app |
| 2 | `src/client/game_client.py` | Game Engine client |
| 2 | `src/client/models.py` | API models |
| 3 | `src/llm/ollama_client.py` | Ollama wrapper |
| 3 | `src/llm/session.py` | Session management |
| 4 | `src/prompts/personalities.py` | Personality configs |
| 4 | `src/prompts/templates.py` | Prompt templates |
| 4 | `src/prompts/builder.py` | Prompt builder |
| 5 | `src/parser/action_parser.py` | Response parsing |
| 6 | `src/agent/monopoly_agent.py` | Agent class |
| 6 | `src/agent/manager.py` | Game orchestration |
| 7 | `src/api/routes.py` | REST API |
| 8 | `src/tests/*.py` | Tests |
| 9 | `Dockerfile` | Container |
| 9 | `README.md` | Documentation |

---

## 11. Hardware Requirements

### Minimum (CPU-only)
- 16GB RAM
- Llama 3 8B runs on CPU but slowly (~30s per response)

### Recommended (GPU)
- NVIDIA GPU with 8GB+ VRAM
- Llama 3 8B: ~5GB VRAM, ~2-5s per response

### Model Options

| Model | Size | VRAM | Speed | Quality |
|-------|------|------|-------|---------|
| llama3:8b | 4.7GB | ~5GB | Fast | Good |
| llama3:70b | 40GB | ~40GB | Slow | Best |
| mistral:7b | 4.1GB | ~5GB | Fast | Good |
| phi3:mini | 2.3GB | ~3GB | Fastest | Decent |

**Recommendation**: Start with `llama3:8b` - best balance for a prototype.

---

## 12. Future Enhancements

1. **Chat Generation**: Generate trash talk for the public chat
2. **Model Switching**: Option to use different models per agent
3. **Learning Mode**: Track decisions for analysis
4. **Streaming**: Stream LLM responses for real-time UI
5. **Cost-free Cloud Option**: Use free tiers (Groq, Together.ai) as backup
