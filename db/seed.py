from typing import cast

from sqlalchemy import Table

from app.db import Base, engine, ensure_database_exists
from app.models.user import UserRecord


def seed() -> None:
    ensure_database_exists()
    Base.metadata.create_all(bind=engine, tables=[cast(Table, UserRecord.__table__)])


if __name__ == "__main__":
    seed()
