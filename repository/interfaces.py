from abc import ABC, abstractmethod
from collections.abc import Mapping

from models import Property, ReportResult


class RecordNotFound(Exception):
    pass


class IRepository[T](ABC):
    @abstractmethod
    def find(self, record_id: int) -> T | None:
        pass

    @abstractmethod
    def find_all(self) -> list[T]:
        pass

    @abstractmethod
    def save(self, record: T) -> T:
        pass

    @abstractmethod
    def delete(self, record_id: int) -> None:
        pass


class IPropertyRepository(IRepository[Property]):
    @abstractmethod
    def find_available(self) -> list[Property]:
        pass

    @abstractmethod
    def get_image(self, property_id: int) -> bytes | None:
        pass

    @abstractmethod
    def set_image(self, property_id: int, image: bytes | None) -> None:
        pass


class IReportRepository(ABC):
    @abstractmethod
    def run(self, query: str, params: Mapping[str, object]) -> ReportResult:
        pass
