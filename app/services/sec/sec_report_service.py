import asyncio
import tempfile
from collections.abc import Sequence
from pathlib import Path
from typing import Final

import httpx
from fastapi.responses import Response
from sqlalchemy.orm import Session

from app.exceptions.sec import SecRequestError
from app.models.company import CompanyRecord
from app.models.report_file import ReportFileRecord
from app.services.company import CompanyService
from app.services.converters.html_to_pdf.html_to_pdf import filing_base_url, html_to_pdf
from app.services.download_history import DownloadHistoryService
from app.services.report_file import ReportFileService
from app.services.sec.filing_url_service import FilingUrlService
from app.services.sec.recent_report_metadata import RecentReportMetadata
from app.services.sec.sec_asset_fetcher import SecAssetFetcher
from app.services.sec.sec_client import SecClient
from app.services.sec.sec_report_request import SecReportRequest
from app.services.storage.storage_service import StorageService


class SecReportService:
    SUPPORTED_REPORT_TYPES: Final[set[str]] = {"10-K"}

    def __init__(self) -> None:
        self._sec_client: SecClient = SecClient()
        self._company_service: CompanyService = CompanyService()
        self._filing_url_service: FilingUrlService = FilingUrlService()
        self._report_file_service: ReportFileService = ReportFileService()
        self._download_history_service: DownloadHistoryService = DownloadHistoryService()
        self._storage_service: StorageService = StorageService()
        self._sec_asset_fetcher: SecAssetFetcher = SecAssetFetcher()

    async def get_recent_report_urls(
        self,
        session: Session,
        report_type: str,
        company_names: Sequence[str],
        public_base_url: str,
        created_by: int,
    ) -> dict[str, str]:
        if report_type not in self.SUPPORTED_REPORT_TYPES:
            raise ValueError(f"Unsupported report type: {report_type}")

        try:
            with tempfile.TemporaryDirectory() as temp_dir:
                request = SecReportRequest(
                    report_type=report_type,
                    public_base_url=public_base_url,
                    created_by=created_by,
                    temp_path=Path(temp_dir),
                )
                return await self._collect_report_urls(
                    session=session,
                    company_names=company_names,
                    request=request,
                )
        except httpx.HTTPStatusError as exc:
            raise SecRequestError(
                status_code=502,
                upstream_status_code=exc.response.status_code,
                upstream_url=str(exc.request.url),
                upstream_message=exc.response.text[:500],
            ) from exc
        except httpx.HTTPError as exc:
            raise SecRequestError(
                status_code=502,
                upstream_url=str(exc.request.url),
                upstream_message=str(exc),
            ) from exc

    async def prefetch_recent_reports(
        self,
        session: Session,
        *,
        created_by: int,
    ) -> None:
        try:
            with tempfile.TemporaryDirectory() as temp_dir:
                request = SecReportRequest(
                    report_type="10-K",
                    public_base_url="",
                    created_by=created_by,
                    temp_path=Path(temp_dir),
                )
                for company in self._company_service.find_all(session):
                    _ = await self._ensure_recent_report_file(
                        session=session,
                        company=company,
                        request=request,
                    )
        except httpx.HTTPStatusError as exc:
            raise SecRequestError(
                status_code=502,
                upstream_status_code=exc.response.status_code,
                upstream_url=str(exc.request.url),
                upstream_message=exc.response.text[:500],
            ) from exc
        except httpx.HTTPError as exc:
            raise SecRequestError(
                status_code=502,
                upstream_url=str(exc.request.url),
                upstream_message=str(exc),
            ) from exc

    def download_file(
        self,
        session: Session,
        file_name: str,
        downloaded_by: int,
    ) -> Response:
        report_file = self._report_file_service.find_by_stored_file_name(session, file_name)
        if report_file is None:
            raise FileNotFoundError(file_name)

        _ = self._download_history_service.create(
            session,
            report_file_id=report_file.id,
            stored_file_name=file_name,
            downloaded_by=downloaded_by,
        )
        return self._storage_service.download_file(file_name)

    async def _collect_report_urls(
        self,
        session: Session,
        company_names: Sequence[str],
        request: SecReportRequest,
    ) -> dict[str, str]:
        report_urls: dict[str, str] = {}
        for company_name in company_names:
            report_urls[company_name] = await self._get_report_url(
                session=session,
                company_name=company_name,
                request=request,
            )

        return report_urls

    async def _get_report_url(
        self,
        session: Session,
        company_name: str,
        request: SecReportRequest,
    ) -> str:
        company = self._get_company(
            session,
            company_name,
        )
        stored_file_name = await self._ensure_recent_report_file(
            session=session,
            company=company,
            request=request,
        )
        return self._storage_service.get_public_url(stored_file_name, request.public_base_url)

    async def _ensure_recent_report_file(
        self,
        session: Session,
        company: CompanyRecord,
        request: SecReportRequest,
    ) -> str:
        report_metadata = await self._get_recent_report_metadata(
            company_cik=company.cik,
            report_type=request.report_type,
        )
        cached_report = self._find_cached_report(
            session,
            company.id,
            request.report_type,
            report_metadata,
        )
        if cached_report is not None and self._storage_service.has_valid_pdf(
            cached_report.stored_file_name,
        ):
            return cached_report.stored_file_name

        stored_file_name = await self._build_and_store_report_file(
            company_name=company.name,
            report_metadata=report_metadata,
            request=request,
        )
        latest_report = self._report_file_service.find_latest_by_company_and_type(
            session,
            company_id=company.id,
            report_type=request.report_type,
        )
        previous_file_name = latest_report.stored_file_name if latest_report is not None else None
        if latest_report is None:
            _ = self._report_file_service.create(
                session=session,
                company_id=company.id,
                report_type=request.report_type,
                report_metadata=report_metadata,
                stored_file_name=stored_file_name,
                created_by=request.created_by,
            )
        else:
            _ = self._report_file_service.update_report(
                session=session,
                report_file=latest_report,
                report_metadata=report_metadata,
                stored_file_name=stored_file_name,
                created_by=request.created_by,
            )
        if previous_file_name is not None and previous_file_name != stored_file_name:
            self._storage_service.delete_file(previous_file_name)
        return stored_file_name

    def _get_company(
        self,
        session: Session,
        company_name: str,
    ) -> CompanyRecord:
        existing_company = self._company_service.find_by_name(session, company_name)
        if existing_company is not None:
            return existing_company
        raise ValueError(f"Company is not supported: {company_name}")

    async def _get_recent_report_metadata(
        self,
        company_cik: str,
        report_type: str,
    ) -> RecentReportMetadata:
        submissions = await self._sec_client.get_submissions(company_cik)
        return self._filing_url_service.get_recent_report_metadata(
            cik=company_cik,
            report_type=report_type,
            submissions=submissions,
        )

    async def _build_and_store_report_file(
        self,
        company_name: str,
        report_metadata: RecentReportMetadata,
        request: SecReportRequest,
    ) -> str:
        origin_path = request.temp_path / self._origin_file_name(
            company_name,
            request.report_type,
            report_metadata.filing_url,
        )
        _ = origin_path.write_bytes(
            await self._sec_client.download_file(report_metadata.filing_url),
        )

        pdf_path = await asyncio.to_thread(
            html_to_pdf,
            origin_path,
            filing_base_url(report_metadata.filing_url),
            self._sec_asset_fetcher.build(),
        )
        return self._storage_service.store_pdf(
            company_name=company_name,
            pdf_path=pdf_path,
        )

    def _origin_file_name(self, company_name: str, report_type: str, filing_url: str) -> str:
        suffix = Path(filing_url).suffix or ".txt"
        normalized_company_name = company_name.lower().replace(" ", "_")
        normalized_report_type = report_type.lower().replace("-", "_")
        return f"{normalized_company_name}_{normalized_report_type}{suffix}"

    def _find_cached_report(
        self,
        session: Session,
        company_id: int,
        report_type: str,
        report_metadata: RecentReportMetadata,
    ) -> ReportFileRecord | None:
        return self._report_file_service.find_cached(
            session,
            company_id=company_id,
            report_type=report_type,
            report_metadata=report_metadata,
        )
