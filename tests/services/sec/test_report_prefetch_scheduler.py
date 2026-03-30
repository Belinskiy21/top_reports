import asyncio

import pytest

import app.services.sec.report_prefetch_scheduler as scheduler_module
from app.models.user import UserRecord
from app.services.sec.report_prefetch_scheduler import ReportPrefetchScheduler


class StubSession:
    def __enter__(self) -> StubSession:
        return self

    def __exit__(self, exc_type: object, exc: object, traceback: object) -> None:
        _ = exc_type
        _ = exc
        _ = traceback


class StubUserService:
    def __init__(self, user: UserRecord | None = None) -> None:
        self.user: UserRecord | None = user
        self.find_by_email_called_with: str | None = None
        self.find_first_called: bool = False

    def find_by_email(self, session: StubSession, email: str) -> UserRecord | None:
        _ = session
        self.find_by_email_called_with = email
        return self.user

    def find_first(self, session: StubSession) -> UserRecord | None:
        _ = session
        self.find_first_called = True
        return self.user


class StubSecReportService:
    def __init__(self) -> None:
        self.called_with: dict[str, object] | None = None

    async def prefetch_recent_reports(
        self,
        session: StubSession,
        *,
        created_by: int,
    ) -> None:
        self.called_with = {
            "session": session,
            "created_by": created_by,
        }


def test_run_once_prefetches_reports_for_configured_user(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("REPORT_PREFETCH_ENABLED", "true")
    monkeypatch.setenv("REPORT_PREFETCH_USER_EMAIL", "seeded-user@quartr.dev")
    scheduler = ReportPrefetchScheduler()
    user_service = StubUserService(
        UserRecord(
            id=1,
            email="seeded-user@quartr.dev",
            password_hash="hashed",
            auth_token="token",
        ),
    )
    sec_report_service = StubSecReportService()
    scheduler._user_service = user_service  # type: ignore[assignment]  # pyright: ignore[reportAttributeAccessIssue, reportPrivateUsage]
    scheduler._sec_report_service = sec_report_service  # type: ignore[assignment]  # pyright: ignore[reportAttributeAccessIssue, reportPrivateUsage]
    monkeypatch.setattr(scheduler_module, "SessionLocal", lambda: StubSession())

    asyncio.run(scheduler._run_once())  # pyright: ignore[reportPrivateUsage]

    assert user_service.find_by_email_called_with == "seeded-user@quartr.dev"
    assert sec_report_service.called_with is not None
    assert sec_report_service.called_with["created_by"] == 1
    assert isinstance(sec_report_service.called_with["session"], StubSession)


def test_run_once_skips_prefetch_when_no_user_exists(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("REPORT_PREFETCH_ENABLED", "true")
    scheduler = ReportPrefetchScheduler()
    user_service = StubUserService()
    sec_report_service = StubSecReportService()
    scheduler._user_service = user_service  # type: ignore[assignment]  # pyright: ignore[reportAttributeAccessIssue, reportPrivateUsage]
    scheduler._sec_report_service = sec_report_service  # type: ignore[assignment]  # pyright: ignore[reportAttributeAccessIssue, reportPrivateUsage]
    monkeypatch.setattr(scheduler_module, "SessionLocal", lambda: StubSession())

    asyncio.run(scheduler._run_once())  # pyright: ignore[reportPrivateUsage]

    assert user_service.find_first_called is True
    assert sec_report_service.called_with is None


def test_start_and_stop_manage_background_task(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("REPORT_PREFETCH_ENABLED", "true")
    monkeypatch.setenv("REPORT_PREFETCH_INTERVAL_SECONDS", "60")
    scheduler = ReportPrefetchScheduler()

    async def stub_run_loop() -> None:
        await asyncio.sleep(3600)

    scheduler._run_loop = stub_run_loop  # type: ignore[method-assign]  # pyright: ignore[reportPrivateUsage]

    async def run_scheduler() -> None:
        scheduler.start()
        assert scheduler._task is not None  # pyright: ignore[reportPrivateUsage]
        await scheduler.stop()
        assert scheduler._task is None  # pyright: ignore[reportPrivateUsage]

    asyncio.run(run_scheduler())
