"""Game API endpoints."""

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.database import get_session
from src.db.repositories import (
    CardDeckRepository,
    GameEventRepository,
    GameRepository,
    PlayerRepository,
    PropertyStateRepository,
)
from src.engine.game_manager import (
    ActionType as EngineActionType,
    GameManager,
    TurnPhase as EngineTurnPhase,
)
from src.models.actions import (
    Action,
    ActionRequest,
    ActionResult,
    ActionType,
    AvailableAction,
    ValidActions,
)
from src.models.game import GameCreate, GameState, GameStatus, TurnPhase
from src.models.player import Player
from src.models.property import PropertyState

router = APIRouter()


@router.post("", response_model=dict, status_code=status.HTTP_201_CREATED)
async def create_game(
    request: GameCreate,
    session: AsyncSession = Depends(get_session),
) -> dict:
    """Create a new game with player configurations.

    Args:
        request: Game creation request with player details
        session: Database session

    Returns:
        Created game info
    """
    if len(request.players) < 2:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="At least 2 players required",
        )
    if len(request.players) > 6:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Maximum 6 players allowed",
        )

    repo = GameRepository(session)
    game = await repo.create(request.players)
    await session.commit()

    return {
        "id": str(game.id),
        "status": game.status,
        "player_count": len(request.players),
        "message": f"Game created with {len(request.players)} players. Call POST /game/{game.id}/start to begin.",
    }


@router.get("/{game_id}", response_model=GameState)
async def get_game(
    game_id: UUID,
    session: AsyncSession = Depends(get_session),
) -> GameState:
    """Get the full current state of a game.

    Args:
        game_id: The game ID
        session: Database session

    Returns:
        Full game state
    """
    repo = GameRepository(session)
    game = await repo.get(game_id)

    if not game:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Game {game_id} not found",
        )

    # Convert to response model
    players = [
        Player(
            id=p.id,
            game_id=p.game_id,
            name=p.name,
            model=p.model,
            personality=p.personality,
            player_order=p.player_order,
            position=p.position,
            cash=p.cash,
            in_jail=p.in_jail,
            jail_turns=p.jail_turns,
            get_out_of_jail_cards=p.get_out_of_jail_cards,
            is_bankrupt=p.is_bankrupt,
            created_at=p.created_at,
        )
        for p in game.players
    ]

    properties = [
        PropertyState(
            property_id=ps.property_id,
            owner_id=ps.owner_id,
            houses=ps.houses,
        )
        for ps in game.property_states
    ]

    return GameState(
        id=game.id,
        status=GameStatus(game.status),
        current_player_index=game.current_player_index,
        turn_number=game.turn_number,
        turn_phase=TurnPhase(game.turn_phase),
        doubles_count=game.doubles_count,
        last_dice_roll=game.last_dice_roll,
        players=players,
        properties=properties,
        winner_id=game.winner_id,
        created_at=game.created_at,
        updated_at=game.updated_at,
    )


@router.post("/{game_id}/start", response_model=dict)
async def start_game(
    game_id: UUID,
    session: AsyncSession = Depends(get_session),
) -> dict:
    """Start a game that is in 'waiting' status.

    Args:
        game_id: The game ID
        session: Database session

    Returns:
        Game start confirmation
    """
    repo = GameRepository(session)
    game = await repo.get(game_id)

    if not game:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Game {game_id} not found",
        )

    if game.status != GameStatus.WAITING.value:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Game is already {game.status}",
        )

    if len(game.players) < 2:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Need at least 2 players to start",
        )

    await repo.start_game(game)
    await session.commit()

    # Get first player
    first_player = sorted(game.players, key=lambda p: p.player_order)[0]

    return {
        "id": str(game.id),
        "status": "in_progress",
        "turn_number": 1,
        "current_player": first_player.name,
        "message": f"Game started! {first_player.name}'s turn.",
    }


@router.get("/{game_id}/actions", response_model=ValidActions)
async def get_valid_actions(
    game_id: UUID,
    session: AsyncSession = Depends(get_session),
) -> ValidActions:
    """Get valid actions for the current player.

    Args:
        game_id: The game ID
        session: Database session

    Returns:
        List of valid actions
    """
    game_repo = GameRepository(session)
    game = await game_repo.get(game_id)

    if not game:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Game {game_id} not found",
        )

    if game.status != GameStatus.IN_PROGRESS.value:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Game is {game.status}, not in progress",
        )

    # Create game manager
    players = sorted(game.players, key=lambda p: p.player_order)
    active_players = [p for p in players if not p.is_bankrupt]

    manager = GameManager(game, list(active_players), list(game.property_states))

    # Get current player
    current_player = manager.current_player

    # Get valid actions
    valid_actions = manager.get_valid_actions()

    return ValidActions(
        game_id=game.id,
        player_id=current_player.id,
        player_name=current_player.name,
        turn_phase=game.turn_phase,
        actions=[
            AvailableAction(
                type=ActionType(action.action_type.value),
                property_id=action.property_id,
                cost=action.cost,
                description=action.description,
            )
            for action in valid_actions
        ],
    )


