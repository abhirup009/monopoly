"""Jail mechanics."""

from dataclasses import dataclass
from enum import Enum

from src.db.models import PlayerModel
from src.engine.dice import DiceRoll

JAIL_FINE = 50
MAX_JAIL_TURNS = 3


class JailEscapeMethod(str, Enum):
    """Methods to escape from jail."""

    PAY_FINE = "pay_fine"
    USE_CARD = "use_card"
    ROLL_DOUBLES = "roll_doubles"
    FORCED_PAY = "forced_pay"  # After 3 turns


@dataclass
class JailEscapeResult:
    """Result of attempting to escape jail."""

    escaped: bool
    method: JailEscapeMethod | None
    cost: int
    message: str


def can_pay_jail_fine(player: PlayerModel) -> tuple[bool, str]:
    """Check if a player can pay the $50 jail fine.

    Args:
        player: The player in jail

    Returns:
        Tuple of (can_pay, reason)
    """
    if not player.in_jail:
        return False, "Player is not in jail"

    if player.cash < JAIL_FINE:
        return False, f"Insufficient funds (need ${JAIL_FINE})"

    return True, "OK"


def can_use_jail_card(player: PlayerModel) -> tuple[bool, str]:
    """Check if a player can use a Get Out of Jail Free card.

    Args:
        player: The player in jail

    Returns:
        Tuple of (can_use, reason)
    """
    if not player.in_jail:
        return False, "Player is not in jail"

    if player.get_out_of_jail_cards <= 0:
        return False, "No Get Out of Jail Free cards"

    return True, "OK"


def can_roll_for_doubles(player: PlayerModel) -> tuple[bool, str]:
    """Check if a player can attempt to roll doubles to escape.

    Args:
        player: The player in jail

    Returns:
        Tuple of (can_roll, reason)
    """
    if not player.in_jail:
        return False, "Player is not in jail"

    # Can always attempt to roll if in jail
    return True, "OK"


def pay_jail_fine(player: PlayerModel) -> JailEscapeResult:
    """Have a player pay the jail fine.

    Args:
        player: The player paying

    Returns:
        JailEscapeResult
    """
    if player.cash < JAIL_FINE:
        return JailEscapeResult(
            escaped=False,
            method=None,
            cost=0,
            message=f"Insufficient funds (need ${JAIL_FINE})",
        )

    return JailEscapeResult(
        escaped=True,
        method=JailEscapeMethod.PAY_FINE,
        cost=JAIL_FINE,
        message=f"Paid ${JAIL_FINE} to get out of jail",
    )


def use_jail_card(player: PlayerModel) -> JailEscapeResult:
    """Have a player use a Get Out of Jail Free card.

    Args:
        player: The player using the card

    Returns:
        JailEscapeResult
    """
    if player.get_out_of_jail_cards <= 0:
        return JailEscapeResult(
            escaped=False,
            method=None,
            cost=0,
            message="No Get Out of Jail Free cards",
        )

    return JailEscapeResult(
        escaped=True,
        method=JailEscapeMethod.USE_CARD,
        cost=0,
        message="Used Get Out of Jail Free card",
    )


def roll_for_doubles(player: PlayerModel, dice_roll: DiceRoll) -> JailEscapeResult:
    """Attempt to roll doubles to escape jail.

    Args:
        player: The player attempting to escape
        dice_roll: The dice roll result

    Returns:
        JailEscapeResult
    """
    if dice_roll.is_doubles:
        return JailEscapeResult(
            escaped=True,
            method=JailEscapeMethod.ROLL_DOUBLES,
            cost=0,
            message=f"Rolled doubles ({dice_roll.die1}, {dice_roll.die2}) and escaped jail!",
        )

    # Check if this is the third turn
    if player.jail_turns >= MAX_JAIL_TURNS - 1:
        # Third failed attempt - must pay
        return JailEscapeResult(
            escaped=True,  # Will escape after paying
            method=JailEscapeMethod.FORCED_PAY,
            cost=JAIL_FINE,
            message=f"Third turn in jail - must pay ${JAIL_FINE} and leave",
        )

    return JailEscapeResult(
        escaped=False,
        method=None,
        cost=0,
        message=f"Did not roll doubles ({dice_roll.die1}, {dice_roll.die2}). Still in jail.",
    )


def should_force_jail_payment(player: PlayerModel) -> bool:
    """Check if a player must pay to leave jail (3rd turn)."""
    return player.in_jail and player.jail_turns >= MAX_JAIL_TURNS


def get_jail_options(player: PlayerModel) -> list[str]:
    """Get available jail escape options for a player.

    Returns:
        List of available options: "pay_fine", "use_card", "roll_for_doubles"
    """
    options = []

    if can_pay_jail_fine(player)[0]:
        options.append("pay_fine")

    if can_use_jail_card(player)[0]:
        options.append("use_card")

    if can_roll_for_doubles(player)[0]:
        options.append("roll_for_doubles")

    return options
