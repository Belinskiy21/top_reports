import pytest

from app.services.sec.recent_filing_metadata_service import RecentFilingMetadataService


def test_get_data_returns_latest_matching_form() -> None:
    service = RecentFilingMetadataService()

    metadata = service.get_data(
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


def test_get_data_raises_for_missing_filings() -> None:
    service = RecentFilingMetadataService()

    with pytest.raises(ValueError, match="does not contain filings"):
        _ = service.get_data(
            cik="0000320193",
            report_type="10-K",
            submissions={},
        )
