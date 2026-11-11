from abc import ABC, abstractmethod
from collections.abc import Mapping, Sequence

from models import Listing, Property, ReportResult

from .fields import Option
from .reports import Report
from .specs import EntitySpec


class IEntityController[T](ABC):
    @property
    @abstractmethod
    def spec(self) -> EntitySpec[T]:
        pass

    @abstractmethod
    def save(self, values: Mapping[str, str]) -> T:
        pass

    @abstractmethod
    def delete(self, record_id: str) -> None:
        pass

    @abstractmethod
    def rows(self) -> list[tuple[str, ...]]:
        pass

    @abstractmethod
    def options(self) -> list[Option]:
        pass


class IPropertyController(IEntityController[Property]):
    @abstractmethod
    def unlisted_options(self) -> list[Option]:
        pass

    @abstractmethod
    def image(self, property_id: str) -> bytes | None:
        pass

    @abstractmethod
    def attach_image(self, property_id: str, path: str) -> None:
        pass

    @abstractmethod
    def remove_image(self, property_id: str) -> None:
        pass


class IListingController(IEntityController[Listing]):
    @abstractmethod
    def available_options(self) -> list[Option]:
        pass


class IReportController(ABC):
    @property
    @abstractmethod
    def reports(self) -> Sequence[Report]:
        pass

    @abstractmethod
    def run(self, report: Report, values: Mapping[str, str]) -> ReportResult:
        pass

    @abstractmethod
    def image(self, property_id: str) -> bytes | None:
        pass
