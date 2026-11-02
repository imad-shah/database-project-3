from dataclasses import dataclass
from datetime import date
from decimal import Decimal


@dataclass(slots=True, kw_only=True)
class Sale:
    property_id: int
    buyer_id: int
    selling_agent_id: int
    sale_price: Decimal
    sale_date: date
    buyers_agent_id: int | None = None
    sale_id: int | None = None
