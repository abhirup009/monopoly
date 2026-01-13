"""Prompt templates for game state formatting."""

# Board space names for better readability
BOARD_SPACES: dict[int, str] = {
    0: "GO",
    1: "Mediterranean Avenue",
    2: "Community Chest",
    3: "Baltic Avenue",
    4: "Income Tax",
    5: "Reading Railroad",
    6: "Oriental Avenue",
    7: "Chance",
    8: "Vermont Avenue",
    9: "Connecticut Avenue",
    10: "Jail / Just Visiting",
    11: "St. Charles Place",
    12: "Electric Company",
    13: "States Avenue",
    14: "Virginia Avenue",
    15: "Pennsylvania Railroad",
    16: "St. James Place",
    17: "Community Chest",
    18: "Tennessee Avenue",
    19: "New York Avenue",
    20: "Free Parking",
    21: "Kentucky Avenue",
    22: "Chance",
    23: "Indiana Avenue",
    24: "Illinois Avenue",
    25: "B&O Railroad",
    26: "Atlantic Avenue",
    27: "Ventnor Avenue",
    28: "Water Works",
    29: "Marvin Gardens",
    30: "Go To Jail",
    31: "Pacific Avenue",
    32: "North Carolina Avenue",
    33: "Community Chest",
    34: "Pennsylvania Avenue",
    35: "Short Line Railroad",
    36: "Chance",
    37: "Park Place",
    38: "Luxury Tax",
    39: "Boardwalk",
}

# Property IDs to friendly names
PROPERTY_NAMES: dict[str, str] = {
    "mediterranean": "Mediterranean Avenue",
    "baltic": "Baltic Avenue",
    "oriental": "Oriental Avenue",
    "vermont": "Vermont Avenue",
    "connecticut": "Connecticut Avenue",
    "st_charles": "St. Charles Place",
    "states": "States Avenue",
    "virginia": "Virginia Avenue",
    "st_james": "St. James Place",
    "tennessee": "Tennessee Avenue",
    "new_york": "New York Avenue",
    "kentucky": "Kentucky Avenue",
    "indiana": "Indiana Avenue",
    "illinois": "Illinois Avenue",
    "atlantic": "Atlantic Avenue",
    "ventnor": "Ventnor Avenue",
    "marvin_gardens": "Marvin Gardens",
    "pacific": "Pacific Avenue",
    "north_carolina": "North Carolina Avenue",
    "pennsylvania": "Pennsylvania Avenue",
    "park_place": "Park Place",
    "boardwalk": "Boardwalk",
    "reading_rr": "Reading Railroad",
    "pennsylvania_rr": "Pennsylvania Railroad",
    "bo_rr": "B&O Railroad",
    "short_line_rr": "Short Line Railroad",
    "electric_company": "Electric Company",
    "water_works": "Water Works",
}

# Color groups
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


def get_space_name(position: int) -> str:
    """Get the name of a board space.

    Args:
        position: Board position (0-39)

    Returns:
        Space name
    """
    return BOARD_SPACES.get(position, f"Position {position}")


def get_property_name(property_id: str) -> str:
    """Get friendly name for a property.

    Args:
        property_id: Property ID

    Returns:
        Friendly property name
    """
    return PROPERTY_NAMES.get(property_id, property_id.replace("_", " ").title())


def get_color_group(property_id: str) -> str | None:
    """Get the color group for a property.

    Args:
        property_id: Property ID

    Returns:
        Color group name or None
    """
    for color, properties in COLOR_GROUPS.items():
        if property_id in properties:
            return color
    return None
