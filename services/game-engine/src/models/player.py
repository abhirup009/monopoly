"""Player models."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field


class PlayerCreate(BaseModel):
    """Request model for creating a player."""

    name: str = Field(..., min_length=1, max_length=100)
    model: str = Field(..., min_length=1, max_length=50)
    personality: str = Field(..., min_length=1, max_length=50)

    class Config:
        json_schema_extra = {
            "example": {
                "name": "Baron Von Moneybags",
                "model": "gpt-4",
                "personality": "aggressive",
            }
        }


class Player(BaseModel):
    """Player state model."""

    id: UUID
    game_id: UUID
    name: str
    model: str
    personality: str
    player_order: int
    position: int = 0
    cash: int = 1500
    in_jail: bool = False
    jail_turns: int = 0
    get_out_of_jail_cards: int = 0
    is_bankrupt: bool = False
    created_at: datetime

    class Config:
        from_attributes = True


class PlayerPublic(BaseModel):
    """Public player info (for opponents)."""

    id: UUID
    name: str
    model: str
    personality: str
    position: int
    cash: int
    in_jail: bool
    is_bankrupt: bool
    property_count: int = 0

    class Config:
        from_attributes = True
