"""REST API routes for the Orchestrator Service."""

import logging
from typing import Any
from uuid import UUID

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from src.game.state import GameSpeed

logger = logging.getLogger(__name__)

router = APIRouter()


# Request/Response models
class AgentConfig(BaseModel):
    """Agent configuration for game creation."""

    name: str = Field(..., description="Agent display name")
    personality: str = Field(..., description="Agent personality type")
    model: str = Field(default="llama3.1:8b", description="LLM model to use")


class GameSettings(BaseModel):
    """Game settings for creation."""

    speed: str = Field(default="normal", description="Game speed: fast, normal, slow")
    turn_timeout: float = Field(default=30.0, description="Turn timeout in seconds")


class CreateGameRequest(BaseModel):
    """Request body for creating a new game."""

    agents: list[AgentConfig] = Field(..., min_length=2, max_length=6)
    settings: GameSettings = Field(default_factory=GameSettings)


class SpeedRequest(BaseModel):
    """Request body for changing game speed."""

    speed: str = Field(..., description="Game speed: fast, normal, slow")


class GameResponse(BaseModel):
    """Standard game response."""

    game_id: str
    status: str
    message: str | None = None


class HealthResponse(BaseModel):
    """Health check response."""

    status: str
    game_engine: str
    ai_agent: str


# These will be set during app startup
_game_engine = None
_ai_agent = None
_session_manager = None
_game_manager = None


def set_dependencies(game_engine, ai_agent, session_manager, game_manager):
    """Set route dependencies (called during app startup)."""
    global _game_engine, _ai_agent, _session_manager, _game_manager
    _game_engine = game_engine
    _ai_agent = ai_agent
    _session_manager = session_manager
    _game_manager = game_manager


@router.get("/health", response_model=HealthResponse)
async def health_check() -> dict[str, Any]:
    """Check service health and dependency status."""
    game_engine_status = "unknown"
    ai_agent_status = "unknown"

    if _game_engine:
        try:
            await _game_engine.health_check()
            game_engine_status = "healthy"
        except Exception:
            game_engine_status = "unhealthy"

    if _ai_agent:
        try:
            await _ai_agent.health_check()
            ai_agent_status = "healthy"
        except Exception:
            ai_agent_status = "unhealthy"

    return {
        "status": "healthy",
        "game_engine": game_engine_status,
        "ai_agent": ai_agent_status,
    }


@router.post("/games", response_model=GameResponse)
async def create_game(request: CreateGameRequest) -> dict[str, Any]:
    """Create and start a new game.

    Creates a game in the Game Engine, registers agents with AI Agent service,
    and starts the game loop.
    """
    if not all([_game_engine, _ai_agent, _session_manager, _game_manager]):
        raise HTTPException(status_code=503, detail="Service not initialized")

    try:
        # Prepare player data for Game Engine
        players = [
            {
                "name": agent.name,
                "model": agent.model,
                "personality": agent.personality,
            }
            for agent in request.agents
        ]

        # Create game in Game Engine
        game_data = await _game_engine.create_game(players)
        game_id = UUID(game_data["id"])
        logger.info(f"Created game {game_id} in Game Engine")

        # Start game in Game Engine
        await _game_engine.start_game(game_id)
        logger.info(f"Started game {game_id} in Game Engine")

        # Register with AI Agent service
        agents_config = [
            {
                "player_id": str(p["id"]),
                "name": p["name"],
                "personality": p["personality"],
            }
            for p in game_data["players"]
        ]
        await _ai_agent.create_game(game_id, agents_config)
        logger.info(f"Registered game {game_id} with AI Agent service")

        # Create session and start game loop
        speed = GameSpeed(request.settings.speed)
        session = _session_manager.create_session(
            game_id=game_id,
            agents=agents_config,
            speed=speed,
        )
        await _game_manager.start_game(session)
        logger.info(f"Started game loop for {game_id}")

        return {
            "game_id": str(game_id),
            "status": "running",
            "message": "Game created and started successfully",
        }

    except Exception as e:
        logger.error(f"Error creating game: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/games/{game_id}")
async def get_game_status(game_id: str) -> dict[str, Any]:
    """Get current game status and state."""
    if not _session_manager or not _game_manager:
        raise HTTPException(status_code=503, detail="Service not initialized")

    session = _session_manager.get_session(game_id)
    if not session:
        raise HTTPException(status_code=404, detail="Game not found")

    is_running = _game_manager.is_game_running(game_id)

    return {
        "game_id": game_id,
        "status": "running" if is_running else "stopped",
        "is_running": is_running,
        "turn_count": session.turn_count,
        "speed": session.speed.value,
        "state": session.current_state,
    }


@router.get("/games/{game_id}/result")
async def get_game_result(game_id: str) -> dict[str, Any]:
    """Get completed game result."""
    if not _session_manager or not _game_engine:
        raise HTTPException(status_code=503, detail="Service not initialized")

    # Get state from Game Engine
    try:
        state = await _game_engine.get_state(UUID(game_id))
    except Exception:
        raise HTTPException(status_code=404, detail="Game not found")

    if state.get("status") != "completed":
        raise HTTPException(status_code=400, detail="Game not completed")

    return {
        "game_id": game_id,
        "status": "completed",
        "winner_id": state.get("winner_id"),
        "final_state": state,
    }


@router.post("/games/{game_id}/stop", response_model=GameResponse)
async def stop_game(game_id: str) -> dict[str, Any]:
    """Stop a running game."""
    if not _session_manager or not _game_manager:
        raise HTTPException(status_code=503, detail="Service not initialized")

    session = _session_manager.get_session(game_id)
    if not session:
        raise HTTPException(status_code=404, detail="Game not found")

    stopped = await _game_manager.stop_game(game_id)
    if stopped:
        return {
            "game_id": game_id,
            "status": "stopped",
            "message": "Game stopped successfully",
        }

    return {
        "game_id": game_id,
        "status": "not_running",
        "message": "Game was not running",
    }


@router.post("/games/{game_id}/speed", response_model=GameResponse)
async def set_game_speed(game_id: str, request: SpeedRequest) -> dict[str, Any]:
    """Set game speed."""
    if not _session_manager:
        raise HTTPException(status_code=503, detail="Service not initialized")

    if request.speed not in ("fast", "normal", "slow"):
        raise HTTPException(
            status_code=400, detail="Speed must be fast, normal, or slow"
        )

    session = _session_manager.get_session(game_id)
    if not session:
        raise HTTPException(status_code=404, detail="Game not found")

    session.set_speed(request.speed)

    return {
        "game_id": game_id,
        "status": "updated",
        "message": f"Speed set to {request.speed}",
    }


@router.get("/games")
async def list_games() -> dict[str, Any]:
    """List all active game sessions."""
    if not _session_manager:
        raise HTTPException(status_code=503, detail="Service not initialized")

    sessions = _session_manager.list_sessions()
    return {
        "count": len(sessions),
        "games": sessions,
    }
