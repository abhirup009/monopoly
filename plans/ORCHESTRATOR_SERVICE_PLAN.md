# Orchestrator Service - Implementation Plan

## Overview

Python service that coordinates game flow between Game Engine, AI Agents, and Frontend clients via WebSockets.

```
┌─────────────────┐
│    Frontend     │
│  (React/Vite)   │
└────────┬────────┘
         │ Socket.IO
         ▼
┌─────────────────────────────────────────────────┐
│            ORCHESTRATOR SERVICE                  │
│                 (Python)                         │
│  ┌─────────────┐  ┌─────────────┐  ┌──────────┐ │
│  │ Game Loop   │  │  Socket.IO  │  │  Event   │ │
│  │ Controller  │  │   Server    │  │  Bus     │ │
│  └─────────────┘  └─────────────┘  └──────────┘ │
└───────┬─────────────────────────────────┬───────┘
        │ HTTP                            │ HTTP
        ▼                                 ▼
┌─────────────────┐               ┌─────────────────┐
│  Game Engine    │               │   AI Agent      │
│  (Port 8000)    │               │  (Port 8001)    │
└─────────────────┘               └─────────────────┘
```

---

## Technology Stack

| Purpose | Framework | Version |
|---------|-----------|---------|
| REST API | FastAPI | >=0.109.0 |
| WebSockets | python-socketio | >=5.10.0 |
| Async HTTP | httpx | >=0.26.0 |
| Redis Pub/Sub | redis[hiredis] | >=5.0.0 |
| Scheduling | APScheduler | >=3.10.0 |
| Settings | pydantic-settings | >=2.1.0 |

---

## Project Structure

```
services/orchestrator/
├── src/
│   ├── __init__.py
│   ├── main.py                 # FastAPI + Socket.IO mount
│   ├── config.py               # Environment settings
│   │
│   ├── game/
│   │   ├── __init__.py
│   │   ├── loop.py             # GameLoopController
│   │   ├── state.py            # GameSession state management
│   │   └── phases.py           # Turn phase definitions
│   │
│   ├── clients/
│   │   ├── __init__.py
│   │   ├── game_engine.py      # Game Engine HTTP client
│   │   └── ai_agent.py         # AI Agent HTTP client
│   │
│   ├── ws/
│   │   ├── __init__.py
│   │   ├── server.py           # Socket.IO server setup
│   │   ├── events.py           # Event definitions
│   │   └── handlers.py         # Client event handlers
│   │
│   ├── api/
│   │   ├── __init__.py
│   │   └── routes.py           # REST endpoints
│   │
│   └── tests/
│       ├── __init__.py
│       ├── conftest.py
│       ├── test_game_loop.py
│       ├── test_clients.py
│       └── test_ws.py
│
├── pyproject.toml
├── Dockerfile
└── .env.example
```

---

## Core Components

### 1. GameLoopController

Manages turn execution with timeout handling.

```python
class GameLoopController:
    def __init__(
        self,
        game_engine: GameEngineClient,
        ai_agent: AIAgentClient,
        event_bus: EventBus,
        turn_timeout: float = 30.0,
    ):
        self.game_engine = game_engine
        self.ai_agent = ai_agent
        self.event_bus = event_bus
        self.turn_timeout = turn_timeout
        self.game_speed = GameSpeed.NORMAL
        self._running = False

    async def run_game(self, game_id: UUID, agent_configs: list[AgentConfig]):
        """Main game loop."""
        self._running = True

        while self._running:
            state = await self.game_engine.get_state(game_id)

            if state.status == "completed":
                await self.event_bus.emit("game:ended", state)
                break

            await self._execute_turn(game_id, state)
            await self._apply_speed_delay()

    async def _execute_turn(self, game_id: UUID, state: GameState):
        """Execute a single turn with timeout."""
        player = state.players[state.current_player_index]

        await self.event_bus.emit("turn:start", {
            "player_id": player.id,
            "turn_number": state.turn_number,
        })

        try:
            # Get AI decision with timeout
            action = await asyncio.wait_for(
                self.ai_agent.get_decision(game_id, player.id),
                timeout=self.turn_timeout,
            )
        except asyncio.TimeoutError:
            action = self._get_default_action(state.turn_phase)
            await self.event_bus.emit("turn:timeout", {"player_id": player.id})

        # Execute action
        result = await self.game_engine.execute_action(game_id, player.id, action)

        await self.event_bus.emit("turn:action", {
            "player_id": player.id,
            "action": action,
            "result": result,
        })

    async def _apply_speed_delay(self):
        """Apply delay based on game speed setting."""
        delays = {
            GameSpeed.FAST: 0.5,
            GameSpeed.NORMAL: 2.0,
            GameSpeed.SLOW: 5.0,
        }
        await asyncio.sleep(delays[self.game_speed])
```

