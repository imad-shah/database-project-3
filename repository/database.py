import os
from pathlib import Path

import psycopg

SCHEMA_PATH = Path(__file__).parent / "schema.sql"
TABLES = ("agents", "buyers", "sellers", "properties", "listings", "sales")
DEFAULT_URL = "postgresql://realestate:realestate@localhost:5432/realestate"


def database_url() -> str:
    return os.environ.get("DATABASE_URL", DEFAULT_URL)


def get_connection(url: str | None = None) -> psycopg.Connection:
    return psycopg.connect(url or database_url(), autocommit=True)


def init_db(con: psycopg.Connection) -> None:
    con.execute(SCHEMA_PATH.read_bytes())
