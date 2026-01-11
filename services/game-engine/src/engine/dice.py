"""Dice rolling logic."""

import random
from dataclasses import dataclass


@dataclass
class DiceRoll:
    """Result of rolling dice."""

    die1: int
    die2: int

    @property
    def total(self) -> int:
        """Get the total of both dice."""
        return self.die1 + self.die2

    @property
    def is_doubles(self) -> bool:
        """Check if the roll is doubles."""
        return self.die1 == self.die2

    def to_list(self) -> list[int]:
        """Convert to list for storage."""
        return [self.die1, self.die2]


def roll_dice() -> DiceRoll:
    """Roll two six-sided dice."""
    return DiceRoll(
        die1=random.randint(1, 6),
        die2=random.randint(1, 6),
    )


def is_doubles(dice: list[int]) -> bool:
    """Check if a dice roll (as list) is doubles."""
    if len(dice) != 2:
        return False
    return dice[0] == dice[1]


def get_total(dice: list[int]) -> int:
    """Get the total of a dice roll (as list)."""
    return sum(dice)
