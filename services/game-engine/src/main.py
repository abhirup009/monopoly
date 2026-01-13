"""FastAPI application entry point for Monopoly Game Engine."""

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.api.router import api_router
from src.config import get_settings
from src.database import close_db, init_db

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    """Application lifespan handler for startup and shutdown."""
    # Startup
    await init_db()
    yield
    # Shutdown
    await close_db()


app = FastAPI(
    title="Monopoly Game Engine",
    description="Core Monopoly game logic and state management API",
    version="0.1.0",
    lifespan=lifespan,
    docs_url="/docs" if settings.is_development else None,
    redoc_url="/redoc" if settings.is_development else None,
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"] if settings.is_development else [],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routes
app.include_router(api_router)


@app.get("/health")
async def health_check() -> dict[str, str]:
    """Basic health check endpoint."""
    return {"status": "healthy", "service": "game-engine"}


@app.get("/health/ready")
async def readiness_check() -> dict[str, str]:
    """Readiness check - verifies database connectivity."""
    try:
        await init_db()
        return {"status": "ready", "database": "connected"}
    except Exception as e:
        return {"status": "not_ready", "database": "disconnected", "error": str(e)}
