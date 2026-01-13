"""Game manager - orchestrates game flow and turn logic."""

import random
from dataclasses import dataclass
from enum import Enum
from uuid import UUID

from src.data.properties import get_property
from src.db.models import GameModel, PlayerModel, PropertyStateModel
from src.engine.bankruptcy import (
    BankruptcyResult,
    check_bankruptcy,
    get_winner,
    handle_bankruptcy_to_bank,
    handle_bankruptcy_to_player,
    is_game_over,
)
from src.engine.building_rules import (
    can_build_hotel,
    can_build_house,
    get_buildable_properties,
    get_house_cost,
)
from src.engine.card_executor import (
    CardEffect,
    CardType,
    execute_chance_card,
    execute_community_chest_card,
)
from src.engine.dice import DiceRoll, roll_dice
from src.engine.jail_rules import (
    JAIL_FINE,
    JailEscapeMethod,
    JailEscapeResult,
    can_pay_jail_fine,
    can_roll_for_doubles,
    can_use_jail_card,
    pay_jail_fine,
    roll_for_doubles,
    use_jail_card,
)
from src.engine.movement import (
    GO_SALARY,
    JAIL_POSITION,
    MovementResult,
    get_property_id_at_position,
    get_space_name,
    get_space_type,
    get_tax_amount,
    move_player,
)
from src.engine.property_rules import (
    calculate_rent,
    can_buy_property,
    get_owner_id,
    get_property_price,
)


class TurnPhase(str, Enum):
    """Phases within a turn."""

    PRE_ROLL = "pre_roll"  # Before dice roll, initial state
    AWAITING_ROLL = "awaiting_roll"  # Waiting for player to roll dice
    AWAITING_BUY_DECISION = "awaiting_buy_decision"  # Player landed on unowned property
    AWAITING_JAIL_DECISION = "awaiting_jail_decision"  # Player in jail, needs decision
    POST_ROLL = "post_roll"  # After main action (can build houses, end turn)


class ActionType(str, Enum):
    """Types of actions a player can take."""

    ROLL_DICE = "roll_dice"
    BUY_PROPERTY = "buy_property"
    PASS_PROPERTY = "pass_property"
    BUILD_HOUSE = "build_house"
    BUILD_HOTEL = "build_hotel"
    PAY_JAIL_FINE = "pay_jail_fine"
    USE_JAIL_CARD = "use_jail_card"
    ROLL_FOR_DOUBLES = "roll_for_doubles"
    END_TURN = "end_turn"


@dataclass
class ValidAction:
    """A valid action that can be taken."""

    action_type: ActionType
    property_id: str | None = None
    cost: int | None = None
    description: str = ""


@dataclass
class ActionResult:
    """Result of executing an action."""

    success: bool
    message: str
    dice_roll: DiceRoll | None = None
    movement: MovementResult | None = None
    card_effect: CardEffect | None = None
    jail_result: JailEscapeResult | None = None
    bankruptcy: BankruptcyResult | None = None
    rent_paid: int = 0
    rent_to_player: UUID | None = None
    next_phase: TurnPhase | None = None
    turn_complete: bool = False
    game_over: bool = False
    winner_id: UUID | None = None


