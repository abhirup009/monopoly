"""Card execution logic for Chance and Community Chest cards."""

from dataclasses import dataclass
from enum import Enum
from uuid import UUID

from src.data.chance_cards import CHANCE_CARDS, get_chance_card
from src.data.community_chest import COMMUNITY_CHEST_CARDS, get_community_chest_card
from src.db.models import PlayerModel, PropertyStateModel
from src.engine.movement import (
    GO_POSITION,
    JAIL_POSITION,
    find_nearest_property_type,
    move_player,
    move_to_position,
)
from src.engine.property_rules import calculate_rent, count_houses_and_hotels


class CardType(str, Enum):
    """Type of card deck."""

    CHANCE = "chance"
    COMMUNITY_CHEST = "community_chest"


@dataclass
class CardEffect:
    """Result of executing a card."""

    card_id: int
    card_type: CardType
    card_text: str
    cash_change: int  # Positive = gain, negative = loss
    new_position: int | None  # If card moves the player
    passed_go: bool  # If player passed GO during movement
    go_to_jail: bool  # If player should go to jail
    get_jail_card: bool  # If player gets a get out of jail card
    payments_to_players: dict[UUID, int]  # Player ID -> amount owed
    collections_from_players: dict[UUID, int]  # Player ID -> amount to collect
    special_rent_multiplier: int | None  # For railroad/utility cards


def execute_chance_card(
    card_id: int,
    player: PlayerModel,
    all_players: list[PlayerModel],
    property_states: list[PropertyStateModel],
) -> CardEffect:
    """Execute a Chance card effect.

    Args:
        card_id: The card ID to execute
        player: The player who drew the card
        all_players: All players in the game
        property_states: All property states

    Returns:
        CardEffect describing what happened
    """
    card = get_chance_card(card_id)
    if not card:
        raise ValueError(f"Invalid Chance card ID: {card_id}")

    return _execute_card(
        card=card,
        card_type=CardType.CHANCE,
        player=player,
        all_players=all_players,
        property_states=property_states,
    )


def execute_community_chest_card(
    card_id: int,
    player: PlayerModel,
    all_players: list[PlayerModel],
    property_states: list[PropertyStateModel],
) -> CardEffect:
    """Execute a Community Chest card effect.

    Args:
        card_id: The card ID to execute
        player: The player who drew the card
        all_players: All players in the game
        property_states: All property states

    Returns:
        CardEffect describing what happened
    """
    card = get_community_chest_card(card_id)
    if not card:
        raise ValueError(f"Invalid Community Chest card ID: {card_id}")

    return _execute_card(
        card=card,
        card_type=CardType.COMMUNITY_CHEST,
        player=player,
        all_players=all_players,
        property_states=property_states,
    )


def _execute_card(
    card: dict,
    card_type: CardType,
    player: PlayerModel,
    all_players: list[PlayerModel],
    property_states: list[PropertyStateModel],
) -> CardEffect:
    """Execute a card effect.

    Args:
        card: The card data
        card_type: Type of card (Chance or Community Chest)
        player: The player who drew the card
        all_players: All players in the game
        property_states: All property states

    Returns:
        CardEffect describing what happened
    """
    action = card["action"]

    # Initialize default effect
    effect = CardEffect(
        card_id=card["id"],
        card_type=card_type,
        card_text=card["text"],
        cash_change=0,
        new_position=None,
        passed_go=False,
        go_to_jail=False,
        get_jail_card=False,
        payments_to_players={},
        collections_from_players={},
        special_rent_multiplier=None,
    )

    if action == "move_to":
        # Move to a specific position
        destination = card["destination"]
        result = move_to_position(player.position, destination)
        effect.new_position = result.new_position
        effect.passed_go = result.passed_go
        if effect.passed_go:
            effect.cash_change += 200

    elif action == "move_to_nearest":
        # Move to nearest railroad or utility
        property_type = card["property_type"]
        destination = find_nearest_property_type(player.position, property_type)
        result = move_to_position(player.position, destination)
        effect.new_position = result.new_position
        effect.passed_go = result.passed_go
        if effect.passed_go:
            effect.cash_change += 200
        # Special rent rules apply (2x for railroad, 10x dice for utility)
        if property_type == "railroad":
            effect.special_rent_multiplier = 2
        elif property_type == "utility":
            effect.special_rent_multiplier = 10  # 10x dice roll

    elif action == "move_relative":
        # Move relative number of spaces
        spaces = card["spaces"]
        result = move_player(player.position, spaces)
        effect.new_position = result.new_position
        # Going backward doesn't pass GO, but check if we land on Go To Jail
        if result.landed_on_go_to_jail:
            effect.go_to_jail = True

    elif action == "collect":
        # Collect money from the bank
        effect.cash_change = card["amount"]

    elif action == "pay":
        # Pay money to the bank
        effect.cash_change = -card["amount"]

    elif action == "get_out_of_jail_card":
        # Get a get out of jail free card
        effect.get_jail_card = True

    elif action == "go_to_jail":
        # Go directly to jail
        effect.go_to_jail = True
        effect.new_position = JAIL_POSITION

    elif action == "pay_per_building":
        # Pay per house and hotel
        house_cost = card.get("house_cost", 0)
        hotel_cost = card.get("hotel_cost", 0)
        houses, hotels = count_houses_and_hotels(player.id, property_states)
        total_cost = (houses * house_cost) + (hotels * hotel_cost)
        effect.cash_change = -total_cost

    elif action == "pay_each_player":
        # Pay each other player
        amount = card["amount"]
        for other_player in all_players:
            if other_player.id != player.id and not other_player.is_bankrupt:
                effect.payments_to_players[other_player.id] = amount
                effect.cash_change -= amount

    elif action == "collect_from_each_player":
        # Collect from each other player
        amount = card["amount"]
        for other_player in all_players:
            if other_player.id != player.id and not other_player.is_bankrupt:
                effect.collections_from_players[other_player.id] = amount
                effect.cash_change += amount

    return effect


def get_card_count(card_type: CardType) -> int:
    """Get the total number of cards in a deck."""
    if card_type == CardType.CHANCE:
        return len(CHANCE_CARDS)
    elif card_type == CardType.COMMUNITY_CHEST:
        return len(COMMUNITY_CHEST_CARDS)
    return 0


def get_all_card_ids(card_type: CardType) -> list[int]:
    """Get all card IDs for a deck."""
    if card_type == CardType.CHANCE:
        return [card["id"] for card in CHANCE_CARDS]
    elif card_type == CardType.COMMUNITY_CHEST:
        return [card["id"] for card in COMMUNITY_CHEST_CARDS]
    return []
