from dataclasses import dataclass
from decimal import Decimal


@dataclass(slots=True, kw_only=True)
class Property:
    street: str
    city: str
    state: str
    zip_code: str
    school_district: str
    bedrooms: int
    bathrooms: Decimal
    square_feet: int
    has_pool: bool
    year_built: int | None = None
    property_id: int | None = None
    status: str | None = None
    has_photo: bool | None = None
