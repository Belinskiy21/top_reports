from datetime import datetime
from typing import final

from sqlalchemy import DateTime, ForeignKey, String, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db import Base


@final
class DownloadHistoryRecord(Base):
    __tablename__ = "download_history"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    report_file_id: Mapped[int] = mapped_column(ForeignKey("report_files.id"), index=True)
    stored_file_name: Mapped[str] = mapped_column(String(255), index=True)
    downloaded_by: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    downloaded_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
    )
