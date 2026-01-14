# WebSocket Events Documentation

This document describes all WebSocket events emitted by the Orchestrator Service.

## Connection

Connect to the Orchestrator via Socket.IO at `ws://localhost:3000`.

## Client Events (Client → Server)

### `join_game`
Join a game room to receive events.

```json
{
  "game_id": "uuid-string"
}
```

**Response:**
```json
{
  "success": true,
  "game_id": "uuid-string",
  "state": { /* current game state or null */ }
}
```

### `leave_game`
Leave a game room.

```json
{
  "game_id": "uuid-string"
}
```

### `set_speed`
Change game speed.

```json
{
  "game_id": "uuid-string",
  "speed": "fast" | "normal" | "slow"
}
```

### `get_state`
Request current game state.

```json
{
  "game_id": "uuid-string"
}
```

---

## Server Events (Server → Client)

### Game Lifecycle Events

#### `game:started`
Emitted when a game begins.

```json
{
  "game_id": "uuid-string",
  "agents": [
    { "name": "AggressiveBot", "personality": "aggressive" },
    { "name": "AnalyticalBot", "personality": "analytical" }
  ]
}
```

#### `game:state`
Emitted after every action with the full updated game state.

```json
{
  "game_id": "uuid-string",
  "state": {
    "id": "uuid-string",
    "status": "in_progress",
    "current_player_index": 0,
    "turn_number": 5,
    "turn_phase": "post_roll",
    "players": [...],
    "properties": [...]
  }
}
```

#### `game:ended`
Emitted when a game completes (one player remaining).

```json
{
  "game_id": "uuid-string",
  "winner_id": "player-uuid",
  "winner_name": "AggressiveBot",
  "final_state": { /* full game state */ }
}
```

#### `game:stopped`
Emitted when a game is manually stopped.

```json
{
  "game_id": "uuid-string",
  "reason": "cancelled"
}
```

#### `game:error`
Emitted when an error occurs in the game loop.

```json
{
  "game_id": "uuid-string",
  "error": "Error message"
}
```

#### `game:over`
Emitted when game over conditions are met.

```json
{
  "game_id": "uuid-string",
  "winner_id": "player-uuid"
}
```

---

### Turn Events

#### `turn:start`
Emitted when a player's turn begins (pre_roll phase).

```json
{
  "game_id": "uuid-string",
  "player_id": "player-uuid",
  "player_name": "AggressiveBot",
  "turn_number": 5,
  "position": 24,
  "cash": 1200
}
```

#### `turn:action`
Emitted after any action is executed.

```json
{
  "game_id": "uuid-string",
  "player_id": "player-uuid",
  "player_name": "AggressiveBot",
  "action": {
    "type": "roll_dice",
    "property_id": null
  },
  "result": {
    "success": true,
    "message": "Rolled 8 and landed on Park Place",
    "dice_roll": [5, 3],
    "new_position": 37
  }
}
```

#### `turn:end`
Emitted when a player's turn ends (after end_turn action).

```json
{
  "game_id": "uuid-string",
  "player_id": "player-uuid",
  "player_name": "AggressiveBot",
  "turn_number": 5
}
```

#### `turn:timeout`
Emitted when AI decision times out (30s default).

```json
{
  "game_id": "uuid-string",
  "player_id": "player-uuid"
}
```

---

### Agent Events

#### `agent:thinking`
Emitted when AI is processing a decision.

```json
{
  "game_id": "uuid-string",
  "player_id": "player-uuid",
  "player_name": "AggressiveBot",
  "phase": "awaiting_buy_decision",
  "valid_actions": ["buy_property", "pass_property"]
}
```

#### `agent:decision`
Emitted when AI makes a decision (before execution).

```json
{
  "game_id": "uuid-string",
  "player_id": "player-uuid",
  "player_name": "AggressiveBot",
  "action": {
    "type": "buy_property",
    "property_id": "park_place"
  },
  "reasoning": "This property completes my color set for the dark blue monopoly."
}
```

---

### Rich Game Events (for animations)

#### `dice:rolled`
Emitted when dice are rolled.

```json
{
  "game_id": "uuid-string",
  "player_id": "player-uuid",
  "player_name": "AggressiveBot",
  "dice": [5, 3],
  "total": 8,
  "is_doubles": false
}
```

#### `player:moved`
Emitted when a player token moves.

```json
{
  "game_id": "uuid-string",
  "player_id": "player-uuid",
  "player_name": "AggressiveBot",
  "from_position": 29,
  "to_position": 37,
  "dice_total": 8
}
```

#### `property:purchased`
Emitted when a property is bought.

```json
{
  "game_id": "uuid-string",
  "player_id": "player-uuid",
  "player_name": "AggressiveBot",
  "property_id": "park_place",
  "price": 350
}
```

#### `property:passed`
Emitted when a player passes on buying a property.

```json
{
  "game_id": "uuid-string",
  "player_id": "player-uuid",
  "player_name": "AnalyticalBot",
  "property_id": "boardwalk"
}
```

#### `rent:paid`
Emitted when rent is paid.

```json
{
  "game_id": "uuid-string",
  "player_id": "player-uuid",
  "player_name": "ChaoticBot",
  "amount": 200
}
```

#### `card:drawn`
Emitted when a Chance or Community Chest card is drawn.

```json
{
  "game_id": "uuid-string",
  "player_id": "player-uuid",
  "player_name": "AggressiveBot",
  "card_text": "Advance to Go. Collect $200."
}
```

#### `building:built`
Emitted when a house or hotel is built.

```json
{
  "game_id": "uuid-string",
  "player_id": "player-uuid",
  "player_name": "AnalyticalBot",
  "property_id": "boardwalk",
  "building_type": "house" | "hotel"
}
```

#### `jail:action`
Emitted when a jail-related action occurs.

```json
{
  "game_id": "uuid-string",
  "player_id": "player-uuid",
  "player_name": "ChaoticBot",
  "action_type": "pay_jail_fine" | "use_jail_card" | "roll_for_doubles",
  "success": true
}
```

---

## Event Flow Example

A typical turn produces these events in order:

1. `turn:start` - Turn begins
2. `agent:thinking` - AI is deciding
3. `agent:decision` - AI chose roll_dice
4. `dice:rolled` - Dice animation data
5. `player:moved` - Token movement data
6. `turn:action` - General action result
7. `game:state` - Updated full state
8. `agent:thinking` - AI deciding on property
9. `agent:decision` - AI chose buy_property
10. `property:purchased` - Purchase animation
11. `turn:action` - Action result
12. `game:state` - Updated state
13. `agent:thinking` - AI deciding
14. `agent:decision` - AI chose end_turn
15. `turn:action` - Action result
16. `game:state` - Updated state
17. `turn:end` - Turn complete

---

## Speed Settings

| Speed | Delay Between Actions |
|-------|----------------------|
| fast | 0.5 seconds |
| normal | 2.0 seconds |
| slow | 5.0 seconds |
