import asyncio
import logging
import os
from contextlib import suppress
from typing import Final

from app.db import SessionLocal
from app.exceptions.sec import SecRequestError
from app.services.sec.sec_report_service import SecReportService
from app.services.user import UserService

logger = logging.getLogger(__name__)


class ReportPrefetchScheduler:
    DEFAULT_PREFETCH_USER_EMAIL: Final[str] = "seeded-user@quartr.dev"

    def __init__(self) -> None:
        self._enabled: bool = os.getenv("REPORT_PREFETCH_ENABLED", "false").lower() == "true"
        self._interval_seconds: int = int(os.getenv("REPORT_PREFETCH_INTERVAL_SECONDS", "86400"))
        self._prefetch_user_email: str = os.getenv(
            "REPORT_PREFETCH_USER_EMAIL",
            self.DEFAULT_PREFETCH_USER_EMAIL,
        )
        self._user_service: UserService = UserService()
        self._sec_report_service: SecReportService = SecReportService()
        self._task: asyncio.Task[None] | None = None

    def start(self) -> None:
        if not self._enabled or self._task is not None:
            return

        self._task = asyncio.create_task(self._run_loop())

    async def stop(self) -> None:
        if self._task is None:
            return

        _ = self._task.cancel()
        with suppress(asyncio.CancelledError):
            await self._task
        self._task = None

    async def _run_loop(self) -> None:
        while True:
            await self._run_once()
            await asyncio.sleep(self._interval_seconds)

    async def _run_once(self) -> None:
        with SessionLocal() as session:
            user = self._user_service.find_by_email(session, self._prefetch_user_email)
            if user is None:
                user = self._user_service.find_first(session)
            if user is None:
                logger.info("Skipping report prefetch because no user exists")
                return

            try:
                await self._sec_report_service.prefetch_recent_reports(
                    session,
                    created_by=user.id,
                )
            except SecRequestError:
                logger.exception("Scheduled SEC prefetch failed")
