"""Static game data: board, properties, cards."""

from src.data.board import BOARD_SPACES
from src.data.properties import COLOR_GROUPS, PROPERTIES
from src.data.chance_cards import CHANCE_CARDS
from src.data.community_chest import COMMUNITY_CHEST_CARDS

__all__ = [
    "BOARD_SPACES",
    "PROPERTIES",
    "COLOR_GROUPS",
    "CHANCE_CARDS",
    "COMMUNITY_CHEST_CARDS",
]
