import os
from collections.abc import Generator
from getpass import getuser

from sqlalchemy import create_engine, text
from sqlalchemy.engine import URL, make_url
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

DEFAULT_DB_USER = os.getenv("PGUSER", getuser())
DEFAULT_DB_PASSWORD = os.getenv("PGPASSWORD", "")
DEFAULT_DB_HOST = os.getenv("PGHOST", "localhost")
DEFAULT_DB_PORT = os.getenv("PGPORT", "5432")
DEFAULT_DB_NAME = os.getenv("PGDATABASE", "top_reports")

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    URL.create(
        drivername="postgresql+psycopg",
        username=DEFAULT_DB_USER,
        password=DEFAULT_DB_PASSWORD or None,
        host=DEFAULT_DB_HOST,
        port=int(DEFAULT_DB_PORT),
        database=DEFAULT_DB_NAME,
    ).render_as_string(hide_password=False),
)

engine = create_engine(DATABASE_URL, future=True)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, expire_on_commit=False)


class Base(DeclarativeBase):
    pass


def ensure_database_exists() -> None:
    url = make_url(DATABASE_URL)
    if not _is_postgres_url(url):
        return

    database_name = url.database
    if not database_name:
        return

    admin_url = url.set(database="postgres")
    admin_engine = create_engine(admin_url, isolation_level="AUTOCOMMIT")

    with admin_engine.connect() as connection:
        database_exists = connection.execute(
            text("SELECT 1 FROM pg_database WHERE datname = :database_name"),
            {"database_name": database_name},
        ).scalar_one_or_none()
        if database_exists is None:
            quoted_database_name = _quote_postgres_identifier(database_name)
            _ = connection.execute(text(f"CREATE DATABASE {quoted_database_name}"))

    admin_engine.dispose()


def get_session() -> Generator[Session]:
    with SessionLocal() as session:
        yield session


def _is_postgres_url(url: URL) -> bool:
    return url.get_backend_name() == "postgresql"


def _quote_postgres_identifier(identifier: str) -> str:
    escaped_identifier = identifier.replace('"', '""')
    return f'"{escaped_identifier}"'
