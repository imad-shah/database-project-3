from collections.abc import Sequence
from datetime import date
from decimal import Decimal
from pathlib import Path

import psycopg

from controller import Controllers, IEntityController, Report, build_controllers
from models import ReportResult
from repository import Repositories, get_connection, init_db
from repository.database import SCHEMA_PATH
from repository.sql_repository import SqlRepository

OUTPUT_DIR = Path(__file__).parent / "docs"
REPORT_PATH = OUTPUT_DIR / "report.md"
IMAGE_DIR = OUTPUT_DIR / "images"
TABLES = ("agents", "buyers", "sellers", "properties", "sales")
LETTERS = "abcdefghijklmnopqrstuvwxyz"


def _markdown_table(columns: Sequence[str], rows: Sequence[Sequence[object]]) -> str:
    lines = [f"| {' | '.join(columns)} |", f"|{' --- |' * len(columns)}"]
    lines += [f"| {' | '.join(str(value) for value in row)} |" for row in rows]
    return "\n".join(lines)


def _code(language: str, text: str) -> str:
    return f"```{language}\n{text.strip()}\n```"


def _answer(result: ReportResult) -> str:
    if not result.rows:
        return "*No rows.*"
    return _markdown_table(result.columns, result.rows)


def _export_images(
    controllers: Controllers, report: Report, result: ReportResult
) -> str:
    IMAGE_DIR.mkdir(exist_ok=True)
    index = result.columns.index(report.image_column)
    links = []
    for row in result.rows:
        property_id = row[index]
        image = controllers.reports.image(property_id)
        if image is not None:
            path = IMAGE_DIR / f"property_{property_id}.png"
            path.write_bytes(image)
            links.append(f"![Property {property_id}]({path.relative_to(OUTPUT_DIR)})")
    return "\n\n".join(links)


def _report_section(letter: str, controllers: Controllers, report: Report) -> str:
    values = {param.name: param.initial() for param in report.params}
    result = controllers.reports.run(report, values)
    used = ", ".join(f"{p.label} = {values[p.name]}" for p in report.params)
    parts = [
        f"### {letter}) {report.title}",
        report.question + (f" ({used})" if used else ""),
        _code("sql", report.query),
        _answer(result),
    ]
    if report.image_column:
        parts.append(_export_images(controllers, report, result))
    return "\n\n".join(parts)


def _plain(values: dict[str, object]) -> dict[str, str]:
    def text(value: object) -> str:
        return "" if value is None else str(value)

    return {name: text(value) for name, value in values.items()}


def _sale_example(controllers: Controllers) -> dict[str, str]:
    property_option = controllers.properties.available_options()[0]
    agents = controllers.agents.options()
    return _plain(
        {
            "property_id": property_option.id,
            "buyer_id": controllers.buyers.options()[0].id,
            "selling_agent_id": agents[0].id,
            "buyers_agent_id": agents[1].id,
            "sale_price": Decimal(240_000),
            "sale_date": date(2005, 4, 12),
        }
    )


def _agent_example() -> dict[str, str]:
    return _plain(
        {
            "first_name": "Morgan",
            "last_name": "Rivera",
            "phone": "610-555-0199",
            "email": "morgan.rivera@example.com",
            "license_number": "RS900001",
            "hire_date": date(2005, 4, 12),
        }
    )


def _write_section(
    con: psycopg.Connection,
    heading: str,
    question: str,
    repository: SqlRepository,
    controller: IEntityController,
    values: dict[str, str],
) -> str:
    with con.transaction(force_rollback=True):
        record = controller.save(values)
    columns = [field.name for field in controller.spec.fields if field.in_form]
    rows = [[getattr(record, name) for name in columns]]
    return "\n\n".join(
        [
            f"### {heading}",
            question,
            _code("sql", repository.insert_statement().as_string(con)),
            "Row written (rolled back so this report leaves the data unchanged):",
            _markdown_table(columns, rows),
        ]
    )


def build_report(con: psycopg.Connection) -> str:
    repositories = Repositories.connect(con)
    controllers = build_controllers(repositories)
    counts = [(table, getattr(repositories, table).count()) for table in TABLES]
    letters = iter(LETTERS)
    required, extra = controllers.reports.reports[:5], controllers.reports.reports[5:]
    sections = [
        "# Project 3: Real Estate Office Database",
        "## Relational schema",
        _code("sql", SCHEMA_PATH.read_text()),
        "## Table sizes",
        _markdown_table(("Relation", "count(*)"), counts),
        "## Queries",
        *(_report_section(next(letters), controllers, r) for r in required),
        _write_section(
            con,
            f"{next(letters)}) Record a sale",
            "Record the sale of a property that had been listed as available.",
            repositories.sales,
            controllers.sales,
            _sale_example(controllers),
        ),
        _write_section(
            con,
            f"{next(letters)}) Add an agent",
            "Add a new agent to the database.",
            repositories.agents,
            controllers.agents,
            _agent_example(),
        ),
        "## Additional queries",
        *(_report_section(next(letters), controllers, r) for r in extra),
    ]
    return "\n\n".join(sections) + "\n"


def main() -> None:
    with get_connection() as con:
        init_db(con)
        REPORT_PATH.write_text(build_report(con))
    print(f"Wrote {REPORT_PATH}")


if __name__ == "__main__":
    main()
