from datetime import datetime
from typing import final

from sqlalchemy import DateTime, ForeignKey, String, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db import Base


@final
class ReportFileRecord(Base):
    __tablename__ = "report_files"
    __table_args__ = (  # pyright: ignore[reportAny]
        UniqueConstraint(
            "company_id",
            "report_type",
            "accession_number",
            "primary_document",
            name="uq_report_files_metadata",
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    company_id: Mapped[int] = mapped_column(ForeignKey("companies.id"), index=True)
    report_type: Mapped[str] = mapped_column(String(20), index=True)
    accession_number: Mapped[str] = mapped_column(String(32), index=True)
    primary_document: Mapped[str] = mapped_column(String(255))
    filing_date: Mapped[str] = mapped_column(String(20))
    filing_url: Mapped[str] = mapped_column(String(2048))
    stored_file_name: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    created_by: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
    )
