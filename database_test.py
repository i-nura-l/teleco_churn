from sqlalchemy import create_engine, text
from sqlalchemy.exc import SQLAlchemyError

from db_config import get_database_url


def main() -> None:
    database_url = get_database_url()
    engine = create_engine(database_url)

    try:
        with engine.connect() as connection:
            result = connection.execute(
                text("SELECT DATABASE() AS database_name, VERSION() AS mysql_version")
            )
            row = result.fetchone()

            print("Successfully connected to the MySQL database.")
            if row is not None:
                print(f"Database: {row.database_name}")
                print(f"MySQL version: {row.mysql_version}")
    except SQLAlchemyError as exc:
        print("Could not connect to MySQL.")
        print("Check MYSQL_HOST, MYSQL_PORT, MYSQL_USER, MYSQL_PASSWORD, and MYSQL_DATABASE.")
        print(f"Details: {exc}")
    finally:
        engine.dispose()


if __name__ == "__main__":
    main()