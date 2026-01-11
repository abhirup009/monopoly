"""Game state models."""

from datetime import datetime
from enum import Enum
from uuid import UUID

from pydantic import BaseModel, Field


class GameStatus(str, Enum):
    """Game status values."""

    WAITING = "waiting"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"


class TurnPhase(str, Enum):
    """Turn phase values."""

    PRE_ROLL = "pre_roll"
    AWAITING_ROLL = "awaiting_roll"
    AWAITING_BUY_DECISION = "awaiting_buy_decision"
    AWAITING_JAIL_DECISION = "awaiting_jail_decision"
    POST_ROLL = "post_roll"


class GameCreate(BaseModel):
    """Request model for creating a new game."""

    players: list["PlayerCreate"]

    class Config:
        json_schema_extra = {
            "example": {
                "players": [
                    {"name": "Baron Von Moneybags", "model": "gpt-4", "personality": "aggressive"},
                    {"name": "Professor Pennypincher", "model": "claude-3", "personality": "analytical"},
                    {"name": "Lady Luck", "model": "llama-3", "personality": "chaotic"},
                ]
            }
        }


class GameState(BaseModel):
    """Full game state response model."""

    id: UUID
    status: GameStatus
    current_player_index: int
    turn_number: int
    turn_phase: TurnPhase
    doubles_count: int = 0
    last_dice_roll: list[int] | None = None
    players: list["Player"]
    properties: list["PropertyState"]
    winner_id: UUID | None = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class GameSummary(BaseModel):
    """Lightweight game summary."""

    id: UUID
    status: GameStatus
    turn_number: int
    current_player_name: str
    player_count: int
    created_at: datetime


# Import at end to avoid circular imports
from src.models.player import Player, PlayerCreate
from src.models.property import PropertyState

GameCreate.model_rebuild()
GameState.model_rebuild()