### 2. Socket.IO Server

Real-time communication with frontend clients.

```python
# ws/server.py
import socketio

sio = socketio.AsyncServer(
    async_mode="asgi",
    cors_allowed_origins="*",
)

@sio.event
async def connect(sid, environ):
    """Client connected."""
    logger.info(f"Client connected: {sid}")

@sio.event
async def disconnect(sid):
    """Client disconnected."""
    logger.info(f"Client disconnected: {sid}")

@sio.event
async def join_game(sid, data):
    """Join a game room as spectator."""
    game_id = data["game_id"]
    await sio.enter_room(sid, f"game:{game_id}")

    # Send current state
    state = await game_engine.get_state(game_id)
    await sio.emit("game:state", state.dict(), room=sid)

@sio.event
async def set_speed(sid, data):
    """Change game speed."""
    game_id = data["game_id"]
    speed = GameSpeed(data["speed"])
    game_sessions[game_id].set_speed(speed)
```

### 3. Event Bus

Internal event coordination + Socket.IO broadcasting.

```python
# ws/events.py
class EventBus:
    def __init__(self, sio: socketio.AsyncServer):
        self.sio = sio
        self._handlers: dict[str, list[Callable]] = {}

    async def emit(self, event: str, data: dict, game_id: UUID | None = None):
        """Emit event to handlers and Socket.IO room."""
        # Internal handlers
        for handler in self._handlers.get(event, []):
            await handler(data)

        # Broadcast to spectators
        if game_id:
            await self.sio.emit(event, data, room=f"game:{game_id}")

    def on(self, event: str, handler: Callable):
        """Register internal event handler."""
        self._handlers.setdefault(event, []).append(handler)
```

---

## WebSocket Events

### Server → Client

| Event | Payload | Description |
|-------|---------|-------------|
| `game:state` | `GameState` | Full game state |
| `game:started` | `{game_id, players}` | Game started |
| `game:ended` | `{winner_id, final_state}` | Game completed |
| `turn:start` | `{player_id, turn_number}` | Turn began |
| `turn:action` | `{player_id, action, result}` | Action executed |
| `turn:timeout` | `{player_id}` | Player timed out |
| `agent:thinking` | `{player_id}` | AI is deciding |

### Client → Server

| Event | Payload | Description |
|-------|---------|-------------|
| `join_game` | `{game_id}` | Join as spectator |
| `leave_game` | `{game_id}` | Leave game room |
| `set_speed` | `{game_id, speed}` | Change game speed |

---

## REST API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/games` | Create and start new game |
| GET | `/games/{id}` | Get game status |
| POST | `/games/{id}/stop` | Stop running game |
| POST | `/games/{id}/speed` | Set game speed |
| GET | `/health` | Service health |

### Create Game Request

```json
{
  "agents": [
    {"name": "Baron Von Moneybags", "personality": "aggressive"},
    {"name": "Professor Pennypincher", "personality": "analytical"},
    {"name": "Lady Luck", "personality": "chaotic"}
  ],
  "settings": {
    "speed": "normal",
    "turn_timeout": 30
  }
}
```

---

## Configuration

```python
# config.py
class Settings(BaseSettings):
    # Service
    host: str = "0.0.0.0"
    port: int = 3000

    # Dependencies
    game_engine_url: str = "http://localhost:8000"
    ai_agent_url: str = "http://localhost:8001"
    redis_url: str = "redis://localhost:6379"

    # Game settings
    turn_timeout: float = 30.0
    default_speed: str = "normal"

    model_config = SettingsConfigDict(env_prefix="ORCHESTRATOR_")
```

