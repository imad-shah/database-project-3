from dataclasses import dataclass
from datetime import date
from decimal import Decimal


@dataclass(slots=True, kw_only=True)
class Listing:
    property_id: int
    seller_id: int
    listing_agent_id: int
    asking_price: Decimal
    listing_date: date
    listing_id: int | None = None
    status: str | None = None
    street: str | None = None
    city: str | None = None
