"""Pydantic models for API schemas."""

from src.models.game import GameCreate, GameState, GameStatus, GameSummary, TurnPhase
from src.models.player import Player, PlayerCreate, PlayerPublic
from src.models.property import PropertyInfo, PropertyPurchaseOption, PropertyState
from src.models.actions import (
    Action,
    ActionRequest,
    ActionResult,
    ActionType,
    AvailableAction,
    ValidActions,
)
from src.models.board import BoardSpace, SpaceType
from src.models.cards import Card, CardAction, CardType
from src.models.events import EventType, GameEvent, GameEventCreate

__all__ = [
    # Game
    "GameCreate",
    "GameState",
    "GameStatus",
    "GameSummary",
    "TurnPhase",
    # Player
    "Player",
    "PlayerCreate",
    "PlayerPublic",
    # Property
    "PropertyInfo",
    "PropertyPurchaseOption",
    "PropertyState",
    # Actions
    "Action",
    "ActionRequest",
    "ActionResult",
    "ActionType",
    "AvailableAction",
    "ValidActions",
    # Board
    "BoardSpace",
    "SpaceType",
    # Cards
    "Card",
    "CardAction",
    "CardType",
    # Events
    "EventType",
    "GameEvent",
    "GameEventCreate",
]
