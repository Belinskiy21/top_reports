# pyright: reportAny=false, reportExplicitAny=false, reportMissingTypeStubs=false
import os
from typing import Any, cast

from celery import Celery

from app.tasks.report_prefetch import build_prefetch_beat_schedule

CELERY_BROKER_URL = os.getenv("CELERY_BROKER_URL", "redis://redis:6379/0")
CELERY_RESULT_BACKEND = os.getenv("CELERY_RESULT_BACKEND", CELERY_BROKER_URL)

celery_app = Celery(
    "top_reports",
    broker=CELERY_BROKER_URL,
    backend=CELERY_RESULT_BACKEND,
)
celery_conf = cast(Any, celery_app.conf)
celery_conf.update(
    timezone=os.getenv("CELERY_TIMEZONE", "UTC"),
    beat_schedule=build_prefetch_beat_schedule(),
    task_default_queue="top_reports",
)
_ = cast(Any, celery_app).autodiscover_tasks(["app.tasks"])
