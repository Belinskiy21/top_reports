import logging
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.api.routes import router as health_router
from app.api.v1 import router
from app.services.sec import ReportPrefetchScheduler


def _configure_app_logging() -> None:
    app_logger = logging.getLogger("app")
    if app_logger.handlers:
        return

    handler = logging.StreamHandler()
    handler.setFormatter(logging.Formatter("%(levelname)s: %(message)s"))
    app_logger.addHandler(handler)
    app_logger.setLevel(logging.INFO)
    app_logger.propagate = False


_configure_app_logging()

scheduler = ReportPrefetchScheduler()


@asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncIterator[None]:
    scheduler.start()
    yield
    await scheduler.stop()


app = FastAPI(title="Top Reports", lifespan=lifespan)


app.include_router(health_router)
app.include_router(router)
