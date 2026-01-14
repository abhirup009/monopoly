"""REST API routes for AI Agent Service."""

import asyncio
import logging
from typing import Any
from uuid import UUID

from fastapi import APIRouter, BackgroundTasks, HTTPException
from pydantic import BaseModel

from src.agent.manager import AgentConfig, AgentManager, GameResult
from src.client.game_client import GameClient
from src.config import settings
from src.llm.ollama_client import OllamaClient
from src.prompts.personalities import list_personalities

logger = logging.getLogger(__name__)

router = APIRouter()

# Store for active games
active_games: dict[UUID, dict[str, Any]] = {}


class AgentRequest(BaseModel):
    """Request model for agent configuration."""

    name: str
    personality: str = "analytical"


class CreateGameRequest(BaseModel):
    """Request to create a new AI game."""

    agents: list[AgentRequest]
    turn_delay: float = 1.0
    action_delay: float = 0.5
    max_turns: int = 1000


class GameStatusResponse(BaseModel):
    """Response for game status."""

    game_id: UUID
    status: str
    current_turn: int | None = None
    current_player: str | None = None
    players: list[dict] | None = None
    message: str | None = None


class GameResultResponse(BaseModel):
    """Response for completed game."""

    game_id: UUID
    status: str
    winner_name: str | None
    total_turns: int
    final_standings: list[dict]


class HealthResponse(BaseModel):
    """Health check response."""

    status: str
    ollama: str
    model: str
    game_engine: str


class DecideRequest(BaseModel):
    """Request for AI decision on a turn."""

    player_id: str
    game_state: dict
    valid_actions: list[dict]


class DecideResponse(BaseModel):
    """Response with AI decision."""

    action: dict
    reasoning: str | None = None


# Store for orchestrator-managed agent sessions
orchestrator_sessions: dict[str, dict[str, Any]] = {}


