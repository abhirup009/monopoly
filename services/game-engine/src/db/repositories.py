"""Database repositories for CRUD operations."""

import random
from uuid import UUID

from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from src.config import get_settings
from src.data.properties import ALL_PROPERTY_IDS
from src.db.models import (
    CardDeckModel,
    GameEventModel,
    GameModel,
    PlayerModel,
    PropertyStateModel,
)
from src.models.game import GameStatus, TurnPhase
from src.models.player import PlayerCreate

settings = get_settings()


class GameRepository:
    """Repository for game operations."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(self, players: list[PlayerCreate]) -> GameModel:
        """Create a new game with players."""
        # Create game
        game = GameModel(
            status=GameStatus.WAITING.value,
            current_player_index=0,
            turn_number=0,
            turn_phase=TurnPhase.PRE_ROLL.value,
        )
        self.session.add(game)
        await self.session.flush()

        # Create players
        for i, player_data in enumerate(players):
            player = PlayerModel(
                game_id=game.id,
                name=player_data.name,
                model=player_data.model,
                personality=player_data.personality,
                player_order=i,
                position=0,
                cash=settings.starting_cash,
            )
            self.session.add(player)

        # Initialize property states (all unowned)
        for property_id in ALL_PROPERTY_IDS:
            prop_state = PropertyStateModel(
                game_id=game.id,
                property_id=property_id,
                owner_id=None,
                houses=0,
            )
            self.session.add(prop_state)

        # Initialize card decks (shuffled)
        chance_order = list(range(1, 17))
        random.shuffle(chance_order)
        chance_deck = CardDeckModel(
            game_id=game.id,
            deck_type="chance",
            card_order=chance_order,
            current_index=0,
        )
        self.session.add(chance_deck)

        community_order = list(range(1, 17))
        random.shuffle(community_order)
        community_deck = CardDeckModel(
            game_id=game.id,
            deck_type="community_chest",
            card_order=community_order,
            current_index=0,
        )
        self.session.add(community_deck)

        await self.session.flush()
        return game

    async def get(self, game_id: UUID) -> GameModel | None:
        """Get a game by ID with all relationships loaded."""
        query = (
            select(GameModel)
            .where(GameModel.id == game_id)
            .options(
                selectinload(GameModel.players),
                selectinload(GameModel.property_states),
                selectinload(GameModel.card_decks),
            )
        )
        result = await self.session.execute(query)
        return result.scalar_one_or_none()

    async def update(self, game: GameModel) -> GameModel:
        """Update a game."""
        await self.session.flush()
        return game

    async def delete(self, game_id: UUID) -> bool:
        """Delete a game."""
        game = await self.get(game_id)
        if game:
            await self.session.delete(game)
            await self.session.flush()
            return True
        return False

    async def start_game(self, game: GameModel) -> GameModel:
        """Start a game (transition from waiting to in_progress)."""
        game.status = GameStatus.IN_PROGRESS.value
        game.turn_number = 1
        game.turn_phase = TurnPhase.AWAITING_ROLL.value
        await self.session.flush()
        return game


class PlayerRepository:
    """Repository for player operations."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def get(self, player_id: UUID) -> PlayerModel | None:
        """Get a player by ID."""
        query = select(PlayerModel).where(PlayerModel.id == player_id)
        result = await self.session.execute(query)
        return result.scalar_one_or_none()

    async def get_by_game(self, game_id: UUID) -> list[PlayerModel]:
        """Get all players in a game."""
        query = (
            select(PlayerModel)
            .where(PlayerModel.game_id == game_id)
            .order_by(PlayerModel.player_order)
        )
        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def get_active_players(self, game_id: UUID) -> list[PlayerModel]:
        """Get all non-bankrupt players in a game."""
        query = (
            select(PlayerModel)
            .where(
                and_(
                    PlayerModel.game_id == game_id,
                    PlayerModel.is_bankrupt.is_(False),
                )
            )
            .order_by(PlayerModel.player_order)
        )
        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def update(self, player: PlayerModel) -> PlayerModel:
        """Update a player."""
        await self.session.flush()
        return player


class PropertyStateRepository:
    """Repository for property state operations."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def get(self, game_id: UUID, property_id: str) -> PropertyStateModel | None:
        """Get property state by game and property ID."""
        query = select(PropertyStateModel).where(
            and_(
                PropertyStateModel.game_id == game_id,
                PropertyStateModel.property_id == property_id,
            )
        )
        result = await self.session.execute(query)
        return result.scalar_one_or_none()

    async def get_by_game(self, game_id: UUID) -> list[PropertyStateModel]:
        """Get all property states for a game."""
        query = select(PropertyStateModel).where(PropertyStateModel.game_id == game_id)
        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def get_by_owner(self, owner_id: UUID) -> list[PropertyStateModel]:
        """Get all properties owned by a player."""
        query = select(PropertyStateModel).where(PropertyStateModel.owner_id == owner_id)
        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def update(self, prop_state: PropertyStateModel) -> PropertyStateModel:
        """Update a property state."""
        await self.session.flush()
        return prop_state


class CardDeckRepository:
    """Repository for card deck operations."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def get(self, game_id: UUID, deck_type: str) -> CardDeckModel | None:
        """Get a card deck by game and type."""
        query = select(CardDeckModel).where(
            and_(
                CardDeckModel.game_id == game_id,
                CardDeckModel.deck_type == deck_type,
            )
        )
        result = await self.session.execute(query)
        return result.scalar_one_or_none()

    async def draw_card(self, deck: CardDeckModel) -> int:
        """Draw the next card from the deck, returning the card ID."""
        card_id = deck.card_order[deck.current_index]
        deck.current_index = (deck.current_index + 1) % len(deck.card_order)
        await self.session.flush()
        return card_id

    async def update(self, deck: CardDeckModel) -> CardDeckModel:
        """Update a card deck."""
        await self.session.flush()
        return deck


class GameEventRepository:
    """Repository for game event operations."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(
        self,
        game_id: UUID,
        turn_number: int,
        event_type: str,
        event_data: dict,
        player_id: UUID | None = None,
    ) -> GameEventModel:
        """Create a new game event."""
        event = GameEventModel(
            game_id=game_id,
            player_id=player_id,
            turn_number=turn_number,
            event_type=event_type,
            event_data=event_data,
        )
        self.session.add(event)
        await self.session.flush()
        return event

    async def get_by_game(
        self, game_id: UUID, limit: int = 50, offset: int = 0
    ) -> list[GameEventModel]:
        """Get events for a game."""
        query = (
            select(GameEventModel)
            .where(GameEventModel.game_id == game_id)
            .order_by(GameEventModel.created_at.desc())
            .limit(limit)
            .offset(offset)
        )
        result = await self.session.execute(query)
        return list(result.scalars().all())
