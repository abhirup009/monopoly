"""Community Chest card definitions for Monopoly.

16 Community Chest cards with various effects.
"""

from typing import TypedDict


class CommunityChestCard(TypedDict, total=False):
    """Type definition for a Community Chest card."""

    id: int
    text: str
    action: str
    destination: int | None
    amount: int | None
    house_cost: int | None
    hotel_cost: int | None


COMMUNITY_CHEST_CARDS: list[CommunityChestCard] = [
    {
        "id": 1,
        "text": "Advance to Go (Collect $200)",
        "action": "move_to",
        "destination": 0,
    },
    {
        "id": 2,
        "text": "Bank error in your favor. Collect $200",
        "action": "collect",
        "amount": 200,
    },
    {
        "id": 3,
        "text": "Doctor's fee. Pay $50",
        "action": "pay",
        "amount": 50,
    },
    {
        "id": 4,
        "text": "From sale of stock you get $50",
        "action": "collect",
        "amount": 50,
    },
    {
        "id": 5,
        "text": "Get Out of Jail Free",
        "action": "get_out_of_jail_card",
    },
    {
        "id": 6,
        "text": "Go to Jail. Go directly to jail, do not pass Go, do not collect $200",
        "action": "go_to_jail",
    },
    {
        "id": 7,
        "text": "Holiday fund matures. Receive $100",
        "action": "collect",
        "amount": 100,
    },
    {
        "id": 8,
        "text": "Income tax refund. Collect $20",
        "action": "collect",
        "amount": 20,
    },
    {
        "id": 9,
        "text": "It is your birthday. Collect $10 from every player",
        "action": "collect_from_each_player",
        "amount": 10,
    },
    {
        "id": 10,
        "text": "Life insurance matures. Collect $100",
        "action": "collect",
        "amount": 100,
    },
    {
        "id": 11,
        "text": "Pay hospital fees of $100",
        "action": "pay",
        "amount": 100,
    },
    {
        "id": 12,
        "text": "Pay school fees of $50",
        "action": "pay",
        "amount": 50,
    },
    {
        "id": 13,
        "text": "Receive $25 consultancy fee",
        "action": "collect",
        "amount": 25,
    },
    {
        "id": 14,
        "text": "You are assessed for street repair. $40 per house. $115 per hotel",
        "action": "pay_per_building",
        "house_cost": 40,
        "hotel_cost": 115,
    },
    {
        "id": 15,
        "text": "You have won second prize in a beauty contest. Collect $10",
        "action": "collect",
        "amount": 10,
    },
    {
        "id": 16,
        "text": "You inherit $100",
        "action": "collect",
        "amount": 100,
    },
]


def get_community_chest_card(card_id: int) -> CommunityChestCard | None:
    """Get Community Chest card by ID (1-indexed)."""
    for card in COMMUNITY_CHEST_CARDS:
        if card["id"] == card_id:
            return card
    return None
