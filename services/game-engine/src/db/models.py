"""SQLAlchemy ORM models."""

from datetime import datetime
from uuid import uuid4

from sqlalchemy import (
    ARRAY,
    JSON,
    Boolean,
    DateTime,
    ForeignKey,
    Integer,
    String,
    func,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.database import Base
from src.models.game import GameStatus, TurnPhase


class GameModel(Base):
    """Game ORM model."""

    __tablename__ = "games"

    id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    status: Mapped[str] = mapped_column(String(20), default=GameStatus.WAITING.value)
    current_player_index: Mapped[int] = mapped_column(Integer, default=0)
    turn_number: Mapped[int] = mapped_column(Integer, default=0)
    turn_phase: Mapped[str] = mapped_column(String(30), default=TurnPhase.PRE_ROLL.value)
    doubles_count: Mapped[int] = mapped_column(Integer, default=0)
    last_dice_roll: Mapped[list[int] | None] = mapped_column(ARRAY(Integer), nullable=True)
    winner_id: Mapped[UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    # Relationships
    players: Mapped[list["PlayerModel"]] = relationship(
        "PlayerModel", back_populates="game", cascade="all, delete-orphan"
    )
    property_states: Mapped[list["PropertyStateModel"]] = relationship(
        "PropertyStateModel", back_populates="game", cascade="all, delete-orphan"
    )
    card_decks: Mapped[list["CardDeckModel"]] = relationship(
        "CardDeckModel", back_populates="game", cascade="all, delete-orphan"
    )
    events: Mapped[list["GameEventModel"]] = relationship(
        "GameEventModel", back_populates="game", cascade="all, delete-orphan"
    )


class PlayerModel(Base):
    """Player ORM model."""

    __tablename__ = "players"

    id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    game_id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("games.id", ondelete="CASCADE"), nullable=False
    )
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    model: Mapped[str] = mapped_column(String(50), nullable=False)
    personality: Mapped[str] = mapped_column(String(50), nullable=False)
    player_order: Mapped[int] = mapped_column(Integer, nullable=False)
    position: Mapped[int] = mapped_column(Integer, default=0)
    cash: Mapped[int] = mapped_column(Integer, default=1500)
    in_jail: Mapped[bool] = mapped_column(Boolean, default=False)
    jail_turns: Mapped[int] = mapped_column(Integer, default=0)
    get_out_of_jail_cards: Mapped[int] = mapped_column(Integer, default=0)
    is_bankrupt: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    game: Mapped["GameModel"] = relationship("GameModel", back_populates="players")
    owned_properties: Mapped[list["PropertyStateModel"]] = relationship(
        "PropertyStateModel", back_populates="owner"
    )


class PropertyStateModel(Base):
    """Property state ORM model."""

    __tablename__ = "property_states"

    id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    game_id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("games.id", ondelete="CASCADE"), nullable=False
    )
    property_id: Mapped[str] = mapped_column(String(50), nullable=False)
    owner_id: Mapped[UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("players.id", ondelete="SET NULL"), nullable=True
    )
    houses: Mapped[int] = mapped_column(Integer, default=0)

    # Relationships
    game: Mapped["GameModel"] = relationship("GameModel", back_populates="property_states")
    owner: Mapped["PlayerModel | None"] = relationship("PlayerModel", back_populates="owned_properties")


class CardDeckModel(Base):
    """Card deck ORM model."""

    __tablename__ = "card_decks"

    id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    game_id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("games.id", ondelete="CASCADE"), nullable=False
    )
    deck_type: Mapped[str] = mapped_column(String(20), nullable=False)
    card_order: Mapped[list[int]] = mapped_column(ARRAY(Integer), nullable=False)
    current_index: Mapped[int] = mapped_column(Integer, default=0)

    # Relationships
    game: Mapped["GameModel"] = relationship("GameModel", back_populates="card_decks")


class GameEventModel(Base):
    """Game event ORM model."""

    __tablename__ = "game_events"

    id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    game_id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("games.id", ondelete="CASCADE"), nullable=False
    )
    player_id: Mapped[UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("players.id", ondelete="SET NULL"), nullable=True
    )
    turn_number: Mapped[int] = mapped_column(Integer, nullable=False)
    event_type: Mapped[str] = mapped_column(String(50), nullable=False)
    event_data: Mapped[dict] = mapped_column(JSON, default={})
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    game: Mapped["GameModel"] = relationship("GameModel", back_populates="events")
