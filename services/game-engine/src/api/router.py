"""Main API router that aggregates all sub-routers."""

from fastapi import APIRouter

from src.api.games import router as games_router

api_router = APIRouter()

# Include game routes
api_router.include_router(games_router, prefix="/game", tags=["games"])
