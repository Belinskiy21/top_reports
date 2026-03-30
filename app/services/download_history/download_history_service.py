from sqlalchemy.orm import Session

from app.models.download_history import DownloadHistoryRecord


class DownloadHistoryService:
    def create(
        self,
        session: Session,
        *,
        report_file_id: int,
        stored_file_name: str,
        downloaded_by: int,
    ) -> DownloadHistoryRecord:
        record = DownloadHistoryRecord(
            report_file_id=report_file_id,
            stored_file_name=stored_file_name,
            downloaded_by=downloaded_by,
        )
        session.add(record)
        session.commit()
        session.refresh(record)
        return record
