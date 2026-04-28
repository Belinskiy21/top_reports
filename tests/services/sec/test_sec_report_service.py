import asyncio
from pathlib import Path
from typing import cast

import pytest
from fastapi.responses import Response
from sqlalchemy.orm import Session

from app.models.company import CompanyRecord
from app.models.report_file import ReportFileRecord
from app.services.sec.recent_filing_metadata_service import RecentFilingMetadataService
from app.services.sec.recent_report_metadata import RecentReportMetadata
from app.services.sec.sec_report_service import SecReportService


class StubCompanyService:
    def __init__(self, company: CompanyRecord | None = None) -> None:
        self.company: CompanyRecord | None = company

    def find_all(self, session: Session) -> list[CompanyRecord]:
        _ = session
        return [] if self.company is None else [self.company]

    def find_by_name(self, session: Session, company_name: str) -> CompanyRecord | None:
        _ = session
        _ = company_name
        return self.company


class StubSecClient:
    def __init__(self) -> None:
        self.download_calls: list[str] = []

    async def get_submissions(self, cik: str) -> dict[str, object]:
        assert cik == "0000320193"
        return {"filings": {"recent": {}}}

    async def download_file(self, url: str) -> bytes:
        self.download_calls.append(url)
        return b"<html>Report</html>"


class StubRecentFilingMetadataService:
    def get_data(
        self,
        cik: str,
        report_type: str,
        submissions: dict[str, object],
    ) -> RecentReportMetadata:
        assert cik == "0000320193"
        assert report_type == "10-K"
        assert submissions == {"filings": {"recent": {}}}
        return RecentReportMetadata(
            accession_number="0000320193-24-000001",
            primary_document="aapl-10k.htm",
            filing_date="2024-10-01",
            filing_url="https://www.sec.gov/Archives/edgar/data/320193/1/aapl-10k.htm",
        )


class StubReportFileService:
    def __init__(self, cached_report: ReportFileRecord | None = None) -> None:
        self.cached_report: ReportFileRecord | None = cached_report
        self.created_kwargs: dict[str, object] | None = None
        self.updated_report_kwargs: dict[str, object] | None = None

    def find_cached(
        self,
        session: Session,
        *,
        company_id: int,
        report_type: str,
        report_metadata: RecentReportMetadata,
    ) -> ReportFileRecord | None:
        _ = session
        _ = company_id
        _ = report_type
        _ = report_metadata
        return self.cached_report

    def create(self, session: Session, **kwargs: object) -> ReportFileRecord:
        _ = session
        self.created_kwargs = kwargs
        report_metadata = kwargs["report_metadata"]
        company_id = kwargs["company_id"]
        report_type = kwargs["report_type"]
        stored_file_name = kwargs["stored_file_name"]
        created_by = kwargs["created_by"]
        assert isinstance(report_metadata, RecentReportMetadata)
        assert isinstance(company_id, int)
        assert isinstance(report_type, str)
        assert isinstance(stored_file_name, str)
        assert isinstance(created_by, int)
        return ReportFileRecord(
            id=1,
            company_id=company_id,
            report_type=report_type,
            accession_number=report_metadata.accession_number,
            primary_document=report_metadata.primary_document,
            filing_date=report_metadata.filing_date,
            filing_url=report_metadata.filing_url,
            stored_file_name=stored_file_name,
            created_by=created_by,
        )

    def find_by_stored_file_name(self, session: Session, file_name: str) -> ReportFileRecord | None:
        _ = session
        _ = file_name
        return self.cached_report

    def find_latest_by_company_and_type(
        self,
        session: Session,
        *,
        company_id: int,
        report_type: str,
    ) -> ReportFileRecord | None:
        _ = session
        _ = company_id
        _ = report_type
        return self.cached_report

    def update_report(self, session: Session, **kwargs: object) -> ReportFileRecord:
        _ = session
        self.updated_report_kwargs = kwargs
        report_file = kwargs["report_file"]
        report_metadata = kwargs["report_metadata"]
        stored_file_name = kwargs["stored_file_name"]
        created_by = kwargs["created_by"]
        assert isinstance(report_file, ReportFileRecord)
        assert isinstance(report_metadata, RecentReportMetadata)
        assert isinstance(stored_file_name, str)
        assert isinstance(created_by, int)
        report_file.accession_number = report_metadata.accession_number
        report_file.primary_document = report_metadata.primary_document
        report_file.filing_date = report_metadata.filing_date
        report_file.filing_url = report_metadata.filing_url
        report_file.stored_file_name = stored_file_name
        report_file.created_by = created_by
        self.cached_report = report_file
        return report_file


