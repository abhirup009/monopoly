"""Tests for property buying and rent calculation."""

import pytest
from uuid import uuid4

from src.engine.property_rules import (
    can_buy_property,
    get_property_price,
    calculate_rent,
    owns_full_color_set,
    get_owner_id,
    count_houses_and_hotels,
)
from src.db.models import PlayerModel, PropertyStateModel


class TestCanBuyProperty:
    """Tests for can_buy_property function."""

    def test_can_buy_unowned_property(
        self,
        wealthy_player: PlayerModel,
        sample_property_states: list[PropertyStateModel],
    ):
        """Test buying an unowned property."""
        can_buy, reason = can_buy_property(
            "mediterranean", wealthy_player, sample_property_states
        )
        assert can_buy is True
        assert reason == "OK"

    def test_cannot_buy_owned_property(
        self,
        wealthy_player: PlayerModel,
        sample_property_states: list[PropertyStateModel],
        sample_players: list[PlayerModel],
    ):
        """Test cannot buy owned property."""
        # Set owner
        prop = next(
            ps for ps in sample_property_states if ps.property_id == "mediterranean"
        )
        prop.owner_id = sample_players[1].id

        can_buy, reason = can_buy_property(
            "mediterranean", wealthy_player, sample_property_states
        )
        assert can_buy is False
        assert "already owned" in reason

    def test_cannot_buy_insufficient_funds(
        self,
        poor_player: PlayerModel,
        sample_property_states: list[PropertyStateModel],
    ):
        """Test cannot buy with insufficient funds."""
        can_buy, reason = can_buy_property(
            "boardwalk", poor_player, sample_property_states
        )
        assert can_buy is False
        assert "Insufficient" in reason

    def test_cannot_buy_invalid_property(
        self,
        wealthy_player: PlayerModel,
        sample_property_states: list[PropertyStateModel],
    ):
        """Test cannot buy non-existent property."""
        can_buy, reason = can_buy_property(
            "fake_property", wealthy_player, sample_property_states
        )
        assert can_buy is False
        assert "does not exist" in reason


class TestCalculateRent:
    """Tests for calculate_rent function."""

    def test_no_rent_unowned(self, sample_property_states: list[PropertyStateModel]):
        """Test no rent for unowned property."""
        rent = calculate_rent("mediterranean", sample_property_states)
        assert rent == 0

    def test_base_rent(
        self,
        sample_property_states: list[PropertyStateModel],
        sample_players: list[PlayerModel],
    ):
        """Test base rent without monopoly."""
        prop = next(
            ps for ps in sample_property_states if ps.property_id == "mediterranean"
        )
        prop.owner_id = sample_players[0].id

        rent = calculate_rent("mediterranean", sample_property_states)
        assert rent == 2  # Base rent for Mediterranean

    def test_double_rent_monopoly(
        self,
        sample_property_states: list[PropertyStateModel],
        sample_players: list[PlayerModel],
    ):
        """Test double rent with monopoly (full color set)."""
        owner_id = sample_players[0].id

        # Own both brown properties
        for prop in sample_property_states:
            if prop.property_id in ["mediterranean", "baltic"]:
                prop.owner_id = owner_id

        rent = calculate_rent("mediterranean", sample_property_states)
        assert rent == 4  # 2 * 2 = 4

    def test_rent_with_houses(
        self,
        sample_property_states: list[PropertyStateModel],
        sample_players: list[PlayerModel],
    ):
        """Test rent with houses."""
        owner_id = sample_players[0].id

        # Own both brown properties
        for prop in sample_property_states:
            if prop.property_id in ["mediterranean", "baltic"]:
                prop.owner_id = owner_id

        # Add house
        prop = next(
            ps for ps in sample_property_states if ps.property_id == "mediterranean"
        )
        prop.houses = 1

        rent = calculate_rent("mediterranean", sample_property_states)
        assert rent == 10  # 1 house rent for Mediterranean

    def test_railroad_rent_one(
        self,
        sample_property_states: list[PropertyStateModel],
        sample_players: list[PlayerModel],
    ):
        """Test railroad rent with one owned."""
        owner_id = sample_players[0].id
        prop = next(
            ps for ps in sample_property_states if ps.property_id == "reading_rr"
        )
        prop.owner_id = owner_id

        rent = calculate_rent("reading_rr", sample_property_states)
        assert rent == 25

    def test_railroad_rent_all_four(
        self,
        sample_property_states: list[PropertyStateModel],
        sample_players: list[PlayerModel],
    ):
        """Test railroad rent with all four owned."""
        owner_id = sample_players[0].id
        for prop in sample_property_states:
            if prop.property_id in [
                "reading_rr",
                "pennsylvania_rr",
                "bo_rr",
                "short_line_rr",
            ]:
                prop.owner_id = owner_id

        rent = calculate_rent("reading_rr", sample_property_states)
        assert rent == 200  # 25 * 2^3 = 200

    def test_utility_rent_one(
        self,
        sample_property_states: list[PropertyStateModel],
        sample_players: list[PlayerModel],
    ):
        """Test utility rent with one owned."""
        owner_id = sample_players[0].id
        prop = next(
            ps for ps in sample_property_states if ps.property_id == "electric_company"
        )
        prop.owner_id = owner_id

        rent = calculate_rent("electric_company", sample_property_states, dice_total=7)
        assert rent == 28  # 4 * 7

    def test_utility_rent_both(
        self,
        sample_property_states: list[PropertyStateModel],
        sample_players: list[PlayerModel],
    ):
        """Test utility rent with both owned."""
        owner_id = sample_players[0].id
        for prop in sample_property_states:
            if prop.property_id in ["electric_company", "water_works"]:
                prop.owner_id = owner_id

        rent = calculate_rent("electric_company", sample_property_states, dice_total=7)
        assert rent == 70  # 10 * 7


