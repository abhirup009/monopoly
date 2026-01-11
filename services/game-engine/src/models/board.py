"""Board space models."""

from enum import Enum

from pydantic import BaseModel


class SpaceType(str, Enum):
    """Types of board spaces."""

    GO = "go"
    PROPERTY = "property"
    COMMUNITY_CHEST = "community_chest"
    CHANCE = "chance"
    TAX = "tax"
    JAIL = "jail"
    FREE_PARKING = "free_parking"
    GO_TO_JAIL = "go_to_jail"


class BoardSpace(BaseModel):
    """A space on the board."""

    position: int
    name: str
    type: SpaceType
    property_id: str | None = None
    amount: int | None = None  # For tax spaces
