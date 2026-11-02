from dataclasses import dataclass
from datetime import date

from .person import Person


@dataclass(slots=True, kw_only=True)
class Agent(Person):
    license_number: str
    hire_date: date
    agent_id: int | None = None
