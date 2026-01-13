"""Socket.IO event handlers for client events."""

import logging
from typing import TYPE_CHECKING, Any

from src.ws.server import sio

if TYPE_CHECKING:
    from src.game.state import GameSessionManager

logger = logging.getLogger(__name__)

# Reference to game session manager (set during app startup)
_session_manager: "GameSessionManager | None" = None


def set_session_manager(manager: "GameSessionManager") -> None:
    """Set the game session manager reference.

    Args:
        manager: The game session manager instance.
    """
    global _session_manager
    _session_manager = manager


@sio.event
async def join_game(sid: str, data: dict[str, Any]) -> dict[str, Any]:
    """Join a game room as spectator.

    Args:
        sid: Socket ID.
        data: {"game_id": "uuid"}

    Returns:
        Status and current game state if available.
    """
    game_id = data.get("game_id")
    if not game_id:
        return {"success": False, "error": "game_id required"}

    room = f"game:{game_id}"
    await sio.enter_room(sid, room)
    logger.info(f"Client {sid} joined room {room}")

    # Send current state if game exists
    if _session_manager:
        session = _session_manager.get_session(game_id)
        if session:
            return {
                "success": True,
                "game_id": game_id,
                "state": session.current_state,
            }

    return {"success": True, "game_id": game_id, "state": None}


@sio.event
async def leave_game(sid: str, data: dict[str, Any]) -> dict[str, Any]:
    """Leave a game room.

    Args:
        sid: Socket ID.
        data: {"game_id": "uuid"}

    Returns:
        Status.
    """
    game_id = data.get("game_id")
    if not game_id:
        return {"success": False, "error": "game_id required"}

    room = f"game:{game_id}"
    await sio.leave_room(sid, room)
    logger.info(f"Client {sid} left room {room}")

    return {"success": True, "game_id": game_id}


@sio.event
async def set_speed(sid: str, data: dict[str, Any]) -> dict[str, Any]:
    """Change game speed.

    Args:
        sid: Socket ID.
        data: {"game_id": "uuid", "speed": "fast|normal|slow"}

    Returns:
        Status and new speed.
    """
    game_id = data.get("game_id")
    speed = data.get("speed")

    if not game_id or not speed:
        return {"success": False, "error": "game_id and speed required"}

    if speed not in ("fast", "normal", "slow"):
        return {"success": False, "error": "speed must be fast, normal, or slow"}

    if _session_manager:
        session = _session_manager.get_session(game_id)
        if session:
            session.set_speed(speed)
            logger.info(f"Game {game_id} speed set to {speed}")
            return {"success": True, "game_id": game_id, "speed": speed}

    return {"success": False, "error": "Game not found"}


@sio.event
async def get_state(sid: str, data: dict[str, Any]) -> dict[str, Any]:
    """Get current game state.

    Args:
        sid: Socket ID.
        data: {"game_id": "uuid"}

    Returns:
        Current game state.
    """
    game_id = data.get("game_id")
    if not game_id:
        return {"success": False, "error": "game_id required"}

    if _session_manager:
        session = _session_manager.get_session(game_id)
        if session:
            return {
                "success": True,
                "game_id": game_id,
                "state": session.current_state,
            }

    return {"success": False, "error": "Game not found"}
