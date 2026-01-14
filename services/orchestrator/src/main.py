"""Main entry point for the Orchestrator Service."""

import logging
from contextlib import asynccontextmanager

import socketio
import uvicorn
from fastapi import FastAPI

from src.api.routes import router, set_dependencies
from src.clients.ai_agent import AIAgentClient
from src.clients.game_engine import GameEngineClient
from src.config import get_settings
from src.game.loop import GameManager
from src.game.state import GameSessionManager
from src.ws.events import EventBus
from src.ws.handlers import set_session_manager
from src.ws.server import sio

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# Global instances
game_engine_client: GameEngineClient | None = None
ai_agent_client: AIAgentClient | None = None
session_manager: GameSessionManager | None = None
game_manager: GameManager | None = None
event_bus: EventBus | None = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager."""
    global game_engine_client, ai_agent_client, session_manager, game_manager, event_bus

    settings = get_settings()
    logger.info("Starting Orchestrator Service...")

    # Initialize clients
    game_engine_client = GameEngineClient()
    ai_agent_client = AIAgentClient()

    # Initialize event bus
    event_bus = EventBus(sio)

    # Initialize session manager
    session_manager = GameSessionManager()
    set_session_manager(session_manager)

    # Initialize game manager
    game_manager = GameManager(
        game_engine=game_engine_client,
        ai_agent=ai_agent_client,
        event_bus=event_bus,
        turn_timeout=settings.turn_timeout,
    )

    # Set route dependencies
    set_dependencies(game_engine_client, ai_agent_client, session_manager, game_manager)

    logger.info(f"Game Engine URL: {settings.game_engine_url}")
    logger.info(f"AI Agent URL: {settings.ai_agent_url}")
    logger.info("Orchestrator Service started")

    yield

    # Cleanup
    logger.info("Shutting down Orchestrator Service...")
    if game_engine_client:
        await game_engine_client.close()
    if ai_agent_client:
        await ai_agent_client.close()
    logger.info("Orchestrator Service stopped")


# Create FastAPI app
app = FastAPI(
    title="Monopoly Orchestrator",
    description="Game coordination and WebSocket server for Monopoly Arena",
    version="0.1.0",
    lifespan=lifespan,
)

# Include API routes
app.include_router(router)

# Create Socket.IO ASGI app and mount it
socket_app = socketio.ASGIApp(sio, other_asgi_app=app)


def create_app() -> socketio.ASGIApp:
    """Create and return the ASGI application."""
    return socket_app


if __name__ == "__main__":
    settings = get_settings()
    uvicorn.run(
        "src.main:socket_app",
        host=settings.host,
        port=settings.port,
        reload=True,
    )
