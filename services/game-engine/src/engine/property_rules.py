"""Property buying and rent calculation rules."""

from uuid import UUID

from src.data.properties import (
    COLOR_GROUPS,
    RAILROAD_IDS,
    UTILITY_IDS,
    get_property,
)
from src.db.models import PlayerModel, PropertyStateModel


def can_buy_property(
    property_id: str,
    player: PlayerModel,
    property_states: list[PropertyStateModel],
) -> tuple[bool, str]:
    """Check if a player can buy a property.

    Args:
        property_id: The property ID
        player: The player attempting to buy
        property_states: All property states in the game

    Returns:
        Tuple of (can_buy, reason)
    """
    prop = get_property(property_id)
    if not prop:
        return False, f"Property {property_id} does not exist"

    # Find the property state
    prop_state = next(
        (ps for ps in property_states if ps.property_id == property_id),
        None,
    )

    if not prop_state:
        return False, f"Property state not found for {property_id}"

    if prop_state.owner_id is not None:
        return False, "Property is already owned"

    if player.cash < prop["price"]:
        return False, f"Insufficient funds (need ${prop['price']}, have ${player.cash})"

    return True, "OK"


def get_property_price(property_id: str) -> int:
    """Get the purchase price of a property."""
    prop = get_property(property_id)
    if not prop:
        raise ValueError(f"Property {property_id} does not exist")
    return prop["price"]


def calculate_rent(
    property_id: str,
    property_states: list[PropertyStateModel],
    dice_total: int | None = None,
) -> int:
    """Calculate rent for landing on a property.

    Args:
        property_id: The property ID
        property_states: All property states in the game
        dice_total: The dice roll total (needed for utilities)

    Returns:
        Rent amount to pay
    """
    prop = get_property(property_id)
    if not prop:
        return 0

    # Find the property state
    prop_state = next(
        (ps for ps in property_states if ps.property_id == property_id),
        None,
    )

    if not prop_state or prop_state.owner_id is None:
        return 0  # Unowned, no rent

    owner_id = prop_state.owner_id

    if prop["type"] == "street":
        return _calculate_street_rent(property_id, prop, prop_state, property_states, owner_id)
    elif prop["type"] == "railroad":
        return _calculate_railroad_rent(property_states, owner_id)
    elif prop["type"] == "utility":
        return _calculate_utility_rent(property_states, owner_id, dice_total)

    return 0


def _calculate_street_rent(
    property_id: str,
    prop: dict,
    prop_state: PropertyStateModel,
    property_states: list[PropertyStateModel],
    owner_id: UUID,
) -> int:
    """Calculate rent for a street property."""
    color = prop["color"]
    color_group = COLOR_GROUPS.get(color, [])

    # Check if owner has full color set
    owns_full_set = all(
        any(
            ps.property_id == pid and ps.owner_id == owner_id
            for ps in property_states
        )
        for pid in color_group
    )

    houses = prop_state.houses

    if houses == 0:
        # No houses - base rent, doubled if full set
        base_rent = prop["rent"][0]
        return base_rent * 2 if owns_full_set else base_rent
    else:
        # Houses/hotel rent
        # houses 1-4 = index 1-4, hotel (houses=5) = index 5
        return prop["rent"][houses]


def _calculate_railroad_rent(
    property_states: list[PropertyStateModel],
    owner_id: UUID,
) -> int:
    """Calculate rent for a railroad."""
    # Count railroads owned by the same owner
    rr_count = sum(
        1
        for ps in property_states
        if ps.property_id in RAILROAD_IDS and ps.owner_id == owner_id
    )

    # Rent: $25, $50, $100, $200 based on count
    if rr_count <= 0:
        return 0
    return 25 * (2 ** (rr_count - 1))


def _calculate_utility_rent(
    property_states: list[PropertyStateModel],
    owner_id: UUID,
    dice_total: int | None,
) -> int:
    """Calculate rent for a utility."""
    if dice_total is None:
        dice_total = 7  # Average dice roll as fallback

    # Count utilities owned by the same owner
    util_count = sum(
        1
        for ps in property_states
        if ps.property_id in UTILITY_IDS and ps.owner_id == owner_id
    )

    # 4x dice if owns 1, 10x dice if owns both
    if util_count == 1:
        return 4 * dice_total
    elif util_count == 2:
        return 10 * dice_total
    return 0


def owns_full_color_set(
    player_id: UUID,
    color: str,
    property_states: list[PropertyStateModel],
) -> bool:
    """Check if a player owns all properties in a color group."""
    color_group = COLOR_GROUPS.get(color, [])
    if not color_group:
        return False

    return all(
        any(
            ps.property_id == pid and ps.owner_id == player_id
            for ps in property_states
        )
        for pid in color_group
    )


def get_owner_id(
    property_id: str,
    property_states: list[PropertyStateModel],
) -> UUID | None:
    """Get the owner ID of a property."""
    prop_state = next(
        (ps for ps in property_states if ps.property_id == property_id),
        None,
    )
    return prop_state.owner_id if prop_state else None


def count_houses_and_hotels(
    player_id: UUID,
    property_states: list[PropertyStateModel],
) -> tuple[int, int]:
    """Count total houses and hotels owned by a player.

    Returns:
        Tuple of (houses, hotels)
    """
    houses = 0
    hotels = 0

    for ps in property_states:
        if ps.owner_id == player_id:
            if ps.houses == 5:
                hotels += 1
            elif ps.houses > 0:
                houses += ps.houses

    return houses, hotels
