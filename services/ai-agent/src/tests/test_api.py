"""Tests for API endpoints."""

from unittest.mock import AsyncMock, patch

import pytest
from fastapi.testclient import TestClient

from src.main import app


@pytest.fixture
def client():
    """Create test client."""
    return TestClient(app)


class TestHealthEndpoint:
    """Tests for health check endpoint."""

    def test_health_check_structure(self, client):
        """Test health check returns expected structure."""
        with patch("src.api.routes.OllamaClient") as mock_ollama, \
             patch("src.api.routes.GameClient") as mock_game:
            # Mock availability checks
            mock_ollama_instance = AsyncMock()
            mock_ollama_instance.is_available = AsyncMock(return_value=False)
            mock_ollama.return_value = mock_ollama_instance

            mock_game_instance = AsyncMock()
            mock_game_instance.is_available = AsyncMock(return_value=False)
            mock_game_instance.close = AsyncMock()
            mock_game.return_value = mock_game_instance

            response = client.get("/health")

            assert response.status_code == 200
            data = response.json()
            assert "status" in data
            assert "ollama" in data
            assert "model" in data
            assert "game_engine" in data


class TestPersonalitiesEndpoint:
    """Tests for personalities endpoint."""

    def test_get_personalities(self, client):
        """Test getting available personalities."""
        response = client.get("/personalities")

        assert response.status_code == 200
        data = response.json()
        assert "personalities" in data
        assert len(data["personalities"]) == 3

        names = {p["name"] for p in data["personalities"]}
        assert names == {"aggressive", "analytical", "chaotic"}

    def test_personalities_have_expected_fields(self, client):
        """Test that personalities have expected fields."""
        response = client.get("/personalities")
        data = response.json()

        for personality in data["personalities"]:
            assert "name" in personality
            assert "temperature" in personality
            assert "decision_style" in personality


class TestListGamesEndpoint:
    """Tests for list games endpoint."""

    def test_list_games_empty(self, client):
        """Test listing games when none exist."""
        # Clear any existing games
        from src.api.routes import active_games
        active_games.clear()

        response = client.get("/games")

        assert response.status_code == 200
        data = response.json()
        assert "games" in data
        assert "count" in data
        assert data["count"] == 0


class TestCreateGameValidation:
    """Tests for create game validation."""

    def test_create_game_requires_agents(self, client):
        """Test that create game requires at least 2 agents."""
        response = client.post("/games", json={"agents": []})
        assert response.status_code == 400
        assert "at least 2" in response.json()["detail"].lower()

    def test_create_game_rejects_single_agent(self, client):
        """Test that create game rejects single agent."""
        response = client.post("/games", json={
            "agents": [{"name": "Solo", "personality": "aggressive"}]
        })
        assert response.status_code == 400

    def test_create_game_rejects_too_many_agents(self, client):
        """Test that create game rejects more than 6 agents."""
        agents = [{"name": f"Agent{i}", "personality": "aggressive"} for i in range(7)]
        response = client.post("/games", json={"agents": agents})
        assert response.status_code == 400
        assert "maximum 6" in response.json()["detail"].lower()

    def test_create_game_rejects_invalid_personality(self, client):
        """Test that create game rejects invalid personality."""
        response = client.post("/games", json={
            "agents": [
                {"name": "Agent1", "personality": "aggressive"},
                {"name": "Agent2", "personality": "invalid_personality"},
            ]
        })
        assert response.status_code == 400
        assert "invalid personality" in response.json()["detail"].lower()


class TestGameNotFound:
    """Tests for game not found scenarios."""

    def test_get_game_not_found(self, client):
        """Test getting non-existent game."""
        response = client.get("/games/00000000-0000-0000-0000-000000000000")
        assert response.status_code == 404

    def test_stop_game_not_found(self, client):
        """Test stopping non-existent game."""
        response = client.post("/games/00000000-0000-0000-0000-000000000000/stop")
        assert response.status_code == 404

    def test_delete_game_not_found(self, client):
        """Test deleting non-existent game."""
        response = client.delete("/games/00000000-0000-0000-0000-000000000000")
        assert response.status_code == 404

    def test_get_result_not_found(self, client):
        """Test getting result of non-existent game."""
        response = client.get("/games/00000000-0000-0000-0000-000000000000/result")
        assert response.status_code == 404
