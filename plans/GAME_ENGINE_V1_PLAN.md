# Game Engine V1 - Implementation Plan

## Overview

Build the core Monopoly game engine as a Python FastAPI service with PostgreSQL persistence.

**Approach:** Build fresh with clean architecture, extract board/property/card data from [MonopolySimulator](https://github.com/giogix2/MonopolySimulator).

---

## 1. Game Rules Configuration (Confirmed)

| Rule | Decision |
|------|----------|
| **Starting Cash** | $1500 (Standard) |
| **Free Parking** | Just a free space (no pool collection) |
| **Dice** | Classic 2d6 (no speed die) |
| **Passing GO to Jail** | No $200 if sent directly to jail |
| **Unowned Property** | Buy or Pass (no auctions in V1) |
| **Trading** | Deferred to V2 |
| **Mortgage** | Deferred to V2 |

---

## 2. Infrastructure (Docker Compose)

### 2.1 File: `docker-compose.yml`

```yaml
version: '3.8'

services:
  # ===================
  # DATA STORES
  # ===================
  postgres:
    image: postgres:16-alpine
    container_name: monopoly-postgres
    ports:
      - "5432:5432"
    environment:
      POSTGRES_USER: monopoly
      POSTGRES_PASSWORD: monopoly
      POSTGRES_DB: monopoly
    volumes:
      - postgres_data:/var/lib/postgresql/data
      - ./infrastructure/init-db:/docker-entrypoint-initdb.d:ro
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U monopoly"]
      interval: 5s
      timeout: 5s
      retries: 5

  redis:
    image: redis:7-alpine
    container_name: monopoly-redis
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 5s
      timeout: 5s
      retries: 5

  # ===================
  # DEV TOOLS
  # ===================
  adminer:
    image: adminer:latest
    container_name: monopoly-adminer
    ports:
      - "8080:8080"
    depends_on:
      - postgres

volumes:
  postgres_data:
  redis_data:
```

### 2.2 File: `infrastructure/init-db/01-schema.sql`

```sql
-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- ===================
-- GAMES TABLE
-- ===================
CREATE TABLE games (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    status VARCHAR(20) NOT NULL DEFAULT 'waiting',
    current_player_index INTEGER NOT NULL DEFAULT 0,
    turn_number INTEGER NOT NULL DEFAULT 0,
    turn_phase VARCHAR(20) NOT NULL DEFAULT 'pre_roll',
    doubles_count INTEGER NOT NULL DEFAULT 0,
    last_dice_roll INTEGER[] DEFAULT NULL,
    winner_id UUID DEFAULT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Status: waiting, in_progress, completed
-- Turn Phase: pre_roll, awaiting_roll, post_roll, awaiting_buy_decision, awaiting_jail_decision

-- ===================
-- PLAYERS TABLE
-- ===================
CREATE TABLE players (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    game_id UUID NOT NULL REFERENCES games(id) ON DELETE CASCADE,
    name VARCHAR(100) NOT NULL,
    model VARCHAR(50) NOT NULL,
    personality VARCHAR(50) NOT NULL,
    player_order INTEGER NOT NULL,
    position INTEGER NOT NULL DEFAULT 0,
    cash INTEGER NOT NULL DEFAULT 1500,
    in_jail BOOLEAN NOT NULL DEFAULT FALSE,
    jail_turns INTEGER NOT NULL DEFAULT 0,
    get_out_of_jail_cards INTEGER NOT NULL DEFAULT 0,
    is_bankrupt BOOLEAN NOT NULL DEFAULT FALSE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_players_game_id ON players(game_id);

-- ===================
-- PROPERTY STATES TABLE
-- ===================
CREATE TABLE property_states (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    game_id UUID NOT NULL REFERENCES games(id) ON DELETE CASCADE,
    property_id VARCHAR(50) NOT NULL,
    owner_id UUID REFERENCES players(id) ON DELETE SET NULL,
    houses INTEGER NOT NULL DEFAULT 0,
    UNIQUE(game_id, property_id)
);

CREATE INDEX idx_property_states_game_id ON property_states(game_id);
CREATE INDEX idx_property_states_owner_id ON property_states(owner_id);

-- ===================
-- CARD DECKS TABLE
-- ===================
CREATE TABLE card_decks (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    game_id UUID NOT NULL REFERENCES games(id) ON DELETE CASCADE,
    deck_type VARCHAR(20) NOT NULL,  -- 'chance' or 'community_chest'
    card_order INTEGER[] NOT NULL,   -- Shuffled card indices
    current_index INTEGER NOT NULL DEFAULT 0,
    UNIQUE(game_id, deck_type)
);

-- ===================
-- GAME EVENTS TABLE (Action Log)
-- ===================
CREATE TABLE game_events (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    game_id UUID NOT NULL REFERENCES games(id) ON DELETE CASCADE,
    player_id UUID REFERENCES players(id) ON DELETE SET NULL,
    turn_number INTEGER NOT NULL,
    event_type VARCHAR(50) NOT NULL,
    event_data JSONB NOT NULL DEFAULT '{}',
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_game_events_game_id ON game_events(game_id);
CREATE INDEX idx_game_events_created_at ON game_events(created_at);

-- ===================
-- UPDATE TRIGGER
-- ===================
CREATE OR REPLACE FUNCTION update_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER games_updated_at
    BEFORE UPDATE ON games
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at();
```

---

## 3. Project Structure

```
services/game-engine/
├── src/
│   ├── __init__.py
│   ├── main.py                 # FastAPI app entry
│   ├── config.py               # Settings via pydantic-settings
│   ├── database.py             # Async SQLAlchemy setup
│   │
│   ├── models/                 # Pydantic schemas (API)
│   │   ├── __init__.py
│   │   ├── game.py             # GameState, GameCreate, GameStatus
│   │   ├── player.py           # Player, PlayerCreate
│   │   ├── property.py         # Property, PropertyState
│   │   ├── board.py            # BoardSpace, SpaceType
│   │   ├── cards.py            # Card, CardType, CardEffect
│   │   └── actions.py          # Action, ActionType, ActionResult
│   │
│   ├── db/                     # SQLAlchemy ORM
│   │   ├── __init__.py
│   │   ├── models.py           # All ORM models
│   │   └── repositories.py     # CRUD operations
│   │
│   ├── engine/                 # Core game logic (stateless)
│   │   ├── __init__.py
│   │   ├── dice.py             # roll_dice(), check_doubles()
│   │   ├── movement.py         # move_player(), handle_passing_go()
│   │   ├── property_rules.py   # can_buy(), calculate_rent()
│   │   ├── building_rules.py   # can_build_house(), can_build_hotel()
│   │   ├── jail_rules.py       # send_to_jail(), try_leave_jail()
│   │   ├── card_executor.py    # execute_card()
│   │   ├── bankruptcy.py       # check_bankruptcy(), handle_bankruptcy()
│   │   └── game_manager.py     # GameManager class - orchestrates flow
│   │
│   ├── api/                    # FastAPI routers
│   │   ├── __init__.py
│   │   ├── router.py           # Main router aggregator
│   │   ├── games.py            # /game/* endpoints
│   │   └── health.py           # /health endpoint
│   │
│   └── data/                   # Static game data (extracted from MonopolySimulator)
│       ├── __init__.py
│       ├── board.py            # BOARD_SPACES list
│       ├── properties.py       # PROPERTIES dict with prices/rents
│       ├── chance_cards.py     # CHANCE_CARDS list
│       └── community_chest.py  # COMMUNITY_CHEST_CARDS list
│
├── tests/
│   ├── __init__.py
│   ├── conftest.py             # Pytest fixtures, test DB
│   ├── test_dice.py
│   ├── test_movement.py
│   ├── test_property_rules.py
│   ├── test_building_rules.py
│   ├── test_jail_rules.py
│   ├── test_card_executor.py
│   ├── test_game_manager.py
│   └── test_api.py
│
├── pyproject.toml
├── Dockerfile
├── .env.example
└── README.md
```

---

## 4. Dependencies

### File: `services/game-engine/pyproject.toml`

```toml
[project]
name = "monopoly-game-engine"
version = "0.1.0"
description = "Monopoly Game Engine API"
requires-python = ">=3.11"

dependencies = [
    "fastapi>=0.109.0",
    "uvicorn[standard]>=0.27.0",
    "pydantic>=2.5.0",
    "pydantic-settings>=2.1.0",
    "sqlalchemy[asyncio]>=2.0.25",
    "asyncpg>=0.29.0",
    "python-dotenv>=1.0.0",
]

[project.optional-dependencies]
dev = [
    "pytest>=7.4.0",
    "pytest-asyncio>=0.23.0",
    "pytest-cov>=4.1.0",
    "httpx>=0.26.0",
    "ruff>=0.1.0",
    "mypy>=1.8.0",
]

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[tool.pytest.ini_options]
asyncio_mode = "auto"
testpaths = ["tests"]

[tool.ruff]
line-length = 100
target-version = "py311"

[tool.mypy]
python_version = "3.11"
strict = true
```

---

## 5. API Endpoints

### 5.1 Game Management

| Method | Endpoint | Description | Request Body | Response |
|--------|----------|-------------|--------------|----------|
| `POST` | `/game` | Create new game | `GameCreate` | `GameState` |
| `GET` | `/game/{id}` | Get game state | - | `GameState` |
| `POST` | `/game/{id}/start` | Start the game | - | `GameState` |
| `DELETE` | `/game/{id}` | Delete game | - | `{message}` |

### 5.2 Game Actions

| Method | Endpoint | Description | Request Body | Response |
|--------|----------|-------------|--------------|----------|
| `GET` | `/game/{id}/actions` | Get valid actions | - | `ValidActions` |
| `POST` | `/game/{id}/action` | Execute action | `ActionRequest` | `ActionResult` |
| `GET` | `/game/{id}/events` | Get event log | `?limit=50` | `list[GameEvent]` |

### 5.3 Health

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/health` | Health check |
| `GET` | `/health/ready` | Readiness (DB connected) |

---

## 6. Core Data Structures

### 6.1 Board Spaces (40 total)

```python
# Extracted from MonopolySimulator board.py
BOARD_SPACES = [
    {"position": 0, "name": "GO", "type": "go"},
    {"position": 1, "name": "Mediterranean Avenue", "type": "property", "property_id": "mediterranean"},
    {"position": 2, "name": "Community Chest", "type": "community_chest"},
    {"position": 3, "name": "Baltic Avenue", "type": "property", "property_id": "baltic"},
    {"position": 4, "name": "Income Tax", "type": "tax", "amount": 200},
    {"position": 5, "name": "Reading Railroad", "type": "property", "property_id": "reading_rr"},
    # ... continues for all 40 spaces
    {"position": 30, "name": "Go To Jail", "type": "go_to_jail"},
    # ...
    {"position": 39, "name": "Boardwalk", "type": "property", "property_id": "boardwalk"},
]
```

### 6.2 Properties (28 total: 22 streets + 4 railroads + 2 utilities)

```python
PROPERTIES = {
    "mediterranean": {
        "name": "Mediterranean Avenue",
        "type": "street",
        "color": "brown",
        "position": 1,
        "price": 60,
        "rent": [2, 10, 30, 90, 160, 250],  # base, 1h, 2h, 3h, 4h, hotel
        "house_cost": 50,
        "mortgage_value": 30,
    },
    "baltic": {
        "name": "Baltic Avenue",
        "type": "street",
        "color": "brown",
        "position": 3,
        "price": 60,
        "rent": [4, 20, 60, 180, 320, 450],
        "house_cost": 50,
        "mortgage_value": 30,
    },
    # ... all 22 streets
    "reading_rr": {
        "name": "Reading Railroad",
        "type": "railroad",
        "position": 5,
        "price": 200,
        "mortgage_value": 100,
    },
    # ... all 4 railroads
    "electric_company": {
        "name": "Electric Company",
        "type": "utility",
        "position": 12,
        "price": 150,
        "mortgage_value": 75,
    },
    # ... both utilities
}

COLOR_GROUPS = {
    "brown": ["mediterranean", "baltic"],
    "light_blue": ["oriental", "vermont", "connecticut"],
    "pink": ["st_charles", "states", "virginia"],
    "orange": ["st_james", "tennessee", "new_york"],
    "red": ["kentucky", "indiana", "illinois"],
    "yellow": ["atlantic", "ventnor", "marvin_gardens"],
    "green": ["pacific", "north_carolina", "pennsylvania"],
    "dark_blue": ["park_place", "boardwalk"],
}
```

### 6.3 Chance Cards (16)

```python
CHANCE_CARDS = [
    {"id": 1, "text": "Advance to Boardwalk", "action": "move_to", "destination": 39},
    {"id": 2, "text": "Advance to Go (Collect $200)", "action": "move_to", "destination": 0},
    {"id": 3, "text": "Advance to Illinois Avenue", "action": "move_to", "destination": 24},
    {"id": 4, "text": "Advance to St. Charles Place", "action": "move_to", "destination": 11},
    {"id": 5, "text": "Advance to nearest Railroad", "action": "move_to_nearest", "type": "railroad"},
    {"id": 6, "text": "Advance to nearest Railroad", "action": "move_to_nearest", "type": "railroad"},
    {"id": 7, "text": "Advance to nearest Utility", "action": "move_to_nearest", "type": "utility"},
    {"id": 8, "text": "Bank pays you dividend of $50", "action": "collect", "amount": 50},
    {"id": 9, "text": "Get Out of Jail Free", "action": "get_out_of_jail_card"},
    {"id": 10, "text": "Go Back 3 Spaces", "action": "move_relative", "spaces": -3},
    {"id": 11, "text": "Go to Jail", "action": "go_to_jail"},
    {"id": 12, "text": "Make general repairs: $25/house, $100/hotel", "action": "pay_per_building", "house": 25, "hotel": 100},
    {"id": 13, "text": "Speeding fine $15", "action": "pay", "amount": 15},
    {"id": 14, "text": "Advance to Reading Railroad", "action": "move_to", "destination": 5},
    {"id": 15, "text": "You have been elected Chairman: Pay $50 to each player", "action": "pay_each_player", "amount": 50},
    {"id": 16, "text": "Your building loan matures: Collect $150", "action": "collect", "amount": 150},
]
```

### 6.4 Community Chest Cards (16)

```python
COMMUNITY_CHEST_CARDS = [
    {"id": 1, "text": "Advance to Go (Collect $200)", "action": "move_to", "destination": 0},
    {"id": 2, "text": "Bank error in your favor: Collect $200", "action": "collect", "amount": 200},
    {"id": 3, "text": "Doctor's fee: Pay $50", "action": "pay", "amount": 50},
    {"id": 4, "text": "From sale of stock you get $50", "action": "collect", "amount": 50},
    {"id": 5, "text": "Get Out of Jail Free", "action": "get_out_of_jail_card"},
    {"id": 6, "text": "Go to Jail", "action": "go_to_jail"},
    {"id": 7, "text": "Holiday fund matures: Collect $100", "action": "collect", "amount": 100},
    {"id": 8, "text": "Income tax refund: Collect $20", "action": "collect", "amount": 20},
    {"id": 9, "text": "It's your birthday: Collect $10 from each player", "action": "collect_from_each_player", "amount": 10},
    {"id": 10, "text": "Life insurance matures: Collect $100", "action": "collect", "amount": 100},
    {"id": 11, "text": "Pay hospital fees of $100", "action": "pay", "amount": 100},
    {"id": 12, "text": "Pay school fees of $50", "action": "pay", "amount": 50},
    {"id": 13, "text": "Receive $25 consultancy fee", "action": "collect", "amount": 25},
    {"id": 14, "text": "Street repairs: $40/house, $115/hotel", "action": "pay_per_building", "house": 40, "hotel": 115},
    {"id": 15, "text": "You have won second prize in a beauty contest: Collect $10", "action": "collect", "amount": 10},
    {"id": 16, "text": "You inherit $100", "action": "collect", "amount": 100},
]
```

---

## 7. Game Logic Details

### 7.1 Turn Flow

```
┌─────────────────────────────────────────────────────────────┐
│ TURN START                                                   │
│   - Set turn_phase = "awaiting_roll"                        │
│   - If in_jail: turn_phase = "awaiting_jail_decision"       │
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│ JAIL DECISION (if applicable)                               │
│   Valid actions:                                             │
│   - PAY_JAIL_FINE ($50)                                     │
│   - USE_JAIL_CARD (if has one)                              │
│   - ROLL_FOR_DOUBLES (attempt to roll doubles)              │
│   After 3 failed attempts: forced to pay $50                │
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│ ROLL DICE                                                    │
│   - Roll 2d6                                                 │
│   - Track doubles (3 in a row = jail)                       │
│   - Move player by total                                     │
│   - Handle passing GO (+$200)                               │
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│ LAND ACTION (based on space type)                           │
│                                                              │
│   property (unowned):                                        │
│     turn_phase = "awaiting_buy_decision"                    │
│     Valid: BUY_PROPERTY, PASS_PROPERTY                      │
│                                                              │
│   property (owned by other):                                 │
│     Auto: pay rent to owner                                  │
│                                                              │
│   property (owned by self):                                  │
│     No action                                                │
│                                                              │
│   chance / community_chest:                                  │
│     Draw card, execute effect                                │
│                                                              │
│   tax:                                                       │
│     Auto: pay tax amount                                     │
│                                                              │
│   go_to_jail:                                                │
│     Move to jail, end turn immediately                       │
│                                                              │
│   go / free_parking / jail_visiting:                         │
│     No action                                                │
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│ POST-ROLL PHASE                                              │
│   turn_phase = "post_roll"                                  │
│   Valid actions:                                             │
│   - BUILD_HOUSE (if owns full color set, even building)     │
│   - BUILD_HOTEL (if has 4 houses on all in set)             │
│   - END_TURN                                                 │
│                                                              │
│   If rolled doubles and not in jail: roll again             │
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼
                    Next Player's Turn
```

### 7.2 Rent Calculation

```python
def calculate_rent(property_id: str, game_state: GameState, dice_roll: int | None = None) -> int:
    prop = PROPERTIES[property_id]
    state = get_property_state(property_id, game_state)

    if state.owner_id is None:
        return 0

    if prop["type"] == "street":
        # Check if owner has full color set
        color = prop["color"]
        owns_full_set = all(
            get_property_state(p, game_state).owner_id == state.owner_id
            for p in COLOR_GROUPS[color]
        )

        if state.houses == 0:
            base_rent = prop["rent"][0]
            return base_rent * 2 if owns_full_set else base_rent
        else:
            return prop["rent"][state.houses]  # 1-5 for houses/hotel

    elif prop["type"] == "railroad":
        # Count railroads owned by same owner
        rr_count = sum(
            1 for p in ["reading_rr", "pennsylvania_rr", "bo_rr", "short_line_rr"]
            if get_property_state(p, game_state).owner_id == state.owner_id
        )
        return 25 * (2 ** (rr_count - 1))  # 25, 50, 100, 200

    elif prop["type"] == "utility":
        # Count utilities owned
        util_count = sum(
            1 for p in ["electric_company", "water_works"]
            if get_property_state(p, game_state).owner_id == state.owner_id
        )
        multiplier = 4 if util_count == 1 else 10
        return multiplier * dice_roll
```

### 7.3 Building Rules

```python
def can_build_house(property_id: str, player_id: str, game_state: GameState) -> tuple[bool, str]:
    prop = PROPERTIES[property_id]
    state = get_property_state(property_id, game_state)
    player = get_player(player_id, game_state)

    # Must own property
    if state.owner_id != player_id:
        return False, "You don't own this property"

    # Must be a street
    if prop["type"] != "street":
        return False, "Can only build on streets"

    # Must own full color set
    color = prop["color"]
    if not all(
        get_property_state(p, game_state).owner_id == player_id
        for p in COLOR_GROUPS[color]
    ):
        return False, "Must own all properties in color group"

    # Max 4 houses before hotel
    if state.houses >= 4:
        return False, "Already has 4 houses, build hotel instead"

    # Even building rule: can't be more than 1 house ahead of others in set
    other_houses = [
        get_property_state(p, game_state).houses
        for p in COLOR_GROUPS[color]
        if p != property_id
    ]
    if state.houses > min(other_houses):
        return False, "Must build evenly across color set"

    # Must afford
    if player.cash < prop["house_cost"]:
        return False, f"Insufficient funds (need ${prop['house_cost']})"

    return True, "OK"
```

---

## 8. Implementation Steps

### Step 1: Infrastructure Setup
- [ ] Create `docker-compose.yml` at project root
- [ ] Create `infrastructure/init-db/01-schema.sql`
- [ ] Verify: `docker compose up -d` and connect to DB

### Step 2: Project Scaffold
- [ ] Create directory structure under `services/game-engine/`
- [ ] Create `pyproject.toml`
- [ ] Create `Dockerfile`
- [ ] Create `src/config.py` (pydantic-settings)
- [ ] Create `src/database.py` (async SQLAlchemy)
- [ ] Create `src/main.py` (FastAPI app)
- [ ] Verify: `docker compose up game-engine` starts

### Step 3: Static Game Data
- [ ] Create `src/data/board.py` - 40 board spaces
- [ ] Create `src/data/properties.py` - 28 properties with prices/rents
- [ ] Create `src/data/chance_cards.py` - 16 Chance cards
- [ ] Create `src/data/community_chest.py` - 16 Community Chest cards

### Step 4: Pydantic Models
- [ ] Create `src/models/game.py` - GameState, GameCreate, GameStatus, TurnPhase
- [ ] Create `src/models/player.py` - Player, PlayerCreate
- [ ] Create `src/models/property.py` - Property, PropertyState
- [ ] Create `src/models/board.py` - BoardSpace, SpaceType
- [ ] Create `src/models/cards.py` - Card, CardEffect
- [ ] Create `src/models/actions.py` - Action, ActionType, ActionResult, ValidActions

### Step 5: Database Layer
- [ ] Create `src/db/models.py` - SQLAlchemy ORM models
- [ ] Create `src/db/repositories.py` - CRUD operations

### Step 6: Game Engine Logic
- [ ] Create `src/engine/dice.py` - roll_dice(), is_doubles()
- [ ] Create `src/engine/movement.py` - move_player(), passes_go()
- [ ] Create `src/engine/property_rules.py` - can_buy(), calculate_rent()
- [ ] Create `src/engine/building_rules.py` - can_build_house(), can_build_hotel()
- [ ] Create `src/engine/jail_rules.py` - send_to_jail(), attempt_jail_escape()
- [ ] Create `src/engine/card_executor.py` - draw_card(), execute_card()
- [ ] Create `src/engine/bankruptcy.py` - is_bankrupt(), handle_bankruptcy()
- [ ] Create `src/engine/game_manager.py` - GameManager class

### Step 7: API Endpoints
- [ ] Create `src/api/health.py` - /health, /health/ready
- [ ] Create `src/api/games.py` - All game endpoints
- [ ] Create `src/api/router.py` - Aggregate routers
- [ ] Wire up in main.py

### Step 8: Testing
- [ ] Create `tests/conftest.py` - Test fixtures
- [ ] Create unit tests for each engine module
- [ ] Create API integration tests
- [ ] Verify all tests pass

---

## 9. Files to Create (Priority Order)

| # | File | Description |
|---|------|-------------|
| 1 | `docker-compose.yml` | PostgreSQL + Redis + Adminer |
| 2 | `infrastructure/init-db/01-schema.sql` | Database schema |
| 3 | `services/game-engine/pyproject.toml` | Python dependencies |
| 4 | `services/game-engine/Dockerfile` | Container build |
| 5 | `services/game-engine/.env.example` | Environment template |
| 6 | `services/game-engine/src/__init__.py` | Package init |
| 7 | `services/game-engine/src/config.py` | Settings |
| 8 | `services/game-engine/src/database.py` | DB connection |
| 9 | `services/game-engine/src/main.py` | FastAPI entry |
| 10 | `services/game-engine/src/data/*.py` | Static game data (4 files) |
| 11 | `services/game-engine/src/models/*.py` | Pydantic schemas (6 files) |
| 12 | `services/game-engine/src/db/models.py` | ORM models |
| 13 | `services/game-engine/src/db/repositories.py` | CRUD |
| 14 | `services/game-engine/src/engine/*.py` | Game logic (8 files) |
| 15 | `services/game-engine/src/api/*.py` | API routes (3 files) |
| 16 | `services/game-engine/tests/*.py` | Tests |
| 17 | `services/game-engine/README.md` | Documentation |

---

## 10. Success Criteria

1. **Infrastructure**: `docker compose up` starts PostgreSQL, Redis, Adminer
2. **API Running**: Game engine accessible at `http://localhost:8000`
3. **Create Game**: `POST /game` returns new game with 3 players
4. **Start Game**: `POST /game/{id}/start` transitions to `in_progress`
5. **Valid Actions**: `GET /game/{id}/actions` returns correct actions per phase
6. **Execute Actions**: `POST /game/{id}/action` processes moves correctly
7. **Full Game**: Can play through a complete game until one player wins
8. **Tests Pass**: All unit and integration tests green
