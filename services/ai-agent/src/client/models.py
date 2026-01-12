"""Pydantic models for Game Engine API responses."""

from enum import Enum
from uuid import UUID

from pydantic import BaseModel


class GameStatus(str, Enum):
    """Game status values."""

    WAITING = "waiting"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"


class TurnPhase(str, Enum):
    """Turn phase values."""

    PRE_ROLL = "pre_roll"
    POST_ROLL = "post_roll"


class ActionType(str, Enum):
    """Valid action types."""

    ROLL_DICE = "roll_dice"
    BUY_PROPERTY = "buy_property"
    PASS_PROPERTY = "pass_property"
    BUILD_HOUSE = "build_house"
    BUILD_HOTEL = "build_hotel"
    PAY_JAIL_FINE = "pay_jail_fine"
    USE_JAIL_CARD = "use_jail_card"
    ROLL_FOR_DOUBLES = "roll_for_doubles"
    END_TURN = "end_turn"


class Player(BaseModel):
    """Player model from game state."""

    id: UUID
    name: str
    model: str
    personality: str
    position: int
    cash: int
    in_jail: bool
    jail_turns: int
    get_out_of_jail_cards: int
    is_bankrupt: bool
    player_order: int


class PropertyState(BaseModel):
    """Property state from game state."""

    property_id: str
    owner_id: UUID | None = None
    houses: int = 0


class GameState(BaseModel):
    """Full game state."""

    id: UUID
    status: GameStatus
    current_player_index: int
    turn_number: int
    turn_phase: TurnPhase
    free_parking_pool: int
    winner_id: UUID | None = None
    players: list[Player]
    properties: list[PropertyState]


class ValidAction(BaseModel):
    """A single valid action."""

    type: ActionType
    property_id: str | None = None
    cost: int | None = None


class ValidActions(BaseModel):
    """Valid actions response."""

    player_id: UUID
    turn_phase: TurnPhase
    actions: list[ValidAction]


class Action(BaseModel):
    """Action to execute."""

    type: ActionType
    property_id: str | None = None


class ActionResult(BaseModel):
    """Result of executing an action."""

    success: bool
    message: str
    game_over: bool = False
    next_phase: str | None = None
    state_changes: dict | None = None


class CreateGameRequest(BaseModel):
    """Request to create a new game."""

    players: list[dict]


class CreateGameResponse(BaseModel):
    """Response from creating a game."""

    id: UUID
    status: GameStatus
    players: list[Player]
    message: str
