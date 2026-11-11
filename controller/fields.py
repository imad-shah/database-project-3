from collections.abc import Callable, Sequence
from dataclasses import dataclass

from .errors import AppError
from .field_types import REFERENCE, TEXT, FieldType


@dataclass(frozen=True, slots=True)
class Option:
    id: int
    label: str

    def __str__(self) -> str:
        return f"{self.id} - {self.label}"


OptionSource = Callable[[], Sequence[Option]]


@dataclass(frozen=True, slots=True)
class Field:
    name: str
    label: str
    type: FieldType = TEXT
    required: bool = False
    editable: bool = True
    fixed: bool = False
    in_form: bool = True
    default: str = ""
    source: OptionSource | None = None
    selectable: OptionSource | None = None

    @property
    def has_choices(self) -> bool:
        return bool(self.source or self.type.choices)

    def choices(self) -> list[str]:
        loader = self.selectable or self.source
        choices = (
            [str(option) for option in loader()] if loader else list(self.type.choices)
        )
        return choices if self.required else ["", *choices]

    def initial(self) -> str:
        if self.default or not (self.required and self.has_choices):
            return self.default
        return next(iter(self.choices()), "")

    def parse(self, raw: str) -> object:
        value = raw.strip()
        if not value:
            if self.required:
                raise AppError(f"{self.label} is required.")
            return None
        try:
            return self.type.parse(value)
        except ValueError as e:
            raise AppError(f"{self.label} {e}") from None

    def formatter(self) -> Callable[[object], str]:
        labels = {o.id: str(o) for o in self.source()} if self.source else {}

        def render(value: object) -> str:
            if value is None:
                return ""
            return labels.get(value) or self.type.show(value)

        return render


def reference(
    name: str,
    label: str,
    source: OptionSource,
    required: bool = True,
    selectable: OptionSource | None = None,
    fixed: bool = False,
) -> Field:
    return Field(
        name,
        label,
        REFERENCE,
        required=required,
        fixed=fixed,
        source=source,
        selectable=selectable,
    )
