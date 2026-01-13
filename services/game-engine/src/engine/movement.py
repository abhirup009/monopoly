"""Player movement logic."""

from dataclasses import dataclass

from src.data.board import get_space

BOARD_SIZE = 40
GO_POSITION = 0
JAIL_POSITION = 10
GO_TO_JAIL_POSITION = 30
GO_SALARY = 200


@dataclass
class MovementResult:
    """Result of moving a player."""

    new_position: int
    passed_go: bool
    landed_on_go_to_jail: bool
    spaces_moved: int


def move_player(current_position: int, spaces: int) -> MovementResult:
    """Move a player by a number of spaces.

    Args:
        current_position: Current board position (0-39)
        spaces: Number of spaces to move (can be negative)

    Returns:
        MovementResult with new position and flags
    """
    # Calculate new position
    new_position = (current_position + spaces) % BOARD_SIZE

    # Check if passed GO (only for forward movement)
    passed_go = False
    if spaces > 0 and new_position < current_position:
        passed_go = True

    # Check if landed on "Go To Jail"
    landed_on_go_to_jail = new_position == GO_TO_JAIL_POSITION

    return MovementResult(
        new_position=new_position,
        passed_go=passed_go,
        landed_on_go_to_jail=landed_on_go_to_jail,
        spaces_moved=spaces,
    )


def move_to_position(current_position: int, destination: int) -> MovementResult:
    """Move a player directly to a specific position.

    Args:
        current_position: Current board position (0-39)
        destination: Target board position (0-39)

    Returns:
        MovementResult with new position and flags
    """
    # Check if we pass GO (moving forward past position 0)
    passed_go = False
    if destination < current_position and destination != JAIL_POSITION:
        # Moving forward and wrapping around (except when going to jail)
        passed_go = True

    # Calculate spaces moved (for display purposes)
    if destination >= current_position:
        spaces_moved = destination - current_position
    else:
        spaces_moved = (BOARD_SIZE - current_position) + destination

    return MovementResult(
        new_position=destination,
        passed_go=passed_go,
        landed_on_go_to_jail=destination == GO_TO_JAIL_POSITION,
        spaces_moved=spaces_moved,
    )


def send_to_jail() -> int:
    """Get the jail position (for when a player is sent to jail)."""
    return JAIL_POSITION


def find_nearest_property_type(current_position: int, property_type: str) -> int:
    """Find the nearest property of a given type (railroad or utility).

    Args:
        current_position: Current board position
        property_type: "railroad" or "utility"

    Returns:
        Position of the nearest property of that type
    """
    # Property positions by type
    if property_type == "railroad":
        positions = [5, 15, 25, 35]  # Reading, Pennsylvania, B&O, Short Line
    elif property_type == "utility":
        positions = [12, 28]  # Electric Company, Water Works
    else:
        raise ValueError(f"Unknown property type: {property_type}")

    # Find the next one clockwise
    for pos in positions:
        if pos > current_position:
            return pos

    # Wrap around to the first one
    return positions[0]


def get_space_type(position: int) -> str:
    """Get the type of space at a position."""
    space = get_space(position)
    return space["type"]


def get_space_name(position: int) -> str:
    """Get the name of space at a position."""
    space = get_space(position)
    return space["name"]


def get_property_id_at_position(position: int) -> str | None:
    """Get the property ID at a position (if it's a property space)."""
    space = get_space(position)
    return space.get("property_id")


def get_tax_amount(position: int) -> int | None:
    """Get the tax amount at a position (if it's a tax space)."""
    space = get_space(position)
    return space.get("amount")
