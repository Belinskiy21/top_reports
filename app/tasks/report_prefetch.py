# pyright: reportAny=false, reportMissingTypeStubs=false, reportUnknownMemberType=false, reportUnknownVariableType=false
import asyncio
import logging
import os
from typing import Final

from celery import shared_task
from celery.schedules import crontab

from app.db import SessionLocal
from app.exceptions.sec import SecRequestError
from app.services.sec.sec_report_service import SecReportService
from app.services.user import UserService

logger = logging.getLogger(__name__)

DEFAULT_PREFETCH_USER_EMAIL: Final[str] = "seeded-user@quartr.dev"
DEFAULT_REPORT_SCHEDULES: Final[dict[str, crontab]] = {
    "10-K": crontab(minute=0, hour=3),
}


def build_prefetch_beat_schedule() -> dict[str, dict[str, object]]:
    return {
        f"prefetch-{report_type.lower().replace('-', '_')}": {
            "task": "app.tasks.report_prefetch.prefetch_report_type",
            "schedule": schedule,
            "args": (report_type,),
        }
        for report_type, schedule in DEFAULT_REPORT_SCHEDULES.items()
    }

def resolve_prefetch_user_id() -> int | None:
    user_service = UserService()
    prefetch_user_email = os.getenv(
        "REPORT_PREFETCH_USER_EMAIL",
        DEFAULT_PREFETCH_USER_EMAIL,
    )

    with SessionLocal() as session:
        user = user_service.find_by_email(session, prefetch_user_email)
        if user is None:
            user = user_service.find_first(session)
        if user is None:
            return None
        return user.id


def run_prefetch_report_type(report_type: str) -> None:
    created_by = resolve_prefetch_user_id()
    if created_by is None:
        logger.info("Skipping report prefetch because no user exists")
        return

    logger.info("Starting report prefetch for %s", report_type)
    sec_report_service = SecReportService()
    with SessionLocal() as session:
        try:
            asyncio.run(
                sec_report_service.prefetch_recent_report_type(
                    session,
                    report_type=report_type,
                    created_by=created_by,
                ),
            )
            logger.info("Scheduled SEC prefetch completed for %s", report_type)
        except SecRequestError:
            logger.exception("Scheduled SEC prefetch failed for %s", report_type)


@shared_task(name="app.tasks.report_prefetch.prefetch_report_type")
def prefetch_report_type(report_type: str) -> None:
    run_prefetch_report_type(report_type)


def run_startup_prefetches() -> None:
    for report_type in DEFAULT_REPORT_SCHEDULES:
        run_prefetch_report_type(report_type)