class GameManager:
    """Manages game flow and turn logic."""

    def __init__(
        self,
        game: GameModel,
        players: list[PlayerModel],
        property_states: list[PropertyStateModel],
    ):
        """Initialize the game manager.

        Args:
            game: The game model
            players: All players in the game
            property_states: All property states
        """
        self.game = game
        self.players = players
        self.property_states = property_states
        self._consecutive_doubles = 0

    @property
    def current_player(self) -> PlayerModel:
        """Get the current player."""
        active_players = [p for p in self.players if not p.is_bankrupt]
        if not active_players:
            raise ValueError("No active players")
        return active_players[self.game.current_player_index % len(active_players)]

    def get_valid_actions(self) -> list[ValidAction]:
        """Get valid actions for the current player based on turn phase."""
        player = self.current_player
        phase = TurnPhase(self.game.turn_phase)
        actions = []

        if phase == TurnPhase.PRE_ROLL or phase == TurnPhase.AWAITING_ROLL:
            if player.in_jail:
                # Jail options
                if can_pay_jail_fine(player)[0]:
                    actions.append(
                        ValidAction(
                            action_type=ActionType.PAY_JAIL_FINE,
                            cost=JAIL_FINE,
                            description=f"Pay ${JAIL_FINE} to get out of jail",
                        )
                    )
                if can_use_jail_card(player)[0]:
                    actions.append(
                        ValidAction(
                            action_type=ActionType.USE_JAIL_CARD,
                            description="Use Get Out of Jail Free card",
                        )
                    )
                if can_roll_for_doubles(player)[0]:
                    actions.append(
                        ValidAction(
                            action_type=ActionType.ROLL_FOR_DOUBLES,
                            description="Try to roll doubles to escape",
                        )
                    )
            else:
                # Normal pre-roll - just roll dice
                actions.append(
                    ValidAction(
                        action_type=ActionType.ROLL_DICE,
                        description="Roll the dice",
                    )
                )

        elif phase == TurnPhase.AWAITING_JAIL_DECISION:
            # Jail decision phase
            if can_pay_jail_fine(player)[0]:
                actions.append(
                    ValidAction(
                        action_type=ActionType.PAY_JAIL_FINE,
                        cost=JAIL_FINE,
                        description=f"Pay ${JAIL_FINE} to get out of jail",
                    )
                )
            if can_use_jail_card(player)[0]:
                actions.append(
                    ValidAction(
                        action_type=ActionType.USE_JAIL_CARD,
                        description="Use Get Out of Jail Free card",
                    )
                )
            if can_roll_for_doubles(player)[0]:
                actions.append(
                    ValidAction(
                        action_type=ActionType.ROLL_FOR_DOUBLES,
                        description="Try to roll doubles to escape",
                    )
                )

        elif phase == TurnPhase.AWAITING_BUY_DECISION:
            # Check what space we're on
            position = player.position
            property_id = get_property_id_at_position(position)

            if property_id:
                # On a property space
                can_buy, reason = can_buy_property(
                    property_id, player, self.property_states
                )
                if can_buy:
                    price = get_property_price(property_id)
                    actions.append(
                        ValidAction(
                            action_type=ActionType.BUY_PROPERTY,
                            property_id=property_id,
                            cost=price,
                            description=f"Buy {property_id} for ${price}",
                        )
                    )
                    actions.append(
                        ValidAction(
                            action_type=ActionType.PASS_PROPERTY,
                            property_id=property_id,
                            description=f"Pass on buying {property_id}",
                        )
                    )
                else:
                    # Can't buy - maybe owned, go to post-roll
                    actions.append(
                        ValidAction(
                            action_type=ActionType.END_TURN,
                            description="Continue (no action available)",
                        )
                    )
            else:
                # Not a property space, move to post-roll
                actions.append(
                    ValidAction(
                        action_type=ActionType.END_TURN,
                        description="Continue",
                    )
                )

        elif phase == TurnPhase.POST_ROLL:
            # Can build houses/hotels or end turn
            buildable = get_buildable_properties(player, self.property_states)
            for prop_id, build_type in buildable:
                cost = get_house_cost(prop_id)
                action_type = (
                    ActionType.BUILD_HOUSE
                    if build_type == "house"
                    else ActionType.BUILD_HOTEL
                )
                actions.append(
                    ValidAction(
                        action_type=action_type,
                        property_id=prop_id,
                        cost=cost,
                        description=f"Build {build_type} on {prop_id} for ${cost}",
                    )
                )

            actions.append(
                ValidAction(
                    action_type=ActionType.END_TURN,
                    description="End turn",
                )
            )

        return actions

    def execute_action(
        self,
        action_type: ActionType,
        property_id: str | None = None,
    ) -> ActionResult:
        """Execute an action for the current player.

        Args:
            action_type: The type of action to take
            property_id: Property ID for property-related actions

        Returns:
            ActionResult describing what happened
        """
        player = self.current_player

        if action_type == ActionType.ROLL_DICE:
            return self._handle_roll_dice(player)
        elif action_type == ActionType.ROLL_FOR_DOUBLES:
            return self._handle_roll_for_doubles(player)
        elif action_type == ActionType.PAY_JAIL_FINE:
            return self._handle_pay_jail_fine(player)
        elif action_type == ActionType.USE_JAIL_CARD:
            return self._handle_use_jail_card(player)
        elif action_type == ActionType.BUY_PROPERTY:
            return self._handle_buy_property(player, property_id)
        elif action_type == ActionType.PASS_PROPERTY:
            return self._handle_pass_property(player, property_id)
        elif action_type == ActionType.BUILD_HOUSE:
            return self._handle_build_house(player, property_id)
        elif action_type == ActionType.BUILD_HOTEL:
            return self._handle_build_hotel(player, property_id)
        elif action_type == ActionType.END_TURN:
            return self._handle_end_turn(player)
        else:
            return ActionResult(
                success=False,
                message=f"Unknown action type: {action_type}",
            )

    def _handle_roll_dice(self, player: PlayerModel) -> ActionResult:
        """Handle rolling dice and moving."""
        dice = roll_dice()
        self._consecutive_doubles = (
            self._consecutive_doubles + 1 if dice.is_doubles else 0
        )

        # Three doubles in a row = go to jail
        if self._consecutive_doubles >= 3:
            player.position = JAIL_POSITION
            player.in_jail = True
            player.jail_turns = 0
            self._consecutive_doubles = 0
            return ActionResult(
                success=True,
                message="Three doubles in a row! Go to jail!",
                dice_roll=dice,
                next_phase=TurnPhase.POST_ROLL,
                turn_complete=True,
            )

        # Move player
        movement = move_player(player.position, dice.total)
        player.position = movement.new_position

        # Check if passed GO
        cash_change = 0
        if movement.passed_go:
            player.cash += GO_SALARY
            cash_change = GO_SALARY

        # Check if landed on Go To Jail
        if movement.landed_on_go_to_jail:
            player.position = JAIL_POSITION
            player.in_jail = True
            player.jail_turns = 0
            return ActionResult(
                success=True,
                message=f"Rolled {dice.total} and landed on Go To Jail!",
                dice_roll=dice,
                movement=movement,
                next_phase=TurnPhase.POST_ROLL,
                turn_complete=True,
            )

        # Handle landing on space
        return self._handle_landing(player, dice, movement, cash_change)

    def _handle_landing(
        self,
        player: PlayerModel,
        dice: DiceRoll,
        movement: MovementResult,
        cash_change: int,
    ) -> ActionResult:
        """Handle landing on a space after moving."""
        position = player.position
        space_type = get_space_type(position)
        space_name = get_space_name(position)

        # Handle different space types
        if space_type == "property":
            return self._handle_land_on_property(player, dice, movement, cash_change)
        elif space_type == "railroad":
            return self._handle_land_on_property(player, dice, movement, cash_change)
        elif space_type == "utility":
            return self._handle_land_on_property(player, dice, movement, cash_change)
        elif space_type == "chance":
            return self._handle_land_on_card(player, dice, movement, CardType.CHANCE)
        elif space_type == "community_chest":
            return self._handle_land_on_card(
                player, dice, movement, CardType.COMMUNITY_CHEST
            )
        elif space_type == "tax":
            return self._handle_land_on_tax(player, dice, movement)
        elif space_type in ("go", "jail", "free_parking"):
            # Safe spaces
            go_msg = f" Collected ${GO_SALARY}!" if cash_change > 0 else ""
            return ActionResult(
                success=True,
                message=f"Rolled {dice.total} and landed on {space_name}.{go_msg}",
                dice_roll=dice,
                movement=movement,
                next_phase=TurnPhase.POST_ROLL,
            )
        else:
            return ActionResult(
                success=True,
                message=f"Rolled {dice.total} and landed on {space_name}.",
                dice_roll=dice,
                movement=movement,
                next_phase=TurnPhase.POST_ROLL,
            )

    def _handle_land_on_property(
        self,
        player: PlayerModel,
        dice: DiceRoll,
        movement: MovementResult,
        cash_change: int = 0,
    ) -> ActionResult:
        """Handle landing on a property space."""
        property_id = get_property_id_at_position(player.position)
        if not property_id:
            return ActionResult(
                success=True,
                message=f"Rolled {dice.total}",
                dice_roll=dice,
                movement=movement,
                next_phase=TurnPhase.POST_ROLL,
            )

        prop = get_property(property_id)
        owner_id = get_owner_id(property_id, self.property_states)

        if owner_id is None:
            # Unowned - player can buy
            return ActionResult(
                success=True,
                message=f"Rolled {dice.total} and landed on {prop['name']} (unowned).",
                dice_roll=dice,
                movement=movement,
                next_phase=TurnPhase.AWAITING_BUY_DECISION,
            )
        elif owner_id == player.id:
            # Own property
            return ActionResult(
                success=True,
                message=f"Rolled {dice.total} and landed on your own property ({prop['name']}).",
                dice_roll=dice,
                movement=movement,
                next_phase=TurnPhase.POST_ROLL,
            )
        else:
            # Pay rent
            rent = calculate_rent(property_id, self.property_states, dice.total)
            bankruptcy = check_bankruptcy(player, rent, owner_id)

            if bankruptcy.is_bankrupt:
                return self._handle_bankruptcy(player, rent, owner_id, dice, movement)

            player.cash -= rent
            # Credit owner
            owner = next((p for p in self.players if p.id == owner_id), None)
            if owner:
                owner.cash += rent

            return ActionResult(
                success=True,
                message=f"Rolled {dice.total} and landed on {prop['name']}. Paid ${rent} rent.",
                dice_roll=dice,
                movement=movement,
                rent_paid=rent,
                rent_to_player=owner_id,
                next_phase=TurnPhase.POST_ROLL,
            )

    def _handle_land_on_card(
        self,
        player: PlayerModel,
        dice: DiceRoll,
        movement: MovementResult,
        card_type: CardType,
    ) -> ActionResult:
        """Handle landing on Chance or Community Chest."""
        # Draw a random card (in real implementation, would use deck state)
        if card_type == CardType.CHANCE:
            card_id = random.randint(1, 16)
            effect = execute_chance_card(
                card_id, player, self.players, self.property_states
            )
        else:
            card_id = random.randint(1, 16)
            effect = execute_community_chest_card(
                card_id, player, self.players, self.property_states
            )

        # Apply effect
        if effect.go_to_jail:
            player.position = JAIL_POSITION
            player.in_jail = True
            player.jail_turns = 0
            return ActionResult(
                success=True,
                message=f"{effect.card_text} - Go to Jail!",
                dice_roll=dice,
                movement=movement,
                card_effect=effect,
                next_phase=TurnPhase.POST_ROLL,
                turn_complete=True,
            )

        if effect.new_position is not None:
            player.position = effect.new_position

        if effect.passed_go:
            player.cash += GO_SALARY

        if effect.get_jail_card:
            player.get_out_of_jail_cards += 1

        if effect.cash_change != 0:
            if effect.cash_change < 0:
                # Check bankruptcy
                bankruptcy = check_bankruptcy(player, -effect.cash_change)
                if bankruptcy.is_bankrupt:
                    return self._handle_bankruptcy(
                        player, -effect.cash_change, None, dice, movement
                    )
            player.cash += effect.cash_change

        # Handle player-to-player payments
        for other_id, amount in effect.payments_to_players.items():
            other = next((p for p in self.players if p.id == other_id), None)
            if other:
                other.cash += amount

        for other_id, amount in effect.collections_from_players.items():
            other = next((p for p in self.players if p.id == other_id), None)
            if other and other.cash >= amount:
                other.cash -= amount

        return ActionResult(
            success=True,
            message=f"Drew card: {effect.card_text}",
            dice_roll=dice,
            movement=movement,
            card_effect=effect,
            next_phase=TurnPhase.POST_ROLL,
        )

    def _handle_land_on_tax(
        self,
        player: PlayerModel,
        dice: DiceRoll,
        movement: MovementResult,
    ) -> ActionResult:
        """Handle landing on a tax space."""
        tax_amount = get_tax_amount(player.position)
        if tax_amount is None:
            tax_amount = 0

        bankruptcy = check_bankruptcy(player, tax_amount)
        if bankruptcy.is_bankrupt:
            return self._handle_bankruptcy(player, tax_amount, None, dice, movement)

        player.cash -= tax_amount
        space_name = get_space_name(player.position)

        return ActionResult(
            success=True,
            message=f"Rolled {dice.total} and landed on {space_name}. Paid ${tax_amount}.",
            dice_roll=dice,
            movement=movement,
            next_phase=TurnPhase.POST_ROLL,
        )

    def _handle_roll_for_doubles(self, player: PlayerModel) -> ActionResult:
        """Handle rolling for doubles to escape jail."""
        dice = roll_dice()
        result = roll_for_doubles(player, dice)

        if result.escaped:
            player.in_jail = False
            player.jail_turns = 0

            if result.method == JailEscapeMethod.FORCED_PAY:
                # Must pay the fine
                if player.cash < JAIL_FINE:
                    return self._handle_bankruptcy(player, JAIL_FINE, None, dice, None)
                player.cash -= JAIL_FINE

            # Move by dice roll
            movement = move_player(player.position, dice.total)
            player.position = movement.new_position

            if movement.passed_go:
                player.cash += GO_SALARY

            return self._handle_landing(player, dice, movement, 0)
        else:
            player.jail_turns += 1
            return ActionResult(
                success=True,
                message=result.message,
                dice_roll=dice,
                jail_result=result,
                next_phase=TurnPhase.POST_ROLL,
                turn_complete=True,
            )

    def _handle_pay_jail_fine(self, player: PlayerModel) -> ActionResult:
        """Handle paying jail fine."""
        result = pay_jail_fine(player)

        if result.escaped:
            player.cash -= JAIL_FINE
            player.in_jail = False
            player.jail_turns = 0
            return ActionResult(
                success=True,
                message=result.message,
                jail_result=result,
                next_phase=TurnPhase.PRE_ROLL,  # Can now roll
            )
        else:
            return ActionResult(
                success=False,
                message=result.message,
                jail_result=result,
            )

    def _handle_use_jail_card(self, player: PlayerModel) -> ActionResult:
        """Handle using get out of jail free card."""
        result = use_jail_card(player)

        if result.escaped:
            player.get_out_of_jail_cards -= 1
            player.in_jail = False
            player.jail_turns = 0
            return ActionResult(
                success=True,
                message=result.message,
                jail_result=result,
                next_phase=TurnPhase.PRE_ROLL,  # Can now roll
            )
        else:
            return ActionResult(
                success=False,
                message=result.message,
                jail_result=result,
            )

    def _handle_buy_property(
        self, player: PlayerModel, property_id: str | None
    ) -> ActionResult:
        """Handle buying a property."""
        if not property_id:
            return ActionResult(success=False, message="No property specified")

        can_buy, reason = can_buy_property(property_id, player, self.property_states)
        if not can_buy:
            return ActionResult(success=False, message=reason)

        price = get_property_price(property_id)
        player.cash -= price

        # Update property state
        prop_state = next(
            (ps for ps in self.property_states if ps.property_id == property_id),
            None,
        )
        if prop_state:
            prop_state.owner_id = player.id

        prop = get_property(property_id)
        return ActionResult(
            success=True,
            message=f"Bought {prop['name']} for ${price}",
            next_phase=TurnPhase.POST_ROLL,
        )

    def _handle_pass_property(
        self, player: PlayerModel, property_id: str | None
    ) -> ActionResult:
        """Handle passing on buying a property."""
        if not property_id:
            return ActionResult(success=False, message="No property specified")

        prop = get_property(property_id)
        return ActionResult(
            success=True,
            message=f"Passed on buying {prop['name']}",
            next_phase=TurnPhase.POST_ROLL,
        )

    def _handle_build_house(
        self, player: PlayerModel, property_id: str | None
    ) -> ActionResult:
        """Handle building a house."""
        if not property_id:
            return ActionResult(success=False, message="No property specified")

        can_build, reason = can_build_house(property_id, player, self.property_states)
        if not can_build:
            return ActionResult(success=False, message=reason)

        cost = get_house_cost(property_id)
        player.cash -= cost

        # Update property state
        prop_state = next(
            (ps for ps in self.property_states if ps.property_id == property_id),
            None,
        )
        if prop_state:
            prop_state.houses += 1

        prop = get_property(property_id)
        return ActionResult(
            success=True,
            message=f"Built house on {prop['name']} for ${cost}",
            next_phase=TurnPhase.POST_ROLL,
        )

    def _handle_build_hotel(
        self, player: PlayerModel, property_id: str | None
    ) -> ActionResult:
        """Handle building a hotel."""
        if not property_id:
            return ActionResult(success=False, message="No property specified")

        can_build, reason = can_build_hotel(property_id, player, self.property_states)
        if not can_build:
            return ActionResult(success=False, message=reason)

        cost = get_house_cost(property_id)
        player.cash -= cost

        # Update property state (hotel = 5 houses)
        prop_state = next(
            (ps for ps in self.property_states if ps.property_id == property_id),
            None,
        )
        if prop_state:
            prop_state.houses = 5

        prop = get_property(property_id)
        return ActionResult(
            success=True,
            message=f"Built hotel on {prop['name']} for ${cost}",
            next_phase=TurnPhase.POST_ROLL,
        )

    def _handle_end_turn(self, player: PlayerModel) -> ActionResult:
        """Handle ending the current turn."""
        # Check for doubles (another roll)
        if self._consecutive_doubles > 0 and not player.in_jail:
            return ActionResult(
                success=True,
                message="Rolled doubles! Roll again.",
                next_phase=TurnPhase.PRE_ROLL,
            )

        # Reset doubles counter
        self._consecutive_doubles = 0

        # Move to next player
        self._advance_to_next_player()

        # Check win condition
        if is_game_over(self.players):
            winner = get_winner(self.players)
            return ActionResult(
                success=True,
                message=f"Game over! {winner.name if winner else 'Unknown'} wins!",
                turn_complete=True,
                game_over=True,
                winner_id=winner.id if winner else None,
            )

        return ActionResult(
            success=True,
            message="Turn ended",
            next_phase=TurnPhase.PRE_ROLL,
            turn_complete=True,
        )

    def _handle_bankruptcy(
        self,
        player: PlayerModel,
        debt: int,
        creditor_id: UUID | None,
        dice: DiceRoll | None,
        movement: MovementResult | None,
    ) -> ActionResult:
        """Handle player bankruptcy."""
        player.is_bankrupt = True
        player.cash = 0

        if creditor_id is None:
            # Debt to bank - properties return to bank
            released = handle_bankruptcy_to_bank(player, self.property_states)
            for prop_id in released:
                prop_state = next(
                    (ps for ps in self.property_states if ps.property_id == prop_id),
                    None,
                )
                if prop_state:
                    prop_state.owner_id = None
                    prop_state.houses = 0
            message = f"{player.name} is bankrupt! All properties returned to the bank."
        else:
            # Debt to player - properties transfer
            transferred = handle_bankruptcy_to_player(
                player,
                next(p for p in self.players if p.id == creditor_id),
                self.property_states,
            )
            for prop_id in transferred:
                prop_state = next(
                    (ps for ps in self.property_states if ps.property_id == prop_id),
                    None,
                )
                if prop_state:
                    prop_state.owner_id = creditor_id
            message = f"{player.name} is bankrupt! All properties transferred to creditor."

        # Check win condition
        game_over = is_game_over(self.players)
        winner = get_winner(self.players) if game_over else None

        return ActionResult(
            success=True,
            message=message,
            dice_roll=dice,
            movement=movement,
            bankruptcy=check_bankruptcy(player, debt, creditor_id),
            turn_complete=True,
            game_over=game_over,
            winner_id=winner.id if winner else None,
        )

    def _advance_to_next_player(self) -> None:
        """Advance to the next non-bankrupt player."""
        active_players = [p for p in self.players if not p.is_bankrupt]
        if len(active_players) <= 1:
            return

        self.game.current_player_index = (
            self.game.current_player_index + 1
        ) % len(active_players)
        self.game.turn_number += 1
        self.game.turn_phase = TurnPhase.PRE_ROLL.value

    def update_phase(self, new_phase: TurnPhase) -> None:
        """Update the current turn phase."""
        self.game.turn_phase = new_phase.value
