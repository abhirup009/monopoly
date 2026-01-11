"""Game event models for action logging."""

from datetime import datetime
from enum import Enum
from uuid import UUID

from pydantic import BaseModel


class EventType(str, Enum):
    """Types of game events."""

    GAME_CREATED = "game_created"
    GAME_STARTED = "game_started"
    GAME_ENDED = "game_ended"
    TURN_STARTED = "turn_started"
    TURN_ENDED = "turn_ended"
    DICE_ROLLED = "dice_rolled"
    PLAYER_MOVED = "player_moved"
    PASSED_GO = "passed_go"
    PROPERTY_PURCHASED = "property_purchased"
    PROPERTY_PASSED = "property_passed"
    RENT_PAID = "rent_paid"
    TAX_PAID = "tax_paid"
    HOUSE_BUILT = "house_built"
    HOTEL_BUILT = "hotel_built"
    CARD_DRAWN = "card_drawn"
    SENT_TO_JAIL = "sent_to_jail"
    LEFT_JAIL = "left_jail"
    JAIL_FINE_PAID = "jail_fine_paid"
    JAIL_CARD_USED = "jail_card_used"
    PLAYER_BANKRUPT = "player_bankrupt"
    PAYMENT_MADE = "payment_made"
    PAYMENT_RECEIVED = "payment_received"


class GameEvent(BaseModel):
    """A game event for the action log."""

    id: UUID
    game_id: UUID
    player_id: UUID | None = None
    turn_number: int
    event_type: EventType
    event_data: dict
    created_at: datetime

    class Config:
        from_attributes = True


class GameEventCreate(BaseModel):
    """Data for creating a game event."""

    player_id: UUID | None = None
    turn_number: int
    event_type: EventType
    event_data: dict = {}