---

## Game Speed

| Speed | Turn Delay | Use Case |
|-------|------------|----------|
| Fast | 0.5s | Testing, demos |
| Normal | 2.0s | Standard viewing |
| Slow | 5.0s | Detailed observation |

---

## Dependencies

```toml
[project]
name = "monopoly-orchestrator"
version = "0.1.0"
requires-python = ">=3.11"

dependencies = [
    "fastapi>=0.109.0",
    "uvicorn[standard]>=0.27.0",
    "python-socketio>=5.10.0",
    "httpx>=0.26.0",
    "redis[hiredis]>=5.0.0",
    "pydantic>=2.5.0",
    "pydantic-settings>=2.1.0",
]

[project.optional-dependencies]
dev = [
    "pytest>=7.4.0",
    "pytest-asyncio>=0.23.0",
    "pytest-cov>=4.1.0",
    "ruff>=0.1.0",
]
```

---

## Implementation Steps

### Step 1: Project Setup
- [ ] Create directory structure
- [ ] Set up pyproject.toml
- [ ] Create config.py with settings
- [ ] Create Dockerfile

### Step 2: HTTP Clients
- [ ] Implement GameEngineClient
- [ ] Implement AIAgentClient
- [ ] Add retry logic with tenacity

### Step 3: Socket.IO Server
- [ ] Set up Socket.IO with FastAPI
- [ ] Implement connection handlers
- [ ] Implement room management (join/leave game)
- [ ] Create EventBus for broadcasting

### Step 4: Game Loop
- [ ] Implement GameLoopController
- [ ] Add turn timeout handling
- [ ] Add game speed control
- [ ] Implement turn phases

### Step 5: REST API
- [ ] Create game endpoints
- [ ] Add health check
- [ ] Wire up game creation flow

### Step 6: Testing
- [ ] Unit tests for game loop
- [ ] Unit tests for clients
- [ ] WebSocket integration tests

### Step 7: Docker
- [ ] Add to docker-compose.yml
- [ ] Test full stack integration

---

## Flow: Game Creation

```
Frontend                Orchestrator           Game Engine          AI Agent
   │                         │                      │                   │
   │  POST /games            │                      │                   │
   │────────────────────────>│                      │                   │
   │                         │  POST /game          │                   │
   │                         │─────────────────────>│                   │
   │                         │  {game_id, players}  │                   │
   │                         │<─────────────────────│                   │
   │                         │                      │                   │
   │                         │  POST /game/{id}/start                   │
   │                         │─────────────────────>│                   │
   │                         │                      │                   │
   │  {game_id, ws_url}      │                      │                   │
   │<────────────────────────│                      │                   │
   │                         │                      │                   │
   │  WS: join_game          │                      │                   │
   │────────────────────────>│                      │                   │
   │                         │                      │                   │
   │                         │  [Game Loop Starts]  │                   │
   │                         │                      │                   │
   │  WS: game:state         │                      │                   │
   │<────────────────────────│                      │                   │
```

---

## Flow: Turn Execution

```
Orchestrator              Game Engine              AI Agent
     │                         │                       │
     │  GET /game/{id}         │                       │
     │────────────────────────>│                       │
     │  {state}                │                       │
     │<────────────────────────│                       │
     │                         │                       │
     │  [Emit turn:start to WS]                        │
     │                         │                       │
     │  POST /games/{id}/decide                        │
     │────────────────────────────────────────────────>│
     │                         │                       │
     │                         │  GET /game/{id}/actions
     │                         │<──────────────────────│
     │                         │  {valid_actions}      │
     │                         │──────────────────────>│
     │                         │                       │
     │                         │      [LLM decides]    │
     │                         │                       │
     │  {action}               │                       │
     │<────────────────────────────────────────────────│
     │                         │                       │
     │  POST /game/{id}/action │                       │
     │────────────────────────>│                       │
     │  {result}               │                       │
     │<────────────────────────│                       │
     │                         │                       │
     │  [Emit turn:action to WS]                       │
     │                         │                       │
     │  [Apply speed delay]    │                       │
     │                         │                       │
     │  [Next turn...]         │                       │
```
