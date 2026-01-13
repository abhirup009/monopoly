# Monopoly Arena

AI agents playing Monopoly using local LLMs.

## Architecture

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│   AI Agent      │────▶│  Game Engine    │────▶│   PostgreSQL    │
│   Service       │     │   Service       │     │                 │
└────────┬────────┘     └─────────────────┘     └─────────────────┘
         │
         ▼
┌─────────────────┐
│     Ollama      │
│  (Llama 3.1)    │
└─────────────────┘
```

| Service | Port | Description |
|---------|------|-------------|
| Game Engine | 8000 | Core game logic, state management, REST API |
| AI Agent | 8001 | LLM-powered agents, game orchestration |
| PostgreSQL | 5432 | Game state persistence |
| Ollama | 11434 | Local LLM inference |

## Quick Start

### Prerequisites

- Docker & Docker Compose
- [Ollama](https://ollama.ai) with `llama3.1:8b` model

```bash
# Pull the model
ollama pull llama3.1:8b
```

### Run

```bash
# Start infrastructure
docker-compose up -d postgres redis

# Start Game Engine
cd services/game-engine
python -m pip install -e ".[dev]"
python -m uvicorn src.main:app --port 8000

# Start AI Agent (new terminal)
cd services/ai-agent
python -m pip install -e ".[dev]"
GAME_ENGINE_URL=http://localhost:8000 \
OLLAMA_HOST=http://localhost:11434 \
OLLAMA_MODEL=llama3.1:8b \
python -m uvicorn src.main:app --port 8001
```

### Create a Game

```bash
curl -X POST http://localhost:8001/games \
  -H "Content-Type: application/json" \
  -d '{
    "agents": [
      {"name": "Baron Von Moneybags", "personality": "aggressive"},
      {"name": "Professor Pennypincher", "personality": "analytical"},
      {"name": "Lady Luck", "personality": "chaotic"}
    ]
  }'
```

### Check Status

```bash
curl http://localhost:8001/games/{game_id}
```

## Agent Personalities

| Personality | Temperature | Behavior |
|-------------|-------------|----------|
| Aggressive | 0.8 | Always buys, takes risks |
| Analytical | 0.3 | ROI-focused, maintains reserves |
| Chaotic | 1.0 | Unpredictable decisions |

## Development

### Run Tests

```bash
# Game Engine
cd services/game-engine
pytest tests/ -v

# AI Agent
cd services/ai-agent
pytest src/tests/ -v
```

### Project Structure

```
monopoly/
├── services/
│   ├── game-engine/     # Core Monopoly rules
│   │   ├── src/
│   │   │   ├── api/     # REST endpoints
│   │   │   ├── engine/  # Game logic
│   │   │   ├── db/      # Database models
│   │   │   └── data/    # Board, cards, properties
│   │   └── tests/
│   │
│   └── ai-agent/        # LLM agent service
│       └── src/
│           ├── api/     # REST endpoints
│           ├── agent/   # Agent orchestration
│           ├── client/  # Game Engine client
│           ├── llm/     # Ollama wrapper
│           ├── parser/  # Action parsing
│           └── prompts/ # Personality prompts
│
├── infrastructure/      # DB init scripts
└── docker-compose.yml
```

## API Reference

### AI Agent Service

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/games` | Create and start AI game |
| GET | `/games/{id}` | Get game status |
| GET | `/games/{id}/result` | Get completed game result |
| POST | `/games/{id}/stop` | Stop running game |
| GET | `/health` | Service health |
| GET | `/personalities` | List personalities |

### Game Engine

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/game` | Create game |
| GET | `/game/{id}` | Get game state |
| POST | `/game/{id}/start` | Start game |
| GET | `/game/{id}/actions` | Get valid actions |
| POST | `/game/{id}/action` | Execute action |
| GET | `/health` | Service health |
