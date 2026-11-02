from collections.abc import Mapping

import psycopg

from models import ReportResult

from .interfaces import IReportRepository


class ReportRepository(IReportRepository):
    def __init__(self, con: psycopg.Connection) -> None:
        self._con = con

    def run(self, query: str, params: Mapping[str, object]) -> ReportResult:
        cursor = self._con.execute(query, params)
        columns = [column.name for column in cursor.description]
        return ReportResult(columns=columns, rows=cursor.fetchall())
