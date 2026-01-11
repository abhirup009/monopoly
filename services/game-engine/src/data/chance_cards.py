"""Chance card definitions for Monopoly.

16 Chance cards with various effects.
"""

from typing import TypedDict


class ChanceCard(TypedDict, total=False):
    """Type definition for a Chance card."""

    id: int
    text: str
    action: str
    destination: int | None
    amount: int | None
    spaces: int | None
    property_type: str | None
    house_cost: int | None
    hotel_cost: int | None


CHANCE_CARDS: list[ChanceCard] = [
    {
        "id": 1,
        "text": "Advance to Boardwalk",
        "action": "move_to",
        "destination": 39,
    },
    {
        "id": 2,
        "text": "Advance to Go (Collect $200)",
        "action": "move_to",
        "destination": 0,
    },
    {
        "id": 3,
        "text": "Advance to Illinois Avenue. If you pass Go, collect $200",
        "action": "move_to",
        "destination": 24,
    },
    {
        "id": 4,
        "text": "Advance to St. Charles Place. If you pass Go, collect $200",
        "action": "move_to",
        "destination": 11,
    },
    {
        "id": 5,
        "text": "Advance to the nearest Railroad. If unowned, you may buy it from the Bank. If owned, pay owner twice the rental to which they are otherwise entitled",
        "action": "move_to_nearest",
        "property_type": "railroad",
    },
    {
        "id": 6,
        "text": "Advance to the nearest Railroad. If unowned, you may buy it from the Bank. If owned, pay owner twice the rental to which they are otherwise entitled",
        "action": "move_to_nearest",
        "property_type": "railroad",
    },
    {
        "id": 7,
        "text": "Advance token to nearest Utility. If unowned, you may buy it from the Bank. If owned, throw dice and pay owner 10 times amount thrown",
        "action": "move_to_nearest",
        "property_type": "utility",
    },
    {
        "id": 8,
        "text": "Bank pays you dividend of $50",
        "action": "collect",
        "amount": 50,
    },
    {
        "id": 9,
        "text": "Get Out of Jail Free",
        "action": "get_out_of_jail_card",
    },
    {
        "id": 10,
        "text": "Go Back 3 Spaces",
        "action": "move_relative",
        "spaces": -3,
    },
    {
        "id": 11,
        "text": "Go to Jail. Go directly to Jail, do not pass Go, do not collect $200",
        "action": "go_to_jail",
    },
    {
        "id": 12,
        "text": "Make general repairs on all your property. For each house pay $25. For each hotel pay $100",
        "action": "pay_per_building",
        "house_cost": 25,
        "hotel_cost": 100,
    },
    {
        "id": 13,
        "text": "Speeding fine $15",
        "action": "pay",
        "amount": 15,
    },
    {
        "id": 14,
        "text": "Take a trip to Reading Railroad. If you pass Go, collect $200",
        "action": "move_to",
        "destination": 5,
    },
    {
        "id": 15,
        "text": "You have been elected Chairman of the Board. Pay each player $50",
        "action": "pay_each_player",
        "amount": 50,
    },
    {
        "id": 16,
        "text": "Your building loan matures. Collect $150",
        "action": "collect",
        "amount": 150,
    },
]


def get_chance_card(card_id: int) -> ChanceCard | None:
    """Get Chance card by ID (1-indexed)."""
    for card in CHANCE_CARDS:
        if card["id"] == card_id:
            return card
    return None