@router.post("/games/{game_id}/decide", response_model=DecideResponse)
async def decide_action(game_id: UUID, request: DecideRequest) -> DecideResponse:
    """Make a decision for a player in an orchestrator-managed game.

    This endpoint is called by the Orchestrator to get AI decisions turn by turn.
    """
    from src.agent.monopoly_agent import MonopolyAgent
    from src.client.models import Action, GameState, ValidActions
    from src.llm.session import AgentSession

    session_key = f"{game_id}:{request.player_id}"

    # Get or create agent session for this player
    if session_key not in orchestrator_sessions:
        # Find player info from game state
        player_info = None
        for p in request.game_state.get("players", []):
            if str(p.get("id")) == request.player_id:
                player_info = p
                break

        if not player_info:
            raise HTTPException(status_code=400, detail="Player not found in game state")

        # Get personality config for temperature
        from src.prompts.personalities import get_personality
        personality_name = player_info.get("personality", "analytical")
        personality_config = get_personality(personality_name)

        # Create session for this agent
        orchestrator_sessions[session_key] = {
            "session": AgentSession(
                agent_id=UUID(request.player_id),
                personality=personality_name,
                temperature=personality_config.temperature,
            ),
            "player_name": player_info.get("name", "Unknown"),
            "personality": personality_name,
        }

    agent_info = orchestrator_sessions[session_key]

    # Get personality config for temperature
    from src.prompts.personalities import get_personality
    personality_config = get_personality(agent_info["personality"])

    # Create Ollama client
    ollama_client = OllamaClient(
        model=settings.ollama_model,
        host=settings.ollama_host,
    )

    # Check availability
    if not await ollama_client.is_available():
        raise HTTPException(
            status_code=503,
            detail=f"Ollama not available or model '{settings.ollama_model}' not found",
        )

    # Create temporary agent for decision
    agent = MonopolyAgent(
        player_id=UUID(request.player_id),
        player_name=agent_info["player_name"],
        personality=agent_info["personality"],
        ollama_client=ollama_client,
        session=agent_info["session"],
    )

    try:
        # Parse game state and valid actions
        from src.client.models import ValidAction
        game_state = GameState(**request.game_state)

        # Find current player
        current_idx = request.game_state.get("current_player_index", 0)
        players = request.game_state.get("players", [])
        player_id_str = players[current_idx]["id"] if players else request.player_id
        turn_phase = request.game_state.get("turn_phase", "pre_roll")

        valid_actions = ValidActions(
            player_id=UUID(player_id_str),
            turn_phase=turn_phase,
            actions=[
                ValidAction(
                    type=a.get("type"),
                    property_id=a.get("property_id"),
                    cost=a.get("cost"),
                )
                for a in request.valid_actions
            ]
        )

        # Get decision
        action = await agent.decide_action(game_state, valid_actions)

        return DecideResponse(
            action={
                "type": action.type.value,
                "property_id": action.property_id,
            },
            reasoning=None,
        )

    except Exception as e:
        logger.error(f"Decision error for {session_key}: {e}")
        # Return first valid action as fallback
        if request.valid_actions:
            return DecideResponse(
                action=request.valid_actions[0],
                reasoning="Error occurred, using default action",
            )
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/games", response_model=GameStatusResponse)
async def create_game(
    request: CreateGameRequest,
    background_tasks: BackgroundTasks,
) -> GameStatusResponse:
    """Create and start a new AI game.

    The game runs in the background. Use GET /games/{id} to check status.
    """
    if len(request.agents) < 2:
        raise HTTPException(
            status_code=400,
            detail="At least 2 agents are required",
        )

    if len(request.agents) > 6:
        raise HTTPException(
            status_code=400,
            detail="Maximum 6 agents allowed",
        )

    # Validate personalities
    valid_personalities = list_personalities()
    for agent in request.agents:
        if agent.personality not in valid_personalities:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid personality '{agent.personality}'. "
                f"Valid: {valid_personalities}",
            )

    # Create clients
    game_client = GameClient(settings.game_engine_url)
    ollama_client = OllamaClient(
        model=settings.ollama_model,
        host=settings.ollama_host,
    )

    # Check Ollama availability
    if not await ollama_client.is_available():
        raise HTTPException(
            status_code=503,
            detail=f"Ollama not available or model '{settings.ollama_model}' not found. "
            f"Run: ollama pull {settings.ollama_model}",
        )

    # Create agent manager
    manager = AgentManager(
        game_client=game_client,
        ollama_client=ollama_client,
        turn_delay=request.turn_delay,
        action_delay=request.action_delay,
    )

    # Create agent configs
    agent_configs = [
        AgentConfig(name=a.name, personality=a.personality)
        for a in request.agents
    ]

    try:
        # Create game
        game_id = await manager.create_game(agent_configs)

        # Start game
        await manager.start_game()

        # Store game info
        active_games[game_id] = {
            "manager": manager,
            "status": "running",
            "result": None,
            "max_turns": request.max_turns,
        }

        # Run game in background
        background_tasks.add_task(
            _run_game_background,
            game_id,
            manager,
            request.max_turns,
        )

        return GameStatusResponse(
            game_id=game_id,
            status="running",
            message=f"Game started with {len(request.agents)} agents",
        )

    except Exception as e:
        logger.error(f"Failed to create game: {e}")
        raise HTTPException(status_code=500, detail=str(e))


async def _run_game_background(
    game_id: UUID,
    manager: AgentManager,
    max_turns: int,
) -> None:
    """Run game in background task."""
    try:
        result = await manager.run_game(max_turns=max_turns)
        active_games[game_id]["status"] = "completed"
        active_games[game_id]["result"] = result
        logger.info(f"Game {game_id} completed. Winner: {result.winner_name}")
    except Exception as e:
        logger.error(f"Game {game_id} error: {e}")
        active_games[game_id]["status"] = "error"
        active_games[game_id]["error"] = str(e)
    finally:
        await manager.cleanup()