@router.post("/{game_id}/action", response_model=ActionResult)
async def execute_action(
    game_id: UUID,
    request: ActionRequest,
    session: AsyncSession = Depends(get_session),
) -> ActionResult:
    """Execute a game action for a player.

    Args:
        game_id: The game ID
        request: Action request with player ID and action
        session: Database session

    Returns:
        Result of the action
    """
    game_repo = GameRepository(session)
    event_repo = GameEventRepository(session)
    game = await game_repo.get(game_id)

    if not game:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Game {game_id} not found",
        )

    if game.status != GameStatus.IN_PROGRESS.value:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Game is {game.status}, not in progress",
        )

    # Get players and property states
    players = sorted(game.players, key=lambda p: p.player_order)
    active_players = [p for p in players if not p.is_bankrupt]
    property_states = list(game.property_states)

    # Create game manager
    manager = GameManager(game, active_players, property_states)

    # Verify it's the correct player's turn
    current_player = manager.current_player
    if current_player.id != request.player_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Not {request.player_id}'s turn. Current player: {current_player.id}",
        )

    # Execute the action
    engine_action_type = EngineActionType(request.action.type.value)
    result = manager.execute_action(engine_action_type, request.action.property_id)

    # Update game state
    if result.next_phase:
        game.turn_phase = result.next_phase.value

    if result.dice_roll:
        game.last_dice_roll = result.dice_roll.to_list()
        if result.dice_roll.is_doubles:
            game.doubles_count += 1
        else:
            game.doubles_count = 0

    if result.game_over:
        game.status = GameStatus.COMPLETED.value
        game.winner_id = result.winner_id

    # Log the event
    await event_repo.create(
        game_id=game.id,
        turn_number=game.turn_number,
        event_type=request.action.type.value,
        event_data={
            "player_id": str(request.player_id),
            "action": request.action.model_dump(),
            "result": result.message,
            "success": result.success,
        },
        player_id=request.player_id,
    )

    await session.commit()

    # Build response
    return ActionResult(
        success=result.success,
        message=result.message,
        action_type=request.action.type,
        dice_roll=result.dice_roll.to_list() if result.dice_roll else None,
        new_position=result.movement.new_position if result.movement else None,
        amount_paid=result.rent_paid if result.rent_paid > 0 else None,
        property_id=request.action.property_id,
        card_drawn=result.card_effect.card_text if result.card_effect else None,
        next_phase=result.next_phase.value if result.next_phase else None,
        game_over=result.game_over,
        winner_id=result.winner_id,
    )


@router.get("/{game_id}/events", response_model=list[dict])
async def get_events(
    game_id: UUID,
    limit: int = 50,
    offset: int = 0,
    session: AsyncSession = Depends(get_session),
) -> list[dict]:
    """Get game event history.

    Args:
        game_id: The game ID
        limit: Maximum events to return
        offset: Offset for pagination
        session: Database session

    Returns:
        List of game events
    """
    game_repo = GameRepository(session)
    event_repo = GameEventRepository(session)

    game = await game_repo.get(game_id)
    if not game:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Game {game_id} not found",
        )

    events = await event_repo.get_by_game(game_id, limit=limit, offset=offset)

    return [
        {
            "id": str(e.id),
            "player_id": str(e.player_id) if e.player_id else None,
            "turn_number": e.turn_number,
            "event_type": e.event_type,
            "event_data": e.event_data,
            "created_at": e.created_at.isoformat(),
        }
        for e in events
    ]


@router.delete("/{game_id}", response_model=dict)
async def delete_game(
    game_id: UUID,
    session: AsyncSession = Depends(get_session),
) -> dict:
    """Delete a game.

    Args:
        game_id: The game ID
        session: Database session

    Returns:
        Deletion confirmation
    """
    repo = GameRepository(session)
    deleted = await repo.delete(game_id)

    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Game {game_id} not found",
        )

    await session.commit()

    return {
        "id": str(game_id),
        "deleted": True,
        "message": f"Game {game_id} deleted successfully",
    }
