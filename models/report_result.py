from collections.abc import Sequence
from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class ReportResult:
    columns: Sequence[str]
    rows: Sequence[Sequence[object]]
