from dataclasses import dataclass


@dataclass(slots=True, kw_only=True)
class Person:
    first_name: str
    last_name: str
    phone: str | None = None
    email: str | None = None

    @property
    def full_name(self) -> str:
        return f"{self.first_name} {self.last_name}"
