from collections.abc import Iterable, Mapping
from dataclasses import fields

import psycopg
from psycopg import sql
from psycopg.rows import class_row

from .interfaces import IRepository, RecordNotFound


def _identifiers(names: Iterable[str]) -> sql.Composed:
    return sql.SQL(", ").join(map(sql.Identifier, names))


class SqlRepository[T](IRepository[T]):
    model: type[T]
    table: str
    key: str
    order_by: str
    source: str | None = None
    computed: frozenset[str] = frozenset()

    def __init__(self, con: psycopg.Connection) -> None:
        self._con = con
        names = [field.name for field in fields(self.model)]
        self._columns = names
        self._writable = [
            name for name in names if name != self.key and name not in self.computed
        ]

    def find(self, record_id: int) -> T | None:
        rows = self._select(f"{self.key} = %s", (record_id,))
        return rows[0] if rows else None

    def find_all(self) -> list[T]:
        return self._select()

    def save(self, record: T) -> T:
        params = {name: getattr(record, name) for name in self._writable}
        record_id = getattr(record, self.key)
        if record_id is None:
            record_id = self._write_one(self.insert_statement(), params)
        else:
            params[self.key] = record_id
            self._write_one(self._update_statement(), params)
        return self.find(record_id)

    def delete(self, record_id: int) -> None:
        statement = sql.SQL("DELETE FROM {table} WHERE {key} = %(id)s RETURNING {key}")
        self._write_one(
            statement.format(
                table=sql.Identifier(self.table), key=sql.Identifier(self.key)
            ),
            {"id": record_id},
        )

    def count(self) -> int:
        statement = sql.SQL("SELECT count(*) FROM {}").format(
            sql.Identifier(self.table)
        )
        return self._con.execute(statement).fetchone()[0]

    def insert_statement(self) -> sql.Composed:
        statement = sql.SQL(
            "INSERT INTO {table} ({columns}) VALUES ({values}) RETURNING {key}"
        )
        return statement.format(
            table=sql.Identifier(self.table),
            columns=_identifiers(self._writable),
            values=sql.SQL(", ").join(map(sql.Placeholder, self._writable)),
            key=sql.Identifier(self.key),
        )

    def _update_statement(self) -> sql.Composed:
        assignments = sql.SQL(", ").join(
            sql.SQL("{} = {}").format(sql.Identifier(name), sql.Placeholder(name))
            for name in self._writable
        )
        statement = sql.SQL(
            "UPDATE {table} SET {assignments} WHERE {key} = {id} RETURNING {key}"
        )
        return statement.format(
            table=sql.Identifier(self.table),
            assignments=assignments,
            key=sql.Identifier(self.key),
            id=sql.Placeholder(self.key),
        )

    def _select(self, condition: str = "TRUE", params: tuple = ()) -> list[T]:
        statement = sql.SQL(
            "SELECT {columns} FROM {source} WHERE {condition} ORDER BY {order}"
        )
        query = statement.format(
            columns=_identifiers(self._columns),
            source=sql.Identifier(self.source or self.table),
            condition=sql.SQL(condition),
            order=sql.SQL(self.order_by),
        )
        with self._con.cursor(row_factory=class_row(self.model)) as cursor:
            return cursor.execute(query, params).fetchall()

    def _write_one(self, statement: sql.Composed, params: Mapping[str, object]) -> int:
        with self._con.transaction():
            row = self._con.execute(statement, params).fetchone()
        if row is None:
            raise RecordNotFound
        return row[0]
