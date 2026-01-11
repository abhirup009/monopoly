# Monopoly Game Engine

A Python FastAPI service that implements core Monopoly game rules.

## Features

- Full Monopoly game logic (dice, movement, property, building, jail, cards, bankruptcy)
- REST API for game management
- PostgreSQL persistence with SQLAlchemy
- Async support with asyncpg

## Development

```bash
# Create virtual environment
python -m venv .venv
source .venv/bin/activate

# Install dependencies
pip install -e ".[dev]"

# Run tests
pytest src/tests/ -v

# Start the server
uvicorn src.main:app --reload
```

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/game` | Create new game |
| GET | `/game/{id}` | Get game state |
| POST | `/game/{id}/start` | Start the game |
| GET | `/game/{id}/actions` | Get valid actions |
| POST | `/game/{id}/action` | Execute an action |
| GET | `/game/{id}/events` | Get event history |
| DELETE | `/game/{id}` | Delete a game |
