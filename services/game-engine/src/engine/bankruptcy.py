"""Bankruptcy detection and handling."""

from dataclasses import dataclass
from uuid import UUID

from src.db.models import PlayerModel, PropertyStateModel


@dataclass
class BankruptcyResult:
    """Result of a bankruptcy check."""

    is_bankrupt: bool
    debt_amount: int
    creditor_id: UUID | None  # None if debt is to the bank
    message: str


def check_bankruptcy(
    player: PlayerModel,
    debt_amount: int,
    creditor_id: UUID | None = None,
) -> BankruptcyResult:
    """Check if a player is bankrupt after incurring a debt.

    In V1, we don't have mortgage, so bankruptcy is simple:
    if cash < debt, player is bankrupt.

    Args:
        player: The player who owes money
        debt_amount: Amount owed
        creditor_id: ID of the player owed (None if bank)

    Returns:
        BankruptcyResult
    """
    if player.cash >= debt_amount:
        return BankruptcyResult(
            is_bankrupt=False,
            debt_amount=debt_amount,
            creditor_id=creditor_id,
            message=f"Player can pay ${debt_amount}",
        )

    creditor_name = "the bank" if creditor_id is None else "another player"
    return BankruptcyResult(
        is_bankrupt=True,
        debt_amount=debt_amount,
        creditor_id=creditor_id,
        message=f"Player is bankrupt! Cannot pay ${debt_amount} to {creditor_name}",
    )


def can_afford(player: PlayerModel, amount: int) -> bool:
    """Check if a player can afford a payment."""
    return player.cash >= amount


def get_net_worth(
    player: PlayerModel,
    property_states: list[PropertyStateModel],
) -> int:
    """Calculate a player's net worth.

    Net worth = cash + property values + house/hotel values

    Args:
        player: The player
        property_states: All property states

    Returns:
        Total net worth
    """
    from src.data.properties import get_property

    net_worth = player.cash

    for prop_state in property_states:
        if prop_state.owner_id == player.id:
            prop = get_property(prop_state.property_id)
            if prop:
                # Add property value
                net_worth += prop["price"]
                # Add building values (houses cost half to sell)
                if prop["type"] == "street" and prop_state.houses > 0:
                    house_cost = prop.get("house_cost", 0)
                    if prop_state.houses == 5:  # Hotel
                        # Hotel = 4 houses + 1 hotel (5 total purchases)
                        net_worth += (house_cost * 5) // 2
                    else:
                        net_worth += (house_cost * prop_state.houses) // 2

    return net_worth


def handle_bankruptcy_to_bank(
    player: PlayerModel,
    property_states: list[PropertyStateModel],
) -> list[str]:
    """Handle bankruptcy when a player owes the bank.

    All properties return to the bank (unowned).

    Args:
        player: The bankrupt player
        property_states: All property states

    Returns:
        List of property IDs that were released
    """
    released_properties = []

    for prop_state in property_states:
        if prop_state.owner_id == player.id:
            released_properties.append(prop_state.property_id)

    return released_properties


def handle_bankruptcy_to_player(
    bankrupt_player: PlayerModel,
    creditor_player: PlayerModel,
    property_states: list[PropertyStateModel],
) -> list[str]:
    """Handle bankruptcy when a player owes another player.

    All properties transfer to the creditor.

    Args:
        bankrupt_player: The bankrupt player
        creditor_player: The player who is owed
        property_states: All property states

    Returns:
        List of property IDs that will transfer
    """
    transferred_properties = []

    for prop_state in property_states:
        if prop_state.owner_id == bankrupt_player.id:
            transferred_properties.append(prop_state.property_id)

    return transferred_properties


def count_active_players(players: list[PlayerModel]) -> int:
    """Count players who are not bankrupt."""
    return sum(1 for p in players if not p.is_bankrupt)


def get_winner(players: list[PlayerModel]) -> PlayerModel | None:
    """Get the winner if only one player remains.

    Returns:
        The winning player, or None if game isn't over
    """
    active_players = [p for p in players if not p.is_bankrupt]
    if len(active_players) == 1:
        return active_players[0]
    return None


def is_game_over(players: list[PlayerModel]) -> bool:
    """Check if the game is over (only one player left)."""
    return count_active_players(players) <= 1
