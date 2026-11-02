from repository import Repositories, get_connection, init_db

from .generator import populate, reset


def main() -> None:
    with get_connection() as con:
        init_db(con)
        repositories = Repositories.connect(con)
        with con.transaction():
            reset(con)
            populate(repositories)
        for name in ("agents", "buyers", "sellers", "properties", "sales"):
            print(f"{name}: {getattr(repositories, name).count()}")


if __name__ == "__main__":
    main()
