"""Card models for Chance and Community Chest."""

from enum import Enum

from pydantic import BaseModel


class CardType(str, Enum):
    """Types of cards."""

    CHANCE = "chance"
    COMMUNITY_CHEST = "community_chest"


class CardAction(str, Enum):
    """Types of card actions."""

    MOVE_TO = "move_to"
    MOVE_TO_NEAREST = "move_to_nearest"
    MOVE_RELATIVE = "move_relative"
    COLLECT = "collect"
    PAY = "pay"
    PAY_EACH_PLAYER = "pay_each_player"
    COLLECT_FROM_EACH_PLAYER = "collect_from_each_player"
    PAY_PER_BUILDING = "pay_per_building"
    GET_OUT_OF_JAIL_CARD = "get_out_of_jail_card"
    GO_TO_JAIL = "go_to_jail"


class Card(BaseModel):
    """A Chance or Community Chest card."""

    id: int
    card_type: CardType
    text: str
    action: CardAction
    destination: int | None = None
    amount: int | None = None
    spaces: int | None = None
    property_type: str | None = None
    house_cost: int | None = None
    hotel_cost: int | None = None
