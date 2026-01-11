"""Property definitions for Monopoly.

28 total properties:
- 22 streets (colored properties)
- 4 railroads
- 2 utilities
"""

from typing import TypedDict


class StreetProperty(TypedDict):
    """Type definition for a street property."""

    name: str
    type: str
    color: str
    position: int
    price: int
    rent: list[int]  # [base, 1h, 2h, 3h, 4h, hotel]
    house_cost: int
    mortgage_value: int


class RailroadProperty(TypedDict):
    """Type definition for a railroad property."""

    name: str
    type: str
    position: int
    price: int
    mortgage_value: int


class UtilityProperty(TypedDict):
    """Type definition for a utility property."""

    name: str
    type: str
    position: int
    price: int
    mortgage_value: int


PropertyType = StreetProperty | RailroadProperty | UtilityProperty

PROPERTIES: dict[str, PropertyType] = {
    # ============================================
    # BROWN (2 properties)
    # ============================================
    "mediterranean": {
        "name": "Mediterranean Avenue",
        "type": "street",
        "color": "brown",
        "position": 1,
        "price": 60,
        "rent": [2, 10, 30, 90, 160, 250],
        "house_cost": 50,
        "mortgage_value": 30,
    },
    "baltic": {
        "name": "Baltic Avenue",
        "type": "street",
        "color": "brown",
        "position": 3,
        "price": 60,
        "rent": [4, 20, 60, 180, 320, 450],
        "house_cost": 50,
        "mortgage_value": 30,
    },

    # ============================================
    # LIGHT BLUE (3 properties)
    # ============================================
    "oriental": {
        "name": "Oriental Avenue",
        "type": "street",
        "color": "light_blue",
        "position": 6,
        "price": 100,
        "rent": [6, 30, 90, 270, 400, 550],
        "house_cost": 50,
        "mortgage_value": 50,
    },
    "vermont": {
        "name": "Vermont Avenue",
        "type": "street",
        "color": "light_blue",
        "position": 8,
        "price": 100,
        "rent": [6, 30, 90, 270, 400, 550],
        "house_cost": 50,
        "mortgage_value": 50,
    },
    "connecticut": {
        "name": "Connecticut Avenue",
        "type": "street",
        "color": "light_blue",
        "position": 9,
        "price": 120,
        "rent": [8, 40, 100, 300, 450, 600],
        "house_cost": 50,
        "mortgage_value": 60,
    },

    # ============================================
    # PINK (3 properties)
    # ============================================
    "st_charles": {
        "name": "St. Charles Place",
        "type": "street",
        "color": "pink",
        "position": 11,
        "price": 140,
        "rent": [10, 50, 150, 450, 625, 750],
        "house_cost": 100,
        "mortgage_value": 70,
    },
    "states": {
        "name": "States Avenue",
        "type": "street",
        "color": "pink",
        "position": 13,
        "price": 140,
        "rent": [10, 50, 150, 450, 625, 750],
        "house_cost": 100,
        "mortgage_value": 70,
    },
    "virginia": {
        "name": "Virginia Avenue",
        "type": "street",
        "color": "pink",
        "position": 14,
        "price": 160,
        "rent": [12, 60, 180, 500, 700, 900],
        "house_cost": 100,
        "mortgage_value": 80,
    },

    # ============================================
    # ORANGE (3 properties)
    # ============================================
    "st_james": {
        "name": "St. James Place",
        "type": "street",
        "color": "orange",
        "position": 16,
        "price": 180,
        "rent": [14, 70, 200, 550, 750, 950],
        "house_cost": 100,
        "mortgage_value": 90,
    },
    "tennessee": {
        "name": "Tennessee Avenue",
        "type": "street",
        "color": "orange",
        "position": 18,
        "price": 180,
        "rent": [14, 70, 200, 550, 750, 950],
        "house_cost": 100,
        "mortgage_value": 90,
    },
    "new_york": {
        "name": "New York Avenue",
        "type": "street",
        "color": "orange",
        "position": 19,
        "price": 200,
        "rent": [16, 80, 220, 600, 800, 1000],
        "house_cost": 100,
        "mortgage_value": 100,
    },

    # ============================================
    # RED (3 properties)
    # ============================================
    "kentucky": {
        "name": "Kentucky Avenue",
        "type": "street",
        "color": "red",
        "position": 21,
        "price": 220,
        "rent": [18, 90, 250, 700, 875, 1050],
        "house_cost": 150,
        "mortgage_value": 110,
    },
    "indiana": {
        "name": "Indiana Avenue",
        "type": "street",
        "color": "red",
        "position": 23,
        "price": 220,
        "rent": [18, 90, 250, 700, 875, 1050],
        "house_cost": 150,
        "mortgage_value": 110,
    },
    "illinois": {
        "name": "Illinois Avenue",
        "type": "street",
        "color": "red",
        "position": 24,
        "price": 240,
        "rent": [20, 100, 300, 750, 925, 1100],
        "house_cost": 150,
        "mortgage_value": 120,
    },

    # ============================================
    # YELLOW (3 properties)
    # ============================================
    "atlantic": {
        "name": "Atlantic Avenue",
        "type": "street",
        "color": "yellow",
        "position": 26,
        "price": 260,
        "rent": [22, 110, 330, 800, 975, 1150],
        "house_cost": 150,
        "mortgage_value": 130,
    },
    "ventnor": {
        "name": "Ventnor Avenue",
        "type": "street",
        "color": "yellow",
        "position": 27,
        "price": 260,
        "rent": [22, 110, 330, 800, 975, 1150],
        "house_cost": 150,
        "mortgage_value": 130,
    },
    "marvin_gardens": {
        "name": "Marvin Gardens",
        "type": "street",
        "color": "yellow",
        "position": 29,
        "price": 280,
        "rent": [24, 120, 360, 850, 1025, 1200],
        "house_cost": 150,
        "mortgage_value": 140,
    },

    # ============================================
    # GREEN (3 properties)
    # ============================================
    "pacific": {
        "name": "Pacific Avenue",
        "type": "street",
        "color": "green",
        "position": 31,
        "price": 300,
        "rent": [26, 130, 390, 900, 1100, 1275],
        "house_cost": 200,
        "mortgage_value": 150,
    },
    "north_carolina": {
        "name": "North Carolina Avenue",
        "type": "street",
        "color": "green",
        "position": 32,
        "price": 300,
        "rent": [26, 130, 390, 900, 1100, 1275],
        "house_cost": 200,
        "mortgage_value": 150,
    },
    "pennsylvania": {
        "name": "Pennsylvania Avenue",
        "type": "street",
        "color": "green",
        "position": 34,
        "price": 320,
        "rent": [28, 150, 450, 1000, 1200, 1400],
        "house_cost": 200,
        "mortgage_value": 160,
    },

    # ============================================
    # DARK BLUE (2 properties)
    # ============================================
    "park_place": {
        "name": "Park Place",
        "type": "street",
        "color": "dark_blue",
        "position": 37,
        "price": 350,
        "rent": [35, 175, 500, 1100, 1300, 1500],
        "house_cost": 200,
        "mortgage_value": 175,
    },
    "boardwalk": {
        "name": "Boardwalk",
        "type": "street",
        "color": "dark_blue",
        "position": 39,
        "price": 400,
        "rent": [50, 200, 600, 1400, 1700, 2000],
        "house_cost": 200,
        "mortgage_value": 200,
    },

    # ============================================
    # RAILROADS (4 properties)
    # ============================================
    "reading_rr": {
        "name": "Reading Railroad",
        "type": "railroad",
        "position": 5,
        "price": 200,
        "mortgage_value": 100,
    },
    "pennsylvania_rr": {
        "name": "Pennsylvania Railroad",
        "type": "railroad",
        "position": 15,
        "price": 200,
        "mortgage_value": 100,
    },
    "bo_rr": {
        "name": "B&O Railroad",
        "type": "railroad",
        "position": 25,
        "price": 200,
        "mortgage_value": 100,
    },
    "short_line_rr": {
        "name": "Short Line Railroad",
        "type": "railroad",
        "position": 35,
        "price": 200,
        "mortgage_value": 100,
    },

    # ============================================
    # UTILITIES (2 properties)
    # ============================================
    "electric_company": {
        "name": "Electric Company",
        "type": "utility",
        "position": 12,
        "price": 150,
        "mortgage_value": 75,
    },
    "water_works": {
        "name": "Water Works",
        "type": "utility",
        "position": 28,
        "price": 150,
        "mortgage_value": 75,
    },
}

