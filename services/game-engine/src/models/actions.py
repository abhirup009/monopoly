"""Action models for game moves."""

from enum import Enum
from uuid import UUID

from pydantic import BaseModel


class ActionType(str, Enum):
    """Types of actions a player can take."""

    ROLL_DICE = "roll_dice"
    BUY_PROPERTY = "buy_property"
    PASS_PROPERTY = "pass_property"
    BUILD_HOUSE = "build_house"
    BUILD_HOTEL = "build_hotel"
    PAY_JAIL_FINE = "pay_jail_fine"
    USE_JAIL_CARD = "use_jail_card"
    ROLL_FOR_DOUBLES = "roll_for_doubles"
    END_TURN = "end_turn"


class Action(BaseModel):
    """An action to be executed."""

    type: ActionType
    property_id: str | None = None  # For buy/build actions

    class Config:
        json_schema_extra = {
            "example": {
                "type": "buy_property",
                "property_id": "boardwalk",
            }
        }


class ActionRequest(BaseModel):
    """Request to execute an action."""

    player_id: UUID
    action: Action


class AvailableAction(BaseModel):
    """An action available to the current player."""

    type: ActionType
    property_id: str | None = None
    cost: int | None = None
    description: str


class ValidActions(BaseModel):
    """Response containing valid actions for current player."""

    game_id: UUID
    player_id: UUID
    player_name: str
    turn_phase: str
    actions: list[AvailableAction]


class ActionResult(BaseModel):
    """Result of executing an action."""

    success: bool
    message: str
    action_type: ActionType
    dice_roll: list[int] | None = None
    new_position: int | None = None
    amount_paid: int | None = None
    amount_received: int | None = None
    property_id: str | None = None
    card_drawn: str | None = None
    next_phase: str | None = None
    game_over: bool = False
    winner_id: UUID | None = None
