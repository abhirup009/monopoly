"""Tests for event bus."""

from uuid import uuid4

import pytest


class TestEventBus:
    """Tests for EventBus class."""

    @pytest.mark.asyncio
    async def test_emit_to_handlers(self, event_bus):
        """Test emitting events to registered handlers."""
        handler_called = False
        received_data = None

        async def handler(data):
            nonlocal handler_called, received_data
            handler_called = True
            received_data = data

        event_bus.on("test:event", handler)

        await event_bus.emit("test:event", {"key": "value"})

        assert handler_called is True
        assert received_data == {"key": "value"}

    @pytest.mark.asyncio
    async def test_emit_broadcasts_to_room(self, event_bus, mock_sio):
        """Test emitting events broadcasts to Socket.IO room."""
        game_id = uuid4()

        await event_bus.emit("game:update", {"data": "test"}, game_id=game_id)

        mock_sio.emit.assert_called_once_with(
            "game:update", {"data": "test"}, room=f"game:{game_id}"
        )

    @pytest.mark.asyncio
    async def test_emit_no_broadcast(self, event_bus, mock_sio):
        """Test emitting without broadcasting."""
        await event_bus.emit("internal:event", {"data": "test"}, broadcast=False)

        mock_sio.emit.assert_not_called()

    @pytest.mark.asyncio
    async def test_emit_to_sid(self, event_bus, mock_sio):
        """Test emitting to specific client."""
        await event_bus.emit_to_sid("personal:event", {"data": "test"}, "client-123")

        mock_sio.emit.assert_called_once_with(
            "personal:event", {"data": "test"}, room="client-123"
        )

    def test_register_handler(self, event_bus):
        """Test registering an event handler."""

        async def handler(data):
            pass

        event_bus.on("test:event", handler)

        assert "test:event" in event_bus._handlers
        assert handler in event_bus._handlers["test:event"]

    def test_unregister_handler(self, event_bus):
        """Test unregistering an event handler."""

        async def handler(data):
            pass

        event_bus.on("test:event", handler)
        event_bus.off("test:event", handler)

        assert handler not in event_bus._handlers.get("test:event", [])

    @pytest.mark.asyncio
    async def test_handler_error_doesnt_break_emit(self, event_bus):
        """Test that handler errors don't break other handlers."""
        handler2_called = False

        async def failing_handler(data):
            raise ValueError("Test error")

        async def working_handler(data):
            nonlocal handler2_called
            handler2_called = True

        event_bus.on("test:event", failing_handler)
        event_bus.on("test:event", working_handler)

        # Should not raise
        await event_bus.emit("test:event", {}, broadcast=False)

        assert handler2_called is True

    @pytest.mark.asyncio
    async def test_multiple_handlers(self, event_bus):
        """Test multiple handlers for same event."""
        calls = []

        async def handler1(data):
            calls.append("handler1")

        async def handler2(data):
            calls.append("handler2")

        event_bus.on("test:event", handler1)
        event_bus.on("test:event", handler2)

        await event_bus.emit("test:event", {}, broadcast=False)

        assert "handler1" in calls
        assert "handler2" in calls
