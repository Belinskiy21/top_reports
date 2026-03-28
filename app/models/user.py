from typing import final

from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column

from app.db import Base


@final
class UserRecord(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    email: Mapped[str] = mapped_column(String(255))