@router.get("/games/{game_id}", response_model=GameStatusResponse)
async def get_game_status(game_id: UUID) -> GameStatusResponse:
    """Get status of a game."""
    if game_id not in active_games:
        raise HTTPException(status_code=404, detail="Game not found")

    game_info = active_games[game_id]
    manager: AgentManager = game_info["manager"]

    if game_info["status"] == "completed":
        result: GameResult = game_info["result"]
        return GameStatusResponse(
            game_id=game_id,
            status="completed",
            current_turn=result.total_turns,
            players=result.final_standings,
            message=f"Winner: {result.winner_name}" if result.winner_name else "No winner",
        )

    if game_info["status"] == "error":
        return GameStatusResponse(
            game_id=game_id,
            status="error",
            message=game_info.get("error", "Unknown error"),
        )

    # Game is running - get current state
    try:
        game_state = await manager.game_client.get_game_state(game_id)
        current_player = game_state.players[game_state.current_player_index]

        players = [
            {
                "name": p.name,
                "cash": p.cash,
                "properties": sum(
                    1 for prop in game_state.properties
                    if prop.owner_id == p.id
                ),
                "bankrupt": p.is_bankrupt,
            }
            for p in game_state.players
        ]

        return GameStatusResponse(
            game_id=game_id,
            status="running",
            current_turn=game_state.turn_number,
            current_player=current_player.name,
            players=players,
        )
    except Exception as e:
        logger.error(f"Error getting game state: {e}")
        return GameStatusResponse(
            game_id=game_id,
            status="running",
            message="Unable to fetch current state",
        )


@router.get("/games/{game_id}/result", response_model=GameResultResponse)
async def get_game_result(game_id: UUID) -> GameResultResponse:
    """Get result of a completed game."""
    if game_id not in active_games:
        raise HTTPException(status_code=404, detail="Game not found")

    game_info = active_games[game_id]

    if game_info["status"] != "completed":
        raise HTTPException(
            status_code=400,
            detail=f"Game not completed. Status: {game_info['status']}",
        )

    result: GameResult = game_info["result"]
    return GameResultResponse(
        game_id=game_id,
        status="completed",
        winner_name=result.winner_name,
        total_turns=result.total_turns,
        final_standings=result.final_standings,
    )


@router.post("/games/{game_id}/stop")
async def stop_game(game_id: UUID) -> dict:
    """Stop a running game."""
    if game_id not in active_games:
        raise HTTPException(status_code=404, detail="Game not found")

    game_info = active_games[game_id]

    if game_info["status"] != "running":
        raise HTTPException(
            status_code=400,
            detail=f"Game not running. Status: {game_info['status']}",
        )

    manager: AgentManager = game_info["manager"]
    manager.stop()

    return {"message": "Stop requested", "game_id": str(game_id)}


@router.delete("/games/{game_id}")
async def delete_game(game_id: UUID) -> dict:
    """Delete a game from memory."""
    if game_id not in active_games:
        raise HTTPException(status_code=404, detail="Game not found")

    game_info = active_games[game_id]

    # Stop if running
    if game_info["status"] == "running":
        manager: AgentManager = game_info["manager"]
        manager.stop()
        await asyncio.sleep(0.5)  # Give time to stop

    del active_games[game_id]
    return {"message": "Game deleted", "game_id": str(game_id)}


@router.get("/games")
async def list_games() -> dict:
    """List all games."""
    games = []
    for game_id, info in active_games.items():
        games.append({
            "game_id": str(game_id),
            "status": info["status"],
        })
    return {"games": games, "count": len(games)}


@router.get("/health", response_model=HealthResponse)
async def health_check() -> HealthResponse:
    """Check service health."""
    # Check Ollama
    ollama_client = OllamaClient(
        model=settings.ollama_model,
        host=settings.ollama_host,
    )
    ollama_ok = await ollama_client.is_available()

    # Check Game Engine
    game_client = GameClient(settings.game_engine_url)
    game_engine_ok = await game_client.is_available()
    await game_client.close()

    overall_status = "healthy" if (ollama_ok and game_engine_ok) else "degraded"

    return HealthResponse(
        status=overall_status,
        ollama="connected" if ollama_ok else "unavailable",
        model=settings.ollama_model,
        game_engine="connected" if game_engine_ok else "unavailable",
    )


@router.get("/personalities")
async def get_personalities() -> dict:
    """Get available personalities."""
    from src.prompts.personalities import PERSONALITIES

    return {
        "personalities": [
            {
                "name": p.name,
                "temperature": p.temperature,
                "decision_style": p.decision_style,
            }
            for p in PERSONALITIES.values()
        ]
    }
