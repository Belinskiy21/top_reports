from dataclasses import dataclass


@dataclass(frozen=True)
class RecentReportMetadata:
    accession_number: str
    primary_document: str
    filing_date: str
    filing_url: str
