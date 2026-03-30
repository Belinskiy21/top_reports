import pytest

from app.services.sec.filing_url_service import FilingUrlService


def test_get_recent_report_metadata_returns_latest_matching_form() -> None:
    service = FilingUrlService()

    metadata = service.get_recent_report_metadata(
        cik="0000320193",
        report_type="10-K",
        submissions={
            "filings": {
                "recent": {
                    "form": ["8-K", "10-K"],
                    "accessionNumber": ["0000320193-24-000002", "0000320193-24-000001"],
                    "filingDate": ["2024-12-01", "2024-11-01"],
                    "primaryDocument": ["current.htm", "aapl-10k.htm"],
                },
            },
        },
    )

    assert metadata.accession_number == "0000320193-24-000001"
    assert metadata.primary_document == "aapl-10k.htm"
    assert metadata.filing_date == "2024-11-01"
    assert metadata.filing_url.endswith("/320193/000032019324000001/aapl-10k.htm")


def test_get_recent_report_metadata_raises_for_missing_filings() -> None:
    service = FilingUrlService()

    with pytest.raises(ValueError, match="does not contain filings"):
        _ = service.get_recent_report_metadata(
            cik="0000320193",
            report_type="10-K",
            submissions={},
        )
