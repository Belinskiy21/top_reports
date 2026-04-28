import pytest

from app.tasks import report_prefetch


def test_build_prefetch_beat_schedule_contains_ten_k() -> None:
    schedule = report_prefetch.build_prefetch_beat_schedule()

    assert "prefetch-10_k" in schedule
    assert schedule["prefetch-10_k"]["task"] == "app.tasks.report_prefetch.prefetch_report_type"
    assert schedule["prefetch-10_k"]["args"] == ("10-K",)


def test_run_prefetch_report_type_skips_when_no_user_exists(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(report_prefetch, "resolve_prefetch_user_id", lambda: None)

    report_prefetch.run_prefetch_report_type("10-K")


def test_run_prefetch_report_type_prefetches_selected_type(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    calls: list[dict[str, object]] = []

    class StubSecReportService:
        async def prefetch_recent_report_type(
            self,
            session: object,
            *,
            report_type: str,
            created_by: int,
        ) -> None:
            calls.append(
                {
                "session": session,
                "report_type": report_type,
                "created_by": created_by,
                },
            )

    class StubSession:
        def __enter__(self) -> StubSession:
            return self

        def __exit__(self, exc_type: object, exc: object, traceback: object) -> None:
            _ = exc_type
            _ = exc
            _ = traceback

    monkeypatch.setattr(report_prefetch, "resolve_prefetch_user_id", lambda: 7)
    monkeypatch.setattr(report_prefetch, "SecReportService", StubSecReportService)
    monkeypatch.setattr(report_prefetch, "SessionLocal", lambda: StubSession())

    report_prefetch.run_prefetch_report_type("10-K")

    assert len(calls) == 1
    assert calls[0]["report_type"] == "10-K"
    assert calls[0]["created_by"] == 7
    assert isinstance(calls[0]["session"], StubSession)


def test_run_startup_prefetches_runs_all_configured_report_types(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    called_with: list[str] = []

    def stub_run_prefetch_report_type(report_type: str) -> None:
        called_with.append(report_type)

    monkeypatch.setattr(
        report_prefetch,
        "run_prefetch_report_type",
        stub_run_prefetch_report_type,
    )

    report_prefetch.run_startup_prefetches()

    assert called_with == ["10-K"]