class StubDownloadHistoryService:
    def __init__(self) -> None:
        self.created_kwargs: dict[str, object] | None = None

    def create(self, session: Session, **kwargs: object) -> object:
        _ = session
        self.created_kwargs = kwargs
        return object()


class StubStorageService:
    def __init__(self, *, has_valid_pdf: bool = True) -> None:
        self.stored_company_name: str | None = None
        self.downloaded_file_name: str | None = None
        self.deleted_file_name: str | None = None
        self._has_valid_pdf: bool = has_valid_pdf

    def store_pdf(self, company_name: str, pdf_path: Path) -> str:
        self.stored_company_name = company_name
        assert pdf_path.suffix == ".pdf"
        assert pdf_path.exists()
        return "apple_report.pdf"

    def get_public_url(self, file_name: str, public_base_url: str) -> str:
        return f"{public_base_url.rstrip('/')}/api/v1/files/{file_name}"

    def has_valid_pdf(self, file_name: str) -> bool:
        _ = file_name
        return self._has_valid_pdf

    def download_file(self, file_name: str) -> Response:
        self.downloaded_file_name = file_name
        return Response(content=b"%PDF-1.4 test", media_type="application/pdf")

    def delete_file(self, file_name: str) -> None:
        self.deleted_file_name = file_name


class StubSecAssetFetcher:
    def build(self) -> object:
        return object()


def test_get_recent_report_urls_returns_cached_file_url(db_session: Session) -> None:
    service = SecReportService()
    service._ten_k_report_service._company_service = StubCompanyService(  # type: ignore[assignment]  # pyright: ignore[reportAttributeAccessIssue, reportPrivateUsage]
        CompanyRecord(id=1, name="Apple", cik="0000320193", ticker="AAPL"),
    )
    service._ten_k_report_service._sec_client = StubSecClient()  # type: ignore[assignment]  # pyright: ignore[reportAttributeAccessIssue, reportPrivateUsage]
    service._ten_k_report_service._recent_filing_metadata_service = cast(  # pyright: ignore[reportPrivateUsage]
        RecentFilingMetadataService,
        cast(object, StubRecentFilingMetadataService()),
    )
    service._ten_k_report_service._report_file_service = StubReportFileService(  # type: ignore[assignment]  # pyright: ignore[reportAttributeAccessIssue, reportPrivateUsage]
        ReportFileRecord(
            id=3,
            company_id=1,
            report_type="10-K",
            accession_number="0000320193-24-000001",
            primary_document="aapl-10k.htm",
            filing_date="2024-10-01",
            filing_url="https://www.sec.gov/test",
            stored_file_name="cached_apple.pdf",
            created_by=1,
        ),
    )
    service._ten_k_report_service._storage_service = StubStorageService()  # type: ignore[assignment]  # pyright: ignore[reportAttributeAccessIssue, reportPrivateUsage]

    report_urls = asyncio.run(
        service.get_recent_report_urls(
            session=db_session,
            report_type="10-K",
            company_names=["Apple"],
            public_base_url="http://testserver/",
            created_by=1,
        ),
    )

    assert report_urls == {"Apple": "http://testserver/api/v1/files/cached_apple.pdf"}


