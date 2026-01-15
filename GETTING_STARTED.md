# Getting Started with Monopoly Arena

This guide will help you set up and run the full Monopoly Arena stack - a real-time AI-powered Monopoly game where multiple AI agents compete against each other.

## Table of Contents

- [Prerequisites](#prerequisites)
- [Architecture Overview](#architecture-overview)
- [Quick Start](#quick-start)
- [Detailed Setup](#detailed-setup)
- [Running the Game](#running-the-game)
- [Configuration Options](#configuration-options)
- [Troubleshooting](#troubleshooting)

## Prerequisites

Before you begin, ensure you have the following installed:

### Required Software

| Software | Version | Purpose |
|----------|---------|---------|
| Python | 3.11+ | Backend services |
| Node.js | 18+ | Frontend |
| Docker & Docker Compose | Latest | PostgreSQL & Redis |
| Ollama | Latest | Local LLM for AI agents |

### Installing Prerequisites

**macOS (using Homebrew):**
```bash
# Python (via pyenv recommended)
brew install pyenv
pyenv install 3.12.0
pyenv global 3.12.0

# Node.js
brew install node

# Docker
brew install --cask docker

# Ollama
brew install ollama
```

**Linux (Ubuntu/Debian):**
```bash
# Python
sudo apt update
sudo apt install python3.11 python3.11-venv python3-pip

# Node.js
curl -fsSL https://deb.nodesource.com/setup_18.x | sudo -E bash -
sudo apt install nodejs

# Docker
sudo apt install docker.io docker-compose
sudo usermod -aG docker $USER

# Ollama
curl -fsSL https://ollama.com/install.sh | sh
```

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                         Frontend (React)                         │
│                      http://localhost:5173                       │
└─────────────────────────────────────────────────────────────────┘
                                │
                                │ WebSocket + REST
                                ▼
┌─────────────────────────────────────────────────────────────────┐
│                    Orchestrator Service                          │
│                    http://localhost:3000                         │
│         (Game coordination, WebSocket server, Event bus)         │
└─────────────────────────────────────────────────────────────────┘
                    │                       │
                    │ REST                  │ REST
                    ▼                       ▼
┌───────────────────────────┐   ┌───────────────────────────────┐
│     Game Engine           │   │       AI Agent Service        │
│  http://localhost:8000    │   │    http://localhost:8001      │
│  (Rules, state, moves)    │   │  (LLM decisions via Ollama)   │
└───────────────────────────┘   └───────────────────────────────┘
            │                               │
            ▼                               ▼
┌───────────────────────────┐   ┌───────────────────────────────┐
│    PostgreSQL (Docker)    │   │      Ollama (Local LLM)       │
│       Port 5432           │   │       Port 11434              │
└───────────────────────────┘   └───────────────────────────────┘
```

## Quick Start

If you want to get up and running quickly:

```bash
# 1. Clone the repository
git clone <repository-url>
cd monopoly

# 2. Start infrastructure (PostgreSQL & Redis)
docker-compose up -d

# 3. Start Ollama and pull the model
ollama serve &
ollama pull llama3.1:8b

# 4. Set up and start all services (run each in a separate terminal)

# Terminal 1: Game Engine
cd services/game-engine
python3 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
uvicorn src.main:app --host 0.0.0.0 --port 8000

# Terminal 2: AI Agent
cd services/ai-agent
python3 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
uvicorn src.main:app --host 0.0.0.0 --port 8001

# Terminal 3: Orchestrator
cd services/orchestrator
python3 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
uvicorn src.main:socket_app --host 0.0.0.0 --port 3000

# Terminal 4: Frontend
cd apps/frontend
npm install
npm run dev

# 5. Open http://localhost:5173 and click "Start new game"
```

## Detailed Setup

### Step 1: Start Infrastructure Services

The game requires PostgreSQL for game state persistence and Redis for caching.

```bash
# Start Docker containers
docker-compose up -d

# Verify they're running
docker-compose ps

# Expected output:
# monopoly-postgres   running   0.0.0.0:5432->5432/tcp
# monopoly-redis      running   0.0.0.0:6379->6379/tcp
```

### Step 2: Set Up Ollama (Local LLM)

The AI agents use Ollama to run a local LLM for decision-making.

```bash
# Start Ollama server (if not already running)
ollama serve

# In another terminal, pull the required model
ollama pull llama3.1:8b

# Verify the model is available
ollama list
```

**Alternative models** (if you have less RAM):
- `llama3.2:3b` - Smaller, faster, less capable
- `mistral:7b` - Good alternative to Llama

### Step 3: Set Up Game Engine Service

```bash
cd services/game-engine

# Create virtual environment
python3 -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install dependencies
pip install -e ".[dev]"

# Create .env file (optional, defaults work)
cp .env.example .env

# Run database migrations (if any)
# The service auto-creates tables on startup

# Start the service
uvicorn src.main:app --host 0.0.0.0 --port 8000

# Verify it's running
curl http://localhost:8000/health
# Expected: {"status":"healthy","service":"game-engine"}
```

### Step 4: Set Up AI Agent Service

```bash
cd services/ai-agent

# Create virtual environment
python3 -m venv .venv
source .venv/bin/activate

# Install dependencies
pip install -e ".[dev]"

# Create .env file (optional)
cp .env.example .env

# Start the service
uvicorn src.main:app --host 0.0.0.0 --port 8001

# Verify it's running
curl http://localhost:8001/health
# Expected: {"status":"healthy","ollama":"connected","model":"llama3",...}
```

### Step 5: Set Up Orchestrator Service

```bash
cd services/orchestrator

# Create virtual environment
python3 -m venv .venv
source .venv/bin/activate

# Install dependencies
pip install -e ".[dev]"

# Create .env file (optional)
cp .env.example .env

# Start the service (note: socket_app for WebSocket support)
uvicorn src.main:socket_app --host 0.0.0.0 --port 3000

# Verify it's running
curl http://localhost:3000/health
# Expected: {"status":"healthy","game_engine":"healthy","ai_agent":"healthy"}
```

### Step 6: Set Up Frontend

```bash
cd apps/frontend

# Install dependencies
npm install

# Start development server
npm run dev

# Frontend will be available at http://localhost:5173
```

## Running the Game

### Using the Web Interface

1. Open http://localhost:5173 in your browser
2. Click **"Start new game"** to create a game with 3 default AI agents
3. Watch the game unfold in real-time!

### Game Controls

| Control | Description |
|---------|-------------|
| **Speed: fast** | 0.5 second delays between actions |
| **Speed: normal** | 2 second delays |
| **Speed: slow** | 5 second delays |
| **Speed: watch** | 10 second delays (best for following along) |
| **Join game** | Enter a game ID to watch an existing game |

### Using the API Directly

You can also create and control games via the REST API:

```bash
# Create a new game
curl -X POST http://localhost:3000/games \
  -H "Content-Type: application/json" \
  -d '{
    "agents": [
      {"name": "Player 1", "personality": "aggressive", "model": "llama3.1:8b"},
      {"name": "Player 2", "personality": "analytical", "model": "llama3.1:8b"},
      {"name": "Player 3", "personality": "chaotic", "model": "llama3.1:8b"}
    ],
    "settings": {"speed": "watch"}
  }'

# Response: {"game_id": "uuid-here", "status": "running", ...}

# Get game state
curl http://localhost:3000/games/{game_id}

# Stop a game
curl -X POST http://localhost:3000/games/{game_id}/stop

# Change game speed
# (via WebSocket: emit "set_speed" event)
```

## Configuration Options

### Agent Personalities

| Personality | Description |
|-------------|-------------|
| `aggressive` | Always buys properties, takes risks |
| `analytical` | Calculates ROI, maintains cash reserves |
| `chaotic` | Unpredictable decisions, keeps opponents guessing |

### Environment Variables

**Game Engine** (`services/game-engine/.env`):
```env
DATABASE_URL=postgresql+asyncpg://monopoly:monopoly@localhost:5432/monopoly
```

**AI Agent** (`services/ai-agent/.env`):
```env
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=llama3.1:8b
GAME_ENGINE_URL=http://localhost:8000
```

**Orchestrator** (`services/orchestrator/.env`):
```env
GAME_ENGINE_URL=http://localhost:8000
AI_AGENT_URL=http://localhost:8001
HOST=0.0.0.0
PORT=3000
```

**Frontend** (`apps/frontend/.env`):
```env
VITE_ORCHESTRATOR_URL=http://localhost:3000
```

## Troubleshooting

### Common Issues

**1. "Ollama not connected" error**
```bash
# Make sure Ollama is running
ollama serve

# Check if model is available
ollama list

# Pull model if missing
ollama pull llama3.1:8b
```

**2. "Database connection failed"**
```bash
# Check if PostgreSQL is running
docker-compose ps

# Restart if needed
docker-compose down && docker-compose up -d
```

**3. "Port already in use"**
```bash
# Find process using the port
lsof -i :8000  # or :8001, :3000, :5173

# Kill the process
kill -9 <PID>
```

**4. "Module not found" errors**
```bash
# Make sure you're in the virtual environment
source .venv/bin/activate

# Reinstall dependencies
pip install -e ".[dev]"
```

**5. Frontend can't connect to backend**
- Ensure all backend services are running
- Check CORS is enabled (it is by default)
- Verify the orchestrator URL in frontend matches

### Health Check Commands

```bash
# Check all services at once
echo "Game Engine:" && curl -s http://localhost:8000/health | jq
echo "AI Agent:" && curl -s http://localhost:8001/health | jq
echo "Orchestrator:" && curl -s http://localhost:3000/health | jq
```

### Logs

Each service outputs logs to stdout. For more detailed logging:

```bash
# Run with debug logging
LOG_LEVEL=DEBUG uvicorn src.main:app --host 0.0.0.0 --port 8000
```

## WebSocket Events

The frontend receives these real-time events:

| Event | Description |
|-------|-------------|
| `game:state` | Full game state update |
| `turn:start` | New turn started |
| `turn:end` | Turn completed |
| `dice:rolled` | Dice roll with values |
| `player:moved` | Player moved on board |
| `property:purchased` | Property bought |
| `property:passed` | Property declined |
| `agent:thinking` | AI is deciding |
| `agent:decision` | AI made a choice |

## Next Steps

- Check out [`DESIGN.md`](./DESIGN.md) for architecture details
- See [`WEBSOCKET_EVENTS.md`](./services/orchestrator/WEBSOCKET_EVENTS.md) for full event documentation
- Explore the API by visiting http://localhost:8000/docs (Game Engine) or http://localhost:3000/docs (Orchestrator)

---

Happy gaming! Watch those AI agents battle it out for Monopoly supremacy.
