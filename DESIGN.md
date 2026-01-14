# AI Monopoly Arena - System Design Document

## Executive Summary

This document outlines the architecture for an AI-powered Monopoly game where 3 LLM agents compete against each other, engage in trash talk, form secret alliances, and make strategic decisions—all visible through a real-time frontend.

---

## 1. Open Source Monopoly Engine Analysis

### Evaluated Options

| Engine | Language | Pros | Cons | AI Support |
|--------|----------|------|------|------------|
| [MonopolySimulator](https://github.com/giogix2/MonopolySimulator) | Python | Designed for ML agents, modular, MIT license | Missing trading/bidding, Jupyter-focused | Native |
| [monopoly-js](https://github.com/francois-roseberry/monopoly-js) | JavaScript | State machine pattern, basic AI | Legacy code (10+ years), incomplete features | Basic |
| [itaylayzer/Monopoly](https://github.com/itaylayzer/Monopoly) | TypeScript | Modern stack, chat system, React UI | P2P architecture, no AI support | None |
| [Open Monopoly](https://github.com/open-monopoly) | Kotlin | Open source | Dormant since 2018 | None |

### Recommendation: **Hybrid Approach**

**Primary Choice: Fork and extend MonopolySimulator** with a TypeScript orchestration layer.

**Rationale:**
1. MonopolySimulator is explicitly designed for ML/AI agent training
2. Python backend integrates well with LLM APIs (OpenAI, Anthropic, local models)
3. We add a TypeScript/Node.js layer for real-time communication and frontend

**Alternative: Build custom engine in TypeScript** if Python integration proves problematic.

---

## 2. System Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                              FRONTEND (React)                                │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────┐ │
│  │  Game Board │  │  Chat Panel │  │ Player Stats│  │  Backroom Chats     │ │
│  │  Visualizer │  │  (Public)   │  │  & Actions  │  │  (1:1 Private)      │ │
│  └─────────────┘  └─────────────┘  └─────────────┘  └─────────────────────┘ │
└───────────────────────────────────┬─────────────────────────────────────────┘
                                    │ WebSocket (Socket.IO)
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                         ORCHESTRATION SERVICE (Node.js/TypeScript)          │
│  ┌───────────────┐  ┌───────────────┐  ┌───────────────┐  ┌──────────────┐  │
│  │  Game Loop    │  │  Chat Router  │  │  Event Bus    │  │  State Sync  │  │
│  │  Controller   │  │  (Pub/Redis)  │  │  (EventEmitter│  │  Manager     │  │
│  └───────────────┘  └───────────────┘  └───────────────┘  └──────────────┘  │
└───────────┬─────────────────┬─────────────────┬─────────────────────────────┘
            │                 │                 │
            ▼                 ▼                 ▼
┌───────────────────┐ ┌───────────────┐ ┌─────────────────────────────────────┐
│   GAME ENGINE     │ │  CHAT SERVICE │ │          AI AGENT SERVICE           │
│   (Python)        │ │  (Node.js)    │ │          (Python/Node.js)           │
│                   │ │               │ │  ┌─────────┐ ┌─────────┐ ┌────────┐ │
│  - Game State     │ │  - Public Room│ │  │ Agent 1 │ │ Agent 2 │ │Agent 3 │ │
│  - Rules Engine   │ │  - Backrooms  │ │  │ (GPT-4) │ │(Claude) │ │(Llama) │ │
│  - Turn Manager   │ │  - History    │ │  └─────────┘ └─────────┘ └────────┘ │
│  - Trade System   │ │               │ │                                     │
└───────────────────┘ └───────────────┘ └─────────────────────────────────────┘
            │                 │                 │
            └─────────────────┴─────────────────┘
                              │
                              ▼
                    ┌───────────────────┐
                    │   DATA STORE      │
                    │  (Redis + Postgres)│
                    │                   │
                    │  - Game State     │
                    │  - Chat History   │
                    │  - Agent Memory   │
                    └───────────────────┘
```

---

## 3. Microservices Breakdown

### 3.1 Game Engine Service (Python)

**Purpose:** Core Monopoly game logic and state management.

**Technology:**
- Python 3.11+
- FastAPI for REST API
- Pydantic for data validation
- Based on MonopolySimulator with extensions

**Responsibilities:**
- Maintain authoritative game state
- Validate all game actions (moves, purchases, building)
- Execute dice rolls and movement
- Handle property transactions and rent collection
- Track player finances and bankruptcy

**API Endpoints:**
```
POST   /game/create              - Initialize new game
GET    /game/{id}/state          - Get current game state
POST   /game/{id}/action         - Submit player action
GET    /game/{id}/valid-actions  - Get valid actions for current player
# Trading endpoints (v2)
# POST   /game/{id}/trade/propose  - Propose a trade
# POST   /game/{id}/trade/respond  - Accept/reject trade
```

**Features to Implement (v1):**
- ✅ Property buying (buy or pass)
- ✅ House/hotel building rules
- ✅ Get Out of Jail logic
- ✅ Rent collection
- ❌ Trading system (deferred to v2)
- ❌ Auction/bidding system (deferred to v2)
- ❌ Mortgage/unmortgage logic (deferred to v2)

---

### 3.2 Orchestration Service (Python)

**Purpose:** Central coordinator between all services and frontend.

**Technology:**
- Python 3.11+
- FastAPI for REST API
- python-socketio for real-time WebSocket communication
- httpx for async HTTP client
- asyncio for coordination and timeouts

**Responsibilities:**
- Manage game loop and turn order
- Coordinate AI agent decision requests
- Broadcast state updates to frontend via Socket.IO
- Handle turn timeouts (30s default)
- Configurable game speed (Fast/Normal/Slow)

**Key Components:**

```python
class GameLoopController:
    async def execute_turn(self, game_id: UUID, state: GameState):
        player = state.players[state.current_player_index]

        # Get AI decision with timeout
        try:
            action = await asyncio.wait_for(
                self.ai_agent.get_decision(game_id, player.id),
                timeout=self.turn_timeout,  # 30s
            )
        except asyncio.TimeoutError:
            action = self._get_default_action(state.turn_phase)

        # Execute action via Game Engine
        result = await self.game_engine.execute_action(game_id, player.id, action)

        # Broadcast to spectators
        await self.event_bus.emit("turn:action", {
            "player_id": player.id,
            "action": action,
            "result": result,
        })

class GameSpeed(str, Enum):
    FAST = "fast"      # 0.5s delay
    NORMAL = "normal"  # 2.0s delay
    SLOW = "slow"      # 5.0s delay
```

---

### 3.3 AI Agent Service (Python)

**Purpose:** Manage LLM-powered game agents.

**Technology:**
- Python 3.11+
- LangChain or direct API calls
- Support for multiple LLM providers:
  - OpenAI (GPT-4)
  - Anthropic (Claude)
  - Local models via Ollama (Llama, Mistral)

**Agent Architecture:**

```python
class MonopolyAgent:
    def __init__(self, name: str, personality: str, model: str):
        self.name = name
        self.personality = personality  # Aggressive, Conservative, Trickster
        self.model = model
        self.memory = AgentMemory()     # Tracks past events, alliances, betrayals

    async def decide_action(self, game_state: GameState, valid_actions: list) -> Action:
        """Make a game decision based on current state."""
        prompt = self._build_decision_prompt(game_state, valid_actions)
        response = await self.llm.generate(prompt)
        return self._parse_action(response)

    async def generate_trash_talk(self, context: ChatContext) -> str:
        """Generate public chat message."""
        prompt = self._build_chat_prompt(context)
        return await self.llm.generate(prompt)

    # V2: Backroom messaging
    # async def generate_backroom_message(self, target: str, context: ChatContext) -> str:
    #     """Generate private 1:1 message."""
    #     prompt = self._build_chat_prompt(context, target=target)
    #     return await self.llm.generate(prompt)
```

**Prompt Engineering Strategy:**

Each agent receives:
1. **System Prompt:** Personality, play style, strategic tendencies
2. **Game Context:** Current board state, property ownership, player finances
3. **Historical Context:** Past interactions, broken promises, alliance history
4. **Available Actions:** Valid moves with consequences explained

**Example Decision Prompt:**
```
You are "Baron Von Moneybags", an aggressive and theatrical Monopoly player.
You love to taunt opponents and make bold moves.

CURRENT GAME STATE:
- Your cash: $1,200
- Your properties: Boardwalk, Park Place, Mediterranean
- You just landed on: Baltic Avenue (unowned, price: $60)

OPPONENTS:
- "Professor Pennypincher" (Claude): $800, owns 4 railroads
- "Lady Luck" (Llama): $2,100, owns all utilities

VALID ACTIONS:
1. BUY Baltic Avenue for $60
2. PASS (property remains unowned)

Recent chat: Professor Pennypincher said "You'll never complete that color set!"

What action do you take? Respond with JSON: {"action": "...", "reasoning": "..."}
```

---

### 3.4 Chat Service (Node.js)

**Purpose:** Manage all chat communications.

**Technology:**
- Node.js with TypeScript
- Redis Pub/Sub for real-time messaging
- PostgreSQL for persistence

**Chat Types (v1):**

| Type | Visibility | Purpose |
|------|------------|---------|
| Public Chatroom | All players + spectators | Trash talk, reactions, taunts |
| System Messages | All | Game events, announcements |

*Backroom 1:1 chats deferred to v2*

**Message Flow:**
```
Agent Decision to Chat
        │
        ▼
┌───────────────────┐
│  Chat Service     │
│  - Validate msg   │
│  - Store in DB    │
│  - Publish Redis  │
└───────────────────┘
        │
        ▼
Redis channel: "game:{id}:public"
        │
        ▼
Socket.IO broadcasts to all clients
```

---

### 3.5 Frontend Service (React)

**Purpose:** Visualize game state and interactions.

**Technology:**
- React 18+ with TypeScript
- Vite for build tooling
- TailwindCSS for styling
- Socket.IO Client for real-time updates
- Framer Motion for animations

**UI Components:**

```
┌─────────────────────────────────────────────────────────────────┐
│  HEADER: Game Title | Turn Counter | Current Player | Speed     │
├─────────────────────────────────────────────────────────────────┤
│                    │                       │                     │
│   GAME BOARD       │   PLAYER PANELS       │   CHAT SECTION      │
│   (Interactive     │   ┌─────────────┐     │   ┌─────────────┐   │
│    Monopoly Board) │   │ Agent 1     │     │   │ Public Chat │   │
│                    │   │ $1,200      │     │   │             │   │
│   - Properties     │   │ Props: 5    │     │   │ [messages]  │   │
│   - Player tokens  │   └─────────────┘     │   │             │   │
│   - Dice animation │   ┌─────────────┐     │   │             │   │
│   - Card popups    │   │ Agent 2     │     │   │             │   │
│                    │   │ $800        │     │   │             │   │
│                    │   │ Props: 4    │     │   │             │   │
│                    │   └─────────────┘     │   │             │   │
│                    │   ┌─────────────┐     │   │             │   │
│                    │   │ Agent 3     │     │   │             │   │
│                    │   │ $2,100      │     │   └─────────────┘   │
│                    │   │ Props: 2    │     │                     │
│                    │   └─────────────┘     │                     │
├─────────────────────────────────────────────────────────────────┤
│  ACTION LOG: Real-time feed of game events and decisions        │
└─────────────────────────────────────────────────────────────────┘
```

**Key Features:**
- Animated token movement
- Property deed popups on click
- Public chat with agent avatars and personalities
- Decision reasoning display (optional debug mode)
- Game speed controls (Fast/Normal/Slow)

---

## 4. Data Models

### 4.1 Game State

```typescript
interface GameState {
  id: string;
  status: 'waiting' | 'in_progress' | 'completed';
  currentPlayerIndex: number;
  turnNumber: number;
  turnPhase: TurnPhase;

  players: Player[];
  properties: Property[];

  communityChestDeck: Card[];
  chanceDeck: Card[];

  freeParkingPool: number;  // House rule option

  // pendingTrade?: TradeProposal;  // Deferred to v2

  winner?: string;
}

interface Player {
  id: string;
  name: string;
  model: string;  // gpt-4, claude-3, llama-3
  personality: string;

  position: number;  // 0-39 board position
  cash: number;
  properties: string[];  // property IDs

  inJail: boolean;
  jailTurns: number;
  getOutOfJailCards: number;

  isBankrupt: boolean;
}

interface Property {
  id: string;
  name: string;
  position: number;
  type: 'street' | 'railroad' | 'utility';
  colorGroup?: string;

  price: number;
  rent: number[];  // Base, 1 house, 2 houses, 3, 4, hotel
  houseCost?: number;

  ownerId?: string;
  houses: number;  // 0-4, 5 = hotel
  // isMortgaged: boolean;  // Deferred to v2
}
```

### 4.2 Agent Memory

```typescript
interface AgentMemory {
  agentId: string;

  // Track promises and agreements
  alliances: Alliance[];

  // Track betrayals for grudges
  betrayals: Betrayal[];

  // Track opponent patterns
  opponentProfiles: Map<string, OpponentProfile>;

  // Recent game events
  recentEvents: GameEvent[];
}

interface Alliance {
  partnerId: string;
  terms: string;  // Natural language description
  formedAt: number;  // Turn number
  status: 'active' | 'broken' | 'fulfilled';
}

interface Betrayal {
  betrayerId: string;
  description: string;
  turn: number;
  severity: 'minor' | 'major' | 'catastrophic';
}
```

---

## 5. Communication Protocols

### 5.1 WebSocket Events

```typescript
// Client -> Server
interface ClientEvents {
  'game:spectate': { gameId: string };
  'chat:send': { gameId: string; message: string; target?: string };
}

// Server -> Client
interface ServerEvents {
  'game:state': GameState;
  'game:action': { playerId: string; action: Action; result: ActionResult };
  'game:turn:start': { playerId: string; turnNumber: number };
  'game:turn:end': { playerId: string };

  'chat:message': ChatMessage;  // Public chat only in v1

  // Trading events (v2)
  // 'trade:proposed': TradeProposal;
  // 'trade:resolved': { accepted: boolean; trade: TradeProposal };

  'agent:thinking': { playerId: string; phase: string };
  'agent:decision': { playerId: string; action: Action; reasoning?: string };
}
```

### 5.2 Inter-Service Communication

```
┌─────────────────┐     REST/HTTP      ┌─────────────────┐
│  Orchestrator   │ ◄────────────────► │   Game Engine   │
└─────────────────┘                    └─────────────────┘
        │
        │ gRPC / REST
        ▼
┌─────────────────┐
│   AI Agents     │
└─────────────────┘
        │
        │ Redis Pub/Sub
        ▼
┌─────────────────┐
│  Chat Service   │
└─────────────────┘
```

---

## 6. AI Decision-Making Flow

```
┌───────────────────────────────────────────────────────────────┐
│                     TURN SEQUENCE                              │
└───────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│ 1. PRE-ROLL PHASE                                               │
│    - Agent reviews game state                                   │
│    - OPTIONAL: Send chat message                                │
│    - Automatic proceed to roll                                  │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│ 2. ROLL & MOVE                                                  │
│    - Dice rolled (by engine, not agent choice)                  │
│    - Token moves to new position                                │
│    - Doubles handling (roll again / jail on 3rd)                │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│ 3. LANDING PHASE                                                │
│    Unowned Property:                                            │
│    ├─► Agent decides: BUY or PASS (stays unowned)               │
│    │                                                            │
│    Owned Property:                                              │
│    ├─► Rent calculated and paid automatically                   │
│    │                                                            │
│    Chance/Community Chest:                                      │
│    ├─► Card drawn and executed                                  │
│    │                                                            │
│    Go To Jail:                                                  │
│    ├─► Agent moved to jail                                      │
│    │                                                            │
│    Free Parking/Just Visiting/Go:                               │
│    └─► No action required                                       │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│ 4. POST-ROLL PHASE                                              │
│    - Agent can build houses/hotels (if owns full color set)     │
│    - OPTIONAL: Generate trash talk (public chat)                │
│    - Agent signals "end turn"                                   │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
                     Next Player's Turn
```

---

## 7. Technology Stack Summary

| Layer | Technology | Purpose |
|-------|------------|---------|
| **Frontend** | React, TypeScript, Vite, TailwindCSS, Socket.IO Client | UI and real-time updates |
| **Orchestrator** | Python, FastAPI, python-socketio, asyncio | Game coordination |
| **Game Engine** | Python, FastAPI, Pydantic, SQLAlchemy | Game rules and state |
| **AI Agents** | Python, FastAPI, Ollama, httpx | LLM integration |
| **Chat** | Python, Redis Pub/Sub | Messaging |
| **Database** | Redis (pub/sub, caching), PostgreSQL (persistence) | Data storage |
| **Container** | Docker, Docker Compose | Deployment |

---

## 8. Development Phases

### Phase 1: Core Game Engine (v1) ✅ COMPLETE
- [x] Build custom Python engine (FastAPI + SQLAlchemy)
- [x] Implement property buying (buy or pass)
- [x] Add house/hotel building logic
- [x] Implement jail mechanics
- [x] Implement rent collection
- [x] Create FastAPI REST interface
- [x] Set up PostgreSQL with game state schema
- [x] Write comprehensive tests

### Phase 2: Orchestration Layer 🔄 IN PROGRESS
- [ ] Set up Python/FastAPI project
- [ ] Implement game loop controller with 30s timeout
- [ ] Create WebSocket server with python-socketio
- [ ] Build inter-service communication (httpx)
- [ ] Add configurable game speed (Fast/Normal/Slow)

### Phase 3: AI Agent System ✅ COMPLETE
- [x] Design agent prompt templates
- [x] Implement Ollama LLM support (local models)
- [x] Create session-based memory system
- [x] Build decision-making pipeline with action parsing
- [x] Add personality configurations (aggressive, analytical, chaotic)

### Phase 4: Chat System
- [ ] Set up Redis Pub/Sub
- [ ] Implement public chatroom
- [ ] Create chat message routing
- [ ] Add chat history persistence (PostgreSQL)

### Phase 5: Frontend
- [ ] Create React project with Vite
- [ ] Build game board visualization
- [ ] Implement player panels
- [ ] Add public chat interface
- [ ] Create action log viewer
- [ ] Add game speed controls
- [ ] Add animations and polish

### Phase 6: Integration & Testing
- [x] Game Engine + AI Agent integration tested
- [ ] Full stack end-to-end testing
- [ ] Performance optimization
- [ ] Bug fixes and edge cases

### Phase 7: Future (v2)
- [ ] Backroom 1:1 private chats
- [ ] Alliance/betrayal memory system
- [ ] Trading system (negotiate property/cash exchanges)
- [ ] Auction/bidding system
- [ ] Mortgage/unmortgage logic
- [ ] Game persistence (save/resume)
- [ ] Multiple concurrent games
- [ ] Multi-provider LLM support (OpenAI, Anthropic)

---

## 9. Directory Structure

```
monopoly/
├── apps/
│   └── frontend/              # React frontend
│       ├── src/
│       │   ├── components/
│       │   ├── hooks/
│       │   └── stores/
│       └── package.json
│
├── services/
│   ├── game-engine/           # Python game engine ✅
│   │   ├── src/
│   │   │   ├── api/           # REST endpoints
│   │   │   ├── engine/        # Game logic
│   │   │   ├── db/            # Database models
│   │   │   ├── models/        # Pydantic schemas
│   │   │   ├── data/          # Board, cards, properties
│   │   │   └── tests/
│   │   ├── pyproject.toml
│   │   └── Dockerfile
│   │
│   ├── ai-agent/              # Python AI agent service ✅
│   │   ├── src/
│   │   │   ├── api/           # REST endpoints
│   │   │   ├── agent/         # Agent orchestration
│   │   │   ├── client/        # Game Engine client
│   │   │   ├── llm/           # Ollama wrapper
│   │   │   ├── parser/        # Action parsing
│   │   │   ├── prompts/       # Personality prompts
│   │   │   └── tests/
│   │   ├── pyproject.toml
│   │   └── Dockerfile
│   │
│   └── orchestrator/          # Python orchestration service
│       ├── src/
│       │   ├── api/           # REST endpoints
│       │   ├── game/          # Game loop controller
│       │   ├── clients/       # Service clients
│       │   ├── ws/            # Socket.IO server
│       │   └── tests/
│       ├── pyproject.toml
│       └── Dockerfile
│
├── infrastructure/
│   └── init-db/               # Database init scripts
│
├── docs/                      # Documentation
├── plans/                     # Implementation plans
├── docker-compose.yml
└── DESIGN.md
```

---

## 10. Configuration

### Environment Variables

```bash
# .env.example

# Database
DATABASE_URL=postgresql://monopoly:monopoly@localhost:5432/monopoly
REDIS_URL=redis://localhost:6379

# Game Engine
GAME_ENGINE_PORT=8000
GAME_ENGINE_HOST=localhost

# Orchestrator
ORCHESTRATOR_PORT=3000
TURN_TIMEOUT_MS=30000
GAME_SPEED=normal  # fast (0.5s), normal (2s), slow (5s)

# AI Agents
OPENAI_API_KEY=sk-...
ANTHROPIC_API_KEY=sk-ant-...
OLLAMA_BASE_URL=http://localhost:11434

# Agent Configuration
AGENT_1_MODEL=gpt-4
AGENT_1_NAME="Baron Von Moneybags"
AGENT_1_PERSONALITY=aggressive

AGENT_2_MODEL=claude-3-opus
AGENT_2_NAME="Professor Pennypincher"
AGENT_2_PERSONALITY=analytical

AGENT_3_MODEL=llama3
AGENT_3_NAME="Lady Luck"
AGENT_3_PERSONALITY=chaotic

# Frontend
VITE_WS_URL=ws://localhost:3000
```

---

## 11. Deployment

### Local Development (Docker Compose)

```yaml
# docker-compose.yml
version: '3.8'

services:
  postgres:
    image: postgres:16-alpine
    ports:
      - "5432:5432"
    environment:
      POSTGRES_USER: monopoly
      POSTGRES_PASSWORD: monopoly
      POSTGRES_DB: monopoly
    volumes:
      - postgres_data:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U monopoly"]
      interval: 5s
      timeout: 5s
      retries: 5

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"

  game-engine:
    build: ./services/game-engine
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=postgresql://monopoly:monopoly@postgres:5432/monopoly
      - REDIS_URL=redis://redis:6379
    depends_on:
      postgres:
        condition: service_healthy

  ai-agents:
    build: ./services/ai-agents
    environment:
      - DATABASE_URL=postgresql://monopoly:monopoly@postgres:5432/monopoly
      - OPENAI_API_KEY=${OPENAI_API_KEY}
      - ANTHROPIC_API_KEY=${ANTHROPIC_API_KEY}
      - OLLAMA_BASE_URL=http://ollama:11434
    depends_on:
      - ollama
      - postgres

  ollama:
    image: ollama/ollama
    ports:
      - "11434:11434"
    volumes:
      - ollama_data:/root/.ollama

  orchestrator:
    build: ./apps/orchestrator
    ports:
      - "3000:3000"
    environment:
      - DATABASE_URL=postgresql://monopoly:monopoly@postgres:5432/monopoly
      - REDIS_URL=redis://redis:6379
      - GAME_ENGINE_URL=http://game-engine:8000
      - AI_AGENTS_URL=http://ai-agents:8001
      - TURN_TIMEOUT_MS=30000
    depends_on:
      - redis
      - postgres
      - game-engine
      - ai-agents

  frontend:
    build: ./apps/frontend
    ports:
      - "5173:5173"
    environment:
      - VITE_WS_URL=ws://localhost:3000

volumes:
  postgres_data:
  ollama_data:
```

---

## 12. Design Decisions (Finalized)

| Decision | Answer | Implementation Notes |
|----------|--------|---------------------|
| **Turn Timing** | 30 second limit | Agents must decide within timeout or forfeit action |
| **Game Speed** | Configurable delays | Speed slider: Fast (0.5s), Normal (2s), Slow (5s) |
| **Human Players** | No | AI-only games, spectator mode for humans |
| **Persistence** | Not in v1 | Games run to completion, no save/resume initially |
| **Multiple Games** | Single game focus | One game instance at a time for v1 |
| **Database** | PostgreSQL | Better concurrency, JSON support, proper indexing |
| **Chat** | Public only in v1 | Backroom 1:1 chats deferred to v2 |

---

## 12.1 V1 Scope Summary

### Included in V1
| Feature | Notes |
|---------|-------|
| ✅ Property buying | Buy or pass (stays unowned) |
| ✅ House/hotel building | Standard Monopoly building rules |
| ✅ Rent collection | Automatic when landing on owned property |
| ✅ Jail mechanics | Go to jail, pay $50 or roll doubles |
| ✅ Chance/Community Chest | Card decks with effects |
| ✅ Public chatroom | Trash talk visible to all |
| ✅ 30s turn timeout | Forfeit action if agent times out |
| ✅ Configurable game speed | Fast/Normal/Slow delays |

### Deferred to V2
| Feature | Rationale |
|---------|-----------|
| ❌ Backroom 1:1 chats | Simplifies chat system; public trash talk only in v1 |
| ❌ Trading system | Agents compete for properties directly |
| ❌ Auction/bidding | If declined, property stays unowned |
| ❌ Mortgage/unmortgage | Simplifies financial decisions |
| ❌ Game persistence | Games run to completion |
| ❌ Multiple concurrent games | Single game focus |
| ❌ Human players | AI-only for v1 |

---

## 13. Sources & References

- [MonopolySimulator](https://github.com/giogix2/MonopolySimulator) - Python ML-focused simulator
- [monopoly-js](https://github.com/francois-roseberry/monopoly-js) - JavaScript state machine implementation
- [itaylayzer/Monopoly](https://github.com/itaylayzer/Monopoly) - Modern React/TypeScript multiplayer
- [Colyseus](https://colyseus.io/) - Node.js multiplayer framework (alternative to custom orchestrator)
- [GitHub Monopoly Topic](https://github.com/topics/monopoly-game) - 230+ implementations for reference
