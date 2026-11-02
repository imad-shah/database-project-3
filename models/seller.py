from dataclasses import dataclass

from .person import Person


@dataclass(slots=True, kw_only=True)
class Seller(Person):
    seller_id: int | None = None
