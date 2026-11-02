from collections.abc import Mapping

from repository import IRepository

from .errors import AppError, friendly_errors
from .fields import Option
from .interfaces import IEntityController
from .specs import EntitySpec


class EntityController[T](IEntityController[T]):
    def __init__(self, spec: EntitySpec[T], repo: IRepository[T]) -> None:
        self._spec = spec
        self._repo = repo

    @property
    def spec(self) -> EntitySpec[T]:
        return self._spec

    def save(self, values: Mapping[str, str]) -> T:
        parsed = {
            field.name: field.parse(values.get(field.name, ""))
            for field in self._spec.fields
            if field.in_form
        }
        record = self._spec.model(**parsed)
        with friendly_errors():
            return self._repo.save(record)

    def delete(self, record_id: str) -> None:
        key = self._parse_key(record_id)
        with friendly_errors():
            self._repo.delete(key)

    def rows(self) -> list[tuple[str, ...]]:
        with friendly_errors():
            records = self._repo.find_all()
            columns = [(field.name, field.formatter()) for field in self._spec.fields]
        return [
            tuple(render(getattr(record, name)) for name, render in columns)
            for record in records
        ]

    def options(self) -> list[Option]:
        with friendly_errors():
            return self._to_options(self._repo.find_all())

    def _to_options(self, records: list[T]) -> list[Option]:
        key = self._spec.key.name
        return [Option(getattr(r, key), self._spec.label(r)) for r in records]

    def _parse_key(self, record_id: str) -> int:
        key = self._spec.key.parse(record_id)
        if key is None:
            raise AppError("Select a record first.")
        return key
