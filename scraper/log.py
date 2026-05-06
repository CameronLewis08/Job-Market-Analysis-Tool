from __future__ import annotations

import logging
import os
import sys


def configure_logging() -> None:
    level = os.getenv("LOG_LEVEL", "INFO").upper()
    logging.basicConfig(
        level=level,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    # playwright and urllib3 can be noisy at DEBUG level — suppress them
    for noisy in ("playwright", "urllib3"):
        logging.getLogger(noisy).setLevel(logging.WARNING)


def get_logger(name: str) -> logging.Logger:
    return logging.getLogger(name)


def validate_env() -> str:
    url = os.getenv("DATABASE_URL")
    if not url:
        logging.getLogger(__name__).critical("DATABASE_URL is not set — aborting")
        sys.exit(1)
    return url
