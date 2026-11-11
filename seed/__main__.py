from repository import TABLES, Repositories, get_connection

from .generator import populate, reset


def main() -> None:
    with get_connection() as con:
        repositories = Repositories.connect(con)
        with con.transaction():
            reset(con)
            populate(repositories)
        for name in TABLES:
            print(f"{name}: {getattr(repositories, name).count()}")


if __name__ == "__main__":
    main()
