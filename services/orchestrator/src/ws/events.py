"""Event bus for internal coordination and Socket.IO broadcasting."""

import logging
from collections.abc import Callable
from typing import Any
from uuid import UUID

import socketio

logger = logging.getLogger(__name__)


class EventBus:
    """Event bus for coordinating internal events and broadcasting to clients."""

    def __init__(self, sio: socketio.AsyncServer):
        """Initialize the event bus.

        Args:
            sio: Socket.IO async server instance.
        """
        self.sio = sio
        self._handlers: dict[str, list[Callable]] = {}

    def on(self, event: str, handler: Callable) -> None:
        """Register an internal event handler.

        Args:
            event: Event name.
            handler: Async callable to handle the event.
        """
        self._handlers.setdefault(event, []).append(handler)
        logger.debug(f"Registered handler for event: {event}")

    def off(self, event: str, handler: Callable) -> None:
        """Unregister an internal event handler.

        Args:
            event: Event name.
            handler: Handler to remove.
        """
        if event in self._handlers:
            try:
                self._handlers[event].remove(handler)
            except ValueError:
                pass

    async def emit(
        self,
        event: str,
        data: dict[str, Any],
        game_id: UUID | None = None,
        broadcast: bool = True,
    ) -> None:
        """Emit an event to handlers and optionally to Socket.IO clients.

        Args:
            event: Event name.
            data: Event data.
            game_id: Game ID for room broadcasting.
            broadcast: Whether to broadcast to Socket.IO clients.
        """
        # Call internal handlers
        for handler in self._handlers.get(event, []):
            try:
                await handler(data)
            except Exception as e:
                logger.error(f"Error in event handler for {event}: {e}")

        # Broadcast to Socket.IO room
        if broadcast and game_id:
            room = f"game:{game_id}"
            await self.sio.emit(event, data, room=room)
            logger.debug(f"Broadcast {event} to room {room}")

    async def emit_to_sid(self, event: str, data: dict[str, Any], sid: str) -> None:
        """Emit an event to a specific client.

        Args:
            event: Event name.
            data: Event data.
            sid: Socket ID of the client.
        """
        await self.sio.emit(event, data, room=sid)
