"""Tests for HTTP clients."""

from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import pytest

from src.clients.ai_agent import AIAgentClient
from src.clients.game_engine import GameEngineClient


class TestGameEngineClient:
    """Tests for GameEngineClient."""

    @pytest.fixture
    def client(self):
        """Create a Game Engine client."""
        with patch("src.clients.game_engine.get_settings") as mock_settings:
            mock_settings.return_value = MagicMock(
                game_engine_url="http://test:8000",
                http_timeout=30.0,
            )
            return GameEngineClient()

    @pytest.mark.asyncio
    async def test_health_check(self, client):
        """Test health check request."""
        mock_response = MagicMock()
        mock_response.json.return_value = {"status": "healthy"}
        mock_response.raise_for_status = MagicMock()

        with patch.object(client, "_get_client") as mock_get_client:
            mock_http = AsyncMock()
            mock_http.get = AsyncMock(return_value=mock_response)
            mock_get_client.return_value = mock_http

            result = await client.health_check()

            assert result == {"status": "healthy"}
            mock_http.get.assert_called_once_with("/health")

    @pytest.mark.asyncio
    async def test_create_game(self, client):
        """Test game creation."""
        players = [
            {"name": "Player 1", "model": "test", "personality": "aggressive"},
        ]
        mock_response = MagicMock()
        mock_response.json.return_value = {"id": "test-uuid", "players": players}
        mock_response.raise_for_status = MagicMock()

        with patch.object(client, "_get_client") as mock_get_client:
            mock_http = AsyncMock()
            mock_http.post = AsyncMock(return_value=mock_response)
            mock_get_client.return_value = mock_http

            result = await client.create_game(players)

            assert result["id"] == "test-uuid"
            mock_http.post.assert_called_once_with(
                "/game/create", json={"players": players}
            )

    @pytest.mark.asyncio
    async def test_get_state(self, client):
        """Test getting game state."""
        game_id = uuid4()
        mock_response = MagicMock()
        mock_response.json.return_value = {"id": str(game_id), "status": "in_progress"}
        mock_response.raise_for_status = MagicMock()

        with patch.object(client, "_get_client") as mock_get_client:
            mock_http = AsyncMock()
            mock_http.get = AsyncMock(return_value=mock_response)
            mock_get_client.return_value = mock_http

            result = await client.get_state(game_id)

            assert result["status"] == "in_progress"
            mock_http.get.assert_called_once_with(f"/game/{game_id}")

    @pytest.mark.asyncio
    async def test_execute_action(self, client):
        """Test executing an action."""
        game_id = uuid4()
        player_id = uuid4()
        action = {"type": "roll_dice"}

        mock_response = MagicMock()
        mock_response.json.return_value = {"success": True}
        mock_response.raise_for_status = MagicMock()

        with patch.object(client, "_get_client") as mock_get_client:
            mock_http = AsyncMock()
            mock_http.post = AsyncMock(return_value=mock_response)
            mock_get_client.return_value = mock_http

            result = await client.execute_action(game_id, player_id, action)

            assert result["success"] is True
            mock_http.post.assert_called_once_with(
                f"/game/{game_id}/action",
                json={"player_id": str(player_id), "action": action},
            )


class TestAIAgentClient:
    """Tests for AIAgentClient."""

    @pytest.fixture
    def client(self):
        """Create an AI Agent client."""
        with patch("src.clients.ai_agent.get_settings") as mock_settings:
            mock_settings.return_value = MagicMock(
                ai_agent_url="http://test:8001",
                http_timeout=30.0,
            )
            return AIAgentClient()

    @pytest.mark.asyncio
    async def test_health_check(self, client):
        """Test health check request."""
        mock_response = MagicMock()
        mock_response.json.return_value = {"status": "healthy"}
        mock_response.raise_for_status = MagicMock()

        with patch.object(client, "_get_client") as mock_get_client:
            mock_http = AsyncMock()
            mock_http.get = AsyncMock(return_value=mock_response)
            mock_get_client.return_value = mock_http

            result = await client.health_check()

            assert result == {"status": "healthy"}

    @pytest.mark.asyncio
    async def test_get_decision(self, client):
        """Test getting AI decision."""
        game_id = uuid4()
        player_id = uuid4()
        game_state = {"status": "in_progress"}
        valid_actions = [{"type": "roll_dice"}]

        mock_response = MagicMock()
        mock_response.json.return_value = {"action": {"type": "roll_dice"}}
        mock_response.raise_for_status = MagicMock()

        with patch.object(client, "_get_client") as mock_get_client:
            mock_http = AsyncMock()
            mock_http.post = AsyncMock(return_value=mock_response)
            mock_get_client.return_value = mock_http

            result = await client.get_decision(
                game_id, player_id, game_state, valid_actions
            )

            assert result["action"]["type"] == "roll_dice"
            mock_http.post.assert_called_once_with(
                f"/games/{game_id}/decide",
                json={
                    "player_id": str(player_id),
                    "game_state": game_state,
                    "valid_actions": valid_actions,
                },
            )

    @pytest.mark.asyncio
    async def test_create_game(self, client):
        """Test registering a game."""
        game_id = uuid4()
        agents = [
            {"player_id": str(uuid4()), "name": "Agent 1", "personality": "aggressive"},
        ]

        mock_response = MagicMock()
        mock_response.json.return_value = {"game_id": str(game_id), "status": "created"}
        mock_response.raise_for_status = MagicMock()

        with patch.object(client, "_get_client") as mock_get_client:
            mock_http = AsyncMock()
            mock_http.post = AsyncMock(return_value=mock_response)
            mock_get_client.return_value = mock_http

            result = await client.create_game(game_id, agents)

            assert result["status"] == "created"
            mock_http.post.assert_called_once_with(
                "/games",
                json={"game_id": str(game_id), "agents": agents},
            )