def test_prefetch_recent_reports_creates_and_stores_missing_report(
    db_session: Session,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    service = SecReportService()
    report_file_service = StubReportFileService()
    storage_service = StubStorageService()
    service._ten_k_report_service._company_service = StubCompanyService(  # type: ignore[assignment]  # pyright: ignore[reportAttributeAccessIssue, reportPrivateUsage]
        CompanyRecord(id=1, name="Apple", cik="0000320193", ticker="AAPL"),
    )
    service._ten_k_report_service._sec_client = StubSecClient()  # type: ignore[assignment]  # pyright: ignore[reportAttributeAccessIssue, reportPrivateUsage]
    service._ten_k_report_service._recent_filing_metadata_service = cast(  # pyright: ignore[reportPrivateUsage]
        RecentFilingMetadataService,
        cast(object, StubRecentFilingMetadataService()),
    )
    service._ten_k_report_service._report_file_service = report_file_service  # type: ignore[assignment]  # pyright: ignore[reportAttributeAccessIssue, reportPrivateUsage]
    service._ten_k_report_service._storage_service = storage_service  # type: ignore[assignment]  # pyright: ignore[reportAttributeAccessIssue, reportPrivateUsage]
    service._ten_k_report_service._sec_asset_fetcher = StubSecAssetFetcher()  # type: ignore[assignment]  # pyright: ignore[reportAttributeAccessIssue, reportPrivateUsage]

    def stub_html_to_pdf(
        origin_file: Path,
        base_url: str | None = None,
        url_fetcher: object | None = None,
    ) -> Path:
        assert base_url == "https://www.sec.gov/Archives/edgar/data/320193/1/"
        assert url_fetcher is not None
        pdf_path = origin_file.with_suffix(".pdf")
        _ = pdf_path.write_bytes(b"%PDF-1.4 test")
        return pdf_path

    monkeypatch.setattr("app.services.sec.ten_k_report_service.html_to_pdf", stub_html_to_pdf)
    _ = asyncio.run(
        service._ten_k_report_service.prefetch_recent_reports(  # pyright: ignore[reportPrivateUsage]
            session=db_session,
            created_by=1,
        ),
    )

    assert report_file_service.created_kwargs is not None
    assert report_file_service.created_kwargs["stored_file_name"] == "apple_report.pdf"
    assert storage_service.stored_company_name == "Apple"


def test_prefetch_recent_reports_regenerates_invalid_cached_pdf(
    db_session: Session,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    service = SecReportService()
    cached_report = ReportFileRecord(
        id=3,
        company_id=1,
        report_type="10-K",
        accession_number="0000320193-24-000001",
        primary_document="aapl-10k.htm",
        filing_date="2024-10-01",
        filing_url="https://www.sec.gov/test",
        stored_file_name="broken_apple.pdf",
        created_by=1,
    )
    report_file_service = StubReportFileService(cached_report)
    storage_service = StubStorageService(has_valid_pdf=False)
    service._ten_k_report_service._company_service = StubCompanyService(  # type: ignore[assignment]  # pyright: ignore[reportAttributeAccessIssue, reportPrivateUsage]
        CompanyRecord(id=1, name="Apple", cik="0000320193", ticker="AAPL"),
    )
    service._ten_k_report_service._sec_client = StubSecClient()  # type: ignore[assignment]  # pyright: ignore[reportAttributeAccessIssue, reportPrivateUsage]
    service._ten_k_report_service._recent_filing_metadata_service = cast(  # pyright: ignore[reportPrivateUsage]
        RecentFilingMetadataService,
        cast(object, StubRecentFilingMetadataService()),
    )
    service._ten_k_report_service._report_file_service = report_file_service  # type: ignore[assignment]  # pyright: ignore[reportAttributeAccessIssue, reportPrivateUsage]
    service._ten_k_report_service._storage_service = storage_service  # type: ignore[assignment]  # pyright: ignore[reportAttributeAccessIssue, reportPrivateUsage]
    service._ten_k_report_service._sec_asset_fetcher = StubSecAssetFetcher()  # type: ignore[assignment]  # pyright: ignore[reportAttributeAccessIssue, reportPrivateUsage]

    def stub_html_to_pdf(
        origin_file: Path,
        base_url: str | None = None,
        url_fetcher: object | None = None,
    ) -> Path:
        assert base_url == "https://www.sec.gov/Archives/edgar/data/320193/1/"
        assert url_fetcher is not None
        pdf_path = origin_file.with_suffix(".pdf")
        _ = pdf_path.write_bytes(b"%PDF-1.4 test")
        return pdf_path

    monkeypatch.setattr("app.services.sec.ten_k_report_service.html_to_pdf", stub_html_to_pdf)
    _ = asyncio.run(
        service._ten_k_report_service.prefetch_recent_reports(  # pyright: ignore[reportPrivateUsage]
            session=db_session,
            created_by=1,
        ),
    )

    assert report_file_service.updated_report_kwargs is not None
    assert report_file_service.updated_report_kwargs["stored_file_name"] == "apple_report.pdf"
    assert report_file_service.created_kwargs is None
    assert storage_service.deleted_file_name == "broken_apple.pdf"


def test_get_recent_report_urls_raises_when_cached_report_is_missing(db_session: Session) -> None:
    service = SecReportService()
    service._ten_k_report_service._company_service = StubCompanyService(  # type: ignore[assignment]  # pyright: ignore[reportAttributeAccessIssue, reportPrivateUsage]
        CompanyRecord(id=1, name="Apple", cik="0000320193", ticker="AAPL"),
    )
    service._ten_k_report_service._report_file_service = StubReportFileService()  # type: ignore[assignment]  # pyright: ignore[reportAttributeAccessIssue, reportPrivateUsage]

    with pytest.raises(ValueError, match="Report is not available yet for company: Apple"):
        _ = asyncio.run(
            service.get_recent_report_urls(
                session=db_session,
                report_type="10-K",
                company_names=["Apple"],
                public_base_url="http://testserver/",
                created_by=1,
            ),
        )


def test_get_recent_report_urls_raises_when_cached_pdf_is_invalid(db_session: Session) -> None:
    service = SecReportService()
    service._ten_k_report_service._company_service = StubCompanyService(  # type: ignore[assignment]  # pyright: ignore[reportAttributeAccessIssue, reportPrivateUsage]
        CompanyRecord(id=1, name="Apple", cik="0000320193", ticker="AAPL"),
    )
    service._ten_k_report_service._report_file_service = StubReportFileService(  # type: ignore[assignment]  # pyright: ignore[reportAttributeAccessIssue, reportPrivateUsage]
        ReportFileRecord(
            id=3,
            company_id=1,
            report_type="10-K",
            accession_number="0000320193-24-000001",
            primary_document="aapl-10k.htm",
            filing_date="2024-10-01",
            filing_url="https://www.sec.gov/test",
            stored_file_name="broken_apple.pdf",
            created_by=1,
        ),
    )
    service._ten_k_report_service._storage_service = StubStorageService(  # type: ignore[assignment]  # pyright: ignore[reportAttributeAccessIssue, reportPrivateUsage]
        has_valid_pdf=False,
    )

    with pytest.raises(ValueError, match="Report is not available yet for company: Apple"):
        _ = asyncio.run(
            service.get_recent_report_urls(
                session=db_session,
                report_type="10-K",
                company_names=["Apple"],
                public_base_url="http://testserver/",
                created_by=1,
            ),
        )


def test_download_file_records_history_and_returns_response(db_session: Session) -> None:
    service = SecReportService()
    service._report_file_service = StubReportFileService(  # type: ignore[assignment]  # pyright: ignore[reportAttributeAccessIssue, reportPrivateUsage]
        ReportFileRecord(
            id=3,
            company_id=1,
            report_type="10-K",
            accession_number="0000320193-24-000001",
            primary_document="aapl-10k.htm",
            filing_date="2024-10-01",
            filing_url="https://www.sec.gov/test",
            stored_file_name="apple_report.pdf",
            created_by=1,
        ),
    )
    download_history_service = StubDownloadHistoryService()
    storage_service = StubStorageService()
    service._download_history_service = download_history_service  # type: ignore[assignment]  # pyright: ignore[reportAttributeAccessIssue, reportPrivateUsage]
    service._storage_service = storage_service  # type: ignore[assignment]  # pyright: ignore[reportAttributeAccessIssue, reportPrivateUsage]

    response = service.download_file(db_session, "apple_report.pdf", downloaded_by=2)

    assert response.media_type == "application/pdf"
    assert download_history_service.created_kwargs is not None
    assert download_history_service.created_kwargs["downloaded_by"] == 2
    assert storage_service.downloaded_file_name == "apple_report.pdf"


def test_get_recent_report_urls_raises_for_unsupported_report_type(db_session: Session) -> None:
    service = SecReportService()

    with pytest.raises(ValueError, match="Unsupported report type"):
        _ = asyncio.run(
            service.get_recent_report_urls(
                session=db_session,
                report_type="8-K",
                company_names=["Apple"],
                public_base_url="http://testserver/",
                created_by=1,
            ),
        )


def test_get_recent_report_urls_raises_for_unsupported_company(db_session: Session) -> None:
    service = SecReportService()
    service._ten_k_report_service._company_service = StubCompanyService()  # type: ignore[assignment]  # pyright: ignore[reportAttributeAccessIssue, reportPrivateUsage]

    with pytest.raises(ValueError, match="Company is not supported: Unknown"):
        _ = asyncio.run(
            service.get_recent_report_urls(
                session=db_session,
                report_type="10-K",
                company_names=["Unknown"],
                public_base_url="http://testserver/",
                created_by=1,
            ),
        )