# Color groups for monopoly checking
COLOR_GROUPS: dict[str, list[str]] = {
    "brown": ["mediterranean", "baltic"],
    "light_blue": ["oriental", "vermont", "connecticut"],
    "pink": ["st_charles", "states", "virginia"],
    "orange": ["st_james", "tennessee", "new_york"],
    "red": ["kentucky", "indiana", "illinois"],
    "yellow": ["atlantic", "ventnor", "marvin_gardens"],
    "green": ["pacific", "north_carolina", "pennsylvania"],
    "dark_blue": ["park_place", "boardwalk"],
}

# Railroad IDs for rent calculation
RAILROAD_IDS: list[str] = ["reading_rr", "pennsylvania_rr", "bo_rr", "short_line_rr"]

# Utility IDs for rent calculation
UTILITY_IDS: list[str] = ["electric_company", "water_works"]

# All property IDs
ALL_PROPERTY_IDS: list[str] = list(PROPERTIES.keys())


def get_property(property_id: str) -> PropertyType | None:
    """Get property by ID."""
    return PROPERTIES.get(property_id)


def get_color_group(color: str) -> list[str]:
    """Get all property IDs in a color group."""
    return COLOR_GROUPS.get(color, [])


def is_street(property_id: str) -> bool:
    """Check if property is a street (colored property)."""
    prop = PROPERTIES.get(property_id)
    return prop is not None and prop["type"] == "street"


def is_railroad(property_id: str) -> bool:
    """Check if property is a railroad."""
    return property_id in RAILROAD_IDS


def is_utility(property_id: str) -> bool:
    """Check if property is a utility."""
    return property_id in UTILITY_IDS
