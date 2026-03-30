from collections.abc import Sequence
from typing import Protocol

from sqlalchemy.orm import Session


class SecReportTypeProtocol(Protocol):
    REPORT_TYPE: str

    async def get_recent_report_urls(
        self,
        session: Session,
        company_names: Sequence[str],
        public_base_url: str,
        created_by: int,
    ) -> dict[str, str]: ...

    async def prefetch_recent_reports(
        self,
        session: Session,
        *,
        created_by: int,
    ) -> None: ...