class TestOwnsFullColorSet:
    """Tests for owns_full_color_set function."""

    def test_owns_full_set(
        self,
        sample_property_states: list[PropertyStateModel],
        sample_players: list[PlayerModel],
    ):
        """Test detecting full color set ownership."""
        owner_id = sample_players[0].id

        # Own both brown properties
        for prop in sample_property_states:
            if prop.property_id in ["mediterranean", "baltic"]:
                prop.owner_id = owner_id

        assert owns_full_color_set(owner_id, "brown", sample_property_states) is True

    def test_owns_partial_set(
        self,
        sample_property_states: list[PropertyStateModel],
        sample_players: list[PlayerModel],
    ):
        """Test detecting partial color set."""
        owner_id = sample_players[0].id

        # Own only one brown property
        prop = next(
            ps for ps in sample_property_states if ps.property_id == "mediterranean"
        )
        prop.owner_id = owner_id

        assert owns_full_color_set(owner_id, "brown", sample_property_states) is False


class TestCountHousesAndHotels:
    """Tests for count_houses_and_hotels function."""

    def test_no_buildings(
        self,
        sample_property_states: list[PropertyStateModel],
        sample_players: list[PlayerModel],
    ):
        """Test counting with no buildings."""
        houses, hotels = count_houses_and_hotels(
            sample_players[0].id, sample_property_states
        )
        assert houses == 0
        assert hotels == 0

    def test_count_houses(
        self,
        sample_property_states: list[PropertyStateModel],
        sample_players: list[PlayerModel],
    ):
        """Test counting houses."""
        owner_id = sample_players[0].id

        for prop in sample_property_states:
            if prop.property_id in ["mediterranean", "baltic"]:
                prop.owner_id = owner_id
                prop.houses = 2

        houses, hotels = count_houses_and_hotels(owner_id, sample_property_states)
        assert houses == 4
        assert hotels == 0

    def test_count_hotels(
        self,
        sample_property_states: list[PropertyStateModel],
        sample_players: list[PlayerModel],
    ):
        """Test counting hotels (5 houses = 1 hotel)."""
        owner_id = sample_players[0].id

        for prop in sample_property_states:
            if prop.property_id == "mediterranean":
                prop.owner_id = owner_id
                prop.houses = 5  # Hotel

        houses, hotels = count_houses_and_hotels(owner_id, sample_property_states)
        assert houses == 0
        assert hotels == 1
