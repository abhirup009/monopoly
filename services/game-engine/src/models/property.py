"""Property models."""

from uuid import UUID

from pydantic import BaseModel


class PropertyState(BaseModel):
    """Runtime state of a property in a game."""

    property_id: str
    owner_id: UUID | None = None
    houses: int = 0  # 0-4 for houses, 5 for hotel

    class Config:
        from_attributes = True


class PropertyInfo(BaseModel):
    """Full property information combining static data and runtime state."""

    property_id: str
    name: str
    type: str  # street, railroad, utility
    position: int
    price: int
    mortgage_value: int

    # Street-specific fields
    color: str | None = None
    rent: list[int] | None = None  # [base, 1h, 2h, 3h, 4h, hotel]
    house_cost: int | None = None

    # Runtime state
    owner_id: UUID | None = None
    owner_name: str | None = None
    houses: int = 0
    current_rent: int = 0


class PropertyPurchaseOption(BaseModel):
    """Property available for purchase."""

    property_id: str
    name: str
    price: int
    type: str
    color: str | None = None
