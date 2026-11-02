import psycopg
import pytest
from psycopg import sql
from psycopg.conninfo import make_conninfo

from controller import Controllers, build_controllers
from repository import Repositories, get_connection, init_db
from repository.database import database_url
from seed import populate

TEST_DATABASE = "realestate_test"


def _recreate(admin: psycopg.Connection, statement: str) -> None:
    admin.execute(sql.SQL(statement).format(sql.Identifier(TEST_DATABASE)))


@pytest.fixture(scope="session")
def session_con():
    try:
        admin = get_connection()
    except psycopg.OperationalError:
        pytest.skip("PostgreSQL is not running")
    _recreate(admin, "DROP DATABASE IF EXISTS {}")
    _recreate(admin, "CREATE DATABASE {}")
    con = get_connection(make_conninfo(database_url(), dbname=TEST_DATABASE))
    init_db(con)
    yield con
    con.close()
    _recreate(admin, "DROP DATABASE {}")
    admin.close()


@pytest.fixture
def con(session_con):
    with session_con.transaction(force_rollback=True):
        yield session_con


@pytest.fixture
def repositories(con) -> Repositories:
    return Repositories.connect(con)


@pytest.fixture
def controllers(repositories) -> Controllers:
    return build_controllers(repositories)


@pytest.fixture
def seeded(repositories) -> Repositories:
    populate(repositories)
    return repositories
