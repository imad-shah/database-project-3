import psycopg

from controller import build_controllers
from gui import RealEstateApp
from repository import Repositories, get_connection, init_db


def main() -> None:
    try:
        con = get_connection()
    except psycopg.OperationalError:
        raise SystemExit(
            "Could not reach PostgreSQL. Start it with: docker compose up -d --wait"
        ) from None
    init_db(con)
    app = RealEstateApp(build_controllers(Repositories.connect(con)))
    app.mainloop()
    con.close()


if __name__ == "__main__":
    main()
