import logging

from app.tasks.report_prefetch import run_startup_prefetches


def _configure_logging() -> None:
    logger = logging.getLogger("app.bootstrap_prefetch")
    if logger.handlers:
        return

    handler = logging.StreamHandler()
    handler.setFormatter(logging.Formatter("%(levelname)s: %(message)s"))
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)
    logger.propagate = False


def main() -> None:
    _configure_logging()
    logger = logging.getLogger("app.bootstrap_prefetch")
    logger.info("Starting startup report prefetch")
    run_startup_prefetches()
    logger.info("Startup report prefetch finished")


if __name__ == "__main__":
    main()
