from collections.abc import Sequence
from typing import Final

import httpx
from fastapi.responses import Response
from sqlalchemy.orm import Session

from app.exceptions.sec import SecRequestError
from app.services.download_history import DownloadHistoryService
from app.services.report_file import ReportFileService
from app.services.sec.sec_report_type_protocol import SecReportTypeProtocol
from app.services.sec.ten_k_report_service import TenKReportService
from app.services.storage.storage_service import StorageService


class SecReportService:
    def __init__(self) -> None:
        self._download_history_service: DownloadHistoryService = DownloadHistoryService()
        self._report_file_service: ReportFileService = ReportFileService()
        self._storage_service: StorageService = StorageService()
        self._ten_k_report_service: TenKReportService = TenKReportService()
        self._report_type_services: Final[dict[str, SecReportTypeProtocol]] = {
            TenKReportService.REPORT_TYPE: self._ten_k_report_service,
        }

    async def get_recent_report_urls(
        self,
        session: Session,
        report_type: str,
        company_names: Sequence[str],
        public_base_url: str,
        created_by: int,
    ) -> dict[str, str]:
        report_service = self._get_report_type_service(report_type)
        try:
            return await report_service.get_recent_report_urls(
                session=session,
                company_names=company_names,
                public_base_url=public_base_url,
                created_by=created_by,
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
            for report_service in self._report_type_services.values():
                await report_service.prefetch_recent_reports(
                    session,
                    created_by=created_by,
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

    def get_supported_report_types(self) -> list[str]:
        return list(self._report_type_services.keys())

    def _get_report_type_service(self, report_type: str) -> SecReportTypeProtocol:
        report_service = self._report_type_services.get(report_type)
        if report_service is None:
            raise ValueError(f"Unsupported report type: {report_type}")
        return report_service
