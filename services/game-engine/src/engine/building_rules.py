"""House and hotel building rules."""

from uuid import UUID

from src.data.properties import COLOR_GROUPS, PROPERTIES, get_property
from src.db.models import PlayerModel, PropertyStateModel


def can_build_house(
    property_id: str,
    player: PlayerModel,
    property_states: list[PropertyStateModel],
) -> tuple[bool, str]:
    """Check if a player can build a house on a property.

    Args:
        property_id: The property ID
        player: The player attempting to build
        property_states: All property states in the game

    Returns:
        Tuple of (can_build, reason)
    """
    prop = get_property(property_id)
    if not prop:
        return False, f"Property {property_id} does not exist"

    # Must be a street
    if prop["type"] != "street":
        return False, "Can only build on street properties"

    # Find the property state
    prop_state = next(
        (ps for ps in property_states if ps.property_id == property_id),
        None,
    )

    if not prop_state:
        return False, f"Property state not found for {property_id}"

    # Must own the property
    if prop_state.owner_id != player.id:
        return False, "You don't own this property"

    # Must own full color set
    color = prop["color"]
    color_group = COLOR_GROUPS.get(color, [])

    for pid in color_group:
        ps = next((p for p in property_states if p.property_id == pid), None)
        if not ps or ps.owner_id != player.id:
            return False, "Must own all properties in the color group"

    # Max 4 houses before hotel
    if prop_state.houses >= 4:
        return False, "Already has 4 houses - build a hotel instead"

    # Even building rule
    current_houses = prop_state.houses
    for pid in color_group:
        if pid != property_id:
            ps = next((p for p in property_states if p.property_id == pid), None)
            if ps and ps.houses < current_houses:
                return False, "Must build evenly across the color group"

    # Must afford
    house_cost = prop["house_cost"]
    if player.cash < house_cost:
        return False, f"Insufficient funds (need ${house_cost})"

    return True, "OK"


def can_build_hotel(
    property_id: str,
    player: PlayerModel,
    property_states: list[PropertyStateModel],
) -> tuple[bool, str]:
    """Check if a player can build a hotel on a property.

    Args:
        property_id: The property ID
        player: The player attempting to build
        property_states: All property states in the game

    Returns:
        Tuple of (can_build, reason)
    """
    prop = get_property(property_id)
    if not prop:
        return False, f"Property {property_id} does not exist"

    # Must be a street
    if prop["type"] != "street":
        return False, "Can only build on street properties"

    # Find the property state
    prop_state = next(
        (ps for ps in property_states if ps.property_id == property_id),
        None,
    )

    if not prop_state:
        return False, f"Property state not found for {property_id}"

    # Must own the property
    if prop_state.owner_id != player.id:
        return False, "You don't own this property"

    # Must have 4 houses
    if prop_state.houses != 4:
        return False, "Must have 4 houses before building a hotel"

    # Must own full color set with 4 houses on each
    color = prop["color"]
    color_group = COLOR_GROUPS.get(color, [])

    for pid in color_group:
        if pid != property_id:
            ps = next((p for p in property_states if p.property_id == pid), None)
            if not ps or ps.owner_id != player.id:
                return False, "Must own all properties in the color group"
            if ps.houses < 4:
                return False, "All properties in the group must have 4 houses first"

    # Must afford (hotel costs same as a house)
    house_cost = prop["house_cost"]
    if player.cash < house_cost:
        return False, f"Insufficient funds (need ${house_cost})"

    return True, "OK"


def get_house_cost(property_id: str) -> int:
    """Get the cost to build a house on a property."""
    prop = get_property(property_id)
    if not prop or prop["type"] != "street":
        raise ValueError(f"Property {property_id} is not a street")
    return prop["house_cost"]


def get_buildable_properties(
    player: PlayerModel,
    property_states: list[PropertyStateModel],
) -> list[tuple[str, str]]:
    """Get all properties where a player can build.

    Returns:
        List of (property_id, build_type) where build_type is "house" or "hotel"
    """
    buildable = []

    for prop_state in property_states:
        if prop_state.owner_id != player.id:
            continue

        prop = get_property(prop_state.property_id)
        if not prop or prop["type"] != "street":
            continue

        # Check if can build house
        can_house, _ = can_build_house(
            prop_state.property_id, player, property_states
        )
        if can_house:
            buildable.append((prop_state.property_id, "house"))
            continue

        # Check if can build hotel
        can_hotel, _ = can_build_hotel(
            prop_state.property_id, player, property_states
        )
        if can_hotel:
            buildable.append((prop_state.property_id, "hotel"))

    return buildable
