from sqlalchemy.orm import Session

from app.services.company import CompanyService
from app.services.report_file import ReportFileService
from app.services.sec.recent_report_metadata import RecentReportMetadata


def test_create_and_find_report_file(db_session: Session) -> None:
    company = CompanyService().create(
        db_session,
        name="Apple",
        cik="0000320193",
        ticker="AAPL",
    )
    report_metadata = RecentReportMetadata(
        accession_number="0000320193-24-000001",
        primary_document="aapl-10k.htm",
        filing_date="2024-10-01",
        filing_url="https://www.sec.gov/Archives/edgar/data/320193/1/aapl-10k.htm",
    )
    service = ReportFileService()

    created_report = service.create(
        db_session,
        company_id=company.id,
        report_type="10-K",
        report_metadata=report_metadata,
        stored_file_name="apple_report.pdf",
        created_by=1,
    )
    cached_report = service.find_cached(
        db_session,
        company_id=company.id,
        report_type="10-K",
        report_metadata=report_metadata,
    )
    found_report = service.find_by_stored_file_name(db_session, "apple_report.pdf")

    assert created_report.id > 0
    assert cached_report is not None
    assert cached_report.id == created_report.id
    assert found_report is not None
    assert found_report.stored_file_name == "apple_report.pdf"
