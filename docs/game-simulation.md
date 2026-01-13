# Game Simulation Walkthrough

This document shows a real game simulation with 3 AI agents.

## Setup

```bash
# Services running
- PostgreSQL: localhost:5432
- Ollama: localhost:11434 (llama3.1:8b)
- Game Engine: localhost:8000
- AI Agent: localhost:8001
```

## Create Game

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

Response:
```json
{
  "game_id": "f6931f70-6455-46fe-86aa-48fa48798315",
  "status": "running",
  "message": "Game started with 3 agents"
}
```

## Game Progress

### Turn 4
```json
{
  "current_turn": 4,
  "players": [
    {"name": "Baron Von Moneybags", "cash": 1208, "properties": 2},
    {"name": "Professor Pennypincher", "cash": 1300, "properties": 1},
    {"name": "Lady Luck", "cash": 1492, "properties": 0}
  ]
}
```

### Turn 10
```json
{
  "current_turn": 10,
  "players": [
    {"name": "Baron Von Moneybags", "cash": 768, "properties": 4},
    {"name": "Professor Pennypincher", "cash": 960, "properties": 3},
    {"name": "Lady Luck", "cash": 1492, "properties": 0}
  ]
}
```

## Agent Behavior (from logs)

### Baron Von Moneybags (Aggressive)
```
Agent 'Baron Von Moneybags' LLM response: {"action": "buy_property", "property_id": "st_james"}
Agent 'Baron Von Moneybags' chose: buy_property (st_james)
```
- Buys properties immediately
- 4 properties by turn 10
- Lowest cash ($768) due to aggressive buying

### Professor Pennypincher (Analytical)
```
Agent 'Professor Pennypincher' LLM response: {"action": "buy_property", "property_id": "virginia"}
Agent 'Professor Pennypincher' chose: buy_property (virginia)
```
- Selective property purchases
- Maintains higher cash reserves ($960)
- 3 properties by turn 10

### Lady Luck (Chaotic)
```
Agent 'Lady Luck' LLM response: {"action": "sell_property", "property_id": null}
Parse failed, using default action: roll_dice

Agent 'Lady Luck' LLM response: {"action": "pass_property", "property_id": "pennsylvania_rr"}
Agent 'Lady Luck' chose: pass_property (pennsylvania_rr)
```
- Unpredictable decisions
- Passes on valuable properties (railroads)
- Attempts invalid actions (sell_property)
- 0 properties, highest cash ($1,492)

## Turn Flow

1. **Get Valid Actions**
   ```
   GET /game/{id}/actions → [roll_dice]
   ```

2. **LLM Decision**
   ```
   POST /api/generate → {"action": "roll_dice"}
   ```

3. **Execute Action**
   ```
   POST /game/{id}/action → {type: "roll_dice"}
   ```

4. **Handle Result**
   - Landed on unowned property → `awaiting_buy_decision`
   - LLM decides buy/pass
   - Move to `post_roll` → end turn

## Action Parser Fallback

When LLM returns invalid actions, parser falls back to safe defaults:

| Phase | Default Action |
|-------|---------------|
| `awaiting_roll` | `roll_dice` |
| `awaiting_buy_decision` | `pass_property` |
| `post_roll` | `end_turn` |

## Key Observations

1. **Personality differentiation works** - Each agent shows distinct behavior
2. **Fallback parsing is robust** - Invalid LLM outputs don't crash the game
3. **Temperature affects output** - Higher temp (chaotic) produces more varied/invalid responses
4. **Game progresses correctly** - Turn phases, property purchases, cash transfers all work
