# Monopoly AI Agent Service

AI agents that play Monopoly using local LLMs (Ollama + Llama 3).

## Features

- **Local LLM**: Uses Ollama with Llama 3 (no cloud API costs)
- **Multiple Personalities**: Aggressive, Analytical, and Chaotic play styles
- **Single Model Architecture**: One LLM with different prompts and temperatures
- **REST API**: Control games via HTTP endpoints

## Prerequisites

- Python 3.11+
- [Ollama](https://ollama.ai/) installed and running
- Game Engine service running on port 8000

## Setup

### 1. Install Ollama

```bash
# macOS
brew install ollama

# Linux
curl -fsSL https://ollama.ai/install.sh | sh

# Start Ollama
ollama serve
```

### 2. Pull the Llama 3 model

```bash
ollama pull llama3
```

### 3. Install Python dependencies

```bash
cd services/ai-agent
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
```

### 4. Configure environment

```bash
cp .env.example .env
# Edit .env if needed
```

### 5. Run the service

```bash
# Development
python -m src.main

# Or with uvicorn
uvicorn src.main:app --reload --port 8001
```

## API Endpoints

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

### Check Game Status

```bash
curl http://localhost:8001/games/{game_id}
```

### Get Game Result

```bash
curl http://localhost:8001/games/{game_id}/result
```

### Stop a Game

```bash
curl -X POST http://localhost:8001/games/{game_id}/stop
```

### Health Check

```bash
curl http://localhost:8001/health
```

### List Personalities

```bash
curl http://localhost:8001/personalities
```

## Personalities

| Name | Temperature | Style |
|------|-------------|-------|
| aggressive | 0.8 | Bold, risk-taking, always buys |
| analytical | 0.3 | Calculated, conservative, data-driven |
| chaotic | 1.0 | Unpredictable, random, fun |

## Architecture

```
┌─────────────────────────────────────────────────┐
│              AI Agent Service                    │
│                                                  │
│  ┌─────────┐  ┌─────────┐  ┌─────────┐         │
│  │ Agent 1 │  │ Agent 2 │  │ Agent 3 │         │
│  │ (aggr.) │  │ (anal.) │  │ (chaos) │         │
│  └────┬────┘  └────┬────┘  └────┬────┘         │
│       │            │            │               │
│       └────────────┼────────────┘               │
│                    │                            │
│           ┌────────▼────────┐                   │
│           │  Agent Manager  │                   │
│           └────────┬────────┘                   │
│                    │                            │
│    ┌───────────────┼───────────────┐           │
│    │               │               │            │
│    ▼               ▼               ▼            │
│ ┌──────┐     ┌──────────┐    ┌────────┐       │
│ │Prompt│     │  Ollama  │    │ Parser │       │
│ │Builder│    │  Client  │    │        │       │
│ └──────┘     └──────────┘    └────────┘       │
│                    │                            │
└────────────────────┼────────────────────────────┘
                     │
     ┌───────────────┼───────────────┐
     │               │               │
     ▼               ▼               ▼
┌──────────┐  ┌───────────┐  ┌──────────┐
│  Ollama  │  │   Game    │  │  Redis   │
│ (Llama3) │  │  Engine   │  │ (future) │
└──────────┘  └───────────┘  └──────────┘
```

## Running with Docker

```bash
# From project root
docker-compose up -d

# Pull the model (first time only)
docker exec -it monopoly-ollama ollama pull llama3
```

## Hardware Requirements

### Minimum (CPU-only)
- 16GB RAM
- ~30s per LLM response

### Recommended (GPU)
- NVIDIA GPU with 8GB+ VRAM
- ~2-5s per LLM response

## Testing

```bash
pytest src/tests/ -v
```
