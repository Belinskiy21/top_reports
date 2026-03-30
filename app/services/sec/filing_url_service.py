from typing import cast
from urllib.parse import urljoin

from app.services.sec.recent_report_metadata import RecentReportMetadata
from app.services.sec.sec_client import SEC_BASE_URL


class FilingUrlService:
    def get_recent_report_metadata(
        self,
        cik: str,
        report_type: str,
        submissions: dict[str, object],
    ) -> RecentReportMetadata:
        filings = submissions.get("filings")
        if not isinstance(filings, dict):
            raise ValueError("SEC submissions payload does not contain filings")

        normalized_filings = cast(dict[str, object], filings)
        recent = normalized_filings.get("recent")
        if not isinstance(recent, dict):
            raise ValueError("SEC submissions payload does not contain recent filings")

        normalized_recent = cast(dict[str, object], recent)
        forms = self._require_string_list(normalized_recent.get("form"))
        accession_numbers = self._require_string_list(normalized_recent.get("accessionNumber"))
        filing_dates = self._require_string_list(normalized_recent.get("filingDate"))
        primary_documents = self._require_string_list(normalized_recent.get("primaryDocument"))

        for index, form in enumerate(forms):
            if form != report_type:
                continue

            accession_number = accession_numbers[index].replace("-", "")
            primary_document = primary_documents[index]
            filing_date = filing_dates[index]
            cik_without_padding = str(int(cik))
            filing_url = urljoin(
                SEC_BASE_URL,
                f"Archives/edgar/data/{cik_without_padding}/{accession_number}/{primary_document}",
            )
            return RecentReportMetadata(
                accession_number=accession_numbers[index],
                primary_document=primary_document,
                filing_date=filing_date,
                filing_url=filing_url,
            )

        raise ValueError(f"Recent {report_type} report was not found")

    def _require_string_list(self, value: object) -> list[str]:
        if not isinstance(value, list):
            raise ValueError("SEC submissions payload has invalid filing arrays")

        normalized_value = cast(list[object], value)
        for item in normalized_value:
            if not isinstance(item, str):
                raise ValueError("SEC submissions payload has invalid filing arrays")

        return cast(list[str], normalized_value)
