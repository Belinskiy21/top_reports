from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.report_file import ReportFileRecord
from app.services.sec.recent_report_metadata import RecentReportMetadata


class ReportFileService:
    def find_cached(
        self,
        session: Session,
        *,
        company_id: int,
        report_type: str,
        report_metadata: RecentReportMetadata,
    ) -> ReportFileRecord | None:
        return session.scalar(
            select(ReportFileRecord).where(
                ReportFileRecord.company_id == company_id,
                ReportFileRecord.report_type == report_type,
                ReportFileRecord.accession_number == report_metadata.accession_number,
                ReportFileRecord.primary_document == report_metadata.primary_document,
            ),
        )

    def create(
        self,
        session: Session,
        *,
        company_id: int,
        report_type: str,
        report_metadata: RecentReportMetadata,
        stored_file_name: str,
        created_by: int,
    ) -> ReportFileRecord:
        report_record = ReportFileRecord(
            company_id=company_id,
            report_type=report_type,
            accession_number=report_metadata.accession_number,
            primary_document=report_metadata.primary_document,
            filing_date=report_metadata.filing_date,
            filing_url=report_metadata.filing_url,
            stored_file_name=stored_file_name,
            created_by=created_by,
        )
        session.add(report_record)
        session.commit()
        session.refresh(report_record)
        return report_record

    def find_by_stored_file_name(self, session: Session, file_name: str) -> ReportFileRecord | None:
        return session.scalar(
            select(ReportFileRecord).where(ReportFileRecord.stored_file_name == file_name),
        )

    def find_latest_by_company_and_type(
        self,
        session: Session,
        *,
        company_id: int,
        report_type: str,
    ) -> ReportFileRecord | None:
        return session.scalar(
            select(ReportFileRecord)
            .where(
                ReportFileRecord.company_id == company_id,
                ReportFileRecord.report_type == report_type,
            )
            .order_by(ReportFileRecord.created_at.desc(), ReportFileRecord.id.desc()),
        )

    def update_stored_file_name(
        self,
        session: Session,
        report_file: ReportFileRecord,
        stored_file_name: str,
    ) -> ReportFileRecord:
        report_file.stored_file_name = stored_file_name
        session.add(report_file)
        session.commit()
        session.refresh(report_file)
        return report_file

    def update_report(
        self,
        session: Session,
        *,
        report_file: ReportFileRecord,
        report_metadata: RecentReportMetadata,
        stored_file_name: str,
        created_by: int,
    ) -> ReportFileRecord:
        report_file.accession_number = report_metadata.accession_number
        report_file.primary_document = report_metadata.primary_document
        report_file.filing_date = report_metadata.filing_date
        report_file.filing_url = report_metadata.filing_url
        report_file.stored_file_name = stored_file_name
        report_file.created_by = created_by
        session.add(report_file)
        session.commit()
        session.refresh(report_file)
        return report_file
