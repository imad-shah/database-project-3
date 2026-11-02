from dataclasses import dataclass
from decimal import Decimal

from .person import Person


@dataclass(slots=True, kw_only=True)
class Buyer(Person):
    max_budget: Decimal | None = None
    min_bedrooms: int | None = None
    preferred_city: str | None = None
    buyer_id: int | None = None
