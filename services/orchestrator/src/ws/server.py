"""Socket.IO server setup."""

import logging

import socketio

logger = logging.getLogger(__name__)

# Create Socket.IO server
sio = socketio.AsyncServer(
    async_mode="asgi",
    cors_allowed_origins="*",
    logger=False,
    engineio_logger=False,
)


@sio.event
async def connect(sid: str, environ: dict) -> None:
    """Handle client connection."""
    logger.info(f"Client connected: {sid}")


@sio.event
async def disconnect(sid: str) -> None:
    """Handle client disconnection."""
    logger.info(f"Client disconnected: {sid}")
