from collections.abc import Mapping, Sequence
from decimal import Decimal

from models import ReportResult
from repository import IReportRepository

from .errors import friendly_errors
from .field_types import YES_NO
from .interfaces import IPropertyController, IReportController
from .reports import Report


def _show(value: object) -> str:
    match value:
        case None:
            return ""
        case bool():
            return YES_NO.show(value)
        case Decimal():
            return f"{value:,.2f}"
        case _:
            return str(value)


class ReportController(IReportController):
    def __init__(
        self,
        reports: Sequence[Report],
        repo: IReportRepository,
        properties: IPropertyController,
    ) -> None:
        self._reports = reports
        self._repo = repo
        self._properties = properties

    @property
    def reports(self) -> Sequence[Report]:
        return self._reports

    def run(self, report: Report, values: Mapping[str, str]) -> ReportResult:
        params = {p.name: p.parse(values.get(p.name, "")) for p in report.params}
        with friendly_errors():
            result = self._repo.run(report.query, params)
        rows = [tuple(_show(value) for value in row) for row in result.rows]
        return ReportResult(columns=result.columns, rows=rows)

    def image(self, property_id: str) -> bytes | None:
        return self._properties.image(property_id)
