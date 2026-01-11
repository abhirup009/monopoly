"""Tests for house and hotel building rules."""

import pytest
from uuid import uuid4

from src.engine.building_rules import (
    can_build_house,
    can_build_hotel,
    get_house_cost,
    get_buildable_properties,
)
from src.db.models import PlayerModel, PropertyStateModel


class TestCanBuildHouse:
    """Tests for can_build_house function."""

    def test_can_build_with_monopoly(
        self,
        wealthy_player: PlayerModel,
        sample_property_states: list[PropertyStateModel],
    ):
        """Test can build house with monopoly."""
        owner_id = wealthy_player.id

        # Own full brown set
        for prop in sample_property_states:
            if prop.property_id in ["mediterranean", "baltic"]:
                prop.owner_id = owner_id

        can_build, reason = can_build_house(
            "mediterranean", wealthy_player, sample_property_states
        )
        assert can_build is True
        assert reason == "OK"

    def test_cannot_build_without_monopoly(
        self,
        wealthy_player: PlayerModel,
        sample_property_states: list[PropertyStateModel],
    ):
        """Test cannot build without monopoly."""
        owner_id = wealthy_player.id

        # Own only one brown property
        prop = next(
            ps for ps in sample_property_states if ps.property_id == "mediterranean"
        )
        prop.owner_id = owner_id

        can_build, reason = can_build_house(
            "mediterranean", wealthy_player, sample_property_states
        )
        assert can_build is False
        assert "Must own all properties" in reason

    def test_cannot_build_uneven(
        self,
        wealthy_player: PlayerModel,
        sample_property_states: list[PropertyStateModel],
    ):
        """Test cannot build unevenly."""
        owner_id = wealthy_player.id

        # Own full brown set
        for prop in sample_property_states:
            if prop.property_id in ["mediterranean", "baltic"]:
                prop.owner_id = owner_id
                if prop.property_id == "mediterranean":
                    prop.houses = 1  # Already has a house

        can_build, reason = can_build_house(
            "mediterranean", wealthy_player, sample_property_states
        )
        assert can_build is False
        assert "evenly" in reason

    def test_cannot_build_at_max_houses(
        self,
        wealthy_player: PlayerModel,
        sample_property_states: list[PropertyStateModel],
    ):
        """Test cannot build more than 4 houses."""
        owner_id = wealthy_player.id

        for prop in sample_property_states:
            if prop.property_id in ["mediterranean", "baltic"]:
                prop.owner_id = owner_id
                prop.houses = 4

        can_build, reason = can_build_house(
            "mediterranean", wealthy_player, sample_property_states
        )
        assert can_build is False
        assert "hotel" in reason.lower()

    def test_cannot_build_on_railroad(
        self,
        wealthy_player: PlayerModel,
        sample_property_states: list[PropertyStateModel],
    ):
        """Test cannot build on railroad."""
        prop = next(ps for ps in sample_property_states if ps.property_id == "reading_rr")
        prop.owner_id = wealthy_player.id

        can_build, reason = can_build_house(
            "reading_rr", wealthy_player, sample_property_states
        )
        assert can_build is False
        assert "street" in reason.lower()

    def test_cannot_build_insufficient_funds(
        self,
        poor_player: PlayerModel,
        sample_property_states: list[PropertyStateModel],
    ):
        """Test cannot build without funds."""
        owner_id = poor_player.id

        for prop in sample_property_states:
            if prop.property_id in ["mediterranean", "baltic"]:
                prop.owner_id = owner_id

        can_build, reason = can_build_house(
            "mediterranean", poor_player, sample_property_states
        )
        assert can_build is False
        assert "Insufficient" in reason


class TestCanBuildHotel:
    """Tests for can_build_hotel function."""

    def test_can_build_hotel(
        self,
        wealthy_player: PlayerModel,
        sample_property_states: list[PropertyStateModel],
    ):
        """Test can build hotel with 4 houses on all."""
        owner_id = wealthy_player.id

        for prop in sample_property_states:
            if prop.property_id in ["mediterranean", "baltic"]:
                prop.owner_id = owner_id
                prop.houses = 4

        can_build, reason = can_build_hotel(
            "mediterranean", wealthy_player, sample_property_states
        )
        assert can_build is True
        assert reason == "OK"

    def test_cannot_build_hotel_without_4_houses(
        self,
        wealthy_player: PlayerModel,
        sample_property_states: list[PropertyStateModel],
    ):
        """Test cannot build hotel without 4 houses."""
        owner_id = wealthy_player.id

        for prop in sample_property_states:
            if prop.property_id in ["mediterranean", "baltic"]:
                prop.owner_id = owner_id
                prop.houses = 3

        can_build, reason = can_build_hotel(
            "mediterranean", wealthy_player, sample_property_states
        )
        assert can_build is False
        assert "4 houses" in reason


class TestGetHouseCost:
    """Tests for get_house_cost function."""

    def test_brown_house_cost(self):
        """Test brown property house cost."""
        cost = get_house_cost("mediterranean")
        assert cost == 50

    def test_dark_blue_house_cost(self):
        """Test dark blue property house cost."""
        cost = get_house_cost("boardwalk")
        assert cost == 200

    def test_invalid_property(self):
        """Test invalid property raises error."""
        with pytest.raises(ValueError):
            get_house_cost("fake_property")


class TestGetBuildableProperties:
    """Tests for get_buildable_properties function."""

    def test_no_buildable_without_monopoly(
        self,
        wealthy_player: PlayerModel,
        sample_property_states: list[PropertyStateModel],
    ):
        """Test no buildable properties without monopoly."""
        # Own one property
        prop = next(
            ps for ps in sample_property_states if ps.property_id == "mediterranean"
        )
        prop.owner_id = wealthy_player.id

        buildable = get_buildable_properties(wealthy_player, sample_property_states)
        assert len(buildable) == 0

    def test_buildable_with_monopoly(
        self,
        wealthy_player: PlayerModel,
        sample_property_states: list[PropertyStateModel],
    ):
        """Test buildable properties with monopoly."""
        owner_id = wealthy_player.id

        for prop in sample_property_states:
            if prop.property_id in ["mediterranean", "baltic"]:
                prop.owner_id = owner_id

        buildable = get_buildable_properties(wealthy_player, sample_property_states)
        assert len(buildable) == 2
        assert all(b[1] == "house" for b in buildable)
