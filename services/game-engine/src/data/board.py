"""Board space definitions for Monopoly.

The board has 40 spaces (positions 0-39).
"""

from typing import TypedDict


class BoardSpace(TypedDict, total=False):
    """Type definition for a board space."""

    position: int
    name: str
    type: str
    property_id: str | None
    amount: int | None  # For tax spaces


BOARD_SPACES: list[BoardSpace] = [
    # Row 1: GO to Jail (positions 0-10)
    {"position": 0, "name": "GO", "type": "go"},
    {"position": 1, "name": "Mediterranean Avenue", "type": "property", "property_id": "mediterranean"},
    {"position": 2, "name": "Community Chest", "type": "community_chest"},
    {"position": 3, "name": "Baltic Avenue", "type": "property", "property_id": "baltic"},
    {"position": 4, "name": "Income Tax", "type": "tax", "amount": 200},
    {"position": 5, "name": "Reading Railroad", "type": "property", "property_id": "reading_rr"},
    {"position": 6, "name": "Oriental Avenue", "type": "property", "property_id": "oriental"},
    {"position": 7, "name": "Chance", "type": "chance"},
    {"position": 8, "name": "Vermont Avenue", "type": "property", "property_id": "vermont"},
    {"position": 9, "name": "Connecticut Avenue", "type": "property", "property_id": "connecticut"},
    {"position": 10, "name": "Jail / Just Visiting", "type": "jail"},

    # Row 2: St. Charles to Free Parking (positions 11-20)
    {"position": 11, "name": "St. Charles Place", "type": "property", "property_id": "st_charles"},
    {"position": 12, "name": "Electric Company", "type": "property", "property_id": "electric_company"},
    {"position": 13, "name": "States Avenue", "type": "property", "property_id": "states"},
    {"position": 14, "name": "Virginia Avenue", "type": "property", "property_id": "virginia"},
    {"position": 15, "name": "Pennsylvania Railroad", "type": "property", "property_id": "pennsylvania_rr"},
    {"position": 16, "name": "St. James Place", "type": "property", "property_id": "st_james"},
    {"position": 17, "name": "Community Chest", "type": "community_chest"},
    {"position": 18, "name": "Tennessee Avenue", "type": "property", "property_id": "tennessee"},
    {"position": 19, "name": "New York Avenue", "type": "property", "property_id": "new_york"},
    {"position": 20, "name": "Free Parking", "type": "free_parking"},

    # Row 3: Kentucky to Go To Jail (positions 21-30)
    {"position": 21, "name": "Kentucky Avenue", "type": "property", "property_id": "kentucky"},
    {"position": 22, "name": "Chance", "type": "chance"},
    {"position": 23, "name": "Indiana Avenue", "type": "property", "property_id": "indiana"},
    {"position": 24, "name": "Illinois Avenue", "type": "property", "property_id": "illinois"},
    {"position": 25, "name": "B&O Railroad", "type": "property", "property_id": "bo_rr"},
    {"position": 26, "name": "Atlantic Avenue", "type": "property", "property_id": "atlantic"},
    {"position": 27, "name": "Ventnor Avenue", "type": "property", "property_id": "ventnor"},
    {"position": 28, "name": "Water Works", "type": "property", "property_id": "water_works"},
    {"position": 29, "name": "Marvin Gardens", "type": "property", "property_id": "marvin_gardens"},
    {"position": 30, "name": "Go To Jail", "type": "go_to_jail"},

    # Row 4: Pacific to Boardwalk (positions 31-39)
    {"position": 31, "name": "Pacific Avenue", "type": "property", "property_id": "pacific"},
    {"position": 32, "name": "North Carolina Avenue", "type": "property", "property_id": "north_carolina"},
    {"position": 33, "name": "Community Chest", "type": "community_chest"},
    {"position": 34, "name": "Pennsylvania Avenue", "type": "property", "property_id": "pennsylvania"},
    {"position": 35, "name": "Short Line Railroad", "type": "property", "property_id": "short_line_rr"},
    {"position": 36, "name": "Chance", "type": "chance"},
    {"position": 37, "name": "Park Place", "type": "property", "property_id": "park_place"},
    {"position": 38, "name": "Luxury Tax", "type": "tax", "amount": 100},
    {"position": 39, "name": "Boardwalk", "type": "property", "property_id": "boardwalk"},
]


def get_space(position: int) -> BoardSpace:
    """Get board space by position."""
    return BOARD_SPACES[position % 40]


def get_space_by_property_id(property_id: str) -> BoardSpace | None:
    """Get board space by property ID."""
    for space in BOARD_SPACES:
        if space.get("property_id") == property_id:
            return space
    return None
